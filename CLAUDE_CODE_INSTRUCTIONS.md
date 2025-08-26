# Instructions for Claude Code TDD Implementation

## Your Mission
Implement an Intelligent Test Case Generator for Server-Driven UI using Test-Driven Development. This is for the Qdrant Hackathon 2025, focusing on MLB mobile app testing.

## TDD Process
1. **Start with test_1_vector_store_initialization.py**
2. Run the test: `pytest tests/test_1_vector_store_initialization.py -v`
3. See the test fail
4. Implement ONLY enough code to make the test pass
5. Run the test again to confirm it passes
6. Commit your changes
7. Move to the next test file

## Implementation Rules
- ✅ Write minimal code to pass the current test
- ✅ Use the hackathon partner technologies (Qdrant, CrewAI, Mistral AI, Linkup)
- ✅ Follow Python best practices and type hints
- ✅ Add docstrings to all functions and classes
- ❌ Don't implement features before their tests
- ❌ Don't modify test files
- ❌ Don't skip tests

## Key Technologies to Use
1. **Qdrant**: Use qdrant-client for vector storage
2. **CrewAI**: Create agents for API analysis, UI validation, edge case discovery
3. **Mistral AI**: Use for generating test descriptions and enhancing test cases
4. **Linkup**: Search for testing best practices and patterns

## MLB Context
This tool will help test:
- Server-driven UI components in MLB mobile apps
- GraphQL API responses from Fastball Gateway
- My Daily Story personalization features
- Cross-platform consistency (iOS/Android)

## Running Tests
```bash
# Run specific test file
pytest tests/test_1_vector_store_initialization.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only failing tests
pytest tests/ --lf