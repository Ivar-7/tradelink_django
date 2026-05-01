   
 Here's the complete payment channel system for your marketplace — how vendors add payment details (like M-Pesa Till numbers) and receive payouts.

---

# 💳 PAYMENT CHANNEL SYSTEM: Vendors Add Till Numbers & Receive Payouts

---

## 1. NEW TABLE: `vendor_payment_channel`

This table stores **how vendors want to get paid**. It's separate from `vendor_profile` because one vendor can have multiple payment methods.

```sql
CREATE TABLE public.vendor_payment_channel (
  channel_id uuid NOT NULL DEFAULT gen_random_uuid(),
  vendor_id uuid NOT NULL REFERENCES public.vendor_profile(vendor_id),
  
  -- Channel Type
  channel_type text NOT NULL,           -- 'mpesa_till', 'mpesa_paybill', 'bank_transfer', 'paypal', 'stripe'
  channel_name text NOT NULL,           -- e.g., 'My M-Pesa Till', 'Business Bank Account'
  
  -- Account Details
  account_number text,                  -- Till number, Paybill number, Bank account, etc.
  account_name text,                    -- Name associated with the account
  bank_name text,                       -- For bank transfers
  bank_branch text,                     -- Branch code/name
  swift_code text,                      -- For international transfers
  phone_number text,                    -- For M-Pesa (phone linked to till)
  
  -- Status & Verification
  is_primary boolean DEFAULT false,     -- Default payout method
  is_verified boolean DEFAULT false,    -- Admin verified the channel
  verification_doc_url text,            -- Proof of ownership document
  status text DEFAULT 'active',         -- 'active', 'suspended', 'pending_verification'
  
  -- Metadata
  country text DEFAULT 'KE',
  currency text DEFAULT 'KES',
  created_at timestamp DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT valid_channel_type CHECK (
    channel_type IN ('mpesa_till', 'mpesa_paybill', 'bank_transfer', 'paypal', 'stripe', 'mobile_money')
  )
);
```

---

## 2. Sample Data: Vendor Payment Channels

| vendor | channel_name | type | account_number | phone | primary | verified | status |
|---|---|---|---|---|---|---|---|
| Bruce Wayne | Main M-Pesa Till | `mpesa_till` | 123456 | +254712345678 | ✅ | ✅ | active |
| Bruce Wayne | Equity Bank Account | `bank_transfer` | 1234567890 | — | ❌ | ✅ | active |
| John Doe | Business Paybill | `mpesa_paybill` | 987654 | +254723456789 | ✅ | ✅ | active |
| Clark Kent | Clark Till | `mpesa_till` | 555555 | +254734567890 | ✅ | ❌ | pending_verification |
| Vendor 4 | KCB Account | `bank_transfer` | 0987654321 | — | ✅ | ✅ | active |

> **Clark Kent's till is pending verification** — admin hasn't approved it yet, so he can't receive payouts.

---

## 3. Updated `vendor_payouts` Table

Now links to the payment channel used for each payout:

```sql
ALTER TABLE public.vendor_payouts 
ADD COLUMN payment_channel_id uuid REFERENCES public.vendor_payment_channel(channel_id),
ADD COLUMN payout_provider text,        -- 'mpesa', 'bank', 'paypal'
ADD COLUMN provider_reference text,     -- Reference from payment provider
ADD COLUMN provider_status text,        -- Status from provider's API
ADD COLUMN failure_reason text;         -- If payout failed, why?
```

---

## 4. Complete Payment Flow: Buyer Pays → Vendor Gets Paid

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: BUYER CHECKOUT & PAYMENT                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  Buyer (John Doe) checks out with $242 from Bruce Wayne's store                         │
│                                                                                         │
│  ┌─────────────┐    POST /payments/initiate    ┌─────────────┐                         │
│  │ E-commerce  │──────────────────────────────▶│   Backend   │                         │
│  │   Store     │                               │     API     │                         │
│  └─────────────┘                               └──────┬──────┘                         │
│                                                       │                                │
│  Payment Options:                                     ▼                                │
│  • M-Pesa (STK Push)                          ┌─────────────┐                         │
│  • Card (Stripe)                              │   PAYMENT   │                         │
│  • PayPal                                     │  PROVIDER   │                         │
│                                               │ (M-Pesa/    │                         │
│                                               │  Stripe)    │                         │
│                                               └──────┬──────┘                         │
│                                                      │                                │
│  ┌─────────────┐    STK Push to buyer's phone        │                                │
│  │   Buyer     │◀─────────────────────────────────────┘                                │
│  │   Phone     │    "Enter M-Pesa PIN to pay $242"                                     │
│  └──────┬──────┘                                                                    │
│         │                                                                             │
│         │ Buyer enters PIN                                                            │
│         │                                                                             │
│         ▼                                                                             │
│  ┌─────────────┐    Callback to platform    ┌─────────────┐                          │
│  │   M-Pesa    │───────────────────────────▶│   Backend   │                          │
│  │  (Safaricom)│    {status: "success",     │     API     │                          │
│  └─────────────┘     receipt: "QWERTY"      └──────┬──────┘                          │
│                                                    │                                 │
│                                                    ▼                                 │
│                                              ┌─────────────┐                        │
│                                              │   payment   │                        │
│                                              │   TABLE     │                        │
│                                              │  INSERT:    │                        │
│                                              │  status:    │                        │
│                                              │  "completed"│                        │
│                                              └──────┬──────┘                        │
│                                                     │                                │
└─────────────────────────────────────────────────────┼────────────────────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼────────────────────────────────┐
│                    STEP 2: PLATFORM COLLECTS MONEY                                │
├─────────────────────────────────────────────────────┼────────────────────────────────┤
│                                                     │                                │
│  Money goes to PLATFORM'S M-Pesa Paybill/Till       │                                │
│  (NOT directly to vendor)                           ▼                                │
│                                              ┌─────────────┐                         │
│  Platform M-Pesa Account:                    │   PLATFORM  │                         │
│  • Paybill: 123456 (Collections)             │   WALLET    │                         │
│                                              │  (Holds all │                         │
│                                              │   payments) │                         │
│                                              └──────┬──────┘                         │
│                                                     │                                │
│  Platform deducts commission (e.g., 5% = $12.10)    │                                │
│  Net to vendor: $242 - $12.10 = $229.90             │                                │
│                                                     ▼                                │
│                                              ┌─────────────┐                         │
│                                              │vendor_wallet│                         │
│                                              │(Bruce Wayne)│                         │
│                                              │pending: +   │                         │
│                                              │$229.90      │                         │
│                                              └─────────────┘                         │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼────────────────────────────────┐
│                    STEP 3: VENDOR REQUESTS PAYOUT                                     │
├─────────────────────────────────────────────────────┼────────────────────────────────┤
│                                                     │                                │
│  Bruce Wayne wants to withdraw $229.90              │                                │
│                                                     │                                │
│  ┌─────────────┐    POST /vendor/payouts            │                                │
│  │ Vendor Dash │────────────────────────────────────▶│                                │
│  │  (Frontend) │    { amount: 229.90,               │                                │
│  └─────────────┘     channel_id: "till_123" }       │                                │
│                                                     │                                │
│  System checks:                                     │                                │
│  ✓ available_balance >= 229.90?                     │                                │
│  ✓ payment_channel is verified?                     │                                │
│  ✓ channel status is 'active'?                      │                                │
│                                                     ▼                                │
│                                              ┌─────────────┐                         │
│                                              │vendor_payouts│                        │
│                                              │  INSERT:    │                        │
│                                              │  status:    │                        │
│                                              │  "pending"  │                        │
│                                              └──────┬──────┘                        │
│                                                     │                                │
└─────────────────────────────────────────────────────┼────────────────────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼────────────────────────────────┐
│                    STEP 4: ADMIN APPROVES & PROCESSES PAYOUT                          │
├─────────────────────────────────────────────────────┼────────────────────────────────┤
│                                                     │                                │
│  Admin reviews and approves                         │                                │
│                                                     │                                │
│  ┌─────────────┐    PUT /admin/payouts/:id/approve  │                                │
│  │ Admin Dash  │────────────────────────────────────▶│                                │
│  │  (Frontend) │    { status: "approved" }          │                                │
│  └─────────────┘                                    │                                │
│                                                     │                                │
│  System fetches vendor's channel:                   │                                │
│  SELECT * FROM vendor_payment_channel                │                                │
│  WHERE channel_id = 'till_123'                       │                                │
│  → M-Pesa Till, Number: 123456, Phone: +254712345678│                                │
│                                                     │                                │
│  System initiates B2C transfer:                       │                                │
│  { to: "+254712345678", amount: 22990,               │                                │
│    reason: "Vendor payout" }                         │                                │
│                                                     │                                │
│                              ┌─────────────┐        │                                │
│                              │   M-Pesa    │        │                                │
│                              │   Daraja    │        │                                │
│                              │    B2C API  │        │                                │
│                              └──────┬──────┘        │                                │
│                                     │                 │                                │
│                                     │ STK Push to     │                                │
│                                     │ vendor's phone  │                                │
│                                     ▼                 │                                │
│                              ┌─────────────┐         │                                │
│                              │Vendor Phone │         │                                │
│                              │+254712345678│        │                                │
│                              │"You received│        │                                │
│                              │ KES 22,990" │        │                                │
│                              └─────────────┘        │                                │
│                                                     │                                │
│  UPDATE vendor_payouts:                             ▼                                │
│    status = "completed"                        ┌─────────────┐                         │
│    provider_reference = "XYZ123"               │vendor_payouts│                        │
│    processed_at = NOW()                        │  UPDATE:    │                        │
│                                                │  status:    │                        │
│  UPDATE vendor_wallet:                         │  "completed"│                        │
│    available_balance -= 229.90                 │  provider:  │                        │
│    pending_balance -= 229.90                   │  "mpesa"    │                        │
│                                                └─────────────┘                        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Endpoints for Payment Channel Management

| Method | Endpoint | Description | Who |
|---|---|---|---|
| `POST` | `/vendor/payment-channels` | Add new payment channel | Vendor |
| `GET` | `/vendor/payment-channels` | List my channels | Vendor |
| `PUT` | `/vendor/payment-channels/:id` | Update channel | Vendor |
| `DELETE` | `/vendor/payment-channels/:id` | Remove channel | Vendor |
| `PUT` | `/vendor/payment-channels/:id/primary` | Set as default | Vendor |
| `GET` | `/admin/vendors/:id/payment-channels` | View vendor's channels | Admin |
| `PUT` | `/admin/payment-channels/:id/verify` | Verify channel | Admin |
| `PUT` | `/admin/payment-channels/:id/suspend` | Suspend channel | Admin |
| `POST` | `/vendor/payouts` | Request payout | Vendor |
| `GET` | `/vendor/payouts` | View payout history | Vendor |
| `GET` | `/admin/payouts` | View all payouts | Admin |
| `PUT` | `/admin/payouts/:id/approve` | Approve & process | Admin |
| `PUT` | `/admin/payouts/:id/reject` | Reject payout | Admin |

---

## 6. Tables Affected in Complete Flow

| Step | Table | Operation | Purpose |
|---|---|---|---|
| 1. Checkout | `orders` | INSERT | Creates order |
| 1. Checkout | `order_item` | INSERT | Links to products/vendors |
| 1. Checkout | `order_suborder` | INSERT | Splits by vendor |
| 2. Payment | `payment` | INSERT | Records buyer payment |
| 2. Payment | `vendor_wallet` | UPDATE | Credits vendor (pending) |
| 3. Payout Request | `vendor_payouts` | INSERT | Creates payout request |
| 3. Payout Request | `vendor_payment_channel` | SELECT | Gets payout method |
| 4. Admin Approval | `vendor_payouts` | UPDATE | Marks completed/failed |
| 4. Admin Approval | `vendor_wallet` | UPDATE | Deducts balance |
| 4. Admin Approval | `admin_audit_log` | INSERT | Logs action |

---

## 7. Key Insights

| # | Principle | Explanation |
|---|---|---|
| 1 | **Platform holds funds** | Buyer pays platform first. Vendor gets paid later via payout. This protects buyers (refunds possible) and ensures commission collection. |
| 2 | **Separate `vendor_payment_channel`** | `vendor_profile` = WHO the vendor is. `vendor_payment_channel` = HOW they get paid. One vendor can have multiple channels. |
| 3 | **Till vs Paybill** | Till = "Buy Goods" (best for vendors receiving money). Paybill = structured payments with account numbers (best for bills). Both work via M-Pesa Daraja API. |
| 4 | **Verification required** | Admin must verify channels before payouts. Prevents fraud (vendor can't add someone else's till number). |
| 5 | **B2C API for payouts** | Platform uses M-Pesa B2C (Business to Customer) API. Sends money FROM platform's business account TO vendor's till. Vendor gets STK push: "You have received KES X." |
| 6 | **Failure handling** | If till number is wrong → payout fails, logged in `failure_reason`. Vendor can update channel and retry. |

---

## 8. M-Pesa Integration Requirements

To make this work with real M-Pesa (Safaricom Kenya):

1. **Daraja Developer Account** — Register at [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. **Business Short Code** — Your platform's Paybill or Till number for collections
3. **Consumer Key & Secret** — API credentials from Daraja
4. **Passkey** — For Lipa Na M-Pesa Online (STK Push)
5. **Callback URLs** — HTTPS endpoints to receive payment confirmations
6. **B2C API Access** — For sending money to vendors (requires additional approval)

The B2C API sends money from your platform's business account to the vendor's registered M-Pesa number. The vendor receives a push notification: *"You have received KES [amount] from [Platform Name]"* .