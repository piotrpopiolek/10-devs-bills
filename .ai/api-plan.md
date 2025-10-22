# REST API Plan

## 1. Resources

- **Users** - User management (corresponds to `users` table)
- **Bills** - Receipt/bill records (corresponds to `bills` table)
- **Bill Items** - Individual items from receipts (corresponds to `bill_items` table)
- **Shops** - Store/shop information (corresponds to `shops` table)
- **Categories** - Product categories (corresponds to `categories` table)
- **Products** - Product dictionary (corresponds to `indexes` table)
- **Product Aliases** - OCR variants and aliases (corresponds to `index_aliases` table)
- **Reports** - Expense summaries and analytics
- **Telegram Messages** - Telegram message tracking (corresponds to `telegram_messages` table)

## 2. Endpoints

### Authentication

#### POST /auth/magic-link

- **Description**: Generate magic link for passwordless authentication
- **Query Parameters**: None
- **Request Body**:

```json
{
  "telegram_user_id": 123456789,
  "redirect_url": "https://app.bills.com/dashboard"
}
```

- **Response Body**:

```json
{
  "magic_link": "https://app.bills.com/auth/verify?token=abc123",
  "expires_at": "2024-01-01T12:00:00Z",
  "sent_to_telegram": true
}
```

- **Success**: 200 OK
- **Errors**: 400 Bad Request, 404 User Not Found, 429 Rate Limited

#### POST /auth/verify

- **Description**: Verify magic link and authenticate user
- **Query Parameters**: `token` (required)
- **Request Body**: None
- **Response Body**:

```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": 1,
    "external_id": 123456789,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

- **Success**: 200 OK
- **Errors**: 400 Invalid Token, 401 Expired Token

### Users

#### GET /users/me

- **Description**: Get current user profile and usage statistics
- **Query Parameters**: None
- **Request Body**: None
- **Response Body**:

```json
{
  "id": 1,
  "external_id": 123456789,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "usage": {
    "bills_this_month": 45,
    "monthly_limit": 100,
    "remaining_bills": 55
  }
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized

### Bills

#### POST /bills

- **Description**: Upload and process a receipt image
- **Query Parameters**: None
- **Request Body** (multipart/form-data):

```json
{
  "image": "file",
  "bill_date": "2024-01-01T10:30:00Z",
  "shop_name": "Supermarket ABC",
  "shop_address": "123 Main St"
}
```

- **Response Body**:

```json
{
  "id": 1,
  "status": "processing",
  "bill_date": "2024-01-01T10:30:00Z",
  "total_amount": null,
  "shop": {
    "id": 1,
    "name": "Supermarket ABC",
    "address": "123 Main St"
  },
  "items": [],
  "created_at": "2024-01-01T10:30:00Z"
}
```

- **Success**: 201 Created
- **Errors**: 400 Bad Request, 401 Unauthorized, 413 Payload Too Large, 429 Rate Limited

#### GET /bills

- **Description**: List user's bills with pagination and filtering
- **Query Parameters**:
  - `page` (optional, default: 1)
  - `limit` (optional, default: 20, max: 100)
  - `status` (optional: pending, processing, completed, error)
  - `shop_id` (optional)
  - `date_from` (optional, ISO 8601)
  - `date_to` (optional, ISO 8601)
- **Request Body**: None
- **Response Body**:

```json
{
  "bills": [
    {
      "id": 1,
      "bill_date": "2024-01-01T10:30:00Z",
      "total_amount": 45.67,
      "status": "completed",
      "shop": {
        "id": 1,
        "name": "Supermarket ABC"
      },
      "items_count": 8,
      "created_at": "2024-01-01T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 400 Bad Request

#### GET /bills/{id}

- **Description**: Get detailed bill information
- **Query Parameters**: None
- **Request Body**: None
- **Response Body**:

```json
{
  "id": 1,
  "bill_date": "2024-01-01T10:30:00Z",
  "total_amount": 45.67,
  "status": "completed",
  "image_url": "https://storage.bills.com/images/bill_1.jpg",
  "image_expires_at": "2024-07-01T10:30:00Z",
  "shop": {
    "id": 1,
    "name": "Supermarket ABC",
    "address": "123 Main St"
  },
  "items": [
    {
      "id": 1,
      "quantity": 2.0,
      "unit_price": 3.5,
      "total_price": 7.0,
      "original_text": "Milk 2L",
      "confidence_score": 0.95,
      "is_verified": true,
      "verification_source": "auto",
      "product": {
        "id": 1,
        "name": "Milk",
        "category": {
          "id": 1,
          "name": "Dairy Products"
        }
      }
    }
  ],
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T10:35:00Z"
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 404 Not Found

#### DELETE /bills/{id}

- **Description**: Delete a bill and all its items
- **Query Parameters**: None
- **Request Body**: None
- **Response Body**: None
- **Success**: 204 No Content
- **Errors**: 401 Unauthorized, 404 Not Found, 403 Forbidden

### Bill Items

#### PUT /bill-items/{id}/verify

- **Description**: Verify or correct a bill item
- **Query Parameters**: None
- **Request Body**:

```json
{
  "is_verified": true,
  "quantity": 2.0,
  "unit_price": 3.5,
  "total_price": 7.0,
  "product_id": 1,
  "notes": "Corrected quantity"
}
```

- **Response Body**:

```json
{
  "id": 1,
  "quantity": 2.0,
  "unit_price": 3.5,
  "total_price": 7.0,
  "is_verified": true,
  "verification_source": "user",
  "product": {
    "id": 1,
    "name": "Milk",
    "category": {
      "id": 1,
      "name": "Dairy Products"
    }
  },
  "updated_at": "2024-01-01T10:35:00Z"
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 404 Not Found, 400 Bad Request

#### GET /bill-items/pending-verification

- **Description**: Get items pending user verification
- **Query Parameters**:
  - `page` (optional, default: 1)
  - `limit` (optional, default: 20)
- **Request Body**: None
- **Response Body**:

```json
{
  "items": [
    {
      "id": 1,
      "quantity": 2.0,
      "unit_price": 3.5,
      "total_price": 7.0,
      "original_text": "Milk 2L",
      "confidence_score": 0.75,
      "bill": {
        "id": 1,
        "bill_date": "2024-01-01T10:30:00Z",
        "shop": {
          "name": "Supermarket ABC"
        }
      },
      "suggested_product": {
        "id": 1,
        "name": "Milk",
        "category": {
          "name": "Dairy Products"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "pages": 1
  }
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized

### Shops

#### GET /shops

- **Description**: List shops with search functionality
- **Query Parameters**:
  - `search` (optional, search by name)
  - `page` (optional, default: 1)
  - `limit` (optional, default: 20)
- **Request Body**: None
- **Response Body**:

```json
{
  "shops": [
    {
      "id": 1,
      "name": "Supermarket ABC",
      "address": "123 Main St",
      "bills_count": 15,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "pages": 2
  }
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized

#### GET /shops/{id}

- **Description**: Get shop details
- **Query Parameters**: None
- **Request Body**: None
- **Response Body**:

```json
{
  "id": 1,
  "name": "Supermarket ABC",
  "address": "123 Main St",
  "bills_count": 15,
  "total_spent": 1250.5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 404 Not Found

### Categories

#### GET /categories

- **Description**: List all product categories
- **Query Parameters**:
  - `parent_id` (optional, filter by parent category)
  - `include_children` (optional, include subcategories)
- **Request Body**: None
- **Response Body**:

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Beverages",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Dairy Products",
          "parent_id": 1,
          "children": []
        }
      ],
      "products_count": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized

### Products

#### GET /products

- **Description**: List products with search and filtering
- **Query Parameters**:
  - `search` (optional, search by name)
  - `category_id` (optional)
  - `page` (optional, default: 1)
  - `limit` (optional, default: 20)
- **Request Body**: None
- **Response Body**:

```json
{
  "products": [
    {
      "id": 1,
      "name": "Milk",
      "synonyms": ["Mleko", "Milk 2L", "Fresh Milk"],
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "usage_count": 45,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 500,
    "pages": 25
  }
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized

### Reports

#### GET /reports/daily

- **Description**: Get daily expense report
- **Query Parameters**:
  - `date` (optional, ISO 8601 date, default: today)
- **Request Body**: None
- **Response Body**:

```json
{
  "date": "2024-01-01",
  "total_amount": 125.5,
  "bills_count": 3,
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 45.67,
      "percentage": 36.4
    }
  ],
  "shops": [
    {
      "shop": {
        "id": 1,
        "name": "Supermarket ABC"
      },
      "amount": 89.3,
      "bills_count": 2
    }
  ]
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 400 Bad Request

#### GET /reports/weekly

- **Description**: Get weekly expense report
- **Query Parameters**:
  - `week_start` (optional, ISO 8601 date, default: start of current week)
- **Request Body**: None
- **Response Body**:

```json
{
  "week_start": "2024-01-01",
  "week_end": "2024-01-07",
  "total_amount": 850.25,
  "bills_count": 15,
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "amount": 125.5,
      "bills_count": 3
    }
  ],
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 320.15,
      "percentage": 37.7
    }
  ]
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 400 Bad Request

#### GET /reports/monthly

- **Description**: Get monthly expense report
- **Query Parameters**:
  - `month` (optional, YYYY-MM format, default: current month)
- **Request Body**: None
- **Response Body**:

```json
{
  "month": "2024-01",
  "total_amount": 3200.75,
  "bills_count": 45,
  "daily_average": 103.25,
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 1200.3,
      "percentage": 37.5
    }
  ],
  "top_shops": [
    {
      "shop": {
        "id": 1,
        "name": "Supermarket ABC"
      },
      "amount": 1800.5,
      "bills_count": 25
    }
  ],
  "weekly_breakdown": [
    {
      "week_start": "2024-01-01",
      "amount": 850.25
    }
  ]
}
```

- **Success**: 200 OK
- **Errors**: 401 Unauthorized, 400 Bad Request

### Telegram Webhook

#### POST /webhooks/telegram

- **Description**: Telegram bot webhook endpoint
- **Query Parameters**: None
- **Request Body**: Telegram webhook payload
- **Response Body**: None
- **Success**: 200 OK
- **Errors**: 400 Bad Request, 401 Unauthorized

## 3. Authentication and Authorization

### Authentication Mechanism

- **Magic Link Authentication**: Passwordless authentication using Telegram integration
- **JWT Tokens**: Short-lived access tokens (15 minutes) with refresh tokens (7 days)
- **Telegram Integration**: Users authenticate through Telegram bot, receive magic link for web app access

### Authorization Rules

- **User Isolation**: All operations are filtered by `user_id` to ensure data isolation
- **Rate Limiting**: 100 bills per month for free tier users
- **Admin-Only Operations**: Category and product creation restricted to administrators
- **Read-Only Web App**: Web application provides read-only access to data

### Security Headers

- **CORS**: Configured for web app domain
- **Rate Limiting**: Per-user rate limiting on all endpoints
- **Input Validation**: All inputs validated against database constraints
- **File Upload Security**: Image uploads restricted to specific formats and sizes

## 4. Validation and Business Logic

### Resource Validation Rules

#### Bills

- `total_amount >= 0` - Non-negative amounts only
- `bill_date` - Must be valid timestamp, not in future
- `image_url` - Must be valid URL format
- `status` - Must be valid enum value
- Monthly limit enforcement (100 bills per month)

#### Bill Items

- `quantity > 0` - Positive quantities only
- `unit_price >= 0` - Non-negative unit prices
- `total_price = ROUND(quantity * unit_price, 2)` - Calculated total validation
- `confidence_score` - Between 0.0 and 1.0
- `verification_source` - Must be valid enum value

#### Shops

- `name` - Required, unique combination with address
- `address` - Optional text field

#### Categories

- `name` - Required, unique across all categories
- `parent_id` - Must reference valid category, prevents circular references

#### Products (Indexes)

- `name` - Required, unique across all products
- `synonyms` - Valid JSON array of strings
- `category_id` - Must reference valid category

#### Product Aliases

- `raw_name` - Required text field
- `index_id` - Must reference valid product
- Unique combination of `raw_name` and `index_id`

### Business Logic Implementation

#### Receipt Processing Pipeline

1. **Image Upload**: Validate file format and size
2. **OCR Processing**: Extract text using PaddlePaddle-OCR
3. **AI Categorization**: Use OpenAI API for product normalization and categorization
4. **Database Storage**: Store bill and items with confidence scores
5. **Verification Queue**: Flag uncertain items for user verification
6. **Notification**: Send Telegram message with results

#### Data Verification Workflow

1. **Confidence Threshold**: Items with confidence < 0.8 flagged for verification
2. **User Review**: Present uncertain items in Telegram with correction options
3. **Learning System**: Update product aliases based on user corrections
4. **Validation**: Cross-check item totals against bill total

#### Monthly Limit Enforcement

1. **Usage Tracking**: Count bills created in current month
2. **Limit Check**: Enforce 100 bills per month for free tier
3. **Graceful Degradation**: Return informative error when limit exceeded
4. **Reset Logic**: Monthly limit resets on first day of each month

#### Product Dictionary Management

1. **Normalization**: Map OCR text to standardized product names
2. **Alias Learning**: Build database of OCR variants for each product
3. **Confirmation Tracking**: Count how often each alias is confirmed
4. **Admin Control**: Only administrators can create new categories and products
