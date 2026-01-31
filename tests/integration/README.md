# Integration Tests

Consolidated integration tests for BarberX platform features.

## Test Files

### `test_redirect_flow.py`

Tests authentication redirect flows and session persistence.

### `test_quota_system.py`

Validates tier-based quota enforcement and usage metering.

### `test_stripe_webhooks.py`

Tests Stripe webhook handling for payment events.

### `simple_import_test.py`

Basic import validation for all Python modules.

### `performance_check.py`

Performance benchmarking for critical endpoints.

### `check_passwords.py`

Password authentication validation (relocated from root).

---

## Running Tests

**Individual test:**

```bash
python tests/integration/test_redirect_flow.py
```

**All integration tests:**

```bash
pytest tests/integration/
```

**With coverage:**

```bash
pytest tests/integration/ --cov=. --cov-report=html
```

---

## Test Organization

```
tests/
├── integration/          # Integration tests (cross-component)
│   ├── test_redirect_flow.py
│   ├── test_quota_system.py
│   ├── test_stripe_webhooks.py
│   ├── simple_import_test.py
│   ├── performance_check.py
│   └── check_passwords.py
├── test_full_integration.py
├── test_foundation.py
└── test_unified_retrieval.py
```

---

**Status:** ✅ Active Testing Suite
