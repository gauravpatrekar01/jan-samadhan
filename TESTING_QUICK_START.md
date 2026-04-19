# 🚀 Testing Quick Start Guide - JanSamadhan

## Setup Testing Environment (5 minutes)

### 1. Install Testing Tools

```bash
# Install Python testing dependencies
cd backend
pip install pytest pytest-cov httpx

# Install Node.js testing tools (global)
npm install -g newman          # Postman CLI for API testing
npm install -g lighthouse      # Performance testing
```

### 2. Download Postman Collection

[Download Postman](https://www.postman.com/downloads/)

Import the API collection from `postman-collection.json` (create this):

```json
{
  "info": {
    "name": "JanSamadhan API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Register Citizen",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/auth/register",
            "body": {
              "mode": "raw",
              "raw": "{\"name\":\"Test\",\"email\":\"test@example.com\",\"password\":\"Test@123\",\"aadhar\":\"123456789012\"}"
            }
          }
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/auth/login",
            "body": {
              "mode": "raw",
              "raw": "{\"email\":\"citizen@example.com\",\"password\":\"CitizenSecure123!\"}"
            }
          }
        }
      ]
    }
  ]
}
```

---

## Daily Testing (15 minutes)

### Morning Smoke Test

```bash
#!/bin/bash

echo "🧪 Starting Daily Smoke Test..."

# Test 1: Frontend loads
echo "✓ Testing frontend..."
curl -s http://localhost:8000 | grep -q "JanSamadhan" && echo "✓ Frontend OK" || echo "❌ Frontend FAILED"

# Test 2: API responds
echo "✓ Testing API..."
curl -s http://localhost:8000/api/stats | grep -q "success" && echo "✓ API OK" || echo "❌ API FAILED"

# Test 3: Database connected
echo "✓ Testing database..."
curl -s http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $TEST_TOKEN" | grep -q "success" && echo "✓ Database OK" || echo "❌ Database FAILED"

echo "✅ Daily smoke test complete!"
```

### Run Test Suite

```bash
cd backend
pytest tests/ -v --tb=short
```

---

## Weekly Testing (1-2 hours)

### Browser Compatibility Test

**Test Matrix:**
| Browser | Device | Status |
|---------|--------|--------|
| Chrome 120 | Desktop | [ ] |
| Firefox 121 | Desktop | [ ] |
| Safari 17 | macOS | [ ] |
| Chrome Mobile | Android | [ ] |
| Safari Mobile | iOS | [ ] |

**Steps for Each:**
1. Open http://localhost:8000
2. Login with test credentials
3. Submit complaint
4. View dashboard
5. Check console (F12) for errors
6. Check responsive design (F12 → Device Mode)

### Performance Baseline

```bash
# Test page load time
lighthouse http://localhost:8000 --view

# Expected: Performance score > 80

# Test API response time
time curl http://localhost:8000/api/complaints/my
# Expected: < 1000ms
```

### Database Integrity Check

```bash
cd backend
python -c "
from db import db
collection = db.get_collection('users')
print(f'Total users: {collection.count_documents({})}')
print(f'Emails index exists: {\"email_1\" in [idx[\"name\"] for idx in collection.list_indexes()]}')
"
```

---

## Pre-Release Testing (Full Day)

### 1. Run Complete Test Suite (30 min)

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html

# Expected: > 80% coverage
```

### 2. API Testing with Postman (30 min)

```bash
# Run Postman collection via CLI
newman run postman-collection.json \
  --environment postman-env.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

### 3. Security Scan (20 min)

```bash
# Check for common vulnerabilities in dependencies
pip check

# Scan Python requirements
safety check -r backend/requirements.txt

# Expected: 0 critical vulnerabilities
```

### 4. Load Test (20 min)

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class UserBehavior(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def login(self):
        self.client.post("/api/auth/login", json={
            "email": "citizen@example.com",
            "password": "CitizenSecure123!"
        })
    
    @task
    def view_complaints(self):
        self.client.get("/api/complaints/my")
EOF

# Run load test: 10 users over 1 minute
locust -f locustfile.py -u 10 -r 5 --run-time 1m
```

### 5. Accessibility Audit (15 min)

```bash
# Install axe DevTools (Chrome extension)
# Or use automated testing

pip install axe-selenium-python

# Create test
cat > test_accessibility.py << 'EOF'
from axe_selenium_python import Axe
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("http://localhost:8000")

axe = Axe(driver)
axe.inject()
axe.run()

violations = axe.results()["violations"]
if not violations:
    print("✓ Accessibility OK")
else:
    print(f"❌ Found {len(violations)} violations")
EOF

pytest test_accessibility.py
```

---

## Test Coverage by Feature

### User Registration & Login

Create `test_auth.py`:

```python
import pytest
from httpx import Client
import sys
sys.path.insert(0, './backend')

BASE_URL = "http://localhost:8000"

def test_citizen_registration():
    """Test citizen can register"""
    response = Client().post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test Citizen",
        "email": f"test_{pytest.config.option.timestamp}@example.com",
        "password": "TestPass123!",
        "aadhar": "123456789012",
        "role": "citizen"
    })
    assert response.status_code == 201
    assert response.json()["data"]["role"] == "citizen"

def test_login_valid_credentials():
    """Test login with valid credentials"""
    response = Client().post(f"{BASE_URL}/api/auth/login", json={
        "email": "citizen@example.com",
        "password": "CitizenSecure123!"
    })
    assert response.status_code == 200
    assert "token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = Client().post(f"{BASE_URL}/api/auth/login", json={
        "email": "citizen@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_officer_cannot_self_register():
    """Test officer cannot register (admin only)"""
    response = Client().post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test Officer",
        "email": "officer@example.com",
        "password": "TestPass123!",
        "role": "officer"
    })
    assert response.status_code == 400
```

Run:
```bash
pytest test_auth.py -v
```

### Complaint Management

Create `test_complaints.py`:

```python
import pytest
from httpx import Client
import sys
sys.path.insert(0, './backend')

BASE_URL = "http://localhost:8000"

@pytest.fixture
def auth_token():
    """Get authentication token"""
    response = Client().post(f"{BASE_URL}/api/auth/login", json={
        "email": "citizen@example.com",
        "password": "CitizenSecure123!"
    })
    return response.json()["data"]["token"]

def test_create_complaint(auth_token):
    """Test citizen can create complaint"""
    response = Client().post(
        f"{BASE_URL}/api/complaints/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Broken streetlight",
            "category": "infrastructure",
            "priority": "high",
            "description": "Street light near XYZ is broken",
            "location": {"lat": 19.0760, "lng": 72.8777}
        }
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "submitted"

def test_citizen_sees_own_complaints(auth_token):
    """Test citizen can only see own complaints"""
    response = Client().get(
        f"{BASE_URL}/api/complaints/my",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)

def test_unauthenticated_cannot_create_complaint():
    """Test unauthenticated user cannot create complaint"""
    response = Client().post(
        f"{BASE_URL}/api/complaints/",
        json={"title": "Test"}
    )
    assert response.status_code == 401
```

Run:
```bash
pytest test_complaints.py -v
```

---

## Manual Testing Checklist (Can be printed)

### Before Release Checklist

```
AUTHENTICATION
□ Citizen can register
□ Citizen can login  
□ Officer can login
□ Admin can login
□ Logout clears session
□ Wrong password shows error
□ Duplicate email shows error
□ Token refresh works

COMPLAINTS
□ Citizen can create complaint
□ Complaint appears in list
□ Can update complaint status
□ Can view complaint details
□ Pagination works
□ Filter by status works
□ Filter by priority works
□ Search works

UI/UX
□ Page loads in < 2 seconds
□ No broken images
□ No 404 errors
□ Mobile view works
□ Dark mode works (if enabled)
□ All buttons clickable
□ Forms validate

DATABASE
□ Data persists after refresh
□ No duplicate entries
□ Timestamps correct
□ User data correct
□ Complaint data correct

PERFORMANCE
□ Login < 1 second
□ Page load < 2 seconds
□ List load < 1 second
□ No memory leaks (open DevTools, check memory)
□ Console has no errors
□ Network tab clean

SECURITY
□ HTTPS working (if deployed)
□ Can't access other user data
□ Can't modify other user complaints
□ Tokens expire
□ Passwords masked in UI
□ No API keys in frontend code
```

---

## Automated Test Execution

### GitHub Actions CI/CD Pipeline

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:latest
        options: >-
          --health-cmd mongosh
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 27017:27017
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Test Result Reporting

### Generate HTML Report

```bash
pytest backend/tests/ --html=report.html --self-contained-html
open report.html
```

### Track Metrics

```python
# test_metrics.py
import time

def test_login_performance():
    """Verify login completes in < 1 second"""
    start = time.time()
    response = Client().post(f"{BASE_URL}/api/auth/login", json={...})
    duration = time.time() - start
    
    assert duration < 1.0, f"Login took {duration}s, expected < 1s"
```

---

## Continuous Integration Setup

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running pre-commit tests..."

cd backend
pytest tests/test_auth.py -q

if [ $? -ne 0 ]; then
    echo "❌ Tests failed, commit aborted"
    exit 1
fi

echo "✓ All checks passed"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Test Data Management

### Create Consistent Test Data

```python
# reset_test_db.py
import sys
sys.path.insert(0, 'backend')

from db import db
from security import hash_password
from datetime import datetime, timezone

def reset_test_database():
    """Reset database to known state for testing"""
    db_client = db._client
    
    # Clear collections
    db_client['jansamadhan'].drop_collection('users')
    db_client['jansamadhan'].drop_collection('complaints')
    
    # Create test users
    users = db.get_collection('users')
    users.insert_many([
        {
            "email": "citizen@example.com",
            "name": "Test Citizen",
            "password": hash_password("CitizenSecure123!"),
            "role": "citizen",
            "aadhar": "123456789012",
            "verified": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "email": "officer@example.com",
            "name": "Test Officer",
            "password": hash_password("OfficerSecure123!"),
            "role": "officer",
            "verified": True,
            "department": "Public Works",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    ])
    
    print("✅ Test database reset complete")

if __name__ == "__main__":
    reset_test_database()
```

Run before testing:
```bash
python reset_test_db.py
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Tests fail with "Connection refused" | Make sure backend is running (`uvicorn app:app --reload`) |
| Database tests fail | Reset test DB: `python reset_test_db.py` |
| Pytest not found | Install: `pip install pytest` |
| Tests timeout | Increase timeout: `pytest --timeout=10` |
| Port 8000 already in use | Kill process: `lsof -i :8000 \| kill -9` |
| CORS errors in browser | Check CORS headers in backend |

---

## Next Steps

1. **Copy test files to your project**
2. **Run daily smoke tests**
3. **Execute weekly regression tests**
4. **Set up CI/CD pipeline**
5. **Generate coverage reports**
6. **Document test results**
7. **Track bugs and regressions**

---

**Ready to test? Start with:**
```bash
pytest backend/tests/ -v
```
