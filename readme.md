# Tradelink Django Marketplace API

A Django REST Framework backend for a Kenya-focused e-commerce marketplace. This project provides user authentication, product and category management, order processing, cart operations, payment integration, reviews, and feedback endpoints.

## Key Features
- JWT authentication with SimpleJWT
- Product browsing, search, and filtering
- Category management
- Cart add/update/remove/clear operations
- Order creation, retrieval, confirmation, cancellation and returns support
- M-Pesa payment integration through PayHero v2
- Product review creation, listing and deletion
- Feedback submission endpoint
- Swagger/OpenAPI docs via drf-spectacular

## Tech Stack

- Python 3.x
- Django 6.0
- Django REST Framework
- drf-spectacular for API documentation
- djangorestframework-simplejwt for JWT auth
- SQLite by default, optional Supabase DB integration
- PayHero v2 payment integration

## Getting Started

### 1. Install dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root and add required values.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*
SUPABASE_DB_URL=
JWT_ACCESS_TOKEN_MINUTES=60
JWT_REFRESH_TOKEN_DAYS=7
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
PAYHERO_V2_BASE_URL=https://backend.payhero.co.ke/api/v2
PAYHERO_API_KEY=your-payhero-key
PAYHERO_API_SECRET=your-payhero-secret
PAYHERO_CHANNEL_ID=133
PAYHERO_CALLBACK_URL=https://your-domain.com/api/v1/callback/payhero/
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Start the server

```bash
python manage.py runserver
```

### 5. Access API documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- Redoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## Architecture Overview

The project is organized as Django apps under `tradelink_django/`:

- `users` - authentication, registration, user profile, admin user management
- `products` - product listing, create, update, delete, search
- `product_categories` - category CRUD operations
- `orders` - order creation, listing, retrieval, confirmation, cancellation, issues, returns
- `payments` - payment initiation, callback handling, status lookup
- `carts` - cart item management
- `reviews` - product review flows
- `feedback` - user-submitted feedback
- `addresses` - placeholder app with no public router endpoints configured

## API Routes Summary

All API routes are mounted under `/api/v1/`.

### Authentication

- `POST /api/v1/auth/register/` - register new user
- `POST /api/v1/auth/login/` - obtain JWT access/refresh tokens
- `POST /api/v1/auth/logout/` - logout current user
- `POST /api/v1/auth/token/refresh/` - refresh access token

### User Profile

- `GET /api/v1/users/me/` - retrieve current user profile
- `PATCH /api/v1/users/me/change-password/` - change password

### Admin User Management

- `GET /api/v1/admin/users/` - list users
- `GET /api/v1/admin/users/{id}/` - retrieve user
- `POST /api/v1/admin/users/{id}/activate/` - activate user
- `POST /api/v1/admin/users/{id}/deactivate/` - deactivate user

### Products

- `GET /api/v1/products/` - list products
- `POST /api/v1/products/` - create product
- `GET /api/v1/products/{id}/` - retrieve product details
- `PUT /api/v1/products/{id}/` - update product
- `PATCH /api/v1/products/{id}/` - partial update
- `DELETE /api/v1/products/{id}/` - delete product
- `GET /api/v1/products/search/` - search products (same behavior as list)

Query parameters supported for product list/search:

- `search` - text search on name or description
- `category_id` - filter by category
- `min_price` / `max_price` - price range
- `in_stock` - `true` / `false`
- `page` / `limit` - paging controls

### Categories

- `GET /api/v1/categories/` - list categories
- `POST /api/v1/categories/` - create category
- `GET /api/v1/categories/{id}/` - retrieve category
- `PUT /api/v1/categories/{id}/` - update category
- `PATCH /api/v1/categories/{id}/` - partial update
- `DELETE /api/v1/categories/{id}/` - delete category

### Orders

- `GET /api/v1/orders/` - list orders (user-specific or admin)
- `GET /api/v1/orders/{id}/` - retrieve order details
- `POST /api/v1/orders/` - create order
- `POST /api/v1/orders/{id}/confirm/` - confirm delivery
- `POST /api/v1/orders/{id}/cancel/` - cancel order
- `POST /api/v1/orders/{id}/issue/` - report issue (currently placeholder)
- `POST /api/v1/orders/{id}/request_return/` - request return (placeholder)

### Cart

- `GET /api/v1/cart/` - get cart contents
- `POST /api/v1/cart/items/` - add item to cart
- `PATCH /api/v1/cart/items/{item_id}/` - update cart item
- `POST /api/v1/cart/items/{item_id}/delete/` - remove cart item
- `POST /api/v1/cart/clear/` - clear the cart

### Reviews

- `GET /api/v1/products/{product_id}/reviews/` - list reviews for a product
- `POST /api/v1/products/{product_id}/reviews/` - add review for a product
- `DELETE /api/v1/reviews/{review_id}/` - delete a review

### Payments

- `POST /api/v1/initiate/` - initiate payment
- `POST /api/v1/callback/payhero/` - PayHero callback endpoint
- `GET /api/v1/status/{payment_id}/` - get payment status
- `GET /api/v1/order/{order_id}/` - get payment by order

### Feedback

- `POST /api/v1/feedback/` - submit user feedback

## Notes

- JWT authentication is required for most user-facing endpoints.
- Swagger docs are the canonical API reference and are available at `/api/docs/`.
- The default database is SQLite (`db.sqlite3`). Supabase connection may be enabled with `SUPABASE_DB_URL`.
- The `addresses` app currently has no public API routes configured in `addresses/urls.py`.

## Useful Commands

```bash
python manage.py check
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```

## Testing

Run app tests with:

```bash
python manage.py test
```

## Project Structure

- `tradelink_django/` - Django project settings and root URL config
- `users/` - auth, registration, profile, admin user management
- `products/` - product CRUD and search
- `product_categories/` - category CRUD
- `orders/` - order lifecycle management
- `payments/` - PayHero payment flow
- `carts/` - cart operations
- `reviews/` - product review endpoints
- `feedback/` - feedback submission
- `addresses/` - delivery address models and future routes

## Contribution

To contribute, create a branch, add tests for new behavior, and ensure `python manage.py check` passes before creating a pull request.
