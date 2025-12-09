# Plan Implementacji Middleware do Logowania Wiadomości Telegram

## 1. Cel

Celem jest automatyczne logowanie wszystkich wiadomości przychodzących (od użytkownika) i wychodzących (od bota) do bazy danych, bez konieczności modyfikowania każdego handlera z osobna. Ma to na celu:

- Eliminację duplikacji kodu (DRY).
- Centralizację logiki logowania.
- Ułatwienie audytu i debugowania.

## 2. Analiza Obecnej Sytuacji

- **Biblioteka:** Projekt używa `python-telegram-bot` (PTB).
- **Struktura:**
  - `TelegramBotService` (singleton) zarządza aplikacją.
  - Handlery są w `src/telegram/handlers.py`.
  - Sesja DB jest wstrzykiwana przez `src/telegram/context.py` (ContextVar).
- **Model Danych:** Tabela `telegram_messages` wymaga `user_id` (FK do tabeli `users`), co oznacza, że musimy zidentyfikować użytkownika w systemie przed zapisaniem logu.

## 3. Strategia Implementacji

### 3.1. Wiadomości Przychodzące (Middleware)

Wykorzystamy mechanizm `TypeHandler` lub `MessageHandler` z niskim priorytetem (grupa -1) w `python-telegram-bot`. Ten handler uruchomi się przed właściwymi handlerami komend/wiadomości.

**Zadania middleware'u:**

1.  Pobrać `telegram_id` z obiektu `Update`.
2.  Uzyskać sesję DB (z `get_db_session`).
3.  Pobrać lub utworzyć użytkownika w DB (`AuthService`).
4.  Zapisać obiekt `User` w `context.user_data['db_user']` (optymalizacja dla kolejnych handlerów).
5.  Zapisać treść wiadomości przychodzącej do tabeli `telegram_messages`.
6.  Zezwolić na dalsze przetwarzanie (nie blokować potoku).

### 3.2. Wiadomości Wychodzące (Custom Bot)

PTB nie posiada globalnego middleware dla wiadomości wychodzących. Najlepszym podejściem "Pythonic" jest stworzenie własnej klasy dziedziczącej po `telegram.Bot` (np. `LoggingBot`) i nadpisanie metod wysyłających wiadomości (`send_message`, `send_photo` itp.).

**Zadania `LoggingBot`:**

1.  Przechwycić wywołanie metody (np. `send_message`).
2.  Wywołać oryginalną metodę (`super().send_message(...)`), aby wysłać wiadomość do Telegrama i otrzymać obiekt `Message` (z nowym ID).
3.  Pobrać sesję DB.
4.  Znaleźć `user_id` na podstawie `chat_id` (lub wykorzystać cache/kontekst).
5.  Zapisać wiadomość wychodzącą w `telegram_messages` używając danych ze zwróconego obiektu `Message`.

## 4. Plan Krok po Kroku

### Krok 1: Przygotowanie Serwisu Logowania (`TelegramLoggingService`)

Utworzenie serwisu w `src/telegram_messages/services.py`, który będzie zawierał logikę biznesową zapisu do bazy:

- `log_incoming_message(update: Update, user: User)`
- `log_outgoing_message(message: Message, user_id: int)`

### Krok 2: Implementacja `LoggingBot`

Stworzenie klasy w `src/telegram/bot.py` (nowy plik):

```python
class LoggingBot(Bot):
    async def send_message(self, chat_id, text, *args, **kwargs):
        result = await super().send_message(chat_id, text, *args, **kwargs)
        # Fire-and-forget logowanie lub await w zależności od wymagań
        await self._log_message(result, chat_id)
        return result

    # Analogicznie dla send_photo, reply_text (używa send_message) itp.
```

### Krok 3: Implementacja Middleware dla Przychodzących

Stworzenie funkcji `logging_middleware` w `src/telegram/middleware.py` (nowy plik):

```python
async def logging_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Logika pobrania usera i zapisu
    # ...
```

### Krok 4: Rejestracja w `TelegramBotService`

Modyfikacja `src/telegram/services.py`:

- Przy budowaniu `Application`: użyć `.bot(LoggingBot(token=...))`.
- Przy rejestracji handlerów: dodać `logging_middleware` do grupy -1.

### Krok 5: Refaktoryzacja Handlerów

Aktualizacja istniejących handlerów w `src/telegram/handlers.py`, aby korzystały z `context.user_data['db_user']` zamiast samodzielnie wołać `auth_service.get_or_create_user...`.

## 5. Wyzwania i Rozwiązania

- **Sesja DB w `LoggingBot`:** Ponieważ `LoggingBot` działa w kontekście requestu FastAPI (webhook), sesja jest dostępna przez `src.telegram.context.get_db_session()`.
- **User ID dla wychodzących:** Metoda `send_message` przyjmuje `chat_id`. Musimy mapować `chat_id` -> `user_id`. Można to zrobić szybkim zapytaniem do DB (skoro mamy sesję) lub cache'ować to w `context` jeśli wysyłka następuje w trakcie obsługi Update'u.

## 6. Struktura Plików

Planowane zmiany w strukturze:

- `src/telegram/bot.py` (Nowy: Custom Bot class)
- `src/telegram/middleware.py` (Nowy: Incoming middleware)
- `src/telegram_messages/services.py` (Nowy/Update: Logika zapisu)
- `src/telegram/services.py` (Modyfikacja: Konfiguracja aplikacji)
