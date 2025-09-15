# Development Scripts

These are manual testing scripts for development and debugging, not automated tests.

## Manual Testing Scripts

### `manual_test_registry.py`
Test labeler registry functionality locally.
- Tests registry configuration loading from database
- Validates mode filtering (production, shadow, experimental)
- Checks backwards compatibility with existing labeler creation

### `manual_test_pipeline.py`  
Test multi-labeler pipeline integration.
- Tests registry integration within pipeline
- Validates multi-labeler execution structure
- Checks database integration for performance metrics

### `manual_test_admin_api.py`
Test admin API endpoints (requires admin backend running).
- Tests labeler configuration management endpoints
- Validates performance analytics API responses
- Checks CRUD operations for labeler configs

## Usage

Run these scripts when:
- Developing new registry features
- Debugging labeler integration issues
- Validating API endpoint functionality
- Testing database schema changes

**Note**: These are development tools, not part of an automated test suite.