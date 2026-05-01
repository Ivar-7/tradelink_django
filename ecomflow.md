  
 Here's the complete flow from **Product → Cart → Order → Vendor Dashboard**, showing exactly how data moves through your tables and how vendors see their orders.

---

# 🛒 COMPLETE E-COMMERCE FLOW: Product → Cart → Order → Vendor Dashboard

---

## STEP 1: Buyer Browses Products (E-commerce Store)
**Endpoint:** `GET /products` (public)

| product_id | product_name | price | stock | store_name | quantity | is_flash_sale |
|---|---|---|---|---|---|---|
| `bc1418fc-...` | Product 1 | $121 | 59 | Store 1 | 289 | False |
| `011e21a6-...` | Product 2 | $268 | 154 | Store 2 | 424 | True |
| `3f6bc5e4-...` | Product 4 | $111 | 183 | Store 4 | 62 | True |
| `48876cac-...` | Product 5 | $342 | 179 | Store 5 | 443 | False |

> Only **verified vendors**' products are shown. Alice Smith (Store 3) is hidden because `is_verified = false`.

---

## STEP 2: Buyer Adds Product to Cart
**Endpoint:** `POST /cart/items`

**Buyer:** John Doe (`user_id: b1e45b65-...`)

**Cart Operation:**
- Product: **Product 1** (from Bruce Wayne's Store 1)
- Stock Item: `6a86db50-...`
- Vendor: Bruce Wayne (`ecb4af56-...`)
- Quantity: **2**
- Unit Price: **$121**
- Total: **$242**

**Tables Created:**

**`cart`**
| cart_id | user_id | date_created | total_price |
|---|---|---|---|
| `5d337d30-...` | `b1e45b65-...` | 2026-05-01 15:06:50 | $242 |

**`cart_item`**
| cart_item_id | cart_id | stock_id | quantity |
|---|---|---|---|
| `0606523e-...` | `5d337d30-...` | `6a86db50-...` | 2 |

---

## STEP 3: Buyer Checkout → Order Created
**Endpoint:** `POST /orders`

**Order Details:**
- Order ID: `68203db5-...`
- Buyer: John Doe
- Address: USA, New York
- Pickup Station: Central Station
- Shipping: standard
- Total: **$242**
- Status: **pending**

**`orders`**
| order_id | user_id | address_id | station_id | shipping_type | total_amount | status |
|---|---|---|---|---|---|---|
| `68203db5-...` | `b1e45b65-...` | `950c57c0-...` | `0a1b6340-...` | standard | $242 | pending |

---

## STEP 4: Order Items Created
**Links order → stock → vendor**

**`order_item`**
| order_item_id | order_id | stock_id | quantity | unit_price | vendor_id |
|---|---|---|---|---|---|
| `f1a30949-...` | `68203db5-...` | `6a86db50-...` | 2 | $121 | `ecb4af56-...` |

> **🔑 CRITICAL:** The `vendor_id` column here is the **glue**. It tells the system Bruce Wayne sold this item. Without it, the vendor dashboard has no way to know this order belongs to Bruce.

---

## STEP 5: Order Suborder Created (Per Vendor)
**Splits the order by vendor**

**`order_suborder`**
| suborder_id | order_id | vendor_id | subtotal | status | created_at |
|---|---|---|---|---|---|
| `9ca03462-...` | `68203db5-...` | `ecb4af56-...` | $242 | pending | 2026-05-01 15:06:50 |

> If a buyer orders from **3 vendors**, there are **3 suborders**. Each vendor only sees their own.

---

## STEP 6: Stock Decreased + Inventory Movement
**Stock reserved for this order**

**`stock` (Updated)**
| stock_id | previous_qty | reserved | new_qty |
|---|---|---|---|
| `6a86db50-...` | 289 | 2 | **287** |

**`inventory_movement` (Audit Trail)**
| movement_id | stock_id | type | change | previous | new | reference_id |
|---|---|---|---|---|---|---|
| `aba99cd0-...` | `6a86db50-...` | sale | -2 | 289 | 287 | `68203db5-...` |

---

## STEP 7: Payment Recorded
**`payment`**
| payment_id | order_id | user_id | amount | provider | status |
|---|---|---|---|---|---|
| `cfd96dfc-...` | `68203db5-...` | `b1e45b65-...` | $242 | stripe | completed |

---

## STEP 8: Vendor Wallet Credited
**Bruce Wayne's pending balance increases**

**`vendor_wallet` (Updated)**
| wallet_id | vendor_id | available | **pending** | currency |
|---|---|---|---|---|
| `3d919069-...` | `ecb4af56-...` | $3,233.19 | **$254.51** ↑ | USD |

- Previous pending: $12.51
- Order amount: $242
- **New pending: $254.51**

---

## STEP 9: Shipment Created
**`shipment`**
| shipment_id | order_id | tracking_number | delivery_fee | status |
|---|---|---|---|---|
| `b879878b-...` | `68203db5-...` | TRK-1750 | $18.23 | pending |

---

# 🏪 STEP 10: Vendor Dashboard — How Bruce Wayne Sees the Order

**Endpoint:** `GET /vendor/orders` (with vendor JWT)

**JWT Token:** `{ user_id: '240cbac9-...', vendor_id: 'ecb4af56-...', role: 'vendor' }`

---

### Query 1: Get Suborders for This Vendor
```sql
SELECT * FROM order_suborder WHERE vendor_id = 'ecb4af56-...'
```

| suborder_id | order_id | subtotal | status |
|---|---|---|---|
| `9ca03462-...` | `68203db5-...` | $242 | pending |

---

### Query 2: Get Full Order Details (Joined)
```sql
SELECT so.*, o.order_date, o.shipping_type, u.fname, u.lname, u.email_address
FROM order_suborder so
JOIN orders o ON so.order_id = o.order_id
JOIN user u ON o.user_id = u.user_id
WHERE so.vendor_id = 'ecb4af56-...'
```

| suborder_id | order_id | subtotal | status | order_date | buyer | email | shipping |
|---|---|---|---|---|---|---|---|
| `9ca03462-...` | `68203db5-...` | $242 | pending | 2026-05-01 | John Doe | jdoe@... | standard |

---

### Query 3: Get Order Items (What Products Were Ordered)
```sql
SELECT oi.*, p.product_name, p.image_url
FROM order_item oi
JOIN stock s ON oi.stock_id = s.stock_id
JOIN product p ON s.product_id = p.product_id
WHERE oi.vendor_id = 'ecb4af56-...'
```

| order_item_id | order_id | product_name | quantity | unit_price |
|---|---|---|---|---|
| `f1a30949-...` | `68203db5-...` | Product 1 | 2 | $121 |

---

### Query 4: Get Shipment Tracking
```sql
SELECT s.* FROM shipment s
WHERE s.order_id IN (
  SELECT order_id FROM order_suborder WHERE vendor_id = 'ecb4af56-...'
)
```

| shipment_id | order_id | tracking_number | delivery_fee | status |
|---|---|---|---|---|
| `b879878b-...` | `68203db5-...` | TRK-1750 | $18.23 | pending |

---

### Query 5: Wallet Summary
```sql
SELECT * FROM vendor_wallet WHERE vendor_id = 'ecb4af56-...'
```

| wallet_id | available | pending | currency |
|---|---|---|---|
| `3d919069-...` | $3,233.19 | **$254.51** | USD |

---

### Query 6: Payout History
```sql
SELECT * FROM vendor_payouts WHERE vendor_id = 'ecb4af56-...'
```

| payout_id | amount | status | reference_code | requested_at |
|---|---|---|---|---|
| `823002ab-...` | $1,356.84 | pending | REF-1000 | 2025-03-01 |

---

## Complete Data Flow Diagram

```
┌─────────────────┐     GET /products          ┌─────────────────┐
│  E-commerce     │◀────────────────────────────│   Backend API   │
│  Store (Buyer)│                             │                 │
└────────┬────────┘                             └─────────────────┘
         │                                               │
         │ POST /cart/items                              │
         ▼                                               │
┌─────────────────┐     INSERT cart, cart_item    ┌─────────────────┐
│     CART        │──────────────────────────────▶│   DATABASE      │
│  (Temporary)    │                             │                 │
└────────┬────────┘                             │  ┌─────────┐  │
         │                                       │  │  cart   │  │
         │ POST /orders                            │  │cart_item│  │
         ▼                                       │  └─────────┘  │
┌─────────────────┐     INSERT orders             │               │
│    CHECKOUT     │─────────────────────────────▶│  ┌─────────┐  │
│   (Payment)     │                             │  │ orders  │  │
└────────┬────────┘     INSERT order_item         │  └─────────┘  │
         │            (with vendor_id!)          │               │
         │            INSERT order_suborder      │  ┌─────────┐  │
         │            (per vendor)               │  │order_item│  │
         │            UPDATE stock (qty--)       │  │order_sub │  │
         │            INSERT inventory_movement  │  │  order  │  │
         │            INSERT payment             │  └─────────┘  │
         │            UPDATE vendor_wallet      │               │
         │            INSERT shipment            │  ┌─────────┐  │
         │                                       │  │  stock  │  │
         │                                       │  │inventory│  │
         │                                       │  │movement │  │
         │                                       │  └─────────┘  │
         │                                       │               │
         │                                       │  ┌─────────┐  │
         │                                       │  │ payment │  │
         │                                       │  │vendor_  │  │
         │                                       │  │ wallet  │  │
         │                                       │  │shipment │  │
         │                                       │  └─────────┘  │
         │                                       └───────────────┘
         │
         │ GET /vendor/orders (Vendor JWT)
         ▼
┌─────────────────┐     Query: order_suborder     ┌─────────────────┐
│  Vendor Dash    │◀─────────────────────────────│   Backend API   │
│ (Bruce Wayne)   │     WHERE vendor_id = 'me'   │                 │
└─────────────────┘     JOIN orders, user, etc.   └─────────────────┘
```

---

## Key Tables & Their Roles in This Flow

| Table | Role in Flow | Who Writes | Who Reads |
|---|---|---|---|
| `product` | Catalog of items | Vendor | Buyer, Admin |
| `stock` | Inventory levels | Vendor (initial), System (on sale) | Buyer, Vendor, Admin |
| `cart` | Temporary shopping cart | Buyer | Buyer |
| `cart_item` | Items in cart | Buyer | Buyer |
| `orders` | Master order record | System (on checkout) | Buyer, Admin |
| `order_item` | **Links order to vendor** | System | **Vendor**, Admin |
| `order_suborder` | **Splits order by vendor** | System | **Vendor**, Admin |
| `payment` | Payment record | System | Buyer, Admin |
| `vendor_wallet` | Vendor earnings | System (credits), Admin (debits on payout) | **Vendor**, Admin |
| `shipment` | Delivery tracking | System | Buyer, **Vendor**, Admin |
| `inventory_movement` | Audit trail | System | Admin |

---

## The Critical Glue: `vendor_id`

| Table | Column | Why It Matters |
|---|---|---|
| `order_item` | `vendor_id` | Tells the system **who sold this item** |
| `order_suborder` | `vendor_id` | Tells the system **which vendor this suborder belongs to** |
| `stock` | `vendor_id` | Links inventory to the vendor who owns it |
| `product` | `vendor_id` | Links product to the vendor who created it |

> **Without `vendor_id` in `order_item` and `order_suborder`, the vendor dashboard has no way to know which orders belong to Bruce Wayne.** The buyer's `user_id` in `orders` only tells you who bought it — not who sold it.