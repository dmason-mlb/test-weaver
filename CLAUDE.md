# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the MLB Intelligent Test Generator, an internal tool for automatically generating comprehensive test suites for MLB's server-driven UI components. The system uses AI-powered vector similarity search, OpenAI embeddings, and Mistral AI to create intelligent, context-aware test cases.

## Key Technologies

- **Qdrant**: Vector database for storing and searching UI test patterns
- **CrewAI**: Multi-agent orchestration for test generation workflow
- **Mistral AI**: Language model for generating test descriptions and enhancing test cases
- **Linkup**: External search for testing best practices and patterns

## Development Setup

### Initial Setup
```bash
# Run the setup script
./start_tdd.sh
```

This will:
- Create a virtual environment (`venv/`)
- Install dependencies from `requirements.txt`
- Copy `.env.example` to `.env` (update with API keys)
- Start Docker services (Qdrant, Neo4j, Redis)
- Run the first failing test to begin TDD

### Docker Services
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down
```

Services:
- Qdrant: localhost:6333 (vector database)
- Neo4j: localhost:7474/7687 (graph database)
- Redis: localhost:6379 (caching)

## Test-Driven Development Process

This project follows strict TDD with numbered test files:

### Running Tests
```bash
# Run specific test (follow the numbered order)
pytest tests/test_1_vector_store_initialization.py -v

# Run all tests
pytest tests/ -v

# Run with coverage (80% required)
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80

# Run only failing tests
pytest tests/ --lf

# Run by test markers
pytest -m unit        # Unit tests
pytest -m integration # Integration tests

# Development tools
black src/ tests/     # Format code
isort src/ tests/     # Sort imports  
flake8 src/ tests/    # Lint code
mypy src/             # Type check
```

### TDD Implementation Rules
1. Start with `test_1_vector_store_initialization.py` and proceed in numerical order
2. Run the test to see it fail
3. Implement ONLY the minimal code needed to make the current test pass
4. Do NOT implement features before their tests exist
5. Do NOT modify test files
6. Each test file represents a feature milestone

## Architecture

The project follows a layered architecture with vector-based pattern matching:

### Core Components
- `ServerDrivenUIVectorStore`: Main vector store implementation using Qdrant
- `CrewAI Agents`: Multi-agent system for test generation orchestration
- `Pattern Extractors`: Extract reusable patterns from UI schemas
- `Similarity Search`: Find similar test patterns using vector embeddings
- `External Search`: Linkup integration for broader test pattern discovery

### Source Structure
- `src/vector_store.py`: Core Qdrant vector storage implementation
- `src/agents/`: CrewAI agents for different aspects of test generation  
- `src/bullpen_integration/`: MLB Bullpen Gateway integration
- `src/schemas/`: Data schemas for UI components and test cases
- `src/pipeline.py`: Main orchestration pipeline (CLI entry point)

### Test Structure
Sequential test files (run in order):
1. `test_1_vector_store_initialization.py` - Qdrant connection and basic vector operations
2. `test_2_pattern_extraction.py` - Extract patterns from UI schemas
3. `test_3_agent_initialization.py` - CrewAI agents setup
4. `test_4_test_case_generation.py` - Generate test cases using AI
5. `test_5_similarity_search.py` - Vector similarity search for test patterns
6. `test_6_edge_case_discovery.py` - Discover edge cases in UI components
7. `test_7_external_search.py` - Linkup integration for external test patterns
8. `test_8_pipeline_integration.py` - Full pipeline orchestration
9. `test_9_bullpen_integration.py` - MLB Bullpen Gateway integration testing
10. `test_10_output_generation.py` - Generate final test output

## MLB Context

The system generates tests for MLB's server-driven UI components:
- Team Page, Browse Menu, Gameday, Scoreboard components
- Cross-platform consistency (iOS/Android)
- My Daily Story personalization features
- GraphQL API responses from Fastball Gateway

Test generation covers: Happy Path, Edge Cases, Error Handling, Performance, Accessibility

## Configuration

- `config/bullpen_config.yaml`: Bullpen Gateway configuration
- `pytest.ini`: Test configuration with coverage requirements (80% minimum)
- `docker-compose.yml`: Required services configuration
- `.env`: API keys (copy from `.env.example`)

## Installation

The project uses setuptools with CLI entry point:
```bash
pip install -e .
test-gen  # CLI entry point -> src.pipeline:main
```

Dependencies managed via `requirements.in` -> `requirements.txt` (pip-compiled)

## Implementation Status Tracking

**IMPORTANT**: Always maintain the `IMPLEMENTATION_STATUS.md` document when making code changes.

### Status Document Requirements
- `IMPLEMENTATION_STATUS.md` tracks real-time implementation progress
- Must be updated immediately after completing any significant task
- Contains critical metrics: files modified, NotImplementedErrors fixed, test coverage
- Includes detailed timeline with specific timestamps and descriptions

### When to Update Status Document
1. **After fixing any NotImplementedError or placeholder code**
2. **After completing any major feature or component**
3. **After making architectural changes**
4. **After achieving significant milestones**
5. **When starting or completing implementation phases**

### Required Updates
When updating `IMPLEMENTATION_STATUS.md`:

1. **Update Metrics Table**:
   - Files Modified count
   - NotImplementedErrors remaining
   - Test coverage percentage
   - Overall progress percentage

2. **Update Status Tables**:
   - Mark fixed issues as ✅ **FIXED**
   - Update component status indicators
   - Change priority levels if needed

3. **Add Recent Updates Entry**:
   - Include timestamp (e.g., "12:45 PM")
   - Describe what was fixed/implemented
   - List specific changes made
   - Use ✅ **FIXED** for completed items

4. **Update "Next" Item**:
   - Point to the next priority task
   - Clear indication of what to work on next

### Status Document Format
```markdown
- **[TIME]**: ✅ **FIXED** [file] [issue description] - [brief summary]
  - [detailed bullet point of changes made]
  - [additional context or technical details]
- **Next**: [next priority task]
```

### Example Status Update
```markdown
- **12:45 PM**: ✅ **FIXED** ai_test_generator.py integration placeholder - Added comprehensive fallback test generator
  - Replaced placeholder pass statement with full Selenium WebDriver integration tests
  - Added component-specific testing based on UI schema analysis
  - Includes responsiveness testing, error handling, and performance validation
- **Next**: Begin Phase 2 implementation
```

**Note**: The implementation status document serves as the single source of truth for project progress and must always reflect the current state of the codebase.