# Python Backend Security Reference (Django / FastAPI)

## Django Security Checklist

### settings.py Audit
```python
# ❌ Production killers
DEBUG = True                          # 🔴 Critical in production
SECRET_KEY = 'hardcoded-secret'       # 🔴 Critical
ALLOWED_HOSTS = ['*']                 # 🟠 High

# ✅ Correct production settings
DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = ['myapp.com', 'www.myapp.com']

# ✅ Security middleware (check these are present)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]

# ✅ Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### SQL Injection (Django ORM)
```python
# ❌ VULNERABLE — raw query with f-string
users = User.objects.raw(f"SELECT * FROM users WHERE name = '{name}'")

# ✅ FIXED — ORM with params
users = User.objects.raw("SELECT * FROM users WHERE name = %s", [name])

# ✅ Even better — use ORM directly
users = User.objects.filter(name=name)
```

### Mass Assignment
```python
# ❌ VULNERABLE — user controls all fields
user.update(**request.POST.dict())

# ✅ FIXED — whitelist fields
SAFE_FIELDS = ['first_name', 'last_name', 'bio']
data = {k: v for k, v in request.POST.items() if k in SAFE_FIELDS}
user.update(**data)
```

---

## FastAPI Security Checklist

### Input Validation (Pydantic)
FastAPI uses Pydantic — check models have appropriate constraints:
```python
# ❌ No constraints
class UserCreate(BaseModel):
    username: str
    age: int

# ✅ With validation
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex='^[a-zA-Z0-9_]+$')
    age: int = Field(..., ge=0, le=120)
```

### Auth & OAuth2
```python
# ❌ Weak: no expiry, no algorithm pin
jwt.decode(token, SECRET)

# ✅ Secure
jwt.decode(token, SECRET, algorithms=["HS256"],
           options={"require": ["exp", "iat", "sub"]})
```

### CORS
```python
# ❌ Vulnerable
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)

# ✅ Note: allow_origins=["*"] with allow_credentials=True is rejected by browsers,
# but still flag open origins as risky
app.add_middleware(CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"])
```

### Race Conditions & Atomic Operations

```python
# ❌ VULNERABLE — TOCTOU race on balance deduction
user = User.objects.get(id=user_id)
if user.balance >= amount:
    user.balance -= amount   # another request can run here!
    user.save()

# ✅ FIXED — atomic update with database-level lock
from django.db.models import F
from django.db import transaction

with transaction.atomic():
    updated = User.objects.filter(
        id=user_id, balance__gte=amount
    ).update(balance=F('balance') - amount)
    if not updated:
        raise InsufficientFunds()
```

## Timing Attack Prevention

```python
# ❌ VULNERABLE — early return leaks timing info (user enumeration)
def login(username, password):
    user = User.objects.filter(username=username).first()
    if not user:
        return False  # returns fast → attacker knows user doesn't exist
    return check_password(password, user.password_hash)

# ✅ FIXED — constant-time comparison
import hmac

def login(username, password):
    user = User.objects.filter(username=username).first()
    dummy_hash = '$2b$12$invalidhashfortimingnormalization'
    stored = user.password_hash if user else dummy_hash
    valid = check_password(password, stored)
    return valid and user is not None
```

## Mass Assignment (Django)

```python
# ❌ VULNERABLE
user.__dict__.update(request.POST.dict())

# ✅ FIXED — explicit field whitelist via form or serializer
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']  # never include 'is_staff', 'role'
```

## Dependency Scan Commands
```bash
pip-audit -r requirements.txt
# or
safety check -r requirements.txt --full-report
```

Common high-severity packages to watch: `pillow`, `cryptography`, `requests`, `urllib3`, `pyyaml`, `lxml`.
