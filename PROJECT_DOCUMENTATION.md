# Tradelink Project Documentation

## 1. Product Vision

Tradelink is a marketplace product designed to connect Kenyan buyers with local vendors in a modern e-commerce experience. Its purpose is to make it easy for buyers to discover, compare, and purchase goods while empowering local sellers to open stores, manage inventory, and monetize orders.

---

## 2. What Tradelink Is

Tradelink is a digital marketplace product that brings together three core groups:

- **Buyers** who need a reliable place to purchase goods.
- **Vendors** who need a simple way to list, sell, and manage products.
- **Admins** who need to run the marketplace, approve sellers, and maintain trust.

---

## 3. Strategic Goals

Tradelink is designed to achieve these business goals:

- provide a seamless shopping journey for everyday customers
- onboard local vendors quickly and transparently
- reduce friction between product discovery and purchase
- support local payment options relevant to Kenyan commerce
- make marketplace operations visible and manageable for admins
- preserve trust through reviews, feedback, and status updates

---

## 4. Primary User Types

### 4.1 Buyer

A Buyer is the primary customer of the marketplace. They are focused on:
- discovering products
- comparing price, stock, and reviews
- adding items to a cart
- choosing delivery or pickup
- placing orders and tracking fulfillment
- providing feedback on purchases

### 4.2 Vendor

A Vendor is a marketplace seller. Their priorities are:
- applying to the platform
- setting up a store profile
- listing products with prices and stock levels
- monitoring sales and inventory
- managing payouts and wallet balances
- responding to marketplace notifications

### 4.3 Admin

An Admin is the marketplace operator. They handle:
- vendor approval workflows
- user and vendor account management
- marketplace reporting
- order exceptions, cancellations, and refunds
- platform governance and compliance

---

## 5. Key Marketplace Features

Tradelink is built around the following product capabilities:

- **Buyer storefront**: search, categories, product detail, cart, checkout, order history.
- **Vendor onboarding**: application, approval, profile setup, product publishing.
- **Inventory management**: stock tracking, product status, low-stock alerts.
- **Order lifecycle**: creation, confirmation, shipment, cancellation, delivery.
- **Payments**: order payment records, payment methods, provider flexibility.
- **Reviews and trust**: buyer reviews, ratings, review moderation.

---

## 6. User Flows (Summary)

- Discovery → Selection → Cart → Checkout → Order Tracking
- Vendor application → Approval → Store setup → Product management → Payouts
- Admin review → Monitoring → Exception handling

---

## 7. System Components (Project View)

- Frontend: React application (SPA) — handles product browsing, cart, checkout, and vendor dashboards.
- Backend: APIs and data storage powering the system.
- Integrations: Payment provider(s), delivery partners, optional Supabase or external services.

---

## 8. Product Entity Model (Conceptual)

The primary domain entities are represented in the data models section. Links:

- User — account and roles (buyer/vendor/admin)
- Product — catalog item with price, images, stock, and vendor link
- Category — hierarchical grouping for products
- Cart — temporary shopping basket
- Order — placed purchase with fulfillment status
- Payment — records payment attempts and status
- Review — buyer feedback and rating
- Feedback — general user messages and reports
- Address — shipping/contact address records

## 9. Data Models

### 9.1 User

- **id**: UUID primary key
- **email**: Email (unique, indexed)
- **username**: Text (unique)
- **first_name**: Text
- **last_name**: Text
- **phone_number**: Text
- **gender**: Male / Female / Other
- **date_of_birth**: Date (optional)
- **role**: Buyer / Vendor / Admin
- **is_active**: Boolean (default: true)
- **is_staff**: Boolean (default: false)
- **date_joined**: DateTime (auto)

### 9.2 ProductCategory

- **id**: UUID primary key
- **name**: Text (unique)
- **description**: Text (optional)
- **image_url**: URL (optional)
- **parent**: Foreign key to self (optional, for hierarchical categories)
- **sort_order**: Integer (default: 0)

### 9.3 Product

- **id**: UUID primary key
- **name**: Text
- **description**: Text
- **price**: Decimal (12 digits, 2 decimals)
- **stock_quantity**: Integer (default: 0)
- **image_url**: URL (optional)
- **category**: Foreign key to ProductCategory (optional)
- **vendor**: Foreign key to User
- **created_at**: DateTime (auto)
- **updated_at**: DateTime (auto)
- **average_rating**: Computed from reviews
- **review_count**: Computed count of reviews

### 9.4 Cart

- **id**: UUID primary key
- **user**: One-to-one to User
- **date_created**: DateTime (auto)
- **updated_at**: DateTime (auto)
- **total_price**: Computed sum of item subtotals

### 9.5 CartItem

- **id**: UUID primary key
- **cart**: Foreign key to Cart
- **product**: Foreign key to Product
- **quantity**: Integer (default: 1)
- **unit_price**: Decimal (10 digits, 2 decimals)
- **added_at**: DateTime (auto)
- **subtotal**: Computed (quantity × unit_price)
- Unique constraint: cart + product

### 9.6 Order

- **id**: UUID primary key
- **user**: Foreign key to User
- **order_date**: DateTime (auto)
- **order_amount**: Decimal (12 digits, 2 decimals)
- **status**: Pending / Confirmed / Shipped / Delivered / Cancelled
- **shipping_method**: Pickup / Delivery
- **tracking_number**: Text (optional)
- **delivered_at**: DateTime (optional)
- **cancelled_at**: DateTime (optional)
- **cancellation_reason**: Text (optional)
- **updated_at**: DateTime (auto)

### 9.7 OrderItem

- **id**: UUID primary key
- **order**: Foreign key to Order
- **product**: Foreign key to Product (optional)
- **product_name**: Text (captured at order time)
- **product_image**: URL (optional)
- **quantity**: Integer
- **unit_price**: Decimal (10 digits, 2 decimals)

### 9.8 DeliveryAddress

- **id**: UUID primary key
- **order**: One-to-one to Order
- **county**: Text
- **city**: Text
- **postal_address**: Text
- **user_contact**: Text (phone)

### 9.9 OrderIssueReport

- **id**: UUID primary key
- **order**: One-to-one to Order
- **type**: Text
- **details**: Text
- **reported_at**: DateTime (auto)

### 9.10 ReturnRequest

- **id**: UUID primary key
- **order**: One-to-one to Order
- **status**: Requested / Approved / Shipped Back / Refunded
- **reason**: Text
- **notes**: Text (optional)
- **created_at**: DateTime (auto)

### 9.11 Payment

- **id**: UUID primary key
- **user**: Foreign key to User
- **order**: Foreign key to Order (optional)
- **amount**: Decimal (12 digits, 2 decimals)
- **payment_provider**: Text
- **status**: Pending / Completed / Failed
- **created_at**: DateTime (auto)
- **updated_at**: DateTime (auto)

### 9.12 Review

- **id**: UUID primary key
- **user**: Foreign key to User
- **product**: Foreign key to Product
- **rating_value**: Integer (1-5)
- **comment**: Text (optional, max 500 chars)
- **verified_purchase**: Boolean (default: false)
- **helpful_count**: Integer (default: 0)
- **date**: DateTime (auto)
- Unique constraint: user + product

### 9.13 Feedback

- **id**: UUID primary key
- **user**: Foreign key to User
- **type**: Bug Report / Feature Request / General / Complaint
- **message**: Text
- **created_at**: DateTime (auto)

### 9.14 ProfileAddress

- **id**: UUID primary key
- **user**: Foreign key to User
- **label**: Text (optional)
- **country**: Text (default: Kenya)
- **county**: Text
- **city**: Text
- **line1**: Text (optional)
- **postal_address**: Text
- **user_email**: Email
- **user_contact**: Text (phone)
- **is_default**: Boolean (default: false)
- **created_at**: DateTime (auto)
- Unique constraint: user + label

10. Frontend

- Technology: React (single-page application)
- Responsibilities: UI, client-side routing, state management, form validation, and calling backend APIs.

11. Integration Notes

- APIs are versioned under `/api/v1/` (see backend code for exact routes).
- Payment and delivery integrations are pluggable — check `payments/` and integration config files.

12. Roadmap & Gaps

- Improve storefront UX and discovery features
- Add multi-vendor cart and routing support
- Complete payment settlement and reconciliation flows
- Add email/SMS notifications for key events

13. Metrics

- Registered buyers and vendors
- Conversion rate (browse → checkout)
- Average order value
- Order completion rate
- Review volume and average rating

---

## 14. Software Engineering Diagrams

### Required Diagrams

1. **Entity Relationship Diagram (ERD)**
   - Shows all database models and their relationships
   - Essential for understanding data structure

2. **System Architecture Diagram**
   - React frontend, Django backend, database, external integrations (payments, delivery)
   - Shows high-level component interactions

3. **User Role & Permission Matrix**
   - Buyer, Vendor, Admin roles and what each can do
   - Access control mapping

4. **Order Lifecycle State Machine**
   - States: Pending → Confirmed → Shipped → Delivered / Cancelled
   - Transitions and conditions

5. **Buyer User Flow Diagram**
   - Discovery → Product Detail → Cart → Checkout → Order Tracking → Review

6. **Vendor Onboarding Flow**
   - Application → Review → Approval → Profile Setup → Product Management

7. **Admin Dashboard Flow**
   - Vendor Approvals, Marketplace Monitoring, Order Governance

8. **API Architecture Diagram**
   - Frontend endpoints, backend routing structure, `/api/v1/` versioning

9. **Payment Flow Diagram**
   - Order creation → Payment initiation → Provider handling → Completion/Failure

10. **Cart & Order Relationship Diagram**
    - How cart items convert to order items, inventory updates

11. **Component Dependency Diagram**
    - Which Django apps depend on which (products, orders, payments, etc.)

12. **Notification/Event Flow**
    - Triggers for order status, reviews, feedback, approvals
