# Test-Driven Development Process

## Overview
This project follows strict Test-Driven Development (TDD) with numbered test files that must be executed sequentially.

## Test Files Structure
Tests are numbered from 1 to 10, each representing a feature milestone:

1. `test_1_vector_store_initialization.py` - Qdrant connection and basic vector operations
2. `test_2_pattern_extraction.py` - Extract patterns from UI schemas  
3. `test_3_agent_initialization.py` - CrewAI agents setup
4. `test_4_test_case_generation.py` - Generate test cases using AI
5. `test_5_similarity_search.py` - Vector similarity search for test patterns
6. `test_6_edge_case_discovery.py` - Discover edge cases in UI components
7. `test_7_external_search.py` - Linkup integration for external test patterns
8. `test_8_pipeline_integration.py` - Full pipeline orchestration
9. `test_9_mlb_integration.py` - MLB-specific server-driven UI testing
10. `test_10_output_generation.py` - Generate final test output

## TDD Rules (STRICT)
1. **Start with test #1** and proceed in numerical order
2. **Run the test first** to see it fail
3. **Implement ONLY** the minimal code needed to make the current test pass
4. **DO NOT** implement features before their tests exist
5. **DO NOT** modify test files
6. **DO NOT** skip ahead to later tests

## TDD Workflow
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Ensure Docker services are running (if needed)
docker-compose up -d

# 3. Run the next failing test
pytest tests/test_N_*.py -v  # where N is current test number

# 4. See the test fail

# 5. Write minimal code to make test pass
# - Edit only the files needed
# - Don't add extra functionality

# 6. Run the test again
pytest tests/test_N_*.py -v

# 7. Once passing, run ALL tests to ensure no regression
pytest tests/ -v

# 8. Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# 9. Run code quality checks
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/

# 10. Move to next numbered test
```

## Current Implementation Status
To check which tests are passing:
```bash
pytest tests/ -v --tb=no
```

## Important Notes
- Each test file represents a complete feature
- Tests build upon each other - don't skip
- The test file itself documents what needs to be implemented
- Read test assertions carefully to understand requirements
- Keep implementations minimal - just enough to pass
- Refactoring comes after tests pass

## When Starting Work
Always check current test status first:
```bash
# Find first failing test
pytest tests/ -v --tb=short | grep FAILED | head -1
```

Then focus only on making that test pass.