# AI Documentation System Test Suite

## Overview
This test suite validates the functionality, integration, and performance of the AI Documentation System's components, with a particular focus on the Review Agent and Acrolinx integration.

## Test Structure

### 1. Agent Tests
- `test_review.py`: Core Review Agent functionality
- `test_drafting.py`: Content drafting capabilities
- `test_query_response.py`: Query handling and responses
- `test_acrolinx_agent.py`: Acrolinx integration features
- `test_review_acrolinx_integration.py`: Combined review process

### 2. Test Categories

#### Unit Tests
- Individual component functionality
- Error handling
- Data processing
- Utility functions

#### Integration Tests
- Agent interactions
- External service integration
- Content workflow processing
- Cross-component functionality

#### Performance Tests
- Response timing
- Resource utilization
- Concurrent operations
- System scalability

## Setup and Configuration

### Prerequisites
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Environment Setup
1. Create a test configuration file:
```bash
cp .env.test.example .env.test
```

2. Configure test credentials:
```env
OPENAI_API_KEY=your-test-key
ACROLINX_API_URL=https://test.acrolinx.cloud
ACROLINX_API_TOKEN=your-test-token
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test Categories
```bash
# Run Review Agent tests
pytest tests/test_agents/test_review.py

# Run Acrolinx integration tests
pytest tests/test_agents/test_acrolinx_agent.py

# Run combined review tests
pytest tests/test_agents/test_review_acrolinx_integration.py
```

### Test Coverage
```bash
pytest --cov=src tests/
```

## Test Cases Documentation

### Review Agent Tests (`test_review.py`)
- Basic content review
- Style guide compliance
- Technical accuracy checks
- Suggestion generation

### Acrolinx Agent Tests (`test_acrolinx_agent.py`)
```python
class TestAcrolinxAgent:
    """
    Test suite for Acrolinx integration functionality.
    
    Key test areas:
    1. Content submission
    2. Result processing
    3. Error handling
    4. Profile management
    """
    
    async def test_check_content_success():
        """
        Validates successful content check submission and processing.
        
        Checks:
        - Quality score calculation
        - Issue identification
        - Guidance processing
        - Metadata handling
        """
        
    async def test_error_handling():
        """
        Validates error handling scenarios.
        
        Scenarios:
        - API failures
        - Timeout conditions
        - Invalid responses
        - Authentication issues
        """
```

### Integration Tests (`test_review_acrolinx_integration.py`)
```python
class TestReviewAcrolinxIntegration:
    """
    Test suite for combined Review and Acrolinx functionality.
    
    Key test areas:
    1. Combined review process
    2. Issue merging
    3. Quality scoring
    4. Error recovery
    """
    
    async def test_combined_review_process():
        """
        Validates complete review workflow.
        
        Steps:
        1. AI review generation
        2. Acrolinx quality check
        3. Result combination
        4. Final report generation
        """
        
    async def test_content_type_handling():
        """
        Validates handling of different content formats.
        
        Formats:
        - HTML
        - Markdown
        - Plain text
        """
```

## Mock Data

### Sample Content
```html
<h1>API Authentication Guide</h1>
<p>This guide explains the authentication process...</p>
```

### Mock Responses
```python
mock_ai_review = {
    "issues": [...],
    "suggestions": [...],
    "metadata": {...}
}

mock_acrolinx_review = {
    "quality_score": 85,
    "issues": [...],
    "guidance": {...}
}
```

## Best Practices

### Writing Tests
1. Use descriptive test names
2. Include docstrings explaining test purpose
3. Follow AAA pattern (Arrange, Act, Assert)
4. Mock external dependencies
5. Handle async operations correctly

### Test Data
1. Use fixtures for common test data
2. Maintain realistic test content
3. Cover edge cases
4. Include error scenarios

### Assertions
1. Be specific in assertions
2. Check all relevant aspects
3. Include error messages
4. Validate data types

## Troubleshooting

### Common Issues
1. **Async Test Failures**
   - Ensure proper async/await usage
   - Check for event loop issues
   
2. **Mock Configuration**
   - Verify mock return values
   - Check mock call assertions
   
3. **Integration Test Failures**
   - Check service availability
   - Verify credentials
   - Validate request formats

### Debug Tools
```bash
# Run tests with detailed output
pytest -v

# Show print statements
pytest -s

# Run specific test
pytest tests/test_agents/test_review_acrolinx_integration.py::TestReviewAcrolinxIntegration::test_combined_review_process
```

## Contributing

### Adding Tests
1. Follow existing test structure
2. Include proper documentation
3. Add relevant fixtures
4. Update test documentation

### Code Review
1. Ensure test coverage
2. Verify error handling
3. Check edge cases
4. Validate async operations 