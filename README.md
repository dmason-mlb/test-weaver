# test-weaver

**MLB Intelligent Test Generator**

An internal MLB tool that leverages artificial intelligence to automatically generate comprehensive test suites for server-driven UI components. This system uses vector similarity search, OpenAI embeddings, and Mistral AI to create intelligent, context-aware test cases.

## 🎯 **Current Status: 45% Complete**

**✅ What's Working:**
- AI-powered test generation with real WebDriver automation
- Authentication handling for secure components (`requires_auth: true`)
- Vector similarity search with enhanced business logic patterns
- End-to-end pipeline validation (7/7 tests passing)
- OpenAI embeddings + Mistral AI integration with graceful fallbacks

**🚧 Major Components in Development:**
- CrewAI multi-agent system (15% gap) - Priority for Phase 2
- Qdrant persistent vector storage (8% gap) - Currently in-memory only
- Advanced test scenarios (7% gap) - Performance/accessibility automation
- External pattern enrichment (3% gap) - Linkup integration

**📅 Next Milestone:** Phase 2 (45% → 75% completion) - 2-3 weeks

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

- **OpenAI**: Real embeddings (1536 dimensions) for intelligent pattern matching
- **Mistral AI**: AI-powered test code generation with contextual understanding
- **Qdrant**: Vector database for storing and searching UI test patterns (with in-memory fallback)
- **Vector Similarity**: Cosine similarity search for finding related test patterns
- **CrewAI**: Multi-agent orchestration framework (partial implementation)
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

| Command | Description | Status |
|---------|-------------|--------|
| `python src/main.py` | Run main test generation pipeline | ✅ Working |
| `python src/web_interface.py` | Start Streamlit web interface | ✅ Working |
| `python src/pipeline.py --config config/bullpen_config.yaml` | Generate tests with specific config | ✅ Working |
| `pytest tests/test_end_to_end_pipeline.py -v` | Run end-to-end validation (7/7 passing) | ✅ All tests passing |
| `docker-compose up -d` | Start all services (Qdrant/Neo4j/Redis) | ⚠️ Services available but not fully integrated |
| `docker-compose down` | Stop all services | ✅ Working |

### Status Validation Commands
```bash
# Test AI components
python -c "from src.ai_test_generator import AITestGenerator; gen = AITestGenerator(); print('AI Generator Ready')"

# Test intelligent pipeline
python -c "from src.intelligent_pipeline import IntelligentTestPipeline; p = IntelligentTestPipeline(); print('Pipeline Ready')"

# Check vector store
python -c "from src.vector_store import ServerDrivenUIVectorStore; vs = ServerDrivenUIVectorStore(); print('Vector Store Ready')"
```

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
9. `test_9_bullpen_integration.py` - MLB Bullpen Gateway integration testing
10. `test_10_output_generation.py` - Test output generation

## Project Structure

```
test-weaver/
├── src/                     # Source code
│   ├── agents/             # CrewAI agents (UI validator, API analyzer)
│   ├── mlb_integration/    # MLB integration (cross-platform, fastball, MDS)
│   ├── bullpen_integration/    # MLB Bullpen Gateway integration
│   ├── schemas/            # Data schemas for UI and tests
│   ├── vector_store.py     # Legacy Qdrant vector storage
│   ├── ai_vector_store.py  # AI-powered vector store with OpenAI embeddings
│   ├── ai_test_generator.py # Mistral AI test generation
│   ├── intelligent_pipeline.py # AI orchestration pipeline
│   ├── pipeline.py         # Main test generation pipeline
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

**AI-Powered Components:**
- `AIVectorStore`: In-memory vector store with real OpenAI embeddings (1536 dimensions)
- `AITestGenerator`: Mistral AI for intelligent test code generation
- `IntelligentPipeline`: AI orchestration with vector similarity search
- `Vector Similarity`: Cosine similarity calculations for pattern matching

**Legacy/Supporting Components:**
- `ServerDrivenUIVectorStore`: Qdrant-based pattern storage (with fallback)
- `CrewAI Agents`: Multi-agent test generation orchestration (partial)
- `Pattern Extractors`: Reusable UI pattern extraction
- `External Search`: Linkup integration for test patterns

## AI Capabilities

**Real AI Features (Fully Functional):**
- **OpenAI Embeddings**: Generate 1536-dimensional vectors for UI patterns
- **Mistral Test Generation**: Context-aware Python test code generation
- **Vector Similarity Search**: Cosine similarity for finding related patterns
- **Intelligent Adaptation**: Adapt existing patterns to new components
- **Edge Case Discovery**: AI-powered edge case identification
- **Performance Testing**: Generate tests with timing and validation logic

**Generates Real Selenium/Playwright Tests:**
- Actual WebDriver automation code (not Mock objects)
- Performance measurements and assertions
- Error handling and state validation
- Cross-browser compatibility checks

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

🚧 **Active Development** - Internal MLB Tool

Built with ❤️ for MLB's server-driven UI testing needs.