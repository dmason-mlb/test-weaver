# test-weaver

**Intelligent Test Case Generator for Server-Driven UI - Qdrant Hackathon 2025**

An AI-powered test generation system that creates intelligent test cases for MLB's server-driven UI components using vector similarity search and multi-agent orchestration.

## 🚀 Quickstart

```bash
git clone <repository-url>
cd test-weaver
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
docker-compose up -d
python src/main.py
```

## Prerequisites

- **Python**: 3.9+ (tested with 3.12)
- **Docker**: For Qdrant, Neo4j, and Redis services
- **Git**: For version control

## Key Technologies

- **Qdrant**: Vector database for storing and searching UI test patterns
- **CrewAI**: Multi-agent orchestration for test generation workflow  
- **Mistral AI**: Language model for generating test descriptions
- **Linkup**: External search for testing best practices and patterns

## Installation & Local Development

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template (create .env from .env.example when available)
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services

```bash
# Start required services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Services:**
- **Qdrant**: `localhost:6333` (vector database)
- **Neo4j**: `localhost:7474/7687` (graph database) 
- **Redis**: `localhost:6379` (caching)

### 4. Run Application

```bash
# Run main application
python src/main.py

# Or start web interface
python src/web_interface.py
```

## Configuration

| Service | Port | Purpose | Environment Variables |
|---------|------|---------|----------------------|
| Qdrant | 6333 | Vector database | `QDRANT_LOG_LEVEL` |
| Neo4j | 7474/7687 | Graph database | `NEO4J_AUTH_FILE` |
| Redis | 6379 | Caching | None |

Required API Keys (add to .env):
- OpenAI API key for GPT models
- Mistral AI API key  
- Linkup SDK credentials

## Available Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `python src/main.py` | Run main test generation pipeline | Primary application entry point |
| `python src/web_interface.py` | Start Streamlit web interface | Interactive demo and testing |
| `docker-compose up -d` | Start all services | Before running application |
| `docker-compose down` | Stop all services | After development session |

## Testing & Quality Assurance

```bash
# Run all tests
pytest tests/ -v

# Run specific test (follow numbered order)
pytest tests/test_1_vector_store_initialization.py -v

# Run with coverage (80% minimum required)
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80

# Run only failing tests
pytest tests/ --lf

# Run by test markers
pytest -m unit        # Unit tests
pytest -m integration # Integration tests
pytest -m hackathon   # Hackathon demo tests

# Code quality tools
black src/ tests/     # Format code
isort src/ tests/     # Sort imports
flake8 src/ tests/    # Lint code
mypy src/             # Type checking
```

## Test-Driven Development Workflow

This project follows strict TDD with sequential numbered tests:

1. **Test Files**: Run in numerical order (test_1_*.py → test_10_*.py)
2. **Implementation Rule**: Only implement minimal code to pass current test
3. **Process**: Red → Green → Refactor for each test
4. **Coverage Target**: 80% minimum (enforced by pytest)

### Test Sequence
1. `test_1_vector_store_initialization.py` - Qdrant connection
2. `test_2_pattern_extraction.py` - UI pattern extraction
3. `test_3_agent_initialization.py` - CrewAI agents setup
4. `test_4_test_case_generation.py` - AI test generation
5. `test_5_similarity_search.py` - Vector similarity search
6. `test_6_edge_case_discovery.py` - Edge case detection
7. `test_7_external_search.py` - Linkup integration
8. `test_8_pipeline_integration.py` - Full pipeline
9. `test_9_mlb_integration.py` - MLB-specific testing
10. `test_10_output_generation.py` - Test output generation

## Project Structure

```
test-weaver/
├── src/                     # Source code
│   ├── agents/             # CrewAI agents (UI validator, API analyzer)
│   ├── mlb_integration/    # MLB-specific components
│   ├── schemas/            # Data schemas for UI and tests
│   ├── vector_store.py     # Qdrant vector storage
│   ├── pipeline.py         # Test generation pipeline
│   ├── main.py             # Application entry point
│   └── web_interface.py    # Streamlit web UI
├── tests/                  # Sequential test files (test_1_*.py → test_10_*.py)
├── examples/               # Sample UI schemas and generated tests
├── config/                 # Configuration files
├── docker-compose.yml      # Service definitions
└── requirements.in/.txt    # Dependencies
```

## MLB Context

Generates tests for MLB's server-driven UI components:

- **Components**: Team Page, Browse Menu, Gameday, Scoreboard
- **Platforms**: iOS/Android cross-platform consistency
- **Features**: My Daily Story personalization
- **API**: GraphQL responses from Fastball Gateway

**Test Coverage**: Happy Path, Edge Cases, Error Handling, Performance, Accessibility

## Architecture

**Core Components:**
- `ServerDrivenUIVectorStore`: Qdrant-based pattern storage
- `CrewAI Agents`: Multi-agent test generation orchestration  
- `Pattern Extractors`: Reusable UI pattern extraction
- `Similarity Search`: Vector-based pattern matching
- `External Search`: Linkup integration for test patterns

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check if ports are in use
lsof -i :6333 -i :7474 -i :7687 -i :6379

# Reset Docker services
docker-compose down -v
docker-compose up -d
```

**Import errors:**
```bash
# Reinstall in development mode
pip install -e .
```

**Test failures:**
```bash
# Run tests individually to isolate issues
pytest tests/test_1_vector_store_initialization.py -v -s

# Clear test cache
pytest --cache-clear
```

**Neo4j authentication:**
```bash
# Check neo4j auth file exists
ls -la secrets/neo4j_auth.txt
```

## Development Tools

Dependencies managed via `pip-compile`:
```bash
# Update dependencies
pip-compile requirements.in
pip install -r requirements.txt
```

## License

MIT License - see [LICENSE.md](LICENSE.md)

**Copyright (c) 2025 Douglas Mason**

## Contributing

We welcome contributions! Please ensure:

- All tests pass: `pytest tests/ -v`
- Code is formatted: `black src/ tests/`
- Imports are sorted: `isort src/ tests/`  
- Code is linted: `flake8 src/ tests/`
- Types are checked: `mypy src/`
- Coverage ≥ 80%: `pytest --cov=src --cov-fail-under=80`

For major changes, please open an issue first to discuss the proposed changes.

## Project Status

🚧 **Active Development** - Qdrant Hackathon 2025 Project

Built with ❤️ for MLB's server-driven UI testing needs.