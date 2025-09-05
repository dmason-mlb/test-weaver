# Project Overview

## Project Name
Intelligent Test Case Generator for Server-Driven UI (test-weaver)

## Purpose
Built for the Qdrant Hackathon 2025, this project generates intelligent test cases for MLB's server-driven UI components using vector similarity search and multi-agent orchestration. It aims to automate test generation for MLB's mobile applications (iOS/Android) with a focus on server-driven UI testing.

## Key Features
- Vector-based test pattern storage and similarity search using Qdrant
- Multi-agent orchestration for test generation workflow using CrewAI
- Integration with Mistral AI for language model-powered test generation
- External search capabilities via Linkup for testing best practices
- Support for MLB-specific server-driven UI components (Team Page, Browse Menu, Gameday, Scoreboard)
- Test generation strategies: Happy Path, Edge Cases, Error Handling, Performance, Accessibility

## Tech Stack
### Core Technologies
- **Python 3.9+** (tested with Python 3.12.6)
- **Qdrant**: Vector database for storing and searching UI test patterns
- **CrewAI**: Multi-agent orchestration framework
- **Mistral AI**: Language model for test generation
- **Linkup SDK**: External search for testing patterns

### Additional Technologies
- **FastAPI**: Web framework for API endpoints
- **Pydantic**: Data validation and schemas
- **Sentence Transformers**: For vector embeddings
- **Docker**: Container services for Qdrant, Neo4j, and Redis
- **Pytest**: Testing framework with coverage requirements

## Project Structure
- `src/`: Main source code
  - `vector_store.py`: Qdrant vector storage implementation
  - `agents/`: CrewAI agents for test generation
  - `mlb_integration/`: MLB-specific integrations
  - `schemas/`: Data schemas for UI components
  - `pipeline.py`: Main orchestration pipeline
- `tests/`: Sequential TDD test files (numbered 1-10)
- `config/`: Configuration files including hackathon_config.yaml
- `demo/`: Demo and presentation materials
- `examples/`: Sample UI schemas and generated tests

## Development Environment
- Platform: Darwin (macOS)
- Virtual environment: venv
- Package management: pip with requirements.in -> requirements.txt (pip-compile)
- Docker services: Qdrant (6333), Neo4j (7474/7687), Redis (6379)