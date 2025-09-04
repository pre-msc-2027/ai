# Test Fixtures

This directory contains test data files used throughout the SecuScan AI test suite.

## Files Description

### Sample Code Files
- `sample_python.py` - Python file with various code quality issues (unused imports, print statements, hardcoded credentials, etc.)
- `sample_javascript.js` - JavaScript file with common issues (console.log, unused imports, TODO comments)

### API Response Data
- `sample_api_response.json` - Complete mock API response with warnings and rules data
- `expected_ollama_responses.json` - Expected AI model responses for different types of code issues

## Usage in Tests

These fixtures are used by various test modules:

### conftest.py
- Loads sample data for fixtures like `mock_api_response`
- Creates temporary workspaces with sample files

### Integration Tests
- Uses sample code files to test complete workflows
- Validates expected outputs against fixture data

### Unit Tests
- Uses individual components from fixtures for targeted testing
- Validates parsing and processing logic

## Adding New Fixtures

When adding new test fixtures:

1. **Keep it realistic**: Use actual code patterns and issues
2. **Document clearly**: Add comments explaining the test scenarios
3. **Update this README**: Describe new fixtures and their purpose
4. **Use in tests**: Ensure fixtures are actually used in test cases

## File Patterns

- Sample code files should contain realistic issues that the application would encounter
- JSON fixtures should match the actual API format and structure
- Keep fixtures focused and not too large to maintain test performance
