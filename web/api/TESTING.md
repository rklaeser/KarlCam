# KarlCam API Testing Guide

This document provides comprehensive guidance for testing the KarlCam API, including setup, execution, and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [Writing Tests](#writing-tests)
- [CI Integration](#ci-integration)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Ensure you're in the API directory
cd web/api
```

### Run All Tests

```bash
# Using the test runner script (recommended)
python run_tests.py all

# Or using pytest directly
python -m pytest tests/
```

### Run Tests with Coverage

```bash
# Generate coverage report
python run_tests.py coverage --html

# View coverage report
open htmlcov/index.html
```

## Test Structure

### Directory Layout

```
tests/
├── conftest.py              # Test configuration and fixtures
├── factories.py             # Test data factories
├── core/                    # Core module tests
│   ├── test_dependencies.py
│   └── test_openapi.py
├── routers/                 # Router endpoint tests
│   ├── test_cameras.py
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_images.py
│   └── test_system.py
├── services/                # Service layer tests
│   ├── test_camera_service.py
│   └── test_stats_service.py
├── utils/                   # Utility tests
│   └── test_exceptions.py
└── integration/             # Integration tests
    └── test_api_workflows.py
```

### Test Categories

Tests are organized into two main categories using pytest markers:

- **Unit Tests** (`@pytest.mark.unit`): Test individual components in isolation
- **Integration Tests** (`@pytest.mark.integration`): Test complete workflows and component interactions

## Running Tests

### Using the Test Runner Script

The `run_tests.py` script provides convenient commands for various testing scenarios:

#### Basic Test Execution

```bash
# Run only unit tests
python run_tests.py unit

# Run only integration tests  
python run_tests.py integration

# Run all tests
python run_tests.py all

# Run with verbose output
python run_tests.py all -v
```

#### Coverage Testing

```bash
# Run all tests with coverage
python run_tests.py coverage

# Run only unit tests with coverage
python run_tests.py coverage --type unit

# Generate HTML coverage report
python run_tests.py coverage --html

# Check coverage meets minimum threshold
python run_tests.py threshold --min 85
```

#### Performance and Debugging

```bash
# Run tests in parallel (faster execution)
python run_tests.py parallel -n 4

# Run only failed tests from last run
python run_tests.py failed

# Run a specific test file
python run_tests.py test tests/routers/test_cameras.py

# Run a specific test function
python run_tests.py test tests/routers/test_cameras.py::TestCameraEndpoints::test_get_cameras_success
```

#### CI Pipeline

```bash
# Run full CI pipeline with coverage check
python run_tests.py ci

# CI with custom coverage threshold
python run_tests.py ci --threshold 90
```

### Using Pytest Directly

You can also run tests directly with pytest for more control:

```bash
# Basic execution
python -m pytest tests/

# Run specific test types
python -m pytest tests/ -m unit
python -m pytest tests/ -m integration

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Run specific tests
python -m pytest tests/routers/test_cameras.py -v
python -m pytest tests/routers/test_cameras.py::TestCameraEndpoints::test_get_cameras_success -v

# Run with specific options
python -m pytest tests/ -v --tb=short  # Verbose with short traceback
python -m pytest tests/ -x             # Stop on first failure
python -m pytest tests/ --pdb          # Drop into debugger on failure
```

## Coverage Reports

### Coverage Configuration

Coverage is configured in `.coveragerc`:

```ini
[run]
source = .
omit = 
    */tests/*
    */venv/*
    */env/*
    */build/*
    */dist/*
    */__pycache__/*
    */migrations/*
    */node_modules/*
    run_tests.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if settings.DEBUG:

[html]
directory = htmlcov
```

### Coverage Targets

- **Overall Coverage**: Target 85%+ for production code
- **Critical Modules**: 95%+ coverage for:
  - Services (`services/`)
  - Routers (`routers/`)
  - Core utilities (`core/`, `utils/`)

### Interpreting Coverage Reports

#### Terminal Report

```bash
Name                           Stmts   Miss  Cover   Missing
----------------------------------------------------------
core/config.py                   45      2    96%   67-68
core/dependencies.py             38      3    92%   45, 78-79
routers/cameras.py               67      1    99%   156
services/camera_service.py       89      4    96%   123-126
----------------------------------------------------------
TOTAL                           498     18    96%
```

#### HTML Report

The HTML report provides:
- Line-by-line coverage visualization
- Branch coverage analysis
- Interactive navigation
- Detailed missing line information

Access via: `open htmlcov/index.html`

## Writing Tests

### Test Naming Conventions

```python
# Test classes
class TestCameraService:
    """Test suite for CameraService"""

# Test methods
def test_get_cameras_success(self):
    """Test successful camera retrieval"""

def test_get_cameras_empty_database(self):
    """Test camera retrieval when database is empty"""

def test_get_cameras_service_error(self):
    """Test error handling in camera retrieval"""
```

### Test Structure Pattern

```python
@pytest.mark.unit
def test_feature_success_scenario(self, test_client, mock_db_manager):
    """Test description explaining what is being tested"""
    # Setup - Arrange test data and mocks
    mock_data = {...}
    mock_service.method.return_value = mock_data
    
    # Execute - Perform the action being tested
    response = test_client.get("/api/endpoint")
    
    # Assert - Verify the results
    assert response.status_code == 200
    assert response.json()["field"] == expected_value
```

### Using Test Fixtures

#### Available Fixtures

```python
# Test client with mocked dependencies
def test_example(self, test_client):
    response = test_client.get("/api/endpoint")

# Mock database manager
def test_example(self, mock_db_manager):
    mock_db_manager.get_data.return_value = test_data

# Sample data fixtures
def test_example(self, sample_webcam_data):
    assert sample_webcam_data["id"] == "test-webcam-1"
```

#### Creating Test Data

```python
from tests.factories import (
    CameraConditionsFactory,
    WebcamFactory,
    create_multi_camera_scenario
)

# Generate single instances
camera = CameraConditionsFactory()
webcam = WebcamFactory(id="custom-id")

# Generate complex scenarios
cameras, images = create_multi_camera_scenario(num_cameras=5)
```

### Mocking Best Practices

#### Service Mocking

```python
with patch('routers.cameras.CameraService') as mock_service_class:
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    mock_service.get_data.return_value = test_data
    
    response = test_client.get("/api/endpoint")
    
    # Verify service interaction
    mock_service.get_data.assert_called_once()
```

#### Database Mocking

```python
def test_with_database_error(self, test_client, mock_db_manager):
    # Mock database failure
    mock_db_manager.get_data.side_effect = Exception("Database error")
    
    response = test_client.get("/api/endpoint")
    assert response.status_code == 500
```

### Testing Error Scenarios

```python
@pytest.mark.unit
def test_validation_error(self, test_client):
    """Test validation error handling"""
    response = test_client.get("/api/cameras/test?hours=-5")
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

@pytest.mark.unit  
def test_not_found_error(self, test_client, mock_db_manager):
    """Test not found error handling"""
    mock_db_manager.get_data.return_value = []
    
    response = test_client.get("/api/cameras/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
```

### Integration Test Patterns

```python
@pytest.mark.integration
def test_complete_workflow(self, test_client, mock_db_manager):
    """Test complete user workflow"""
    # Setup complex scenario
    cameras, images = create_multi_camera_scenario(num_cameras=3)
    mock_db_manager.get_active_webcams.return_value = cameras
    
    # Step 1: Get camera list
    list_response = test_client.get("/api/public/cameras")
    assert list_response.status_code == 200
    
    # Step 2: Get details for first camera
    camera_id = list_response.json()["cameras"][0]["id"]
    detail_response = test_client.get(f"/api/public/cameras/{camera_id}")
    assert detail_response.status_code == 200
    
    # Step 3: Verify consistency
    assert detail_response.json()["camera"]["id"] == camera_id
```

## CI Integration

### GitHub Actions Configuration

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd web/api
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        cd web/api
        python run_tests.py ci --threshold 85
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./web/api/coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run unit tests
        entry: python web/api/run_tests.py unit
        language: system
        pass_filenames: false
        always_run: true
```

### Makefile Integration

Add to `Makefile`:

```makefile
test:
	cd web/api && python run_tests.py all

test-unit:
	cd web/api && python run_tests.py unit

test-integration:
	cd web/api && python run_tests.py integration

test-coverage:
	cd web/api && python run_tests.py coverage --html

test-ci:
	cd web/api && python run_tests.py ci

.PHONY: test test-unit test-integration test-coverage test-ci
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'services'
# Solution: Run from the API directory
cd web/api
python -m pytest tests/
```

#### Database Connection Issues

```bash
# Error: Database connection failed in tests
# Solution: Tests use mocked database by default
# Check that mock_db_manager fixture is being used
```

#### Coverage Not Updating

```bash
# Clean coverage data and re-run
python run_tests.py clean
python run_tests.py coverage
```

#### Tests Running Slowly

```bash
# Use parallel execution
python run_tests.py parallel -n 4

# Or run only unit tests for faster feedback
python run_tests.py unit
```

### Debugging Test Failures

#### Verbose Output

```bash
# Get detailed test output
python run_tests.py all -v

# Even more detailed pytest output
python -m pytest tests/ -vvv
```

#### Debugging Specific Tests

```bash
# Run single failing test
python run_tests.py test tests/routers/test_cameras.py::TestCameraEndpoints::test_get_cameras_success -v

# Drop into debugger on failure
python -m pytest tests/routers/test_cameras.py::TestCameraEndpoints::test_get_cameras_success --pdb
```

#### Mock Verification

```python
# Debug mock calls
print(mock_service.method.call_args_list)
print(mock_service.method.call_count)

# Verify mock was called with specific arguments
mock_service.method.assert_called_with(expected_arg)
```

### Performance Optimization

#### Test Execution Speed

- Use `pytest-xdist` for parallel execution
- Run unit tests during development, integration tests before commits
- Use `--lf` flag to re-run only failed tests
- Mock external dependencies to avoid network calls

#### Coverage Collection

- Coverage collection adds overhead; disable for development iterations
- Use `--cov-append` for incremental coverage builds
- Focus coverage analysis on changed code areas

### Test Environment Issues

#### Dependencies

```bash
# Ensure all test dependencies are installed
pip install -r requirements-test.txt

# Update dependencies if tests fail unexpectedly
pip install --upgrade -r requirements-test.txt
```

#### Environment Variables

```bash
# Set test environment
export ENVIRONMENT=test

# Or use pytest env plugin
pip install pytest-env
```

## Best Practices Summary

1. **Test Organization**: Keep unit and integration tests separated
2. **Naming**: Use descriptive test names that explain the scenario
3. **Structure**: Follow Arrange-Act-Assert pattern
4. **Coverage**: Aim for 85%+ overall, 95%+ for critical paths
5. **Mocking**: Mock external dependencies, test business logic
6. **CI Integration**: Run tests automatically on every commit
7. **Performance**: Use parallel execution for large test suites
8. **Documentation**: Document complex test scenarios and workflows

For questions or issues, refer to the pytest documentation or consult with the development team.