# Code Style and Conventions

## Python Version
- Python 3.9+ required (currently using Python 3.12.6)
- Use modern Python features and type hints where applicable

## Code Formatting
- **Black**: Code formatter with default settings
- **isort**: Import sorting with default configuration
- Line length: Default Black settings (88 characters)
- Indentation: 4 spaces (Python standard)

## Code Style Patterns Observed
### Classes
- Use PascalCase for class names (e.g., `ServerDrivenUIVectorStore`, `TestGenerator`)
- Include docstrings for classes and methods
- Initialize attributes in `__init__` method

### Functions and Methods
- Use snake_case for function and method names (e.g., `health_check`, `search_patterns`)
- Include descriptive docstrings using triple quotes
- Type hints are encouraged but not consistently used in current codebase

### File Organization
- One main class per file typically
- Related utility functions in the same file
- Import statements at the top, organized by:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports

### Naming Conventions
- Variables: snake_case (e.g., `vector_store`, `test_patterns`)
- Constants: UPPER_SNAKE_CASE (not observed yet but standard)
- Private methods/attributes: prefix with underscore (e.g., `_internal_method`)
- Module names: lowercase with underscores (e.g., `vector_store.py`, `pattern_extractor.py`)

## Testing Conventions
### Test Files
- Named with `test_N_feature.py` pattern where N is sequential number
- Tests run in numbered order for TDD approach
- Located in `tests/` directory

### Test Functions
- Prefix with `test_` (e.g., `test_qdrant_client_not_initialized`)
- Descriptive names indicating what is being tested
- Use pytest framework conventions

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.hackathon` - Hackathon demo tests
- `@pytest.mark.slow` - Slow running tests

### Coverage Requirements
- Minimum 80% code coverage enforced
- Coverage reports in both terminal and HTML format
- Use `--cov-fail-under=80` to enforce minimum

## Documentation
- Docstrings for all public classes and methods
- Use triple quotes for docstrings
- Brief description on first line
- More detailed explanation if needed after blank line

## Import Style
- Group imports logically
- Avoid wildcard imports (`from module import *`)
- Use absolute imports for clarity
- Sort imports with isort tool

## Error Handling
- Use specific exception types when possible
- Include helpful error messages
- Document exceptions in docstrings when relevant

## Project-Specific Conventions
- Vector store implementations should inherit from base classes
- Agent classes follow CrewAI patterns
- MLB integration code in dedicated `mlb_integration/` module
- Schemas defined using Pydantic models in `schemas/` module

## Configuration
- Environment variables in `.env` file (not committed)
- YAML for configuration files (e.g., `hackathon_config.yaml`)
- Use python-dotenv for loading environment variables

## Linting Rules
- Follow flake8 default rules
- Use mypy for type checking (though not strictly enforced)
- Black formatting takes precedence over other style guides