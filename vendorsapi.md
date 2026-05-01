  
  
  
     
 Here's the complete picture of **how administrators manage vendors** in your system — the endpoints, tables affected, and exactly how data moves.

---

# 🛡️ ADMINISTRATOR VENDOR MANAGEMENT SYSTEM

---

## 1. ADMIN VENDOR MANAGEMENT ENDPOINTS

All require: `Authorization: Bearer <admin_jwt_token>`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/vendors` | List all vendors with filters |
| `GET` | `/admin/vendors/pending` | Vendors awaiting verification |
| `GET` | `/admin/vendors/:id` | Full vendor profile + store + wallet |
| `PUT` | `/admin/vendors/:id/verify` | **Approve/reject vendor** |
| `PUT` | `/admin/vendors/:id/suspend` | **Suspend vendor immediately** |
| `PUT` | `/admin/vendors/:id/activate` | Reactivate suspended vendor |
| `GET` | `/admin/vendors/:id/products` | All products by vendor |
| `GET` | `/admin/vendors/:id/orders` | All orders for vendor |
| `GET` | `/admin/vendors/:id/payouts` | Payout requests by vendor |
| `PUT` | `/admin/vendors/:id/payouts/:payoutId` | **Approve/reject payout** |
| `GET` | `/admin/vendors/:id/wallet` | Wallet balance & history |
| `PUT` | `/admin/vendors/:id/dropoff` | Assign pickup station |
| `DELETE` | `/admin/vendors/:id` | Soft-delete (Super Admin) |
| `GET` | `/admin/vendors/analytics` | Platform-wide KPIs |

---

## 2. TABLES AFFECTED & HOW

| Table | Columns Admin Modifies | Purpose |
|---|---|---|
| **`vendor_profile`** | `is_verified`, `default_dropoff_station_id` | Core gatekeeping |
| **`vendor_store`** | `is_active` (cascades) | Store visibility |
| **`vendor_wallet`** | Read-only | Financial oversight |
| **`vendor_payouts`** | `status`, `processed_at`, `reference_code` | Payout workflow |
| **`product`** | `is_active` (bulk hide/show) | Product moderation |
| **`stock`** | `is_flash_sale` | Inventory control |
| **`orders`** | `status` (cancel/refund) | Order intervention |
| **`pickup_station`** | `is_active` | Station management |
| **`admin_audit_log`** | INSERT only | Compliance trail |

---

## 3. CURRENT VENDOR STATUS (Admin Dashboard View)

| vendor_id | store_name | vendor | email | type | status | wallet | products | orders |
|---|---|---|---|---|---|---|---|---|
| `0bfca61a-...` | Store 1 | Bruce Wayne | bwayne@... | individual | ✅ VERIFIED | $3,233.19 | 1 | 1 |
| `c5f91a8b-...` | Store 2 | John Doe | jdoe@... | business | ✅ VERIFIED | $1,447.64 | 1 | 1 |
| `fd34f55b-...` | Store 3 | Alice Smith | asmith@... | individual | ⏳ PENDING | $3,708.71 | 1 | 1 |
| `36209048-...` | Store 4 | Clark Kent | ckent@... | business | ⏳ PENDING | $4,471.68 | 1 | 1 |
| `3cfe5b01-...` | Store 5 | — | — | individual | ✅ VERIFIED | $2,167.42 | 1 | 1 |

**Quick Stats:** 5 vendors | 3 verified | 2 pending | $15,028.64 total wallet

---

## 4. DETAILED DATA FLOW FOR KEY ACTIONS

### ACTION 1: Admin Verifies a Vendor
`PUT /admin/vendors/:id/verify`

```json
// Request Body
{
  "is_verified": true,
  "admin_notes": "Documents verified. Business license valid."
}
```

**Database Operations:**
```sql
-- 1. Approve vendor
UPDATE vendor_profile
SET is_verified = true
WHERE vendor_id = 'fd34f55b-...';

-- 2. Activate store (now visible to buyers)
UPDATE vendor_store
SET is_active = true
WHERE vendor_id = 'fd34f55b-...';

-- 3. Log the action
INSERT INTO admin_audit_log 
(admin_user_id, action, target_type, target_id, details, created_at)
VALUES 
('dprince_admin_id', 'VENDOR_VERIFY', 'vendor_profile', 
 'fd34f55b-...', 'Verified by admin. Business license valid.', NOW());
```

**Tables affected:** `vendor_profile`, `vendor_store`, `admin_audit_log`

---

### ACTION 2: Admin Suspends a Vendor
`PUT /admin/vendors/:id/suspend`

```json
// Request Body
{
  "reason": "Counterfeit products reported",
  "suspend_duration_days": 30
}
```

**Database Operations:**
```sql
-- 1. Suspend vendor profile
UPDATE vendor_profile
SET is_verified = false,
    suspension_reason = 'Counterfeit products',
    suspended_at = NOW(),
    suspension_expires_at = NOW() + INTERVAL '30 days'
WHERE vendor_id = '0bfca61a-...';

-- 2. Hide store
UPDATE vendor_store
SET is_active = false
WHERE vendor_id = '0bfca61a-...';

-- 3. Hide all products
UPDATE product
SET is_active = false
WHERE vendor_id = '0bfca61a-...';

-- 4. Disable flash sales
UPDATE stock
SET is_flash_sale = false
WHERE vendor_id = '0bfca61a-...';

-- 5. Log action
INSERT INTO admin_audit_log ...
```

**Cascade Effects:**
- ✅ Store invisible to buyers
- ✅ Products removed from search
- ✅ Existing orders still ship (don't punish buyers)
- ❌ New orders blocked
- ❌ Wallet frozen (can't withdraw)

**Tables affected:** `vendor_profile`, `vendor_store`, `product`, `stock`, `admin_audit_log`

---

### ACTION 3: Admin Approves Payout
`PUT /admin/vendors/:id/payouts/:payoutId`

```json
// Request Body
{
  "status": "completed",
  "reference_code": "BANK-TRANSFER-987654"
}
```

**Database Operations:**
```sql
-- 1. Mark payout complete
UPDATE vendor_payouts
SET status = 'completed',
    reference_code = 'BANK-TRANSFER-987654',
    processed_at = NOW()
WHERE payout_id = 'payout_001';

-- 2. Deduct from wallet
UPDATE vendor_wallet
SET available_balance = available_balance - 476.34,
    updated_at = NOW()
WHERE vendor_id = '0bfca61a-...';

-- 3. Financial audit trail
INSERT INTO inventory_movement 
(movement_id, movement_type, quantity_change, previous_quantity, 
 new_quantity, reference_id, created_at)
VALUES 
(gen_random_uuid(), 'payout', -476.34, 3233.19, 2756.85, 
 'payout_001', NOW());

-- 4. Log admin action
INSERT INTO admin_audit_log ...
```

**Tables affected:** `vendor_payouts`, `vendor_wallet`, `inventory_movement`, `admin_audit_log`

---

### ACTION 4: Admin Assigns Pickup Station
`PUT /admin/vendors/:id/dropoff`

```json
// Request Body
{
  "station_id": "09e39766-cc98-...",
  "reason": "Closest to vendor location"
}
```

```sql
UPDATE vendor_profile
SET default_dropoff_station_id = '09e39766-cc98-...'
WHERE vendor_id = 'c5f91a8b-...';
```

**Tables affected:** `vendor_profile`, `admin_audit_log`

---

## 5. ADMIN VENDOR WORKFLOW (Complete Lifecycle)

```
┌─────────────┐     POST /auth/vendor/register      ┌─────────────┐
│ Vendor App  │────────────────────────────────────▶│   Backend   │
└─────────────┘                                     └──────┬──────┘
                                                           │
                              ┌────────────────────────────┼────────────────────────────┐
                              │                            │                            │
                              ▼                            ▼                            ▼
                        ┌─────────┐                 ┌─────────────┐               ┌─────────────┐
                        │  user   │                 │vendor_profile│              │vendor_store │
                        │role=    │                 │is_verified=  │              │(inactive)   │
                        │vendor   │                 │FALSE         │              │             │
                        └─────────┘                 └─────────────┘               └─────────────┘
                                                           │
                              GET /admin/vendors/pending   │
┌─────────────┐◀───────────────────────────────────────────┘
│  Admin Dash │     Returns pending vendors with docs
│  (Frontend) │
└──────┬──────┘
       │
       │ PUT /admin/vendors/:id/verify
       │ {is_verified: true}
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │
       │ UPDATE vendor_profile SET is_verified=true
       │ UPDATE vendor_store SET is_active=true
       ▼
┌─────────────┐     Vendor sells products, earns money     ┌─────────────┐
│  LIVE VENDOR│◀───────────────────────────────────────────│ Vendor Dash │
│  (Verified) │                                            │  (Frontend) │
└──────┬──────┘                                            └─────────────┘
       │
       │ POST /vendor/payouts (requests withdrawal)
       ▼
┌─────────────┐
│vendor_payouts│
│status=PENDING│
└──────┬──────┘
       │
       │ Admin reviews & approves
       ▼
┌─────────────┐     PUT /admin/vendors/:id/payouts/:pid   ┌─────────────┐
│   Backend   │◀──────────────────────────────────────────│  Admin Dash │
└──────┬──────┘                                            │  (Frontend) │
       │                                                   └─────────────┘
       │ UPDATE vendor_payouts SET status='completed'
       │ UPDATE vendor_wallet (deduct amount)
       ▼
┌─────────────┐
│  PAYOUT DONE│
└─────────────┘
```

---

## 6. PERMISSION MATRIX

| Action | Admin | Vendor | Buyer |
|---|---|---|---|
| View all vendors | ✅ | ❌ | ❌ |
| Verify/reject vendor | ✅ | ❌ | ❌ |
| Suspend vendor | ✅ | ❌ | ❌ |
| View vendor wallet | ✅ | ✅ (own) | ❌ |
| Approve payouts | ✅ | ❌ | ❌ |
| View vendor orders | ✅ | ✅ (own) | ❌ |
| Edit vendor products | ✅ | ✅ (own) | ❌ |
| Assign pickup station | ✅ | ❌ | ❌ |
| Delete vendor account | ✅ (Super) | ❌ | ❌ |
| View platform analytics | ✅ | ❌ | ❌ |

---

## 7. NEW TABLE YOU NEED: `admin_audit_log`

Not in your current schema — add this for compliance:

```sql
CREATE TABLE public.admin_audit_log (
  log_id uuid NOT NULL DEFAULT gen_random_uuid(),
  admin_user_id uuid NOT NULL REFERENCES public.user(user_id),
  action text NOT NULL,           -- 'VENDOR_VERIFY', 'PAYOUT_APPROVE', etc.
  target_type text NOT NULL,      -- 'vendor_profile', 'vendor_payouts'
  target_id uuid NOT NULL,
  details text,
  ip_address inet,
  created_at timestamp DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT admin_audit_log_pkey PRIMARY KEY (log_id)
);

CREATE INDEX idx_admin_audit_admin ON admin_audit_log(admin_user_id);
CREATE INDEX idx_admin_audit_target ON admin_audit_log(target_id);
CREATE INDEX idx_admin_audit_action ON admin_audit_log(action);
```

---

## 8. KEY PRINCIPLES

| Principle | Implementation |
|---|---|
| **Gatekeeping** | No vendor sells without admin approval (`is_verified`) |
| **Financial Oversight** | All payouts require admin approval |
| **Operational Control** | Suspend cascades: profile → store → products → stock |
| **Audit Trail** | Every admin action logged with who/what/when/why |
| **Data Isolation** | Vendors see own data only; admins see everything |

---

**Bottom line:** The admin is the **gatekeeper, accountant, and police** of your marketplace. They control who enters, who gets paid, and who gets removed — with every action permanently logged for accountability.