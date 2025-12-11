import re
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.ai.schemas import NormalizedItem
from src.ai.exceptions import CategorizationError
from src.ocr.schemas import OCRItem
from src.product_indexes.models import ProductIndex
from src.product_index_aliases.models import ProductIndexAlias
from src.product_indexes.services import ProductIndexService
from src.product_index_aliases.services import ProductIndexAliasService
from src.categories.services import CategoryService


class AICategorizationService:
    """
    Serwis odpowiedzialny za kategoryzację i normalizację produktów z OCR.

    """
    
    def __init__(
        self,
        session: AsyncSession,
        product_index_service: ProductIndexService,
        alias_service: ProductIndexAliasService,
        category_service: CategoryService
    ):
        """
        Inicjalizacja serwisu z wstrzyknięciem zależności.
        
        Args:
            session: SQLAlchemy async session (do ręcznych zapytań)
            product_index_service: Serwis do zarządzania produktami
            alias_service: Serwis do zarządzania aliasami
            category_service: Serwis do zarządzania kategoriami
        """
        self.session = session
        self.product_index_service = product_index_service
        self.alias_service = alias_service
        self.category_service = category_service

    def _preprocess_text(self, raw_text: str) -> str:
        """
        Cleans text from OCR noise.
        1. Whitespace normalization (remove double spaces)
        2. Symbol removal (remove weird characters at ends, e.g., _, #)
        3. Decimal normalization (replace , with . in numbers)
        """
        if not raw_text:
            return ""

        # 1. Whitespace normalization
        text = " ".join(raw_text.split())

        # 2. Symbol removal (leading/trailing specific noise characters)
        # Removing common OCR artifacts from ends: _ # - * | \ /
        text = text.strip(" _#-*|\\/")

        # 3. Decimal normalization (replace , with . in numbers)
        # Regex to find comma between digits: (\d),(\d) -> \1.\2
        text = re.sub(r'(\d),(\d)', r'\1.\2', text)

        return text.strip()

    async def _find_by_alias(
        self,
        cleaned_text: str,
        shop_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Optional[ProductIndex]:
        """
        Wyszukuje produkt w aliasach z priorytetyzacją (User+Shop -> Shop -> Global).
        
        Strategia (MVP - 3 zapytania):
        1. Próba User+Shop (jeśli oba dostępne) - najwyższy priorytet
        2. Próba Shop (jeśli dostępny) - średni priorytet
        3. Próba Global (user_id=NULL, shop_id=NULL) - najniższy priorytet
        
        Indeks: LOWER(raw_name) - wyszukiwanie case-insensitive
        
        Args:
            cleaned_text: Wyczyszczony tekst po pre-processingu
            shop_id: ID sklepu (opcjonalne)
            user_id: ID użytkownika (opcjonalne)
            
        Returns:
            ProductIndex jeśli znaleziono alias, None w przeciwnym razie
        """
        # Próba 1: User+Shop (najwyższy priorytet)
        if user_id and shop_id:
            stmt = (
                select(ProductIndex)
                .join(ProductIndexAlias, ProductIndex.id == ProductIndexAlias.index_id)
                .where(
                    func.lower(ProductIndexAlias.raw_name) == func.lower(cleaned_text),
                    ProductIndexAlias.user_id == user_id,
                    ProductIndexAlias.shop_id == shop_id
                )
                .order_by(ProductIndexAlias.confirmations_count.desc())
                .limit(1)
            )
            result = await self.session.execute(stmt)
            product = result.scalar_one_or_none()
            if product:
                return product

        # Próba 2: Shop (średni priorytet)
        if shop_id:
            stmt = (
                select(ProductIndex)
                .join(ProductIndexAlias, ProductIndex.id == ProductIndexAlias.index_id)
                .where(
                    func.lower(ProductIndexAlias.raw_name) == func.lower(cleaned_text),
                    ProductIndexAlias.shop_id == shop_id,
                    ProductIndexAlias.user_id.is_(None)
                )
                .order_by(ProductIndexAlias.confirmations_count.desc())
                .limit(1)
            )
            result = await self.session.execute(stmt)
            product = result.scalar_one_or_none()
            if product:
                return product

        # Próba 3: Global (najniższy priorytet)
        stmt = (
            select(ProductIndex)
            .join(ProductIndexAlias, ProductIndex.id == ProductIndexAlias.index_id)
            .where(
                func.lower(ProductIndexAlias.raw_name) == func.lower(cleaned_text),
                ProductIndexAlias.user_id.is_(None),
                ProductIndexAlias.shop_id.is_(None)
            )
            .order_by(ProductIndexAlias.confirmations_count.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _fuzzy_search_product(
        self,
        cleaned_text: str,
        category_suggestion: Optional[str] = None
    ) -> Optional[ProductIndex]:
        """
        Wyszukuje produkt używając fuzzy search (PostgreSQL pg_trgm).
        
        Strategia [MVP]:
        1. Dynamiczny threshold: dla krótkich słów (<5 znaków) wyższy threshold (0.9)
        2. Bazowy threshold: 0.75 (zwiększony z 0.6 dla lepszej precyzji)
        3. Opcjonalnie: filtrowanie po kategorii (jeśli category_suggestion dostępna)
        
        Indeks: idx_product_indexes_name_trgm (GIN trigram)
        
        Args:
            cleaned_text: Wyczyszczony tekst po pre-processingu
            category_suggestion: Opcjonalna sugestia kategorii z OCR/LLM
            
        Returns:
            ProductIndex jeśli znaleziono match, None w przeciwnym razie
        """
        # Dynamiczny threshold dla krótkich słów
        word_length = len(cleaned_text)
        if word_length < settings.AI_MIN_WORD_LENGTH_STRICT:
            threshold = settings.AI_STRICT_THRESHOLD
        else:
            threshold = settings.AI_SIMILARITY_THRESHOLD

        # PostgreSQL similarity search with pg_trgm
        # Używamy similarity() zamiast operatora %, aby móc kontrolować threshold w query
        stmt = (
            select(
                ProductIndex,
                func.similarity(ProductIndex.name, cleaned_text).label('score')
            )
            .where(func.similarity(ProductIndex.name, cleaned_text) >= threshold)
            .order_by(func.similarity(ProductIndex.name, cleaned_text).desc())
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        row = result.first()
        
        return row[0] if row else None

    async def normalize_item(
        self,
        ocr_item: OCRItem,
        shop_id: Optional[int] = None,
        user_id: Optional[int] = None,
        save_alias: bool = True
    ) -> NormalizedItem:
        """
        Główna metoda normalizacji produktu z OCR.
        
        Workflow:
        1. Pre-processing (czyszczenie tekstu)
        2. Wyszukiwanie w aliasach (priorytet: User+Shop -> Shop -> Global)
        3. Jeśli nie znaleziono: Fuzzy search w ProductIndex
        4. Jeśli nie znaleziono: Fallback do kategorii "Inne"
        5. Opcjonalnie: Zapisanie nowego aliasu (UPSERT)
        
        Args:
            ocr_item: Pozycja z OCR (surowe dane)
            shop_id: ID sklepu (dla kontekstu aliasów)
            user_id: ID użytkownika (dla kontekstu aliasów)
            save_alias: Czy zapisać alias po normalizacji (domyślnie True)
            
        Returns:
            NormalizedItem: Znormalizowana pozycja gotowa do zapisu jako BillItem
            
        Raises:
            CategorizationError: W przypadku krytycznego błędu kategoryzacji
        """
        # Step 0: Pre-processing
        cleaned_text = self._preprocess_text(ocr_item.name)
        
        if not cleaned_text:
            # Pusty tekst po czyszczeniu - fallback
            fallback_category = await self.category_service.get_fallback_category()
            return NormalizedItem(
                original_text=ocr_item.name,
                normalized_name=None,
                quantity=ocr_item.quantity,
                unit_price=ocr_item.unit_price or Decimal("0.0"),
                total_price=ocr_item.total_price,
                category_id=fallback_category.id,
                product_index_id=None,
                confidence_score=0.0,
                is_confident=False
            )

        # Step 1: Szukaj w aliasach
        product_from_alias = await self._find_by_alias(cleaned_text, shop_id, user_id)
        
        if product_from_alias:
            # Znaleziono w aliasach - najwyższa pewność
            return NormalizedItem(
                original_text=ocr_item.name,
                normalized_name=product_from_alias.name,
                quantity=ocr_item.quantity,
                unit_price=ocr_item.unit_price or Decimal("0.0"),
                total_price=ocr_item.total_price,
                category_id=product_from_alias.category_id,
                product_index_id=product_from_alias.id,
                confidence_score=1.0,
                is_confident=True
            )

        # Step 2: Fuzzy search w ProductIndex
        product_from_fuzzy = await self._fuzzy_search_product(
            cleaned_text,
            ocr_item.category_suggestion
        )
        
        if product_from_fuzzy:
            # Znaleziono przez fuzzy search - średnia pewność
            # Opcjonalnie zapisz nowy alias (uczenie się systemu)
            if save_alias:
                try:
                    await self.alias_service.upsert_alias(
                        raw_name=cleaned_text,
                        index_id=product_from_fuzzy.id,
                        shop_id=shop_id,
                        user_id=user_id
                    )
                except Exception as e:
                    # Log error, ale nie przerywaj procesu
                    # (alias nie jest krytyczny dla normalizacji)
                    pass
            
            return NormalizedItem(
                original_text=ocr_item.name,
                normalized_name=product_from_fuzzy.name,
                quantity=ocr_item.quantity,
                unit_price=ocr_item.unit_price or Decimal("0.0"),
                total_price=ocr_item.total_price,
                category_id=product_from_fuzzy.category_id,
                product_index_id=product_from_fuzzy.id,
                confidence_score=ocr_item.confidence_score * 0.8,  # Fuzzy match penalty
                is_confident=True
            )

        # Step 3: Fallback - produkt nieznany systemowi
        fallback_category = await self.category_service.get_fallback_category()
        
        return NormalizedItem(
            original_text=ocr_item.name,
            normalized_name=None,
            quantity=ocr_item.quantity,
            unit_price=ocr_item.unit_price or Decimal("0.0"),
            total_price=ocr_item.total_price,
            category_id=fallback_category.id,
            product_index_id=None,
            confidence_score=ocr_item.confidence_score * 0.5,  # Unknown product penalty
            is_confident=False
        )

