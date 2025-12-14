# Auth Module

Moduł autoryzacji dla aplikacji Bills implementujący **passwordless authentication** (Magic Link) + **JWT tokens**.

## 📋 Spis treści

- [Architektura](#architektura)
- [Workflow](#workflow)
- [API Endpoints](#api-endpoints)
- [Bezpieczeństwo](#bezpieczeństwo)
- [Użycie](#użycie)
- [Konfiguracja](#konfiguracja)

## 🏗️ Architektura

### Pliki modułu:

```
backend/src/auth/
├── __init__.py          # Marker modułu
├── models.py            # Model MagicLink (SQLAlchemy)
├── schemas.py           # Pydantic schemas (request/response)
├── services.py          # AuthService (logika biznesowa)
├── routes.py            # FastAPI endpoints
├── jwt.py               # JWT utilities (encoding/decoding)
├── exceptions.py        # Auth-specific exceptions
└── README.md            # Ta dokumentacja
```

### Zależności:

- **FastAPI**: Framework webowy
- **SQLAlchemy**: ORM (async)
- **Pydantic**: Walidacja danych
- **python-jose**: JWT encoding/decoding
- **secrets**: Bezpieczne generowanie tokenów

## 🔄 Workflow

### 1. Generowanie Magic Link (Telegram Bot → API)

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│             │         │             │         │             │
│  Telegram   │─────────│   Backend   │─────────│  Database   │
│     Bot     │         │   (Auth)    │         │   (Magic    │
│             │         │             │         │   Links)    │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      │ POST /auth/magic-link │                       │
      │ {telegram_user_id}    │                       │
      │──────────────────────>│                       │
      │                       │                       │
      │                       │ Check user exists     │
      │                       │──────────────────────>│
      │                       │                       │
      │                       │ User found            │
      │                       │<──────────────────────│
      │                       │                       │
      │                       │ Generate secure token │
      │                       │ (secrets.token_urlsafe)
      │                       │                       │
      │                       │ Create MagicLink      │
      │                       │──────────────────────>│
      │                       │                       │
      │   Magic Link URL      │                       │
      │<──────────────────────│                       │
      │                       │                       │
```

### 2. Weryfikacja Magic Link (User → Web App → API)

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│             │         │             │         │             │
│  User (Web) │─────────│   Backend   │─────────│  Database   │
│             │         │   (Auth)    │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      │ Click magic link      │                       │
      │──────────────────────>│                       │
      │ POST /auth/verify     │                       │
      │ ?token=abc123         │                       │
      │                       │                       │
      │                       │ Find token            │
      │                       │──────────────────────>│
      │                       │                       │
      │                       │ Check:                │
      │                       │ - Exists?             │
      │                       │ - Not expired?        │
      │                       │ - Not used?           │
      │                       │                       │
      │                       │ Mark as used          │
      │                       │──────────────────────>│
      │                       │                       │
      │                       │ Load user             │
      │                       │──────────────────────>│
      │                       │                       │
      │                       │ Generate JWT tokens:  │
      │                       │ - access (15 min)     │
      │                       │ - refresh (7 days)    │
      │                       │                       │
      │   JWT Tokens + User   │                       │
      │<──────────────────────│                       │
      │                       │                       │
```

### 3. Chronione Endpointy (Authenticated Requests)

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│             │         │             │         │             │
│  Frontend   │─────────│   Backend   │─────────│  Database   │
│             │         │             │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      │ GET /api/v1/bills     │                       │
      │ Authorization: Bearer │                       │
      │ eyJhbGciOi...         │                       │
      │──────────────────────>│                       │
      │                       │                       │
      │                       │ Decode JWT            │
      │                       │ Extract user_id       │
      │                       │                       │
      │                       │ Load user             │
      │                       │──────────────────────>│
      │                       │                       │
      │                       │ Check is_active       │
      │                       │                       │
      │   Bills data (filtered│                       │
      │   by user_id)         │                       │
      │<──────────────────────│                       │
      │                       │                       │
```

## 🌐 API Endpoints

### `POST /api/v1/auth/magic-link`

Generuje magic link dla użytkownika.

**Request:**

```json
{
  "telegram_user_id": 123456789,
  "redirect_url": "https://app.bills.com/dashboard"
}
```

**Response (200 OK):**

```json
{
  "magic_link": "https://app.bills.com/auth/verify?token=abc123...",
  "expires_at": "2024-01-01T12:30:00Z",
  "sent_to_telegram": true
}
```

**Errors:**

- `404 Not Found`: User z telegram_user_id nie istnieje

---

### `POST /api/v1/auth/verify`

Weryfikuje token i zwraca JWT.

**Query Parameters:**

- `token` (required): Magic link token

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "external_id": 123456789,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Errors:**

- `400 Bad Request`: Token nieprawidłowy
- `401 Unauthorized`: Token wygasł lub został już użyty

---

### `GET /api/v1/auth/me`

Zwraca informacje o aktualnie zalogowanym użytkowniku.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": 1,
  "external_id": 123456789,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**

- `401 Unauthorized`: Brak tokenu lub token nieprawidłowy

## 🔒 Bezpieczeństwo

### Magic Link Token

- **Generowanie**: `secrets.token_urlsafe(32)` (256 bitów entropii)
- **Długość**: 43 znaki (URL-safe base64)
- **Single-use**: Token może być użyty tylko raz
- **Expiracja**: 30 minut (konfigurowalne)
- **Storage**: Przechowywany w bazie jako plain text (bezpieczny, bo jednorazowy)

### JWT Tokens

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Access Token**: 15 minut lifetime
- **Refresh Token**: 7 dni lifetime
- **Secret**: Musi być long random string (minimum 32 znaki)
- **Payload**: Zawiera tylko `sub` (user_id) i `exp` (expiration)

### Best Practices Implemented

✅ **Secure token generation** - używamy `secrets` module (CSPRNG)
✅ **Single-use tokens** - magic link działa tylko raz
✅ **Time-bound tokens** - wszystkie tokeny wygasają
✅ **JWT verification** - każde żądanie weryfikuje token
✅ **User isolation** - wszystkie dane filtrowane per user_id
✅ **HTTPS requirement** - magic links powinny być wysyłane tylko przez HTTPS
✅ **No password storage** - brak haseł w bazie danych

## 📦 Użycie

### W Routes (Dependency Injection)

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from src.deps import get_current_user
from src.users.models import User

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Ten endpoint wymaga autoryzacji.
    get_current_user automatycznie weryfikuje JWT i zwraca User model.
    """
    return {
        "message": f"Hello, user {current_user.id}!",
        "telegram_id": current_user.external_id
    }
```

### W Service Layer

```python
from src.auth.services import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

async def my_service_function(session: AsyncSession):
    auth_service = AuthService(session)

    # Create magic link
    request = MagicLinkCreateRequest(telegram_user_id=123456)
    magic_link, url = await auth_service.create_magic_link(request)

    # Verify token
    user = await auth_service.verify_magic_link(token="abc123")

    # Create JWT tokens
    access_token, refresh_token = auth_service.create_tokens_for_user(user)
```

### W Frontend (przykład)

```typescript
// 1. Request magic link (called by Telegram bot)
const response = await fetch('/api/v1/auth/magic-link', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ telegram_user_id: 123456 }),
});
const { magic_link } = await response.json();

// 2. User clicks magic link → frontend extracts token
const token = new URLSearchParams(window.location.search).get('token');

// 3. Verify token and get JWT
const authResponse = await fetch(`/api/v1/auth/verify?token=${token}`, {
  method: 'POST',
});
const { access_token, refresh_token, user } = await authResponse.json();

// 4. Store tokens (localStorage or httpOnly cookie)
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// 5. Use access_token for authenticated requests
const billsResponse = await fetch('/api/v1/bills', {
  headers: {
    Authorization: `Bearer ${access_token}`,
  },
});
```

## ⚙️ Konfiguracja

### Environment Variables (`.env`)

```bash
# JWT Settings
JWT_SECRET_KEY=your-secret-key-here-use-32-chars-minimum
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
MAGIC_LINK_EXPIRE_MINUTES=30

# Frontend URL
WEB_APP_URL=http://localhost:4321
```

### Generowanie JWT Secret

```bash
# W Pythonie
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Lub w terminalu (Linux/Mac)
openssl rand -base64 32
```

## 🧪 Testing (TODO)

```python
# Example test for magic link creation
async def test_create_magic_link():
    # Create user
    user = await create_test_user(telegram_id=123456)

    # Request magic link
    request = MagicLinkCreateRequest(telegram_user_id=123456)
    magic_link, url = await auth_service.create_magic_link(request)

    assert magic_link.user_id == user.id
    assert magic_link.used == False
    assert "token=" in url
```

## 🚀 Next Steps

1. **Implementacja Refresh Token endpoint** - `POST /auth/refresh`
2. **Token Revocation** - Endpoint do wylogowania (blacklist tokens)
3. **Rate Limiting** - Ochrona przed brute force
4. **Audit Log** - Logowanie prób autoryzacji
5. **2FA** - Opcjonalna dodatkowa weryfikacja

## 📚 Dodatkowe Zasoby

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
