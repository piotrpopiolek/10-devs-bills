from typing import Sequence, List, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.common.services import AppService
from src.bill_items.models import BillItem, VerificationSource
from src.bill_items.schemas import BillItemCreate, BillItemUpdate
from src.common.exceptions import ResourceNotFoundError, BillAccessDeniedError
from src.bills.models import Bill
from src.product_indexes.models import ProductIndex


class BillItemService(AppService[BillItem, BillItemCreate, BillItemUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=BillItem, session=session)

    async def create(self, data: BillItemCreate) -> BillItem:
        # Bill Existence Check (Referential Integrity check before DB hit)
        await self._ensure_exists(model=Bill, field=Bill.id, value=data.bill_id, resource_name="Bill")

        # ProductIndex Existence Check (if provided)
        if data.index_id:
            await self._ensure_exists(model=ProductIndex, field=ProductIndex.id, value=data.index_id, resource_name="ProductIndex")

        # Object Construction
        new_bill_item = BillItem(
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=data.total_price,
            is_verified=data.is_verified,
            verification_source=data.verification_source,
            bill_id=data.bill_id,
            index_id=data.index_id,
            original_text=data.original_text,
            confidence_score=data.confidence_score,
            category_id=data.category_id
        )

        # Persistence (Unit of Work)
        self.session.add(new_bill_item)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_bill_item)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return new_bill_item

    async def update(self, bill_item_id: int, data: BillItemUpdate, user_id: Optional[int] = None) -> BillItem:
        """
        Aktualizuje BillItem z opcjonalną weryfikacją ownership.
        
        Most Koncepcyjny (PHP → Python):
        W Symfony/Laravel używałbyś ParamConverter lub Form Request z walidacją ownership.
        W FastAPI wstrzykujemy user_id jako parametr i sprawdzamy ownership przez relację Bill -> user_id.
        To idiomatyczne podejście w Pythonie - jawne sprawdzenie uprawnień w serwisie.
        
        Args:
            bill_item_id: ID BillItem do aktualizacji
            data: Dane do aktualizacji
            user_id: Opcjonalny ID użytkownika do weryfikacji ownership (jeśli None, pomija sprawdzenie)
            
        Returns:
            BillItem: Zaktualizowany obiekt
            
        Raises:
            ResourceNotFoundError: Jeśli BillItem nie istnieje
            BillAccessDeniedError: Jeśli user_id podane i BillItem nie należy do użytkownika
        """
        bill_item = await self.get_by_id(bill_item_id)
        
        # Ownership verification (jeśli user_id podane)
        if user_id is not None:
            # Pobierz Bill przez relację i sprawdź user_id
            stmt = select(Bill).where(Bill.id == bill_item.bill_id)
            result = await self.session.execute(stmt)
            bill = result.scalar_one_or_none()
            
            if not bill:
                raise ResourceNotFoundError("Bill", bill_item.bill_id)
            
            if bill.user_id != user_id:
                raise BillAccessDeniedError(bill_item.bill_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return bill_item

        # Bill Existence Check (if bill_id is being updated)
        if "bill_id" in update_data and update_data["bill_id"] != bill_item.bill_id:
            await self._ensure_exists(model=Bill, field=Bill.id, value=update_data["bill_id"], resource_name="Bill")

        # ProductIndex Existence Check (if index_id is being updated)
        if "index_id" in update_data and update_data["index_id"] != bill_item.index_id:
            new_index_id = update_data["index_id"]
            if new_index_id is not None:
                await self._ensure_exists(model=ProductIndex, field=ProductIndex.id, value=new_index_id, resource_name="ProductIndex")

        # Apply updates
        for key, value in update_data.items():
            setattr(bill_item, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(bill_item)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return bill_item
    
    async def find_unindexed_verified_items_for_candidate(
        self,
        candidate_representative_name: str,
        candidate_category_id: Optional[int],
        fuzzy_threshold: float
    ) -> List[BillItem]:
        """
        Znajduje wszystkie zweryfikowane BillItems, które fuzzy matchują kandydata.
        
        Używa PostgreSQL similarity() z pg_trgm do fuzzy matching.
        Zwraca tylko BillItems, które:
        - Są zweryfikowane przez użytkownika (is_verified=True, verification_source='user')
        - Nie mają jeszcze przypisanego ProductIndex (index_id IS NULL)
        - Fuzzy matchują representative_name kandydata (similarity >= threshold)
        - Opcjonalnie: mają tę samą kategorię (jeśli candidate_category_id podane)
        
        Most Koncepcyjny (PHP → Python):
        W Doctrine (Symfony) używałbyś DQL z funkcją podobieństwa lub natywnego SQL.
        W SQLAlchemy używamy func.similarity() z pg_trgm - idiomatyczne dla PostgreSQL.
        
        Args:
            candidate_representative_name: Reprezentatywna nazwa kandydata do porównania
            candidate_category_id: Opcjonalna kategoria do filtrowania (jeśli None, pomija filtrowanie)
            fuzzy_threshold: Próg podobieństwa (0.0-1.0) dla fuzzy matching
            
        Returns:
            List[BillItem]: Lista znalezionych BillItems
        """
        stmt = (
            select(BillItem)
            .options(selectinload(BillItem.bill))  # Eager load relacji bill
            .where(
                BillItem.is_verified == True,
                BillItem.verification_source == VerificationSource.USER.value,
                BillItem.index_id.is_(None),
                func.similarity(func.lower(BillItem.original_text), func.lower(candidate_representative_name)) >= fuzzy_threshold
            )
        )
        
        # Opcjonalne filtrowanie po kategorii
        if candidate_category_id is not None:
            stmt = stmt.where(BillItem.category_id == candidate_category_id)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def bulk_update_index_id(self, bill_item_ids: List[int], new_product_index_id: int) -> int:
        """
        Masowo aktualizuje index_id dla listy BillItems.
        
        Most Koncepcyjny (PHP → Python):
        W Doctrine używałbyś QueryBuilder z WHERE IN i executeUpdate().
        W SQLAlchemy używamy update() z where() - bardziej idiomatyczne dla bulk operations.
        
        Args:
            bill_item_ids: Lista ID BillItems do aktualizacji
            new_product_index_id: Nowy ProductIndex ID do przypisania
            
        Returns:
            int: Liczba zaktualizowanych rekordów
            
        Raises:
            ResourceNotFoundError: Jeśli ProductIndex nie istnieje
        """
        if not bill_item_ids:
            return 0
        
        # Sprawdź czy ProductIndex istnieje
        await self._ensure_exists(
            model=ProductIndex,
            field=ProductIndex.id,
            value=new_product_index_id,
            resource_name="ProductIndex"
        )
        
        stmt = (
            update(BillItem)
            .where(BillItem.id.in_(bill_item_ids))
            .values(index_id=new_product_index_id)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount

    async def get_by_bill_id(
        self, 
        bill_id: int, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> dict[str, Any]:
        """
        Pobiera wszystkie pozycje dla konkretnego rachunku z weryfikacją ownership.
        
        Most Koncepcyjny (PHP → Python):
        W Symfony używałbyś ParamConverter do automatycznej weryfikacji ownership.
        W FastAPI wstrzykujemy user_id i sprawdzamy przez relację Bill -> user_id.
        To idiomatyczne podejście w Pythonie - jawne sprawdzenie uprawnień w serwisie.
        
        Args:
            bill_id: ID rachunku
            user_id: ID użytkownika (do weryfikacji ownership)
            skip: Liczba pozycji do pominięcia (paginacja)
            limit: Maksymalna liczba pozycji do zwrócenia
            
        Returns:
            Dictionary z paginowanymi pozycjami i metadanymi
            
        Raises:
            ResourceNotFoundError: Jeśli rachunek nie istnieje
            BillAccessDeniedError: Jeśli rachunek nie należy do użytkownika
        """
        # Weryfikacja ownership: sprawdź czy Bill istnieje i należy do user_id
        stmt = select(Bill).where(Bill.id == bill_id)
        result = await self.session.execute(stmt)
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise ResourceNotFoundError("Bill", bill_id)
        
        if bill.user_id != user_id:
            raise BillAccessDeniedError(bill_id)
        
        # Count total items for this bill
        count_stmt = (
            select(func.count())
            .select_from(BillItem)
            .where(BillItem.bill_id == bill_id)
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Fetch items with eager loading relacji (index, category)
        stmt = (
            select(BillItem)
            .options(
                selectinload(BillItem.index),  # Eager load ProductIndex
                selectinload(BillItem.category)  # Eager load Category
            )
            .where(BillItem.bill_id == bill_id)
            .offset(skip)
            .limit(limit)
            .order_by(BillItem.id)
        )
        
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def delete(self, bill_item_id: int) -> None:
        bill_item = await self.get_by_id(bill_item_id)
        
        self.session.delete(bill_item)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

