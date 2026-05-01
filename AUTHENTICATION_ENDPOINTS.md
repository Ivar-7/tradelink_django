# Authentication Endpoints Implementation

## Overview
Implemented comprehensive authentication endpoints for the Tradelink Django backend with support for Buyer, Vendor, and Admin authentication flows.

## New Models Added

### User Model Extensions
- `is_email_verified`: Boolean flag for email verification status
- `email_verification_token`: Token for email verification
- `password_reset_token`: Token for password reset
- `password_reset_token_expiry`: Expiry timestamp for password reset token

### VendorProfile Model
New model to extend User with vendor-specific information:
- `user`: OneToOne relationship to User
- `vendor_type`: 'individual' or 'business'
- `business_name`: Vendor's business name
- `verification_doc_url`: URL to verification document
- `is_verified`: Vendor verification status (admin approval required)
- `verified_at`: Timestamp when vendor was verified

## New Endpoints

### Public Endpoints (No Authentication Required)

#### 1. Buyer Registration
- **Endpoint**: `POST /api/v1/auth/register/`
- **Purpose**: Create new buyer account
- **Request Body**:
  ```json
  {
    "email": "buyer@example.com",
    "username": "buyer_username",
    "password": "secure_password_123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "254712345678"
  }
  ```
- **Response**: User profile + JWT tokens
- **Status**: 201 Created

#### 2. Vendor Registration
- **Endpoint**: `POST /api/v1/auth/vendor/register/`
- **Purpose**: Create new vendor account
- **Request Body**:
  ```json
  {
    "email": "vendor@example.com",
    "username": "vendor_username",
    "password": "secure_password_123",
    "first_name": "Jane",
    "last_name": "Smith",
    "vendor_type": "business",
    "business_name": "Jane's Store",
    "verification_doc_url": "https://example.com/docs/verification.pdf"
  }
  ```
- **Response**: User profile + Vendor profile + JWT tokens + pending approval message
- **Status**: 201 Created
- **Note**: Vendors must be verified by admin before accessing vendor features

#### 3. Login
- **Endpoint**: `POST /api/v1/auth/login/`
- **Purpose**: Authenticate any user type (Buyer, Vendor, Admin)
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password_123"
  }
  ```
- **Response**: User profile + JWT tokens
- **Status**: 200 OK

#### 4. Refresh Token
- **Endpoint**: `POST /api/v1/auth/token/refresh/`
- **Purpose**: Refresh expired access token
- **Request Body**:
  ```json
  {
    "refresh": "refresh_token_value"
  }
  ```
- **Response**: New access token
- **Status**: 200 OK

#### 5. Verify Email
- **Endpoint**: `GET /api/v1/auth/verify-email/?token=verification_token`
- **Purpose**: Verify user email address
- **Query Parameters**: `token` (required) - Email verification token
- **Response**: Verification success message
- **Status**: 200 OK

#### 6. Forgot Password
- **Endpoint**: `POST /api/v1/auth/forgot-password/`
- **Purpose**: Request password reset link
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**: Reset link (remove from production!) + confirmation message
- **Status**: 200 OK

#### 7. Reset Password
- **Endpoint**: `POST /api/v1/auth/reset-password/`
- **Purpose**: Reset password using reset token
- **Request Body**:
  ```json
  {
    "token": "reset_token_value",
    "new_password": "new_secure_password_123",
    "new_password_confirm": "new_secure_password_123"
  }
  ```
- **Response**: Success message
- **Status**: 200 OK

### Protected Endpoints (Authentication Required)

#### 1. Get Current User Profile
- **Endpoint**: `GET /api/v1/users/me/`
- **Purpose**: Get authenticated user's profile
- **Authentication**: Bearer Token (Required)
- **Response**: User profile data
- **Status**: 200 OK

#### 2. Update Current User Profile
- **Endpoint**: `PATCH /api/v1/users/me/`
- **Purpose**: Update user's profile information
- **Authentication**: Bearer Token (Required)
- **Request Body**: Partial update of profile fields
- **Response**: Updated user profile
- **Status**: 200 OK

#### 3. Change Password
- **Endpoint**: `POST /api/v1/users/me/change-password/`
- **Purpose**: Change password for authenticated user
- **Authentication**: Bearer Token (Required)
- **Request Body**:
  ```json
  {
    "current_password": "current_password_123",
    "new_password": "new_password_456",
    "new_password_confirm": "new_password_456"
  }
  ```
- **Response**: Success message
- **Status**: 200 OK

#### 4. Logout
- **Endpoint**: `POST /api/v1/auth/logout/`
- **Purpose**: Logout user (blacklist refresh token)
- **Authentication**: Bearer Token (Required)
- **Request Body**:
  ```json
  {
    "refresh": "refresh_token_value"
  }
  ```
- **Response**: Success message
- **Status**: 200 OK

### Admin-Only Endpoints

#### 1. List All Users
- **Endpoint**: `GET /api/v1/admin/users/`
- **Purpose**: List all users with filtering options
- **Authentication**: Admin Bearer Token (Required)
- **Query Parameters**:
  - `role`: Filter by role (buyer, vendor, admin)
  - `is_active`: Filter by active status (true/false)
  - `search`: Search across email, username, name
- **Response**: Paginated user list
- **Status**: 200 OK

#### 2. Retrieve User Details
- **Endpoint**: `GET /api/v1/admin/users/{user_id}/`
- **Purpose**: Get detailed information about a specific user
- **Authentication**: Admin Bearer Token (Required)
- **Response**: User details
- **Status**: 200 OK

#### 3. Update User (Admin)
- **Endpoint**: `PATCH /api/v1/admin/users/{user_id}/`
- **Purpose**: Admin update user information
- **Authentication**: Admin Bearer Token (Required)
- **Request Body**: User fields to update
- **Response**: Updated user profile
- **Status**: 200 OK

#### 4. Delete User (Admin)
- **Endpoint**: `DELETE /api/v1/admin/users/{user_id}/`
- **Purpose**: Delete a user account
- **Authentication**: Admin Bearer Token (Required)
- **Status**: 204 No Content

#### 5. Activate User
- **Endpoint**: `POST /api/v1/admin/users/{user_id}/activate/`
- **Purpose**: Reactivate a deactivated user account
- **Authentication**: Admin Bearer Token (Required)
- **Status**: 200 OK

#### 6. Deactivate User
- **Endpoint**: `POST /api/v1/admin/users/{user_id}/deactivate/`
- **Purpose**: Deactivate a user account
- **Authentication**: Admin Bearer Token (Required)
- **Status**: 200 OK

#### 7. Verify Vendor (Admin)
- **Endpoint**: `PUT /api/v1/admin/vendors/{vendor_id}/verify/`
- **Purpose**: Approve or reject vendor registration
- **Authentication**: Admin Bearer Token (Required)
- **Request Body**:
  ```json
  {
    "status": "approved",
    "notes": "Additional review notes (optional)"
  }
  ```
- **Response**: Vendor profile with verification status
- **Status**: 200 OK

## JWT Token Structure

### Access Token (15-30 mins)
```json
{
  "token_type": "access",
  "exp": 1714475400,
  "iat": 1714475100,
  "jti": "...",
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "buyer|vendor|admin"
}
```

### Refresh Token (7-30 days)
```json
{
  "token_type": "refresh",
  "exp": 1715078400,
  "iat": 1714475100,
  "jti": "...",
  "user_id": "uuid"
}
```

## Serializers

### VendorRegisterSerializer
Handles vendor registration with vendor-specific fields

### VendorProfileSerializer
Represents vendor profile information

### ForgotPasswordSerializer
Email validation for password reset request

### ResetPasswordSerializer
Token and new password validation

### VerifyEmailSerializer
Email verification token validation

## Decorators & Schemas

All endpoints are documented with drf-spectacular decorators:
- `vendor_register_schema`: Vendor registration endpoint documentation
- `verify_email_schema`: Email verification endpoint documentation
- `forgot_password_schema`: Forgot password endpoint documentation
- `reset_password_schema`: Reset password endpoint documentation
- `admin_vendor_verify_schema`: Admin vendor verification endpoint documentation

All schemas are available in the Swagger UI at `/api/docs/`

## Key Implementation Details

1. **Email Verification**: Users receive verification tokens (not yet sent via email)
2. **Password Reset**: 24-hour token expiry for password reset
3. **Vendor Approval Flow**: Vendors are created with `is_verified=false` and must be approved by admin
4. **Role-Based Access**: Separate endpoints for user, vendor, and admin operations
5. **Token Management**: JWT tokens with refresh mechanism
6. **Error Handling**: Comprehensive error responses with validation details

## Error Responses

Standard error format:
```json
{
  "detail": "Error message",
  "field_name": ["Field-specific error"]
}
```

Status codes:
- `200`: Success
- `201`: Created
- `400`: Validation error / Bad request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not found
- `500`: Server error

## Next Steps

1. Set up email service for verification and password reset emails
2. Configure token expiry times in settings
3. Add rate limiting to auth endpoints
4. Implement HTTPS enforcement
5. Add CORS configuration
6. Create seed data for testing
7. Add comprehensive test coverage
