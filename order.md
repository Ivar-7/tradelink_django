Here's the complete **Order Tracking** system — how buyers, vendors, and admins track orders from placement to delivery.

---

# 📦 ORDER TRACKING SYSTEM

---

## 1. Current Order Status (All Perspectives)

### **`orders`** (Master Records)
| order_id | user_id | shipping_type | order_date | total_amount | status |
|---|---|---|---|---|---|
| `453f4de6-...` | John Doe | standard | 2025-04-12 11:00 | $128.47 | **pending** |
| `738cad9b-...` | Alice Smith | express | 2025-04-13 11:00 | $255.00 | **shipped** |
| `561db83f-...` | John Doe | pickup | 2025-04-14 11:00 | $499.99 | **delivered** |

### **`order_suborder`** (Per Vendor)
| suborder_id | order_id | vendor_id | subtotal | status |
|---|---|---|---|---|
| `963f390d-...` | `453f4de6-...` | Bruce Wayne | $128.47 | pending |
| `cc9fdbbd-...` | `738cad9b-...` | John Doe (Vendor) | $255.00 | shipped |
| `bd5ef783-...` | `561db83f-...` | Bruce Wayne | $499.99 | delivered |

### **`shipment`** (Tracking Info)
| shipment_id | order_id | tracking_number | status | last_update | pickup_time |
|---|---|---|---|---|---|
| `0ea02054-...` | `453f4de6-...` | TRK-9000 | pending | 2025-04-13 14:00 | — |
| `2fd80b02-...` | `738cad9b-...` | TRK-9001 | in_transit | 2025-04-14 14:00 | 2025-04-15 10:00 |
| `65ba642a-...` | `561db83f-...` | TRK-9002 | delivered | 2025-04-15 14:00 | 2025-04-16 09:00 |

---

## 2. Buyer Perspective — "My Orders" Page

**Endpoint:** `GET /orders` (with buyer JWT)

**Buyer:** John Doe

| order_id | order_date | total_amount | status | tracking_number | shipment_status |
|---|---|---|---|---|---|
| `453f4de6-...` | 2025-04-12 11:00 | $128.47 | pending | TRK-9000 | pending |
| `561db83f-...` | 2025-04-14 11:00 | $499.99 | delivered | TRK-9002 | delivered |

**SQL:**
```sql
SELECT * FROM orders 
WHERE user_id = '0f59caa0-4a57-41f1-ac86-9f9f282cad81'
```

---

## 3. Vendor Perspective — "Incoming Orders" Page

**Endpoint:** `GET /vendor/orders` (with vendor JWT)

**Vendor:** Bruce Wayne

| suborder_id | order_id | subtotal | status | buyer | tracking_number | shipment |
|---|---|---|---|---|---|---|
| `963f390d-...` | `453f4de6-...` | $128.47 | pending | John Doe | TRK-9000 | pending |
| `bd5ef783-...` | `561db83f-...` | $499.99 | delivered | John Doe | TRK-9002 | delivered |

**SQL:**
```sql
SELECT so.*, o.order_date, u.fname, u.lname, s.tracking_number
FROM order_suborder so
JOIN orders o ON so.order_id = o.order_id
JOIN user u ON o.user_id = u.user_id
LEFT JOIN shipment s ON o.order_id = s.order_id
WHERE so.vendor_id = '49b54d0d-ef35-49f8-9e2a-d08f8f9b08c8'
```

---

## 4. Admin Perspective — "All Orders" Dashboard

**Endpoint:** `GET /admin/orders` (with admin JWT)

**Admin:** Diana Prince

| order_id | buyer | order_date | total | status | tracking | shipment |
|---|---|---|---|---|---|---|
| `453f4de6-...` | John Doe | 2025-04-12 | $128.47 | pending | TRK-9000 | pending |
| `738cad9b-...` | Alice Smith | 2025-04-13 | $255.00 | shipped | TRK-9001 | in_transit |
| `561db83f-...` | John Doe | 2025-04-14 | $499.99 | delivered | TRK-9002 | delivered |

---

## 5. Order Status Lifecycle

```
pending → processing → shipped → out_for_delivery → delivered
   ↓          ↓           ↓            ↓                ↓
 Buyer     Vendor     Vendor       Courier          Buyer
placed    accepted   shipped      delivering       received
order     order      package      package          package

CANCELLATION:
pending → cancelled (by buyer or admin)

RETURN:
delivered → return_requested → return_approved → returned → refunded
```

---

## 6. New Table: `order_status_history` (Audit Trail)

Tracks **every status change** with who did it and when.

```sql
CREATE TABLE public.order_status_history (
  history_id uuid NOT NULL DEFAULT gen_random_uuid(),
  order_id uuid NOT NULL REFERENCES public.orders(order_id),
  suborder_id uuid REFERENCES public.order_suborder(suborder_id),
  
  old_status text NOT NULL,
  new_status text NOT NULL,
  
  changed_by uuid NOT NULL REFERENCES public.user(user_id),
  changed_by_role text NOT NULL,  -- 'buyer', 'vendor', 'admin', 'system'
  
  notes text,      -- "Package damaged in transit"
  location text,   -- "Nairobi Hub", "Downtown Station"
  
  created_at timestamp DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT order_status_history_pkey PRIMARY KEY (history_id)
);

CREATE INDEX idx_order_status_history_order ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_created ON order_status_history(created_at);
```

### Sample Data

| history_id | order_id | old_status | new_status | role | notes | time |
|---|---|---|---|---|---|---|
| `3f768de8-...` | `453f4de6-...` | created | pending | buyer | Order placed | 2025-04-12 11:00 |
| `4a32b262-...` | `738cad9b-...` | created | pending | buyer | Order placed | 2025-04-13 11:00 |
| `c657bea9-...` | `738cad9b-...` | pending | processing | vendor | Vendor accepted | 2025-04-13 14:00 |
| `8ec3c7e0-...` | `738cad9b-...` | processing | shipped | vendor | Handed to courier | 2025-04-14 09:00 |
| `6795aa04-...` | `561db83f-...` | shipped | out_for_delivery | admin | At destination station | 2025-04-15 08:00 |
| `aca8f8c0-...` | `561db83f-...` | out_for_delivery | delivered | buyer | Buyer confirmed | 2025-04-16 09:00 |

---

## 7. Tracking Timeline for Order #2 (Shipped)

**Order:** `738cad9b-...` | **Tracking:** TRK-9001 | **Status:** shipped

```
👤 2025-04-13 11:00 | created         → pending         | buyer   | Order placed
🏪 2025-04-13 14:00 | pending         → processing      | vendor  | Vendor accepted order
🏪 2025-04-14 09:00 | processing      → shipped         | vendor  | Package handed to courier
```

**Shipment Details:**
- Origin: West Hub
- Destination: Central Station
- Courier: AGT-002
- Est. Arrival: 2025-04-16

---

## 8. Order Tracking Endpoints

| Method | Endpoint | Description | Who |
|---|---|---|---|
| `GET` | `/orders` | List my orders | Buyer |
| `GET` | `/orders/:id` | Order details with tracking | Buyer |
| `GET` | `/orders/:id/tracking` | Full timeline | Buyer |
| `PUT` | `/orders/:id/cancel` | Cancel (if pending) | Buyer |
| `PUT` | `/orders/:id/confirm-delivery` | Mark received | Buyer |
| `GET` | `/vendor/orders` | Incoming orders | Vendor |
| `PUT` | `/vendor/orders/:id/accept` | Accept order | Vendor |
| `PUT` | `/vendor/orders/:id/ship` | Mark shipped | Vendor |
| `PUT` | `/vendor/orders/:id/reject` | Reject order | Vendor |
| `GET` | `/admin/orders` | All orders | Admin |
| `PUT` | `/admin/orders/:id/status` | Update status | Admin |
| `PUT` | `/admin/orders/:id/assign-courier` | Assign delivery | Admin |
| `GET` | `/shipments/:trackingNumber` | Public tracking | Anyone |

---

## 9. Complete Tracking Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BUYER PLACES ORDER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  POST /orders → INSERT orders (status=pending)                        │
│              → INSERT order_item (links stock + vendor)               │
│              → INSERT order_suborder (per vendor, pending)              │
│              → INSERT shipment (tracking_number generated)            │
│              → INSERT order_status_history (created→pending)          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Vendor gets notification
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VENDOR ACCEPTS ORDER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  PUT /vendor/orders/:id/accept                                        │
│    → UPDATE order_suborder SET status='processing'                    │
│    → INSERT order_status_history (pending→processing)               │
│    → Reserve stock via inventory_movement                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Vendor prepares package
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VENDOR SHIPS ORDER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  PUT /vendor/orders/:id/ship                                          │
│    → UPDATE order_suborder SET status='shipped'                       │
│    → UPDATE shipment SET status='in_transit'                          │
│    → INSERT order_status_history (processing→shipped)               │
│    → UPDATE stock SET quantity -= order_qty                           │
│    → INSERT inventory_movement (sale)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Courier picks up
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 COURIER DELIVERS TO STATION                             │
├─────────────────────────────────────────────────────────────────────────┤
│  PUT /admin/orders/:id/status                                           │
│    → UPDATE shipment SET status='out_for_delivery'                    │
│    → INSERT order_status_history (shipped→out_for_delivery)          │
│    → Notification: "Your order is ready for pickup"                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Buyer picks up
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 BUYER CONFIRMS DELIVERY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  PUT /orders/:id/confirm-delivery                                     │
│    → UPDATE orders SET status='delivered'                             │
│    → UPDATE order_suborder SET status='delivered'                     │
│    → UPDATE shipment SET status='delivered', pickup_time=NOW()        │
│    → INSERT order_status_history (out_for_delivery→delivered)         │
│    → UPDATE vendor_wallet: available += subtotal, pending -= subtotal │
│    → Vendor can now request payout!                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Key Tables & Their Roles

| Table | Role in Tracking | Who Queries |
|---|---|---|
| `orders` | Master record. `status` = overall state | Buyer, Admin |
| `order_suborder` | Per-vendor split. `status` = vendor's part | Vendor, Admin |
| `shipment` | Physical tracking. `tracking_number`, location, status | All |
| `order_status_history` | Audit trail. WHO changed WHAT and WHEN | Admin |
| `payment` | Payment status. Money received? | Buyer, Admin |
| `vendor_wallet` | Earnings. `pending` → `available` on delivery | Vendor |
| `pickup_station` | Where packages drop/pick up | All |

---

**Bottom line:** Order tracking connects `orders` → `suborders` → `shipments` → `status_history` → `wallet`. Each table serves a different audience (buyer sees orders, vendor sees suborders, admin sees everything), and `order_status_history` creates an immutable audit trail of every change.