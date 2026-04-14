# Tradelink Backend API Integration Guide (Frontend)

This document is the frontend handoff for integrating with the Tradelink backend.

## 1. Base URLs

- Base API prefix: `/api/v1/`
- Swagger UI: `/api/docs/`
- OpenAPI schema JSON: `/api/schema/`

Examples:
- Local backend: `http://127.0.0.1:8000/api/v1/`
- Docs: `http://127.0.0.1:8000/api/docs/`

## 2. Authentication

JWT Bearer auth is required for protected endpoints.

Header format:

```http
Authorization: Bearer <access_token>
```

Token lifecycle:
1. Call `POST /api/v1/auth/login/`
2. Store `tokens.access` and `tokens.refresh`
3. Use `tokens.access` for API calls
4. Refresh with `POST /api/v1/auth/token/refresh/` when access token expires
5. Logout with `POST /api/v1/auth/logout/` (send refresh token)

## 3. Standard Error Format

Most errors return one of:

```json
{ "detail": "Error message" }
```

or validation map:

```json
{
  "field_name": ["Validation message"]
}
```

## 4. Auth and User Endpoints

### 4.1 Register
- Method: `POST`
- URL: `/api/v1/auth/register/`
- Auth: Public

Request:

```json
{
  "email": "jane@example.com",
  "username": "jane",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+254700000000",
  "gender": "F",
  "role": "buyer"
}
```

Response `201`:

```json
{
  "user": {
    "id": "uuid",
    "email": "jane@example.com",
    "username": "jane",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "phone_number": "+254700000000",
    "gender": "F",
    "date_of_birth": null,
    "role": "buyer",
    "date_joined": "2026-04-01T12:00:00Z"
  }
}
```

### 4.2 Login
- Method: `POST`
- URL: `/api/v1/auth/login/`
- Auth: Public

Request:

```json
{
  "email": "jane@example.com",
  "password": "StrongPass123!"
}
```

Response `200`:

```json
{
  "user": {
    "id": "uuid",
    "email": "jane@example.com",
    "username": "jane",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "phone_number": "+254700000000",
    "gender": "F",
    "date_of_birth": null,
    "role": "buyer",
    "date_joined": "2026-04-01T12:00:00Z"
  },
  "tokens": {
    "refresh": "jwt_refresh",
    "access": "jwt_access"
  }
}
```

### 4.3 Refresh Access Token
- Method: `POST`
- URL: `/api/v1/auth/token/refresh/`
- Auth: Public

Request:

```json
{
  "refresh": "jwt_refresh"
}
```

Response `200`:

```json
{
  "access": "new_access_token"
}
```

### 4.4 Logout
- Method: `POST`
- URL: `/api/v1/auth/logout/`
- Auth: Bearer

Request:

```json
{
  "refresh": "jwt_refresh"
}
```

Response `200`:

```json
{ "detail": "Successfully logged out." }
```

### 4.5 Get Current User
- Method: `GET`
- URL: `/api/v1/users/me/`
- Auth: Bearer

Response `200`: same `user` shape as login/register.

### 4.6 Update Current User
- Method: `PATCH`
- URL: `/api/v1/users/me/`
- Auth: Bearer

Request (partial):

```json
{
  "first_name": "Janet",
  "phone_number": "+254711111111"
}
```

Response `200`: updated user profile.

### 4.7 Change Password
- Method: `POST`
- URL: `/api/v1/users/me/change-password/`
- Auth: Bearer

Request:

```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password_confirm": "NewPass123!"
}
```

Response `200`:

```json
{ "detail": "Password changed successfully." }
```

## 5. Product Categories

Base: `/api/v1/categories/`

### 5.1 List Categories
- Method: `GET`
- URL: `/api/v1/categories/`
- Auth: Public

Response `200`:

```json
[
  {
    "id": "category_uuid",
    "name": "Electronics",
    "description": "Phones, laptops, accessories",
    "image_url": "https://..."
  }
]
```

### 5.2 Retrieve Category
- Method: `GET`
- URL: `/api/v1/categories/{id}/`
- Auth: Public

### 5.3 Create Category
- Method: `POST`
- URL: `/api/v1/categories/`
- Auth: Public (current implementation)

### 5.4 Update Category
- Method: `PUT/PATCH`
- URL: `/api/v1/categories/{id}/`
- Auth: Public (current implementation)

### 5.5 Delete Category
- Method: `DELETE`
- URL: `/api/v1/categories/{id}/`
- Auth: Public (current implementation)

## 6. Products

Base: `/api/v1/products/`

Frontend data contracts:

```ts
type Product = {
  id: string;
  name: string;
  price: number;
  description: string;
  stock_quantity: number;
  image_url: string;
  status: string;
  images: Array<{ id: string; image_url: string }>;
  category_id: string | null;
  vendor_id: string | null;
  vendor_name: string | null;
  average_rating: number;
  review_count: number;
  created_at: string | null;
};

type ProductListResponse = {
  products: Product[];
  total: number;
  page: string | number;
  limit: string | number;
};
```

### 6.1 List Products
- Method: `GET`
- URL: `/api/v1/products/`
- Auth: Public

Query params:
- `search`
- `category_id`
- `min_price`
- `max_price`
- `in_stock=true|false`
- `page`
- `limit`

Response `200`:

```json
{
  "products": [
    {
      "id": "product_uuid",
      "name": "iPhone 14",
      "price": 120000,
      "description": "...",
      "stock_quantity": 4,
      "image_url": "https://...",
      "status": "draft",
      "images": [],
      "category_id": "category_uuid",
      "vendor_id": "vendor_uuid",
      "vendor_name": "vendor_username",
      "average_rating": 4.5,
      "review_count": 11,
      "created_at": "2026-04-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": "1",
  "limit": "20"
}
```

Possible error responses:
- `400`: invalid query params
- `404`: product not found (retrieve)
- `500`: unexpected backend error

### 6.2 Search Products Alias
- Method: `GET`
- URL: `/api/v1/products/search/`
- Auth: Public
- Behavior: same as list with query params.

### 6.3 Retrieve Product
- Method: `GET`
- URL: `/api/v1/products/{id}/`
- Auth: Public

Response `200`: single `Product` object (same shape as list items).

### 6.4 Create Product
- Method: `POST`
- URL: `/api/v1/products/`
- Auth: Public (current implementation)

Request:

```json
{
  "name": "MacBook Pro",
  "price": 250000,
  "description": "16-inch",
  "stock_quantity": 8,
  "image_url": "https://...",
  "category": "category_uuid"
}
```

### 6.5 Update Product
- Method: `PUT/PATCH`
- URL: `/api/v1/products/{id}/`
- Auth: Public (current implementation)

### 6.6 Delete Product
- Method: `DELETE`
- URL: `/api/v1/products/{id}/`
- Auth: Public (current implementation)

## 7. Cart

All cart endpoints require Bearer auth.

Frontend data contracts:

```ts
type CartItem = {
  product_id: string | null;
  stock_id: string;
  product_name: string;
  product_image: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  cart_item_id: string;
};

type CartResponse = {
  id: string;
  user_id: string;
  date_created: string;
  total_price: number;
  products: CartItem[];
};
```

### 7.1 Get Cart
- Method: `GET`
- URL: `/api/v1/cart/`

Purpose:
- Fetch the authenticated user's current cart and all cart items.
- The cart items are returned in the `products` array.

Required headers:

```http
Authorization: Bearer <access_token>
```

Query params:
- None

Response `200`:

```json
{
  "id": "cart_uuid",
  "user_id": "user_uuid",
  "date_created": "2026-04-01T12:00:00Z",
  "total_price": 3500,
  "products": [
    {
      "product_id": "product_uuid",
      "stock_id": "stock_uuid",
      "product_name": "Product name",
      "product_image": "https://...",
      "quantity": 2,
      "unit_price": 1750,
      "subtotal": 3500,
      "cart_item_id": "cart_item_uuid"
    }
  ]
}
```

How to read cart items from response:
- Use `response.products` as the source of cart items.
- Each item in `products` has:
  - `cart_item_id`: unique row id for update/delete actions
  - `product_id`: product UUID (can be null if upstream product lookup fails)
  - `stock_id`: stock UUID used by backend foreign key
  - `quantity`, `unit_price`, `subtotal`

Empty cart response example (`200`):

```json
{
  "id": "cart_uuid",
  "user_id": "user_uuid",
  "date_created": "2026-04-01T12:00:00Z",
  "total_price": 0,
  "products": []
}
```

Possible error responses:
- `401`: missing/invalid token
- `502`: upstream DB/API failure
- `503`: transient upstream network issue

Frontend handling notes:
1. If `products.length === 0`, show Empty Cart UI.
2. Prefer `cart_item_id` for update/delete endpoint paths.
3. If `503`, retry with short backoff (max 2 retries).
4. If `502`, show retry action to user.

### 7.2 Add Item
- Method: `POST`
- URL: `/api/v1/cart/items/`

Request:

```json
{
  "product_id": "product_uuid",
  "quantity": 2
}
```

Notes for frontend:
- `product_id` can be either `product.product_id` or `stock.stock_id`.
- Backend resolves this to `stock_id` internally.
- `quantity` must be an integer `>= 1`.

Response `200`: full cart payload.

Error responses:
- `400`: validation error (example: `{ "product_id": ["Product stock not found."] }`)
- `401`: unauthorized
- `404`: product stock not found
- `502`: upstream DB/API failure
- `503`: transient upstream network issue

### 7.3 Update Item Quantity
- Method: `PATCH`
- URL: `/api/v1/cart/items/{item_id}/`

Request:

```json
{
  "product_id": "product_uuid",
  "quantity": 3
}
```

Response `200`: full cart payload.

Note: `product_id` is currently validated even on quantity update, so include it.

Error responses:
- `400`, `401`, `404`, `502`, `503`

### 7.4 Delete Item
- Method: `DELETE`
- URL: `/api/v1/cart/items/{item_id}/delete/`

Response `200`: full cart payload.

Error responses:
- `401`, `404`, `502`, `503`

### 7.5 Clear Cart
- Method: `POST`
- URL: `/api/v1/cart/clear/`

Response `200`: empty cart payload.

Error responses:
- `401`, `502`, `503`

Recommended frontend retry behavior for cart:
1. On `503`, retry with backoff (e.g., 500ms, 1s, 2s), max 2 retries.
2. On `502`, show a user-friendly error and allow manual retry.
3. On `400`, show field-level message from response body.

## 8. Orders

All order endpoints require Bearer auth.

Base: `/api/v1/orders/`

### 8.1 List Orders
- Method: `GET`
- URL: `/api/v1/orders/`
- Optional query: `status`

Response `200`:

```json
{
  "orders": [
    {
      "id": "order_uuid",
      "user_id": "user_uuid",
      "order_date": "2026-04-01T12:00:00Z",
      "order_amount": 3500,
      "products": [
        {
          "product_id": "product_uuid",
          "quantity": 2,
          "unit_price": 1750,
          "subtotal": 3500
        }
      ],
      "status": "pending",
      "shipping_method": "delivery",
      "tracking_number": null,
      "delivered_at": null,
      "cancelled_at": null,
      "cancellation_reason": "",
      "issue_report": null,
      "return_request": null,
      "delivery_address": {
        "county": "Nairobi",
        "city": "Nairobi",
        "postal_address": "00100",
        "user_contact": "+254700000000"
      }
    }
  ],
  "total": 1
}
```

### 8.2 Retrieve Order
- Method: `GET`
- URL: `/api/v1/orders/{id}/`

### 8.3 Create Order
- Method: `POST`
- URL: `/api/v1/orders/`

Request (from explicit products):

```json
{
  "shipping_method": "delivery",
  "products": [
    { "product_id": "product_uuid", "quantity": 2 }
  ],
  "delivery_address": {
    "county": "Nairobi",
    "city": "Nairobi",
    "postal_address": "00100",
    "user_contact": "+254700000000"
  }
}
```

Request (cart checkout):

```json
{
  "shipping_method": "pickup"
}
```

Response `201` (typical):

```json
{
  "id": "order_uuid",
  "user_id": "user_uuid",
  "order_date": "2026-04-14T12:00:00Z",
  "order_amount": 3500,
  "products": [
    {
      "product_id": "product_uuid",
      "quantity": 2,
      "unit_price": 1750,
      "subtotal": 3500
    }
  ],
  "status": "pending",
  "shipping_method": "delivery",
  "tracking_number": null,
  "delivered_at": null,
  "cancelled_at": null,
  "cancellation_reason": "",
  "delivery_address": {
    "county": "Nairobi",
    "city": "Nairobi",
    "postal_address": "00100",
    "user_contact": "+254700000000"
  }
}
```

Create order error responses:
- `400`: invalid payload (missing `shipping_method`, invalid products, bad address shape)
- `401`: missing or invalid Bearer token
- `404`: referenced product not found
- `502`: upstream order/cart service failure
- `503`: transient upstream network issue

### 8.4 Confirm Delivery
- Method: `POST`
- URL: `/api/v1/orders/{id}/confirm/`

### 8.5 Cancel Order
- Method: `POST`
- URL: `/api/v1/orders/{id}/cancel/`

Request:

```json
{ "reason": "Changed my mind" }
```

### 8.6 Report Issue (Not Yet Backed by Table)
- Method: `POST`
- URL: `/api/v1/orders/{id}/issue/`
- Current response: `501 Not Implemented`

Request:

```json
{
  "type": "damaged_item",
  "details": "Screen cracked"
}
```

### 8.7 Request Return (Not Yet Backed by Table)
- Method: `POST`
- URL: `/api/v1/orders/{id}/request_return/`
- Current response: `501 Not Implemented`

Request:

```json
{
  "reason": "Wrong size",
  "notes": "Need replacement"
}
```

### 8.8 Check Order Status
- Use `GET /api/v1/orders/{id}/` for a single order status screen.
- Use `GET /api/v1/orders/?status=<value>` for list filtering.

Common order statuses to handle in UI:
- `pending`: order created, waiting for payment/processing
- `processing`: vendor/system is preparing the order
- `shipped`: order is in transit
- `delivered`: completed successfully
- `cancelled`: cancelled by user/system

Order status page checklist:
1. Fetch order by id.
2. Show `status`, `order_amount`, `products`, and delivery info.
3. If status is `pending`, show pay-now CTA.
4. If status is `delivered`, show confirm/feedback/review actions.
5. If status is `cancelled`, show `cancellation_reason` when present.

### 8.9 Recommended Frontend Order Creation Flow
1. Validate cart or manual products locally before submit.
2. `POST /api/v1/orders/`.
3. On `201`, store returned `order.id` and navigate to payment step.
4. On `400`, show field-level errors.
5. On `503`, retry once automatically, then show manual retry button.

## 9. Reviews

### 9.1 List Product Reviews
- Method: `GET`
- URL: `/api/v1/reviews/products/{product_id}/reviews/`
- Auth: Public

Response `200`:

```json
{
  "reviews": [
    {
      "id": "review_uuid",
      "user_id": "user_uuid",
      "username": "jane",
      "product_id": "product_uuid",
      "rating_value": 5,
      "comment": "Great product",
      "verified_purchase": false,
      "helpful_count": 0,
      "date": "2026-04-01T12:00:00Z"
    }
  ],
  "total": 1,
  "average_rating": 5.0
}
```

### 9.2 Create Product Review
- Method: `POST`
- URL: `/api/v1/reviews/products/{product_id}/reviews/`
- Auth: Bearer

Request:

```json
{
  "rating_value": 4,
  "comment": "Very good"
}
```

### 9.3 Delete Review
- Method: `DELETE`
- URL: `/api/v1/reviews/reviews/{review_id}/`
- Auth: Bearer

## 10. Payments

All payment endpoints require Bearer auth.

### 10.1 Payment Methods (In-memory per process)

These are temporary and reset when server restarts.

- `GET /api/v1/payments/methods/`
- `POST /api/v1/payments/methods/`
- `PATCH /api/v1/payments/methods/{method_id}/default/`
- `DELETE /api/v1/payments/methods/{method_id}/`

Create method request:

```json
{
  "brand": "visa",
  "card_number": "4242 4242 4242 4242",
  "expiry_month": "12",
  "expiry_year": "28",
  "holder_name": "Jane Doe"
}
```

### 10.2 Create Payment
- Method: `POST`
- URL: `/api/v1/payments/`

Request:

```json
{
  "order_id": "order_uuid",
  "payment_provider": "mpesa",
  "amount": 3500,
  "phone_number": "+254700000000"
}
```

Card example:

```json
{
  "order_id": "order_uuid",
  "payment_provider": "card",
  "amount": 3500,
  "payment_method_id": "method_uuid"
}
```

Response `201`:

```json
{
  "id": "payment_uuid",
  "user_id": "user_uuid",
  "order_id": "order_uuid",
  "amount": 3500,
  "payment_provider": "mpesa",
  "status": "pending",
  "created_at": "2026-04-01T12:00:00Z",
  "phone_number": "+254700000000",
  "payment_method_id": ""
}
```

### 10.3 Verify Payment
- Method: `GET`
- URL: `/api/v1/payments/{payment_id}/verify/`

Response: payment object with current status.

### 10.4 Payment Status Values (Frontend)
Treat these as the main state machine for checkout UI:
- `pending`: payment initiated, waiting for provider confirmation
- `completed`: payment successful
- `failed`: payment failed

### 10.5 Recommended Payment Flow
1. Create order first with `POST /api/v1/orders/`.
2. Create payment with `POST /api/v1/payments/` using the returned `order_id`.
3. Save `payment.id` from response.
4. Poll `GET /api/v1/payments/{payment_id}/verify/` every 3 to 5 seconds (max 6 attempts).
5. If status becomes `completed`, route to success page.
6. If status becomes `failed`, show retry payment action.
7. If still `pending` after max attempts, show "Still processing" and allow manual refresh.

Payment error responses to handle:
- `400`: invalid payload (`order_id`, `amount`, provider fields)
- `401`: missing/invalid Bearer token
- `404`: payment/order not found
- `502`: upstream payment provider/service issue
- `503`: transient upstream network issue

Provider-specific request tips:
- For `mpesa`, always include `phone_number`.
- For `card`, include `payment_method_id` when using stored methods.
- Ensure `amount` matches order total shown to user.

## 11. Feedback

### 11.1 Submit Feedback
- Method: `POST`
- URL: `/api/v1/feedback/`
- Auth: Bearer

Request:

```json
{
  "type": "feature_request",
  "message": "Please add product wishlists"
}
```

Response `201`:

```json
{
  "success": true,
  "item": {
    "id": "feedback_uuid",
    "user_id": "user_uuid",
    "type": "feature_request",
    "message": "Please add product wishlists",
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

## 12. Frontend Integration Checklist

1. Set a shared API client with base `/api/v1/`.
2. Add Bearer token interceptor.
3. On `401`, call token refresh once and retry original request.
4. If refresh fails, clear session and redirect to login.
5. Handle `detail` and field-level validation errors in UI.
6. Treat order issue/return endpoints as unavailable (`501`) for now.
7. Do not rely on persistence of payment methods until DB-backed.

## 13. Quick Endpoint Map

- Auth:
  - `POST /auth/register/`
  - `POST /auth/login/`
  - `POST /auth/logout/`
  - `POST /auth/token/refresh/`
- User:
  - `GET /users/me/`
  - `PATCH /users/me/`
  - `POST /users/me/change-password/`
- Categories:
  - `GET/POST /categories/`
  - `GET/PUT/PATCH/DELETE /categories/{id}/`
- Products:
  - `GET/POST /products/`
  - `GET /products/search/`
  - `GET/PUT/PATCH/DELETE /products/{id}/`
- Cart:
  - `GET /cart/`
  - `POST /cart/items/`
  - `PATCH /cart/items/{item_id}/`
  - `DELETE /cart/items/{item_id}/delete/`
  - `POST /cart/clear/`
- Orders:
  - `GET/POST /orders/`
  - `GET /orders/{id}/`
  - `POST /orders/{id}/confirm/`
  - `POST /orders/{id}/cancel/`
  - `POST /orders/{id}/issue/` (501)
  - `POST /orders/{id}/request_return/` (501)
- Reviews:
  - `GET /reviews/products/{product_id}/reviews/`
  - `POST /reviews/products/{product_id}/reviews/`
  - `DELETE /reviews/reviews/{review_id}/`
- Payments:
  - `GET/POST /payments/methods/`
  - `PATCH /payments/methods/{method_id}/default/`
  - `DELETE /payments/methods/{method_id}/`
  - `POST /payments/`
  - `GET /payments/{payment_id}/verify/`
- Feedback:
  - `POST /feedback/`
