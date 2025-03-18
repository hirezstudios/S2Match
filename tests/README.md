# S2Match Test Suite

This directory contains the test suite for the S2Match SDK. It includes unit tests, integration tests, and mock responses for testing the SDK functionality without making actual API calls.

## Test Structure

- `conftest.py`: Contains fixtures and helper functions used across the test suite
- `test_authentication.py`: Tests for authentication-related functionality
- `test_data_retrieval.py`: Tests for data retrieval methods
- `test_transformations.py`: Tests for data transformation methods
- `test_integration.py`: Integration tests that verify complete workflows

## Mock Responses

The `mock_responses` directory contains JSON files with sample responses used for testing:

- `player_data.json`: Mock player lookup response
- `match_data.json`: Mock match data response
- `stats_data.json`: Mock player statistics response

## Running Tests

To run the tests, you'll need pytest installed. You can install it with pip:

```bash
pip install pytest
```

Then, from the root directory of the project, run:

```bash
pytest
```

To run tests with verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest tests/test_authentication.py
```

To run a specific test:

```bash
pytest tests/test_authentication.py::test_init_with_env_vars
```

## Writing New Tests

When adding new tests:

1. Add unit tests for individual methods in the appropriate test file
2. Add integration tests for complete workflows in `test_integration.py`
3. Add any necessary mock responses to the `mock_responses` directory
4. Use fixtures from `conftest.py` where possible to reduce duplication

## Test Coverage

The test suite aims to cover:

- SDK initialization with different parameter combinations
- Authentication token acquisition and caching
- All data retrieval methods
- Data transformation and enrichment
- Error handling
- Complete workflows from authentication to data transformation

## Mocking Strategy

The tests use pytest's monkeypatch and unittest.mock to:

- Mock environment variables
- Mock API responses
- Mock file operations (for items.json loading)

This allows the tests to run without making actual API calls or requiring actual credentials. 