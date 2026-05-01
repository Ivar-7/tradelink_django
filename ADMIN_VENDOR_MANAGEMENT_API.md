# Admin Vendor Management API Documentation

## Overview

Complete implementation of the administrator vendor management system for the Tradelink marketplace. This system allows admins to verify vendors, suspend accounts, manage payouts, and maintain an audit trail of all actions.

## Implementation Summary

### Models Added/Updated

#### 1. **VendorProfile Model Extensions**
Added the following fields to support vendor management:
- `is_suspended`: Boolean flag for vendor suspension status
- `suspension_reason`: Text field for suspension reason
- `suspended_at`: Timestamp when vendor was suspended
- `suspension_expires_at`: Timestamp when suspension expires
- `default_dropoff_station_id`: UUID for assigned pickup station
- `status` property: Returns vendor status (pending/active/suspended)

#### 2. **New AdminAuditLog Model**
```python
- id: UUID (Primary Key)
- admin: ForeignKey to User (with PROTECT delete)
- action: Choice field (15+ action types)
- target_type: String ('vendor', 'product', 'order', etc.)
- target_id: UUID of target
- details: Text field for action details
- ip_address: GenericIPAddressField (optional)
- created_at: Auto-created timestamp
```

### Services Created

#### 1. **AdminVendorService**
Methods for vendor management:
- `verify_vendor()` - Approve/reject vendor applications
- `suspend_vendor()` - Suspend with reason and duration
- `activate_vendor()` - Reactivate suspended vendors
- `assign_dropoff_station()` - Assign pickup location

#### 2. **AuditLogService**
Methods for logging:
- `log_action()` - Create audit log entry
- `get_logs()` - Retrieve logs with filters

## API Endpoints

### 1. List All Vendors
**Endpoint:** `GET /api/v1/admin/vendors/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** GET

**Query Parameters:**
- `status`: Filter by status (verified | pending | suspended)
- `vendor_type`: Filter by type (individual | business)
- `search`: Search by email or business name

**Response (200 OK):**
```json
{
  "total": 5,
  "vendors": [
    {
      "id": "uuid",
      "user_email": "vendor@example.com",
      "user_name": "John Doe",
      "vendor_type": "business",
      "business_name": "John's Store",
      "is_verified": true,
      "is_suspended": false,
      "status": "active",
      "created_at": "2024-05-01T10:00:00Z"
    }
  ]
}
```

### 2. Get Vendor Details
**Endpoint:** `GET /api/v1/admin/vendors/{vendor_id}/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** GET

**Response (200 OK):**
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "email": "vendor@example.com",
    "username": "vendor_user",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    ...
  },
  "vendor_type": "business",
  "business_name": "John's Store",
  "verification_doc_url": "https://example.com/doc.pdf",
  "is_verified": true,
  "verified_at": "2024-05-01T11:00:00Z",
  "is_suspended": false,
  "suspension_reason": null,
  "suspended_at": null,
  "suspension_expires_at": null,
  "default_dropoff_station_id": "uuid",
  "status": "active",
  "created_at": "2024-05-01T10:00:00Z",
  "updated_at": "2024-05-01T12:00:00Z"
}
```

### 3. Verify/Reject Vendor
**Endpoint:** `PUT /api/v1/admin/vendors/{vendor_id}/verify/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** PUT

**Request Body:**
```json
{
  "status": "approved",
  "notes": "Business license verified. Documentation complete."
}
```

**Response (200 OK):**
```json
{
  "detail": "Vendor approved.",
  "vendor_profile": { ... }
}
```

**Side Effects:**
- Updates `vendor_profile.is_verified = true/false`
- Updates `vendor_profile.verified_at` timestamp
- Creates audit log entry
- (Future) Sends notification to vendor

### 4. Suspend Vendor
**Endpoint:** `PUT /api/v1/admin/vendors/{vendor_id}/suspend/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** PUT

**Request Body:**
```json
{
  "reason": "Counterfeit products reported by customers",
  "suspend_duration_days": 30
}
```

**Response (200 OK):**
```json
{
  "detail": "Vendor suspended for 30 days.",
  "vendor": { ... }
}
```

**Database Operations:**
```sql
UPDATE vendor_profile
SET is_suspended = true,
    suspension_reason = 'Counterfeit products...',
    suspended_at = NOW(),
    suspension_expires_at = NOW() + INTERVAL '30 days'
WHERE id = :vendor_id;

UPDATE vendor_store SET is_active = false WHERE vendor_id = :vendor_id;
UPDATE product SET is_active = false WHERE vendor_id = :vendor_id;
UPDATE stock SET is_flash_sale = false WHERE vendor_id = :vendor_id;
```

**Cascade Effects:**
- ✅ Store hidden from buyers
- ✅ Products removed from listings
- ✅ Flash sales disabled
- ✅ Wallet frozen
- ⚠️ Existing orders continue to ship
- ⚠️ New orders blocked

### 5. Reactivate Vendor
**Endpoint:** `PUT /api/v1/admin/vendors/{vendor_id}/activate/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** PUT

**Request Body:**
```json
{}
```

**Response (200 OK):**
```json
{
  "detail": "Vendor activated.",
  "vendor": { ... }
}
```

**Database Operations:**
```sql
UPDATE vendor_profile
SET is_suspended = false,
    suspension_reason = '',
    suspended_at = NULL,
    suspension_expires_at = NULL
WHERE id = :vendor_id;
```

### 6. Assign Pickup Station
**Endpoint:** `PUT /api/v1/admin/vendors/{vendor_id}/assign-station/`  
**Authentication:** Admin Bearer Token (Required)  
**Method:** PUT

**Request Body:**
```json
{
  "station_id": "uuid",
  "reason": "Closest to vendor location"
}
```

**Response (200 OK):**
```json
{
  "detail": "Pickup station assigned.",
  "vendor": { ... }
}
```

**Database Operations:**
```sql
UPDATE vendor_profile
SET default_dropoff_station_id = :station_id
WHERE id = :vendor_id;
```

## Serializers

### AdminVendorListSerializer
For listing vendors (minimal data)

### AdminVendorDetailSerializer
For detailed vendor view (all vendor data + user info)

### AdminVendorVerifySerializer
```json
{
  "is_verified": boolean,
  "notes": string (optional)
}
```

### AdminVendorSuspendSerializer
```json
{
  "reason": string (required),
  "suspend_duration_days": integer (1-365, default=30)
}
```

### AdminVendorActivateSerializer
Empty request body

### AdminVendorAssignStationSerializer
```json
{
  "station_id": UUID,
  "reason": string (optional)
}
```

### AdminAuditLogSerializer
For retrieving audit logs

## Audit Logging

Every admin action is logged in `AdminAuditLog` table with:
- Admin user who performed action
- Action type (vendor_verify, vendor_suspend, etc.)
- Target (vendor, product, order)
- Target ID
- Detailed description
- Timestamp
- IP address (optional)

### Available Actions
- `vendor_verify` - Vendor verified
- `vendor_reject` - Vendor rejected
- `vendor_suspend` - Vendor suspended
- `vendor_activate` - Vendor activated
- `payout_approve` - Payout approved
- `payout_reject` - Payout rejected
- `product_hide` - Product hidden
- `product_show` - Product shown
- `user_delete` - User deleted
- `other` - Other actions

## Permission Model

All admin vendor endpoints require `IsAdminUser` permission:
```python
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'
```

## Status Codes

- `200 OK` - Successful GET/PUT/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Validation error or invalid state
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - User lacks admin permission
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Unexpected server error

## Error Responses

Standard error format:
```json
{
  "detail": "Error message",
  "field_name": ["Validation error for field"]
}
```

## Workflow Example

### Vendor Verification Workflow

1. **Vendor applies** → `POST /auth/vendor/register/`
   - User table: created with role='vendor'
   - VendorProfile: created with is_verified=false

2. **Admin reviews pending** → `GET /api/v1/admin/vendors/?status=pending`
   - Shows all unverified vendors

3. **Admin verifies** → `PUT /api/v1/admin/vendors/{id}/verify/`
   - Request: `{"status": "approved"}`
   - Result: vendor_profile.is_verified = true
   - Audit log created
   - (Future) Email sent to vendor

4. **Vendor can now sell** → Products visible to buyers, orders accepted

### Vendor Suspension Workflow

1. **Issue detected** (counterfeit products, bad behavior, etc.)

2. **Admin suspends** → `PUT /api/v1/admin/vendors/{id}/suspend/`
   - Request: `{"reason": "...", "suspend_duration_days": 30}`
   - Result: Vendor hidden, products hidden, wallet frozen

3. **Duration expires or admin reactivates** → `PUT /api/v1/admin/vendors/{id}/activate/`
   - Result: Vendor can sell again

## Swagger Documentation

All endpoints are auto-documented in Swagger UI at `/api/docs/`:
- Full request/response schemas
- Parameter descriptions
- Error responses
- Example values
- Try-it-out functionality

## Testing

Test the endpoints:

```bash
# List vendors
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/v1/admin/vendors/

# Get vendor details
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/v1/admin/vendors/{vendor_id}/

# Verify vendor
curl -X PUT -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"approved","notes":"Verified"}' \
  http://localhost:8000/api/v1/admin/vendors/{vendor_id}/verify/

# Suspend vendor
curl -X PUT -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Counterfeit products","suspend_duration_days":30}' \
  http://localhost:8000/api/v1/admin/vendors/{vendor_id}/suspend/

# Activate vendor
curl -X PUT -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/v1/admin/vendors/{vendor_id}/activate/

# Assign station
curl -X PUT -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"station_id":"uuid","reason":"Closest location"}' \
  http://localhost:8000/api/v1/admin/vendors/{vendor_id}/assign-station/
```

## Files Modified

- [users/models.py](users/models.py) - Added VendorProfile suspension fields, AdminAuditLog model
- [users/serializers.py](users/serializers.py) - Added 6 new serializers
- [users/views.py](users/views.py) - Added 5 new view classes
- [users/schemas.py](users/schemas.py) - Added 5 schema decorators
- [users/urls.py](users/urls.py) - Added 6 new URL routes
- [users/services.py](users/services.py) - Added AdminVendorService, AuditLogService

## Future Enhancements

- Email notifications to vendors on verification/suspension
- Bulk vendor operations (batch verify, suspend)
- Custom suspension reasons dropdown
- Payout approval workflow integration
- Analytics dashboard for admin
- Vendor appeal/dispute system
- Product moderation workflow
- Advanced filtering and sorting
