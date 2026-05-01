# E-Commerce Flow Implementation

Complete multi-vendor e-commerce platform with order management, inventory tracking, and vendor wallet system.

## Features

### Product Browsing (Public)
- Browse products from verified vendors
- Filter by category, price, search
- View stock options from different vendors
- Pagination support

### Shopping Cart
- Add products to cart
- Update quantities
- Remove items
- Clear cart
- Real-time price calculations

### Checkout & Orders
- Multi-vendor order support (one order = multiple vendor suborders)
- Automatic stock reservation
- Inventory audit trail
- Order status tracking
- Order cancellation with stock reversal

### Vendor Dashboard
- View all orders assigned to vendor
- Track order status per vendor
- Access wallet balance
- Request payouts
- Inventory management

### Stock & Inventory
- Vendor-managed stock per product
- Quantity tracking with reservations
- Movement audit trail (sales, returns, adjustments)
- Flash sale support with discounts

### Vendor Wallet & Payouts
- Available balance (shipped orders)
- Pending balance (awaiting shipment)
- Total earned/withdrawn tracking
- Payout history
- Multiple payout methods (M-Pesa, Bank Transfer)

## Core Models

### Order Flow
```
Order (master order)
  ├─ OrderItem (product x quantity with vendor_id)
  ├─ OrderSuborder (one per vendor involved)
  ├─ Payment (transaction record)
  └─ Shipment (tracking info)
```

### Inventory
```
Stock (product inventory per vendor)
  ├─ quantity (total available)
  ├─ reserved_quantity (in pending orders)
  └─ InventoryMovement (audit trail)
```

### Vendor Wallet
```
VendorWallet (per vendor)
  ├─ available_balance (can be withdrawn)
  ├─ pending_balance (awaiting shipment)
  └─ VendorPayout (payout history)
```

## API Endpoints

### Shopping (Public)

**GET /api/v1/products/browse/**
- Browse all products from verified vendors
- Query: `?search=name&category_id=uuid&min_price=0&max_price=1000&page=1`

**GET /api/v1/products/browse/{id}/**
- Get product details

**GET /api/v1/products/browse/{id}/stock_options/**
- Get available stock entries (different vendors/prices)

### Cart (Authenticated)

**GET /api/v1/cart/**
- Get user's shopping cart with items and total

**POST /api/v1/cart/add_item/**
```json
{
  "product_id": "uuid",
  "stock_id": "uuid",
  "quantity": 1
}
```

**POST /api/v1/cart/remove_item/**
```json
{
  "product_id": "uuid"
}
```

**POST /api/v1/cart/clear/**
- Clear all items from cart

### Orders (Authenticated)

**GET /api/v1/orders/**
- List user's orders with summary

**GET /api/v1/orders/{id}/**
- Get order details with items, vendors, shipment

**POST /api/v1/orders/checkout/**
```json
{
  "shipping_method": "pickup",
  "station_id": "uuid (optional)"
}
```
- Creates order from cart
- Automatically handles multi-vendor suborders
- Returns order details

**POST /api/v1/orders/{id}/cancel/**
```json
{
  "reason": "Changed mind"
}
```
- Cancel order and reverse all changes

### Vendor Dashboard (Vendor Only)

**GET /api/v1/vendor/dashboard/my_orders/**
- List all orders assigned to vendor

**GET /api/v1/vendor/dashboard/wallet/**
- Get vendor's wallet details

**POST /api/v1/vendor/dashboard/request_payout/**
```json
{
  "amount": "1000.00",
  "payout_method": "mpesa"
}
```

### Vendor Product Management (Vendor Only)

**GET /api/v1/vendor/products/**
- List vendor's products

**POST /api/v1/vendor/products/**
```json
{
  "name": "Product Name",
  "description": "...",
  "price": "99.99",
  "stock_quantity": 100,
  "image_url": "...",
  "category": "uuid",
  "is_active": true
}
```

**PATCH /api/v1/vendor/products/{id}/**
- Update product

**DELETE /api/v1/vendor/products/{id}/**
- Delete product

**POST /api/v1/vendor/products/{id}/toggle_active/**
- Enable/disable product

**GET /api/v1/vendor/products/{id}/stock/**
- Get stock entries for product

**POST /api/v1/vendor/products/{id}/update_stock/**
```json
{
  "quantity": 100,
  "price": "99.99"
}
```

**GET /api/v1/vendor/products/{id}/inventory_movements/**
- Get inventory audit trail

## Order Lifecycle

### Order Creation (Checkout)
1. **Validate Cart**: Ensure items in stock
2. **Create Master Order**: Store total amount, shipping method
3. **Create OrderItems**: Each item includes vendor_id (THE GLUE)
4. **Group by Vendor**: Identify unique vendors
5. **Create Suborders**: One per vendor with subtotal
6. **Reserve Stock**: Increment reserved_quantity
7. **Create Inventory Movement**: Audit entry for each item
8. **Credit Wallet**: Add to vendor pending_balance
9. **Clear Cart**: Remove items from cart

### Order Confirmation
- Status: pending → confirmed
- Stock: reserved_quantity → quantity decrease
- Wallet: No change (balance still pending)

### Order Shipment
- Status: confirmed → shipped
- Wallet: pending_balance → available_balance
- Create Shipment record with tracking

### Order Delivery
- Status: shipped → delivered
- Shipment status: shipped → delivered

### Order Cancellation
- **Before Confirmed**: Reverse all changes
  - Restore stock to vendor
  - Remove from wallet
  - Delete inventory movements
  
- **After Confirmed**: Must allow returns (separate flow)

## Stock Management

### Available Quantity Calculation
```
available_quantity = quantity - reserved_quantity
```

### Flash Sales
- Set `is_flash_sale = True`
- Add `discount_percentage`
- `discounted_price` calculated automatically

## Vendor Wallet Flow

### Balance Tracking
```
total_earned = sum of all shipped order subtotals
available_balance = ready for withdrawal
pending_balance = awaiting shipment
total_withdrawn = sum of completed payouts
```

### Payout Process
1. Vendor requests payout (amount ≤ available_balance)
2. Create VendorPayout record (status: pending)
3. Deduct from available_balance
4. Increment total_withdrawn
5. Payment processor handles transfer
6. Update payout status to processed

## Inventory Audit Trail

Each stock change creates InventoryMovement record:
- Movement type: sale, return, restock, adjustment, cancellation
- Previous/new quantities
- Reference ID (order_id, return_id, etc.)
- Timestamp

## Permissions

### Public
- Browse products
- View categories

### Authenticated User
- View/manage own cart
- View/manage own orders
- Submit returns/reports

### Vendor User
- Manage own products
- Manage own stock
- View orders assigned to them
- View/request payouts
- View inventory history

### Admin
- View all orders (admin endpoints)
- Manage vendors
- View all vendor wallets

## Key Implementation Details

### Multi-Vendor Orders
- Single checkout creates multiple suborders
- Each vendor gets separate suborder (tracks their portion)
- OrderItem.vendor_id identifies which vendor sold each product
- Vendor dashboard queries filter by vendor_id in order_items/suborders

### Stock Reservation
- Cart doesn't reserve stock (user can abandon cart)
- Checkout reserves stock
- Confirmation actually decreases stock
- Cancellation reverses reservation and stock decrease

### Wallet Mechanics
- Pending balance locked until order shipped
- Available balance can be withdrawn anytime
- Total earned purely informational
- Withdrawal creates audit trail

### Vendor Suspension Impact
- Suspended vendor's products hidden in browse
- Orders to/from suspended vendor still visible
- Payouts to suspended vendor blocked
- Admin can override for edge cases

## Database Indexes

- Order: user_id, status, created_at
- OrderItem: order_id, vendor_id
- OrderSuborder: (vendor_id, created_at)
- Stock: (vendor_id, product_id, quantity)
- InventoryMovement: (stock_id, created_at), reference_id
- VendorWallet: vendor_id
- VendorPayout: (vendor_id, created_at), status

## Testing Checklist

- [ ] Product browse filters work correctly
- [ ] Cart operations (add/remove/clear)
- [ ] Multi-vendor checkout
- [ ] Stock reservation and confirmation
- [ ] Inventory movement audit trail
- [ ] Vendor wallet balance updates
- [ ] Shipment status changes wallet
- [ ] Order cancellation reverses changes
- [ ] Vendor dashboard shows only their orders
- [ ] Payout requests deduct from available balance
- [ ] Permissions enforced correctly
- [ ] Pagination works for product lists
- [ ] Flash sale discount calculated correctly
