# 🔐 Security Requirements for Admin System

## Overview
Security features to implement before production deployment of the admin authentication system.

---

## 1. Cloudflare Turnstile (Bot Protection)

### Purpose
Prevent automated bot attacks on admin registration and login endpoints.

### Implementation
- **Add Turnstile to registration form**: Require captcha completion before allowing admin registration
- **Add Turnstile to login form**: Protect login endpoint from brute force attempts
- **Server-side verification**: Validate Turnstile token on backend before processing request

### Dependencies
```bash
# Frontend
npm install @cloudflare/turnstile

# Backend - add to requirements.txt
requests==2.31.0  # Already installed
```

### Configuration
```python
# backend/.env
TURNSTILE_SECRET_KEY=your_cloudflare_secret_key
TURNSTILE_SITE_KEY=your_cloudflare_site_key  # For frontend
```

### Endpoints to Protect
- `POST /api/auth/register` - Admin registration
- `POST /api/auth/login` - Admin login

---

## 2. Rate Limiting

### Purpose
Prevent brute force attacks and API abuse.

### Implementation Strategy

#### Option A: Redis-based (Recommended)
Already have Redis running - use `slowapi` for rate limiting.

```bash
# Add to requirements.txt
slowapi==0.1.9
```

#### Option B: In-Memory (Development only)
Use FastAPI built-in middleware for testing.

### Rate Limits
```python
# Recommended limits for admin endpoints:
RATE_LIMITS = {
    "/api/auth/register": "3 per hour",      # Very restrictive
    "/api/auth/login": "5 per 15 minutes",   # Prevent brute force
    "/api/admin/*": "100 per minute",        # General admin operations
    "/api/*": "1000 per hour"                # General API
}
```

### Implementation Example
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/auth/register")
@limiter.limit("3/hour")
async def register_admin(request: Request, ...):
    ...

@app.post("/api/auth/login")
@limiter.limit("5/15minutes")
async def login(request: Request, ...):
    ...
```

---

## 3. SQL Injection Protection

### Current Status
✅ **Already Protected** - Using SQLAlchemy ORM with parameterized queries.

### Verification Checklist
- [ ] All database queries use SQLAlchemy ORM (no raw SQL)
- [ ] No string concatenation in queries
- [ ] User input is validated with Pydantic models
- [ ] Email validation uses `pydantic[email]` (already installed)

### Additional Hardening
```python
# Ensure all admin endpoints validate input
from pydantic import EmailStr, validator

class AdminRegister(BaseModel):
    email: EmailStr  # Automatic email validation
    password: str
    full_name: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

---

## 4. Admin Approval via Email Notification

### Purpose
Require manual approval from system administrator before granting admin access.

### Workflow
1. User fills admin registration form (with Turnstile)
2. Backend creates user with `is_admin=false`, `pending_approval=true`
3. Send email notification to system admin email
4. System admin clicks approval link or manually approves in database
5. User receives email confirmation and can login

### Implementation

#### Email Configuration
```python
# backend/.env
ADMIN_NOTIFICATION_EMAIL=your-gmail-address@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-app-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not account password
SMTP_FROM_EMAIL=noreply@fantcric.fun
```

#### Database Schema Update
```python
# Add to User model in main.py
class User(Base):
    ...
    pending_admin_approval = Column(Boolean, default=False)
    admin_approved_at = Column(DateTime, nullable=True)
    admin_approved_by = Column(String(255), nullable=True)
```

#### Email Template
```python
# backend/email_templates/admin_approval_request.html
"""
Subject: New Admin Registration Request - Fantasy Cricket

A new admin registration request has been received:

Email: {email}
Full Name: {full_name}
Registration Time: {timestamp}
IP Address: {ip_address}

To approve this admin:
1. Login to the database
2. Run: UPDATE users SET is_admin=true, pending_admin_approval=false, admin_approved_at=NOW(), admin_approved_by='system' WHERE email='{email}';

Or visit: https://fantcric.fun/admin/approve?token={approval_token}

To reject, simply ignore this email. The account will remain as a regular user.
"""
```

#### Registration Endpoint Update
```python
@app.post("/api/auth/register")
@limiter.limit("3/hour")
async def register_admin(
    request: Request,
    user_data: AdminRegister,
    turnstile_token: str,
    background_tasks: BackgroundTasks
):
    # 1. Verify Turnstile
    if not verify_turnstile(turnstile_token):
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    # 2. Create user (non-admin, pending approval)
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_admin=False,
        pending_admin_approval=True
    )
    db.add(user)
    db.commit()

    # 3. Send notification email to system admin
    background_tasks.add_task(
        send_admin_approval_email,
        user_email=user_data.email,
        user_name=user_data.full_name,
        ip_address=request.client.host
    )

    return {"message": "Registration received. Awaiting admin approval."}
```

---

## 5. Additional Security Measures

### HTTPS Only (Production)
```python
# Enforce HTTPS in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### CORS Configuration
```python
# Restrict CORS to your domain only
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fantcric.fun"],  # No wildcards in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### JWT Token Security
```python
# Use secure JWT settings
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60  # Short-lived tokens
JWT_REFRESH_TOKEN_DAYS = 7
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Strong random key

# Rotate JWT secret quarterly
# Store invalidated tokens in Redis blacklist
```

### Password Policy
```python
MIN_PASSWORD_LENGTH = 12
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL_CHAR = True
PASSWORD_EXPIRY_DAYS = 90  # For admin accounts
```

### Audit Logging
```python
# Log all admin actions
class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(Integer, primary_key=True)
    admin_email = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "CREATE_SEASON", "UPDATE_PLAYER"
    resource_type = Column(String(50))  # e.g., "season", "player", "club"
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Additional context
```

---

## Implementation Priority

### Phase 1: Critical (Before ANY Production Use)
1. ✅ SQL Injection Protection (already done via SQLAlchemy)
2. 🔴 Rate Limiting
3. 🔴 HTTPS Enforcement
4. 🔴 Strong Password Policy

### Phase 2: High Priority (Before Public Launch)
1. 🔴 Cloudflare Turnstile
2. 🔴 Admin Email Approval System
3. 🔴 Audit Logging
4. 🔴 CORS Restriction

### Phase 3: Nice to Have
1. Two-Factor Authentication (2FA)
2. IP Whitelisting for admin endpoints
3. Automated security scanning
4. Intrusion detection

---

## Testing Checklist

### Security Testing
- [ ] Test rate limiting with multiple requests
- [ ] Verify Turnstile blocks bot requests
- [ ] Attempt SQL injection on all input fields
- [ ] Test with expired/invalid JWT tokens
- [ ] Verify admin approval workflow
- [ ] Test CORS with different origins
- [ ] Check audit logs for all admin actions
- [ ] Verify password policy enforcement
- [ ] Test account lockout after failed logins

### Penetration Testing
- [ ] Run OWASP ZAP scan
- [ ] SQL injection testing
- [ ] XSS testing
- [ ] CSRF testing
- [ ] Session hijacking attempts
- [ ] Brute force attempts

---

## Dependencies Summary

```txt
# Add to backend/requirements.txt

# Rate limiting
slowapi==0.1.9

# Email
aiosmtplib==3.0.1

# Additional security
python-jose[cryptography]==3.3.0  # Already installed
passlib[bcrypt]==1.7.4  # Already installed
bcrypt==3.2.2  # Already pinned
email-validator>=2.0.0  # Already installed via pydantic[email]
```

---

## Environment Variables Required

```bash
# backend/.env.production

# Turnstile
TURNSTILE_SECRET_KEY=
TURNSTILE_SITE_KEY=

# Email
ADMIN_NOTIFICATION_EMAIL=admin@fantcric.fun
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@fantcric.fun

# Security
JWT_SECRET_KEY=  # Generate with: openssl rand -hex 32
ENVIRONMENT=production
ALLOWED_ORIGINS=https://fantcric.fun

# Rate Limiting
REDIS_URL=redis://localhost:6379
```

---

## Next Steps

1. Review this document with stakeholders
2. Implement Phase 1 (Critical) items
3. Set up Gmail App Password for email notifications
4. Configure Cloudflare Turnstile keys
5. Test each security feature in staging
6. Conduct security audit
7. Deploy to production

---

**Document Status**: Draft for Review
**Last Updated**: 2025-11-05
**Owner**: Development Team
