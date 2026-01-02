# Courier Module Tests

This test suite has been migrated from the FastAPI implementation to Django.

## Test Structure

```
courier/tests/
├── __init__.py           # Test package initialization
├── conftest.py           # Pytest fixtures and configuration
├── test_health.py        # Health check endpoint tests
├── test_engine.py        # Pricing calculation engine tests
├── test_zones.py         # Zone resolution logic tests
├── test_api.py           # Main API endpoints tests
├── test_orders.py        # Order CRUD operations tests
├── test_add_carrier.py   # Carrier addition tests
└── test_admin_extended.py # Admin extended functionality tests
```

## Running Tests

### Run all tests:
```bash
pytest courier/tests/
```

### Run specific test file:
```bash
pytest courier/tests/test_engine.py
```

### Run specific test class:
```bash
pytest courier/tests/test_engine.py::TestCalculateCost
```

### Run specific test method:
```bash
pytest courier/tests/test_engine.py::TestCalculateCost::test_base_rate_calculation
```

### Run with coverage:
```bash
pytest --cov=courier --cov-report=html courier/tests/
```

### Run with verbose output:
```bash
pytest -v courier/tests/
```

## Test Categories

### 1. Health Check Tests (test_health.py)
- Endpoint availability
- Response structure validation
- Database status checks

### 2. Engine Tests (test_engine.py)
- Cost calculation logic
- Weight slab calculations
- COD fee calculations
- Escalation and GST calculations
- Edge cases and boundary conditions

### 3. Zone Tests (test_zones.py)
- Pincode lookup functionality
- Zone assignment logic
- Metro detection
- State normalization
- Special state handling

### 4. API Tests (test_api.py)
- Compare rates endpoint
- Input validation
- Response structure
- Admin authentication
- Error handling

### 5. Order Tests (test_orders.py)
- Order creation
- Order retrieval
- Order updates
- Input validation
- CRUD operations

### 6. Carrier Addition Tests (test_add_carrier.py)
- Adding new carriers
- Validation rules
- Duplicate detection
- Backup creation
- Authentication checks

### 7. Admin Extended Tests (test_admin_extended.py)
- Admin order management
- Filtering and search
- Carrier management

## Test Fixtures

The `conftest.py` file provides shared fixtures:

- `client`: Django test client
- `admin_token`: Admin authentication token
- `sample_rate_request`: Sample rate comparison request data
- `sample_carrier_data`: Sample carrier configuration
- `sample_order`: Database fixture with sample order
- `sample_booked_order`: Database fixture with booked order
- `sample_order_data`: Sample order creation data
- `valid_carrier_data`: Valid carrier data for tests
- `restore_rate_cards`: Auto-fixture that backs up and restores rate cards

## Environment Variables

Make sure to set the following environment variables for tests:

```bash
export ADMIN_PASSWORD="your-secret-admin-password"
```

Or use a `.env` file.

## Notes

1. Tests automatically backup and restore `rate_cards.json` to ensure test isolation
2. Database tests use `@pytest.mark.django_db` decorator
3. Tests use Django's test client instead of FastAPI's TestClient
4. URL reversing uses Django's `reverse()` function with URL names from `urls.py`
5. Authentication uses `HTTP_X_ADMIN_TOKEN` header in Django test client

## Migration from FastAPI

Key changes from FastAPI tests:

1. **Test Client**: `TestClient(app)` → `Client()` (Django test client)
2. **Status Codes**: `status.HTTP_200_OK` → `200` (or keep DRF status codes)
3. **Headers**: `headers={"X-Admin-Token": token}` → `HTTP_X_ADMIN_TOKEN=token`
4. **URLs**: `"/compare-rates"` → `reverse('courier:compare-rates')`
5. **Database**: `SessionLocal()` → Django ORM with `@pytest.mark.django_db`
6. **Async Tests**: Removed `@pytest.mark.asyncio` and `async`/`await` (Django is sync)

## Troubleshooting

### Tests can't find Django settings
Make sure `DJANGO_SETTINGS_MODULE` is set:
```bash
export DJANGO_SETTINGS_MODULE=courier_module.settings
```

### Database errors
Run migrations before tests:
```bash
python manage.py migrate
```

### Import errors
Make sure you're running tests from project root:
```bash
cd /path/to/Courier_Module
pytest courier/tests/
```
