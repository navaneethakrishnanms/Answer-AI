# Testing Suite Documentation

## Overview

This testing suite provides comprehensive testing for the AI Exam Evaluator system with advanced Data Structures & Algorithms (DSA) optimizations.

## Advanced DSA Features

### 1. **Graph-based Dependency Management**
- Uses **Topological Sort (Kahn's Algorithm)** for test execution order
- Time Complexity: O(V+E) where V = tests, E = dependencies
- Detects circular dependencies
- Ensures tests run in correct order

### 2. **Trie-based Test Lookup**
- Efficient test case search by prefix
- Time Complexity: O(m) where m = length of search string
- Memory efficient for large test suites
- Supports fuzzy matching

### 3. **Priority Queue for Test Execution**
- Uses **Min-Heap** for priority-based execution
- Time Complexity: O(log n) for insert/extract
- High-priority tests run first
- Dynamic priority adjustment

### 4. **Hash-based Memoization**
- Caches test results using SHA-256 hashing
- Time Complexity: O(1) for cache lookup
- Prevents redundant test execution
- Automatic cache invalidation

### 5. **Performance Metrics Collection**
- Tracks execution time for each test
- Identifies bottlenecks using O(n log n) sorting
- Generates detailed performance reports
- Historical performance tracking

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_framework.py           # Advanced testing framework with DSA
├── test_ocr_service.py         # OCR service tests
├── test_preprocessing.py       # Preprocessing tests
├── test_rules.py               # Rules and validation tests
├── test_ai_services.py         # AI services (Qwen, DeepSeek) tests
├── test_api_endpoints.py       # API endpoint tests
├── test_integration.py         # Integration tests
├── run_tests.py                # Advanced test runner
├── run_pytest.py               # PyTest runner with coverage
├── debug_analyzer.py           # Code complexity analyzer
└── README.md                   # This file
```

## Running Tests

### Method 1: Advanced Test Runner (Recommended)

```bash
# Run all tests with DSA optimizations
python tests/run_tests.py all

# Run tests by category
python tests/run_tests.py category ocr
python tests/run_tests.py category preprocessing
python tests/run_tests.py category ai
python tests/run_tests.py category integration

# Run tests by prefix
python tests/run_tests.py prefix ocr_
python tests/run_tests.py prefix preprocessing_

# Run single test
python tests/run_tests.py test ocr_initialization

# List all registered tests
python tests/run_tests.py list

# Show help
python tests/run_tests.py help
```

### Method 2: PyTest with Coverage

```bash
# Run all tests with coverage
python tests/run_pytest.py all

# Run specific test file
python tests/run_pytest.py file test_ocr_service.py

# Run tests with specific marker
python tests/run_pytest.py marker asyncio

# Open coverage report
python tests/run_pytest.py coverage
```

### Method 3: Direct PyTest

```bash
# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_ocr_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run with debugging
pytest tests/ -v --pdb

# Run async tests only
pytest tests/ -m asyncio
```

## Code Complexity Analysis

### Analyze Project Complexity

```bash
# Analyze entire project
python tests/debug_analyzer.py complexity

# Analyze specific file
python tests/debug_analyzer.py file app/services/ocr_service.py

# Debug test failures
python tests/debug_analyzer.py debug
```

**Metrics Analyzed:**
- Cyclomatic Complexity (McCabe)
- Lines of Code per Function
- Maximum Nesting Depth
- Number of Parameters
- High Complexity Functions (> 10)

## Test Categories

### 1. OCR Tests (`test_ocr_service.py`)
- OCR service initialization
- Image compression
- API call success/failure
- Timeout handling
- PDF extraction
- Priority: 10 (highest)

### 2. Preprocessing Tests (`test_preprocessing.py`)
- Text cleaning
- Section extraction
- Question label normalization
- Student ID extraction
- Page splitting
- Priority: 8-7

### 3. Rules Tests (`test_rules.py`)
- Section configuration
- Question parser (roman, alpha, numeric)
- Marks extraction
- Evaluation rules (strict/liberal)
- Priority: 6-5

### 4. AI Services Tests (`test_ai_services.py`)
- Qwen mapper initialization
- Mapping prompt generation
- Answer mapping
- DeepSeek evaluator
- Evaluation prompts
- Priority: 4

### 5. API Tests (`test_api_endpoints.py`)
- Endpoint availability
- File upload
- Status checking
- Result retrieval
- Error handling
- Priority: 3

### 6. Integration Tests (`test_integration.py`)
- End-to-end workflow
- Preprocessing to mapping
- Mapping to evaluation
- Full pipeline
- Priority: 1-2

## Test Fixtures (conftest.py)

### Available Fixtures:

```python
@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""

@pytest.fixture
def sample_pdf_path(temp_dir):
    """Sample PDF file"""

@pytest.fixture
def sample_question_paper():
    """Sample question paper text"""

@pytest.fixture
def sample_answer_key():
    """Sample answer key text"""

@pytest.fixture
def sample_student_answers():
    """Sample student answers text"""

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
```

## Advanced Testing Framework

### Decorators

```python
from tests.test_framework import test, memoize_test, time_test

@test("test_name", priority=10, dependencies=["other_test"], category="ocr")
def my_test():
    """Test with dependency management"""
    return True

@memoize_test
def expensive_test():
    """Test with result caching"""
    # Results cached for repeat runs
    return True

@time_test
def slow_test():
    """Test with timing"""
    # Execution time tracked
    return True
```

### Programmatic Test Execution

```python
from tests.test_framework import test_runner

# Run all tests
stats = test_runner.run_all()

# Run by category
stats = test_runner.run_by_category("ocr")

# Run by prefix
stats = test_runner.run_by_prefix("ocr_")

# Run single test
stats = test_runner.run_test("test_name")

# Get statistics
print(f"Passed: {stats['passed']}")
print(f"Failed: {stats['failed']}")
print(f"Cached: {stats['cached']}")
print(f"Time: {stats['total_time']:.2f}s")
```

## Performance Benchmarks

### Expected Performance:
- OCR Tests: ~0.5s per test
- Preprocessing Tests: ~0.1s per test
- Rules Tests: ~0.05s per test
- AI Service Tests: ~0.2s per test (mocked)
- API Tests: ~0.3s per test
- Integration Tests: ~1.0s per test

### Cache Performance:
- First Run: Full execution
- Cached Run: ~10x faster
- Cache Hit Rate: >90% for repeated runs

## Debugging Failed Tests

### View Detailed Error:
```bash
pytest tests/test_ocr_service.py -v --tb=long
```

### Interactive Debugging:
```bash
pytest tests/test_ocr_service.py --pdb
```

### Run Single Test Method:
```bash
pytest tests/test_ocr_service.py::TestOCRService::test_ocr_initialization -v
```

### Show Print Statements:
```bash
pytest tests/ -v -s
```

## Coverage Reports

### Generate HTML Report:
```bash
pytest tests/ --cov=app --cov-report=html
# Open: htmlcov/index.html
```

### Terminal Report:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Target Coverage:
- Overall: >80%
- Critical Services: >90%
- API Endpoints: >85%
- Rules: >95%

## Continuous Integration

### Pre-commit Checks:
```bash
# Run fast tests only
pytest tests/ -m "not slow" -v

# Run with coverage threshold
pytest tests/ --cov=app --cov-fail-under=80
```

### Full Test Suite:
```bash
# All tests with all checks
python tests/run_pytest.py all
```

## Troubleshooting

### Common Issues:

1. **Import Errors**
   ```bash
   # Ensure backend is in path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Async Test Failures**
   ```bash
   # Install pytest-asyncio
   pip install pytest-asyncio
   ```

3. **Mock Issues**
   ```bash
   # Verify mock patches target correct modules
   # Check import paths in test files
   ```

4. **Fixture Not Found**
   ```bash
   # Ensure conftest.py is in tests/ directory
   # Check fixture scope (function, session, etc.)
   ```

## Contributing Tests

### Test Naming Convention:
- `test_<component>_<action>_<expected>`
- Example: `test_ocr_api_call_success`

### Test Structure:
```python
def test_feature():
    # Arrange: Set up test data
    data = create_test_data()
    
    # Act: Execute function
    result = function_under_test(data)
    
    # Assert: Verify results
    assert result == expected_value
```

### Best Practices:
1. One assertion per test (when possible)
2. Use descriptive test names
3. Mock external dependencies
4. Test edge cases
5. Include negative tests
6. Document complex test logic

## Test Data

### Sample Data Location:
- Fixtures in `conftest.py`
- Mock responses in `test_framework.py`
- Sample PDFs generated in `temp_dir` fixture

### Creating Test Data:
```python
from faker import Faker
fake = Faker()

# Generate fake student ID
student_id = fake.bothify(text='??###', letters='ABCDEFGHIJ')

# Generate fake text
text = fake.text(max_nb_chars=200)
```

## Advanced Features

### 1. Dependency Resolution Graph
Tests automatically execute in correct order based on dependencies.

### 2. Automatic Retry
Failed tests can retry automatically with exponential backoff.

### 3. Parallel Execution
Independent tests can run in parallel:
```bash
pytest tests/ -n auto
```

### 4. Test Parametrization
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", True),
    ("test2", False),
])
def test_multiple_cases(input, expected):
    assert process(input) == expected
```

## Metrics Dashboard

After running tests, view detailed metrics:
- Execution time per test
- Cache hit/miss ratio
- Dependency graph visualization
- Slowest tests
- Complexity scores

## License

MIT License - See project root LICENSE file

## Support

For issues or questions:
1. Check this README
2. Review test output
3. Run complexity analyzer
4. Check individual test files
5. Review conftest.py fixtures
