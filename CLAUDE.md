# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Intelligent Test Case Generator for Server-Driven UI, built for the Qdrant Hackathon 2025. The project generates intelligent test cases for MLB's server-driven UI components using vector similarity search and multi-agent orchestration.

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
- Create a virtual environment
- Install dependencies
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
- Neo4j: localhost:7474/7687 (auth: neo4j/hackathon2025)
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
pytest -m hackathon   # Hackathon demo tests
```

### TDD Implementation Rules
1. Start with `test_1_vector_store_initialization.py` and proceed in numerical order
2. Run the test to see it fail
3. Implement ONLY the minimal code needed to make the current test pass
4. Do NOT implement features before their tests exist
5. Do NOT modify test files
6. Each test file represents a feature milestone

## Architecture

### Source Structure
- `src/vector_store.py`: Core Qdrant vector storage implementation
- `src/agents/`: CrewAI agents for different aspects of test generation
- `src/mlb_integration/`: MLB-specific server-driven UI integration
- `src/schemas/`: Data schemas for UI components and test cases

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
9. `test_9_mlb_integration.py` - MLB-specific server-driven UI testing
10. `test_10_output_generation.py` - Generate final test output

## MLB Context

The system generates tests for MLB's server-driven UI components:
- Team Page, Browse Menu, Gameday, Scoreboard components
- Cross-platform consistency (iOS/Android)
- My Daily Story personalization features
- GraphQL API responses from Fastball Gateway

## Configuration

- `config/hackathon_config.yaml`: Project and partner configuration
- `pytest.ini`: Test configuration with coverage requirements
- `docker_compose.yml`: Required services configuration

## Installation

The project uses setuptools with entry point:
```bash
pip install -e .
test-gen  # CLI entry point
```

Dependencies are managed in `requirements.txt` and automatically installed during setup.