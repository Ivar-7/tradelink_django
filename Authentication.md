 I'll break down authentication for your three user types (Buyer, Vendor, Admin) — what endpoints you need, which tables are touched, and how data flows during login/signup.

---

## 1. AUTHENTICATION ENDPOINTS

### **Public Endpoints (No Token Required)**

| Endpoint | Method | Purpose | Who Uses It |
|---|---|---|---|
| `/auth/register` | `POST` | Create new buyer account | Buyers |
| `/auth/vendor/register` | `POST` | Create new vendor account | Vendors |
| `/auth/login` | `POST` | Login any user type (returns JWT) | All |
| `/auth/refresh` | `POST` | Refresh expired access token | All |
| `/auth/forgot-password` | `POST` | Send password reset email | All |
| `/auth/reset-password` | `POST` | Reset password with token | All |
| `/auth/verify-email` | `GET` | Verify email address | All |

### **Protected Endpoints (Token Required)**

| Endpoint | Method | Purpose | Who Uses It |
|---|---|---|---|
| `/auth/me` | `GET` | Get current user profile | All |
| `/auth/logout` | `POST` | Invalidate refresh token | All |
| `/auth/change-password` | `POST` | Change password while logged in | All |
| `/admin/vendors/:id/verify` | `PUT` | Admin verifies a vendor | Admin only |
| `/admin/users` | `GET` | List all users | Admin only |

---

## 2. TABLES AFFECTED & HOW

### **Table: `user`** — The Core Identity Table

| Column | How It's Affected |
|---|---|
| `user_id` | Auto-generated UUID on registration |
| `username` | Set by user, must be unique |
| `fname`, `lname` | Set during registration |
| `email_address` | Set during registration, must be unique, verified via token |
| `password_hash` | **bcrypt hash** stored (never plain text) |
| `gender`, `date_of_birth` | Optional profile fields |
| `role` | Set at registration: `customer`, `vendor`, or `admin` |

**Key Rule:** One `user` row = one login identity. Vendors are users first, then extended via `vendor_profile`.

---

### **Table: `vendor_profile`** — Vendor Extension

| Column | How It's Affected |
|---|---|
| `vendor_id` | Auto-generated when vendor registers |
| `user_id` | **Links to `user.user_id`** (1:1 relationship) |
| `vendor_type` | Set during vendor registration (`individual` or `business`) |
| `verification_doc_url` | Uploaded during registration, reviewed by admin |
| `is_verified` | `false` by default; admin flips to `true` after review |
| `default_dropoff_station_id` | Set by vendor later in dashboard |

**Flow:** Vendor registers → row created in `user` (role=`vendor`) → row created in `vendor_profile` (is_verified=`false`) → admin approves → `is_verified` becomes `true`.

---

### **Table: `vendor_store`** — Vendor's Shopfront

| Column | How It's Affected |
|---|---|
| `store_id` | Auto-generated when vendor creates store |
| `vendor_id` | Links to `vendor_profile.vendor_id` |
| `store_name`, `display_name` | Set by vendor in dashboard |
| `logo_url`, `banner_url` | Uploaded by vendor |
| `theme_preference` | Default `light`, changeable by vendor |

**Flow:** Vendor creates store after registration → row created here. Store is inactive until `vendor_profile.is_verified = true`.

---

## 3. DATA FLOW DURING AUTHENTICATION

### **Scenario A: Buyer Registration & Login**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   BUYER APP     │────▶│   BACKEND API   │────▶│   DATABASE      │
│  (Frontend)     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                      │
        │  POST /auth/register   │                      │
        │  {email, password,     │                      │
        │   fname, lname, ...}   │                      │
        │───────────────────────▶│                      │
        │                        │  INSERT INTO user    │
        │                        │  (role='customer')   │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ Row created
        │                        │◀─────────────────────│
        │  {user_id, email,      │                      │
        │   message: "Check      │                      │
        │   your email"}         │                      │
        │◀───────────────────────│                      │
        │                        │                      │
        │  [Buyer clicks email   │                      │
        │   verification link]   │                      │
        │                        │                      │
        │  GET /auth/verify-     │                      │
        │  email?token=xyz       │                      │
        │───────────────────────▶│                      │
        │                        │  UPDATE user          │
        │                        │  SET email_verified   │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ Email confirmed
        │  {message: "Email       │                      │
        │   verified"}           │                      │
        │◀───────────────────────│                      │
        │                        │                      │
        │  POST /auth/login      │                      │
        │  {email, password}     │                      │
        │───────────────────────▶│                      │
        │                        │  SELECT * FROM user   │
        │                        │  WHERE email=...       │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ User found
        │                        │  bcrypt.compare()     │
        │                        │  ✓ Password matches   │
        │                        │                      │
        │                        │  Generate JWT:        │
        │                        │  {user_id, role,      │
        │                        │   email, exp}         │
        │                        │                      │
        │  {access_token,         │                      │
        │   refresh_token,        │                      │
        │   user: {...}}          │                      │
        │◀───────────────────────│                      │
        │                        │                      │
        │  [Subsequent requests]  │                      │
        │  Header: Authorization: │                      │
        │  Bearer <access_token>  │                      │
        │───────────────────────▶│                      │
        │                        │  Verify JWT signature │
        │                        │  Extract user_id, role│
        │                        │  ✓ Allow if role=     │
        │                        │    'customer'         │
```

**Tables touched:** `user` only (for buyers).

---

### **Scenario B: Vendor Registration & Login**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  VENDOR APP     │────▶│   BACKEND API   │────▶│   DATABASE      │
│  (Frontend)     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                      │
        │  POST /auth/vendor/    │                      │
        │  register              │                      │
        │  {email, password,     │                      │
        │   fname, lname,        │                      │
        │   vendor_type,         │                      │
        │   verification_doc,    │                      │
        │   business_name, ...}  │                      │
        │───────────────────────▶│                      │
        │                        │  BEGIN TRANSACTION   │
        │                        │                      │
        │                        │  INSERT INTO user    │
        │                        │  (role='vendor')     │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ user row
        │                        │                      │
        │                        │  INSERT INTO         │
        │                        │  vendor_profile      │
        │                        │  (user_id=<new_id>,  │
        │                        │   is_verified=false) │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ vendor_profile row
        │                        │                      │
        │                        │  INSERT INTO         │
        │                        │  vendor_store        │
        │                        │  (vendor_id=<new_id>,│
        │                        │   store_name=...)    │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ vendor_store row
        │                        │                      │
        │                        │  COMMIT              │
        │                        │                      │
        │  {user_id, message:    │                      │
        │   "Pending admin        │                      │
        │   approval"}           │                      │
        │◀───────────────────────│                      │
        │                        │                      │
        │  [ADMIN ACTION]         │                      │
        │                        │                      │
        │  PUT /admin/vendors/    │                      │
        │  :id/verify             │                      │
        │  (Admin only)           │                      │
        │                        │                      │
        │                        │  UPDATE vendor_profile│
        │                        │  SET is_verified=true │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ Vendor approved
        │                        │                      │
        │  POST /auth/login       │                      │
        │  {email, password}      │                      │
        │───────────────────────▶│                      │
        │                        │  SELECT u.*, vp.*    │
        │                        │  FROM user u           │
        │                        │  JOIN vendor_profile vp│
        │                        │  ON u.user_id=vp.user_id│
        │                        │  WHERE email=...       │
        │                        │─────────────────────▶│
        │                        │                      │
        │                        │  Check: is_verified?  │
        │                        │  ✓ true → allow login │
        │                        │  ✗ false → reject:    │
        │                        │    "Pending approval" │
        │                        │                      │
        │  {access_token,         │                      │
        │   refresh_token,        │                      │
        │   user: {...,           │                      │
        │    is_verified: true}}  │                      │
        │◀───────────────────────│                      │
```

**Tables touched:** `user`, `vendor_profile`, `vendor_store`.

---

### **Scenario C: Admin Login**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ADMIN DASHBOARD│────▶│   BACKEND API   │────▶│   DATABASE      │
│  (Frontend)     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                      │
        │  POST /auth/login       │                      │
        │  {email, password}      │                      │
        │───────────────────────▶│                      │
        │                        │  SELECT * FROM user  │
        │                        │  WHERE email=...      │
        │                        │─────────────────────▶│
        │                        │                      │  ✓ User found
        │                        │                      │
        │                        │  Check role='admin'   │
        │                        │  ✓ Yes → proceed      │
        │                        │  ✗ No → 403 Forbidden │
        │                        │    "Admin access only"│
        │                        │                      │
        │                        │  Generate JWT with    │
        │                        │  role='admin'         │
        │                        │                      │
        │  {access_token,         │                      │
        │   refresh_token,        │                      │
        │   user: {role: 'admin'}}│                      │
        │◀───────────────────────│                      │
        │                        │                      │
        │  [Access admin-only     │                      │
        │   endpoints]            │                      │
        │                        │                      │
        │  GET /admin/users       │                      │
        │  Header: Bearer <token> │                      │
        │───────────────────────▶│                      │
        │                        │  Decode JWT           │
        │                        │  Check role == 'admin'│
        │                        │  ✓ Allow              │
        │                        │                      │
        │                        │  SELECT * FROM user   │
        │                        │─────────────────────▶│
        │  [List of all users]    │                      │
        │◀───────────────────────│                      │
```

**Tables touched:** `user` (admins are pre-seeded or promoted manually).

---

## 4. JWT TOKEN STRUCTURE

Your backend should issue two tokens:

### **Access Token** (Short-lived, 15-30 mins)
```json
{
  "user_id": "c695d51c-ae35-4cc3-9ed3-75042a4e0d1b",
  "email": "jdoe@example.com",
  "role": "customer",
  "vendor_id": null,
  "iat": 1714473600,
  "exp": 1714475400
}
```

### **Refresh Token** (Long-lived, 7-30 days)
```json
{
  "user_id": "c695d51c-ae35-4cc3-9ed3-75042a4e0d1b",
  "token_version": 1,
  "iat": 1714473600,
  "exp": 1715078400
}
```

**For vendors**, the access token includes `vendor_id` so the backend knows which vendor's data to serve without extra DB lookups.

---

## 5. AUTHORIZATION MATRIX (Who Can Do What)

| Action | Buyer | Vendor | Admin |
|---|---|---|---|
| Register | `/auth/register` | `/auth/vendor/register` | Pre-seeded only |
| Login | `/auth/login` | `/auth/login` | `/auth/login` |
| View own profile | ✅ | ✅ | ✅ |
| Edit own profile | ✅ | ✅ | ✅ |
| View products | ✅ | ✅ | ✅ |
| Buy products | ✅ | ❌ | ❌ |
| Create products | ❌ | ✅ (if verified) | ❌ |
| Manage orders | ❌ | ✅ (own only) | ✅ (all) |
| Verify vendors | ❌ | ❌ | ✅ |
| View all users | ❌ | ❌ | ✅ |
| View all payouts | ❌ | ❌ | ✅ |
| Access dashboard | ❌ | `/vendor/dashboard` | `/admin/dashboard` |

---

## 6. SECURITY RECOMMENDATIONS

| Layer | Implementation |
|---|---|
| **Password hashing** | bcrypt with cost factor 12+ |
| **Token storage** | HttpOnly cookies (not localStorage) |
| **HTTPS** | Required for all auth endpoints |
| **Rate limiting** | 5 login attempts per IP per minute |
| **Email verification** | Required before login for buyers; required before approval for vendors |
| **Vendor approval** | Admin must manually verify `vendor_profile.is_verified` |
| **Role checking** | Middleware validates JWT role on every protected route |
| **Token refresh** | Sliding window — refresh token rotates on each use |

---

## 7. SUMMARY: TABLE IMPACT

| Table | Buyer Auth | Vendor Auth | Admin Auth |
|---|---|---|---|
| `user` | ✅ Created, read, updated | ✅ Created, read, updated | ✅ Read (pre-seeded) |
| `vendor_profile` | ❌ Not touched | ✅ Created, updated by admin | ✅ Updated (verification) |
| `vendor_store` | ❌ Not touched | ✅ Created at registration | ❌ Not touched |
| `vendor_wallet` | ❌ Not touched | ✅ Auto-created (balance=0) | ❌ Not touched |
| `delivery_address` | ✅ Created after login | ❌ Not touched | ❌ Not touched |
| `cart` | ✅ Created on first add | ❌ Not touched | ❌ Not touched |

The key architectural decision is that **vendors are users first** — they authenticate through the same `user` table, but their extended data lives in `vendor_profile`, `vendor_store`, and `vendor_wallet`. The `role` column in `user` determines which dashboard they see and which endpoints they can hit.