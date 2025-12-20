Faza 0: Przygotowanie Struktury Monorepo
Zanim dotkniesz serwerów, musisz uporządkować repozytorium, aby CI/CD "rozumiało", co gdzie leży.

[ ] Standaryzacja struktury katalogów: Upewnij się, że repozytorium wygląda tak:

Plaintext

/ (root)
├── .github/workflows/ # Tutaj trafią pliki YAML dla Actions
├── backend/ # Cały kod FastAPI + Dockerfile backendu
├── astro/ # Cały kod Astro/React + Dockerfile frontendu + nginx.conf
└── README.md
[ ] Pliki .dockerignore: Stwórz osobny .dockerignore w folderze backend/ i astro/, aby nie kopiować do kontenerów śmieci (np. node_modules, .venv, .git, **pycache**).

Faza 1: Konteneryzacja (Docker)
Railway uwielbia Dockera. To Twoja gwarancja, że "działa u mnie" = "działa na produkcji".

1.1. Backend (FastAPI)
[ ] Stwórz backend/Dockerfile:

Baza: python:3.11-slim.

Ustaw WORKDIR /app.

Zainstaluj zależności (najlepiej rozdzielając COPY requirements.txt . od COPY . . dla cache'owania warstw).

Uruchomienie: CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"].

[ ] Telegram Webhook:

✅ **JUŻ ZAIMPLEMENTOWANE**: Projekt już używa webhooków (TelegramBotService.process_webhook_update). Webhook jest dostępny pod endpointem `/api/v1/webhooks/telegram`. W produkcji upewnij się, że:

- TELEGRAM_WEBHOOK_URL jest ustawione na publiczny URL backendu (np. https://backend-production.up.railway.app/api/v1/webhooks/telegram)
- TELEGRAM_WEBHOOK_SECRET jest ustawione dla bezpieczeństwa
- Webhook jest zarejestrowany w Telegramie (można to zrobić przez API lub dashboard Telegram)

  1.2. Frontend (Astro + Nginx)
  To kluczowy punkt. Nginx będzie serwował pliki statyczne ORAZ działał jako bramka do API.

[ ] Stwórz astro/nginx.conf:

Skonfiguruj blok server, który:

Obsługuje pliki statyczne (root /usr/share/nginx/html).

Obsługuje routing SPA (try_files $uri $uri/ /index.html).

Proxy do backendu: Przekierowuje location /api/ do serwisu backendu wewnątrz sieci Railway.

[ ] Stwórz astro/Dockerfile (Multi-stage):

Stage 1 (Build): Obraz node:20. Wykonaj npm install i npm run build.

Stage 2 (Run): Obraz nginx:alpine. Skopiuj folder dist/ ze Stage 1 do katalogu html Nginxa. Skopiuj też swój nginx.conf.

Faza 2: Baza Danych (Supabase)
[ ] Tryb Transakcyjny (Pooler):

W panelu Supabase przejdź do Database -> Connection Pooling.

Skopiuj Transaction Pooler URL (port 6543). Python w trybie async na serverlessie potrafi szybko wyczerpać limity bezpośrednich połączeń.

[ ] Migracje (Supabase):

Migracje znajdują się w `supabase/migrations/`.

Opcje wdrożenia migracji:

- **Opcja 1 (Rekomendowana)**: Użyj Supabase CLI w skrypcie prestart.sh:
  ```bash
  supabase db push --db-url $DATABASE_URL
  ```
- **Opcja 2**: Uruchamiaj migracje ręcznie przed wdrożeniem (mniej automatyczne)
- **Opcja 3**: Użyj Supabase Dashboard do aplikowania migracji

Przygotuj skrypt (np. w backend/prestart.sh), który uruchamia migracje przed startem aplikacji. Dzięki temu baza zaktualizuje się sama przy każdym wdrożeniu nowej wersji.

**Uwaga**: Alembic jest w requirements.txt, ale nie jest używany w projekcie. Można go usunąć jeśli nie planujesz migracji na Alembic.

Faza 3: Infrastruktura (Railway)
[ ] Inicjalizacja Projektu:

Utwórz "Empty Project" w Railway.

[ ] Serwis Backend:

Dodaj serwis z repozytorium GitHub.

Ważne: W ustawieniach (Settings) ustaw Root Directory na /backend.

W sekcji Variables dodaj wszystkie wymagane zmienne środowiskowe:

- **Database**: DATABASE_URL (z Supabase Connection Pooler, port 6543)
- **Telegram**: TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, TELEGRAM_WEBHOOK_SECRET
- **AI Services**: OPENAI_API_KEY, GEMINI_API_KEY
- **Supabase**: SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET
- **JWT**: JWT_SECRET_KEY
- **App**: ENV=production, PORT=8000, WEB_APP_URL (URL frontendu)
- **Opcjonalne**: Wszystkie pozostałe zmienne z backend/src/config.py (z domyślnymi wartościami jeśli mają)

[ ] Serwis Frontend:

Dodaj serwis z repozytorium GitHub.

Ważne: W ustawieniach ustaw Root Directory na /astro.

W sekcji Variables dodaj:

- BACKEND_URL (adres wewnętrzny serwisu backendu, np. http://backend-production.up.railway.app lub http://backend:8000 jeśli używasz Private Networking)
- **Uwaga**: Sprawdź czy frontend potrzebuje dodatkowych zmiennych środowiskowych (np. Supabase URL/Key dla klienta)

[ ] Public Domain:

Wygeneruj domenę publiczną (np. moj-projekt.up.railway.app) tylko dla serwisu Frontend. Backend powinien być schowany i dostępny tylko przez Nginx (chyba że potrzebujesz publicznego Webhooka dla Telegrama – wtedy wystaw też backend, ale zabezpiecz inne endpointy).

Faza 4: CI/CD (GitHub Actions)
Automatyzacja testów i wdrożeń z uwzględnieniem Monorepo.

4.1. Pipeline Backend (.github/workflows/backend.yml)
[ ] Trigger: Push do main/master, ale z filtrem paths: ['backend/**'].

[ ] Jobs:

test: Instalacja Pythona, pip install, pytest (mockowanie API OpenAI i Telegrama).

- Użyj working-directory: ./backend (podobnie jak w istniejącym pull-request.yml)

deploy: Użyj railwayapp/cli-action (lub deploy automatyczny przez trigger w dashboardzie Railway – dla side projectu trigger w dashboardzie jest prostszy i wystarczający, o ile testy przejdą).

**Uwaga**: Istnieje już `.github/workflows/pull-request.yml` z lintowaniem. Rozważ rozszerzenie go o testy lub utworzenie osobnych workflow dla deploy.

4.2. Pipeline Frontend (.github/workflows/frontend.yml)
[ ] Trigger: Push do main/master, filtr paths: ['astro/**'].

[ ] Jobs:

test: npm install, npm run test (Vitest), npm run build (sprawdzenie czy build w ogóle przechodzi).

- Użyj working-directory: ./astro (podobnie jak w istniejącym pull-request.yml)
- Sprawdź czy projekt ma skrypt `test` w package.json

e2e: Opcjonalnie Playwright dla kluczowych ścieżek (np. logowanie).

- Sprawdź czy istnieją już testy E2E w projekcie (szukaj w astro/e2e/)

**Uwaga**: Istnieje już `.github/workflows/pull-request.yml` z lintowaniem Astro. Rozważ rozszerzenie go o testy lub utworzenie osobnych workflow dla deploy.

Faza 5: "Day 2 Operations" (Monitoring i Utrzymanie)
Twoja aplikacja już działa. Teraz sprawiamy, żeby działała długo i stabilnie.

[ ] Sentry (Error Tracking):

Zainstaluj SDK Sentry w FastAPI oraz w React/Astro. To absolutna podstawa, żeby widzieć błędy 500 i crashe JS u użytkowników.

[ ] Healthchecki:

✅ **JUŻ ZAIMPLEMENTOWANE**: Endpoint `/health` już istnieje w `backend/src/health.py`. Dostępne są dwa endpointy:

- `/health` - podstawowy healthcheck
- `/health/db` - healthcheck z testem połączenia do bazy

W konfiguracji Railway (Settings -> Deploy -> Healthcheck Path) ustaw `/health`. Jeśli aplikacja się zawiesi, Railway sam ją zrestartuje.

[ ] Budżet:

Side projecty lubią generować koszty przez pomyłkę. Ustaw "Spending Limit" w Railway na kwotę, którą akceptujesz (np. 5 USD), aby uniknąć niespodzianek.

Podsumowanie Strategii
Monorepo: Rozdzielasz logikę buildów za pomocą Root Directory w Railway.

Architektura: Nginx (Frontend) jest twoją tarczą i routerem. Ukrywa Backend przed światem (za wyjątkiem webhooków).

Baza: Connection Pooler to "must-have" przy Pythonie i chmurze.

## ✅ Co już jest zaimplementowane:

- ✅ Healthcheck endpoint (`/health`)
- ✅ Telegram webhook (nie polling)
- ✅ Sentry SDK w requirements.txt (backend)
- ✅ Struktura monorepo (backend/, astro/)
- ✅ GitHub Actions workflow dla PR (lint)

## ⚠️ Co wymaga aktualizacji/korekty:

- ⚠️ Plan mówił o `/frontend` - poprawione na `/astro`
- ⚠️ Plan mówił o Alembic - projekt używa Supabase migrations
- ⚠️ Brak Dockerfile w backend/ i astro/
- ⚠️ Brak .dockerignore w backend/ i astro/
- ⚠️ Brak nginx.conf w astro/
- ⚠️ Brak workflow dla deploy (tylko PR workflow)
- ⚠️ Brak konfiguracji Sentry w frontendzie
- ⚠️ Brak prestart.sh dla migracji Supabase
