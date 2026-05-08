# Auth Module Testing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set database environment variables:
```bash
export DB_HOST=your_db_host
export DB_PORT=5432
export DB_NAME=cartlow
export DB_USER=your_db_user
export DB_PASS=your_db_password
```

## Run Tests

```bash
# Run all auth tests
pytest tests/auth\ module\ testing/test_auth.py

# Run specific test
pytest tests/auth\ module\ testing/test_auth.py::test_valid_login
```

## Test Coverage

### Login Tests
- Valid login
- Invalid password
- Invalid email
- Empty credentials
- Empty password only
- Empty email only
- Invalid email format
- Logout

### Registration Tests
- Valid email registration with OTP
- Valid phone registration with OTP
- Empty fields validation
- Invalid email format
- Weak password validation
- Existing email error
- Invalid OTP error
