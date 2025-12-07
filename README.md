# Bills

[![Project Status](https://img.shields.io/badge/status-MVP_in_progress-blue.svg)](./)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](./LICENSE)

## Table of Contents

- [Project name](#bills)
- [Project description](#project-description)
- [Tech stack](#tech-stack)
- [Getting started locally](#getting-started-locally)
- [Available scripts](#available-scripts)
- [Project scope](#project-scope)
- [Project status](#project-status)
- [License](#license)

## Project description

Bills automates personal expense tracking by letting users send receipt photos to a Telegram bot. The system uses OCR to extract line items, applies AI to normalize and categorize products, validates the sum against the receipt total, and stores the data for summaries. A read‑only web app complements the bot with clear summaries and a passwordless “magic link” login delivered by the bot.

Key highlights:

- Capture receipts via Telegram; instant confirmation and processing.
- OCR with high‑quality text extraction; AI normalization and categorization to predefined categories, with fallback to “Other”.
- Low‑confidence items can be confirmed by the user directly in the bot.
- Text summaries available in the bot (daily/weekly/monthly).
- Read‑only web app for visual summaries; login via one‑time magic link.
- Freemium plan: up to 100 receipts per month; warnings at 90; blocks at 101 with reset info.
- Privacy by design: avoid processing personal data from receipts; simple privacy policy accessible in the bot.

For full product details, see the PRD:

- PRD (workspace): `.ai/prd.md`

## Tech stack

- Backend:
  - Python 3.11+, FastAPI, Uvicorn
  - SQLAlchemy (ORM), Alembic (migrations), Pydantic (validation)
  - SQLAdmin (admin panel)
  - python-telegram-bot (Telegram integration)
  - sentry-sdk (logging/monitoring)
- Data & AI:
  - PaddlePaddle-OCR (OCR)
  - OpenAI API (categorization & normalization)
  - Celery (task queue), RabbitMQ (broker)
- Frontend:
  - React.js, Tailwind CSS
- Database & Hosting:
  - PostgreSQL
- Infrastructure:
  - Nginx (reverse proxy)
- Testing:
  - Backend: pytest, pytest-asyncio, pytest-mock
  - Frontend: Vitest (unit tests), Playwright (E2E tests)
  - Mocking: unittest.mock (Python)

See also: `.ai/tech-stack.md`

## Getting started locally

> Note: This repository may not yet include all service directories or dependency manifests. The steps below provide a sensible local setup for development. Adjust paths and tool choices as needed.

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm or pnpm
- PostgreSQL 14+ (local or remote)
- RabbitMQ 3.12+ (local)
- OpenAI API key
- PaddleOCR system dependencies (per your OS)
- Optional: Sentry DSN (for error tracking)

### Environment variables

Create a `.env` file (or export as environment variables) for the backend:

Application
APP_ENV=development
APP_PORT=8000
Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/bills
Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_URL=https://your-dev-tunnel-or-domain/telegram/webhook
OpenAI
OPENAI_API_KEY=your-openai-api-key
Celery / RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=rpc://
Sentry (optional)
SENTRY_DSN=

### Backend (FastAPI)

```bash
# 1) Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
. .\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run database migrations (if Alembic is configured)
# alembic upgrade head

# 4) Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Task queue (Celery)

```bash
# Start RabbitMQ (Docker example)
docker run --rm -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Start Celery worker (adjust app path)
celery -A app.worker.celery_app worker --loglevel=INFO
```

### Telegram bot

- Set `TELEGRAM_BOT_TOKEN` in `.env`.
- For local development:
  - Either run in polling mode within your bot service, or
  - Expose a public URL for webhooks (e.g., ngrok) and set `TELEGRAM_WEBHOOK_URL`.
- Commands supported by MVP (as per PRD): `/start`, `/dzis`, `/tydzien`, `/miesiac`, `/login`, `/prywatnosc`.

### Frontend (React + Tailwind)

```bash
# From frontend directory if present
npm install
npm run dev
# or with pnpm
# pnpm install
# pnpm dev
```

### Reverse proxy (optional)

If you need a unified entrypoint, configure Nginx to proxy to:

- FastAPI at `http://localhost:8000`
- Frontend dev server at its port (e.g., `http://localhost:5173`)
- Telegram webhook endpoint mapped to your public URL

## Available scripts

> Adjust to your project structure. If no package/Makefile exists yet, these examples can be added.

- Backend

  - Start API (dev): `uvicorn app.main:app --reload --port 8000`
  - Run migrations: `alembic upgrade head`
  - Generate migration: `alembic revision --autogenerate -m "message"`
  - Lint (example): `ruff check .` or `flake8`
  - Tests: `pytest -q`
  - Tests with coverage: `pytest --cov=. --cov-report=html`

- Celery

  - Worker: `celery -A app.worker.celery_app worker --loglevel=INFO`
  - Beat (if scheduled tasks): `celery -A app.worker.celery_app beat`

- Frontend
  - Dev: `npm run dev`
  - Build: `npm run build`
  - Preview: `npm run preview`
  - Unit tests: `npm run test` (Vitest)
  - E2E tests: `npm run test:e2e` (Playwright)

## Project scope

In scope (MVP):

- Telegram bot to accept receipt photos and simple text commands.
- OCR extraction of line items.
- AI-based normalization and categorization into predefined categories; low-confidence items go through user confirmation.
- Receipt total validation versus sum of items.
- Text summaries in the bot: daily, weekly, monthly.
- Read-only web app with the same summaries as in the bot.
- Passwordless login to the web app via bot-provided magic link.
- Freemium model: 100 receipts/month; notify at 90; block at 101; show reset date.
- Privacy policy available through a bot command; avoid processing personal data from receipts.

Out of scope (MVP):

- Advanced analytics and forecasting.
- Non-image formats (e.g., PDFs, emails).
- Bulk import of multiple receipts at once.
- Interactive charts/advanced visualizations.
- User-managed categories.
- Group/shared budgets.
- Data export (CSV/Excel, etc.).
- Bank account integrations.
- Multi-currency support.

## Testing

### Backend Tests (pytest)

```bash
# Z katalogu backend/
cd backend

# Wszystkie testy
pytest

# Testy z pokryciem
pytest --cov=src --cov-report=html

# Konkretny plik
pytest tests/example_test.py

# Testy z markerem
pytest -m unit
pytest -m integration
```

Więcej informacji: `backend/tests/README.md`

### Frontend Tests

#### Testy jednostkowe (Vitest)

```bash
# Z katalogu astro/
cd astro

# Wszystkie testy
npm run test

# Tryb watch
npm run test:watch

# UI mode
npm run test:ui

# Z pokryciem
npm run test:coverage
```

#### Testy E2E (Playwright)

```bash
# Z katalogu astro/
cd astro

# Wszystkie testy E2E
npm run test:e2e

# UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug
```

Więcej informacji: `astro/src/test/README.md`

## Project status

MVP in progress. Initial focus:

- Bot receipt processing and OCR + AI categorization pipeline
- User verification for low-confidence items
- Magic link authentication for read-only web app
- Summaries parity between bot and web app

Success metrics:

- 90% of items correctly processed automatically (OCR, normalization, categorization)
- <10% of items require manual verification

## License

MIT (to be confirmed). If you intend to use a different license, add a `LICENSE` file and update the badge above accordingly.
