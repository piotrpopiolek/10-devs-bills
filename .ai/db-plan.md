# Schemat bazy danych PostgreSQL - Bills MVP

## 1. Lista tabel z kolumnami, typami danych i ograniczeniami

### Tabela: users

This table is managed by Supabase Auth.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    external_id BIGINT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX idx_users_external_id ON users(external_id);
```

### Tabela: shops

```sql
CREATE TABLE shops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_shop_name_address UNIQUE (LOWER(name), LOWER(COALESCE(address, '')))
);

CREATE INDEX idx_shops_name ON shops(LOWER(name));
```

### Tabela: categories

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
```

### Tabela: indexes (słownik produktów)

```sql
CREATE TABLE indexes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    synonyms JSONB,
    category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_indexes_name ON indexes(name);
CREATE INDEX idx_indexes_category_id ON indexes(category_id);
CREATE INDEX idx_indexes_synonyms ON indexes USING GIN(synonyms);
```

### Tabela: index_aliases (warianty OCR)

```sql
CREATE TABLE index_aliases (
    id SERIAL PRIMARY KEY,
    raw_name TEXT NOT NULL,
    index_id INTEGER NOT NULL REFERENCES indexes(id) ON DELETE CASCADE,
    confirmations_count INTEGER NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    locale VARCHAR(10),
    shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_raw_name_index UNIQUE (LOWER(raw_name), index_id)
);

CREATE INDEX idx_index_aliases_index_id ON index_aliases(index_id);
CREATE INDEX idx_index_aliases_shop_id ON index_aliases(shop_id);
CREATE INDEX idx_index_aliases_user_id ON index_aliases(user_id);
CREATE INDEX idx_index_aliases_raw_name ON index_aliases USING GIN(LOWER(raw_name) gin_trgm_ops);
```

### Tabela: bills

```sql
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'error');

CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    bill_date TIMESTAMPTZ NOT NULL,
    total_amount NUMERIC(12,2),
    image_url TEXT,
    image_hash VARCHAR(64),
    image_expires_at TIMESTAMPTZ,
    image_status VARCHAR(50) DEFAULT 'active',
    status processing_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_total_amount_positive CHECK (total_amount >= 0)
);

CREATE INDEX idx_bills_user_id_bill_date ON bills(user_id, bill_date DESC);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_shop_id ON bills(shop_id);
CREATE INDEX idx_bills_image_expires_at ON bills(image_expires_at) WHERE image_expires_at IS NOT NULL;
```

### Tabela: bill_items

```sql
CREATE TYPE verification_source AS ENUM ('auto', 'user', 'admin');

CREATE TABLE bill_items (
    id SERIAL PRIMARY KEY,
    quantity NUMERIC(10,4) NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    total_price NUMERIC(12,2) NOT NULL,
    original_text TEXT,
    confidence_score DECIMAL(3,2),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_source verification_source NOT NULL DEFAULT 'auto',
    bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    index_id INTEGER REFERENCES indexes(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_quantity_positive CHECK (quantity > 0),
    CONSTRAINT check_unit_price_non_negative CHECK (unit_price >= 0),
    CONSTRAINT check_total_price_calculation CHECK (total_price = ROUND(quantity * unit_price, 2))
);

CREATE INDEX idx_bill_items_bill_id ON bill_items(bill_id);
CREATE INDEX idx_bill_items_index_id ON bill_items(index_id);
CREATE INDEX idx_bill_items_unverified ON bill_items(bill_id) WHERE is_verified = FALSE;
```

### Tabela: telegram_messages

```sql
CREATE TYPE telegram_message_status AS ENUM ('sent', 'delivered', 'read', 'failed');
CREATE TYPE telegram_message_type AS ENUM ('text', 'photo', 'document', 'audio', 'video', 'voice', 'sticker');

CREATE TABLE telegram_messages (
    id SERIAL PRIMARY KEY,
    telegram_message_id BIGINT NOT NULL UNIQUE,
    chat_id BIGINT NOT NULL,
    message_type telegram_message_type NOT NULL,
    content TEXT NOT NULL,
    file_id VARCHAR(255),
    file_path TEXT,
    status telegram_message_status NOT NULL DEFAULT 'sent',
    error_message TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bill_id INTEGER REFERENCES bills(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_telegram_messages_telegram_id ON telegram_messages(telegram_message_id);
CREATE INDEX idx_telegram_messages_chat_id_created_at ON telegram_messages(chat_id, created_at DESC);
CREATE INDEX idx_telegram_messages_user_id ON telegram_messages(user_id);
CREATE INDEX idx_telegram_messages_bill_id ON telegram_messages(bill_id);
```

## 2. Relacje między tabelami

### Relacje jeden-do-wielu:

- `users` (1) → `bills` (N) przez `bills.user_id`
- `users` (1) → `telegram_messages` (N) przez `telegram_messages.user_id`
- `shops` (1) → `bills` (N) przez `bills.shop_id`
- `bills` (1) → `bill_items` (N) przez `bill_items.bill_id`
- `indexes` (1) → `bill_items` (N) przez `bill_items.index_id`
- `indexes` (1) → `index_aliases` (N) przez `index_aliases.index_id`
- `categories` (1) → `indexes` (N) przez `indexes.category_id`
- `categories` (1) → `categories` (N) przez `categories.parent_id` (hierarchia)
- `telegram_messages` (N) → `bills` (1) przez `telegram_messages.bill_id` (opcjonalna)

### Relacje opcjonalne:

- `shops` (1) → `index_aliases` (N) przez `index_aliases.shop_id`
- `users` (1) → `index_aliases` (N) przez `index_aliases.user_id`

## 3. Indeksy

### Indeksy kluczowe dla wydajności:

- `idx_users_external_id` - szybkie wyszukiwanie użytkowników po ID Telegram
- `idx_bills_user_id_bill_date` - raporty wydatków użytkownika
- `idx_bills_status` - filtrowanie rachunków według statusu przetwarzania
- `idx_bill_items_unverified` - workflow weryfikacji pozycji
- `idx_telegram_messages_chat_id_created_at` - historia wiadomości w czacie
- `idx_index_aliases_raw_name` - wyszukiwanie aliasów produktów (GIN z pg_trgm)

### Indeksy wspierające:

- `idx_shops_name` - wyszukiwanie sklepów
- `idx_categories_parent_id` - nawigacja hierarchii kategorii
- `idx_indexes_category_id` - produkty w kategorii
- `idx_bills_image_expires_at` - retencja obrazów

## 4. Zasady PostgreSQL (RLS)

**Decyzja:** Nie używamy RLS (Row Level Security). Kontrola dostępu jest wymuszana na poziomie aplikacji (FastAPI) poprzez konsekwentne filtrowanie po `user_id` w każdej operacji.

## 5. Dodatkowe uwagi i wyjaśnienia

### Walidacja danych:

- **Kwoty:** `NUMERIC(12,2)` dla PLN z dokładnością do groszy
- **Ilości:** `NUMERIC(10,4)` dla precyzyjnych pomiarów (kg, litry)
- **Walidacja sum:** CHECK constraint zapewnia `total_price = ROUND(quantity * unit_price, 2)`
- **Walidacja pozytywności:** CHECK constraints dla `quantity > 0` i `unit_price >= 0`

### Retencja obrazów:

- Obrazy paragonów przechowywane maksymalnie 6 miesięcy
- Kolumny `image_expires_at` i `image_status` do zarządzania cyklem życia
- Indeks `idx_bills_image_expires_at` dla joba czyszczącego

### Słownik produktów:

- Tabela `indexes` jako "złota lista" znormalizowanych produktów
- Tabela `index_aliases` dla wariantów OCR z licznikiem potwierdzeń
- Unikalność `(LOWER(raw_name), index_id)` zapobiega duplikatom
- GIN indeks z pg_trgm dla szybkiego wyszukiwania podobnych nazw

### Hierarchia kategorii:

- `parent_id` w tabeli `categories` umożliwia drzewiastą strukturę
- `ON DELETE RESTRICT` zapobiega usuwaniu kategorii z przypisanymi produktami
- Wymagany trigger/constraint do zapobiegania cyklom w hierarchii

### Skalowalność:

- Partycjonowanie `telegram_messages` miesięcznie (opcjonalne przy dużym wolumenie)
- Indeksy częściowe dla niezweryfikowanych pozycji
- Optymalizacja zapytań raportowych przez indeksy złożone

### Bezpieczeństwo:

- Wszystkie operacje filtrowane po `user_id` w aplikacji
- Brak przechowywania danych osobowych zgodnie z PRD
- Walidacja sum rachunków vs pozycji na poziomie aplikacji
