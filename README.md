# test-weaver

**MLB Intelligent Test Generator**

An internal MLB tool that leverages artificial intelligence to automatically generate comprehensive test suites for server-driven UI components. This system uses vector similarity search, OpenAI embeddings, and Mistral AI to create intelligent, context-aware test cases.

## 🎯 **Current Status: 91% Complete**

**✅ What's Working:**
- AI-powered test generation with real WebDriver automation (fully implemented)
- External test enrichment with Linkup API integration (fully functional)
- Vector similarity search with enhanced two-stage pattern ranking
- Component ID resolution with intelligent semantic generation
- End-to-end pipeline validation (all 26 integration tests passing)
- OpenAI embeddings + Mistral AI integration with graceful fallbacks
- **CrewAI multi-agent system** with UIValidator, APIAnalyzer, PatternDiscovery agents
- **Qdrant persistent storage** with pattern learning and evolution
- **Advanced test scenarios** including performance and accessibility automation
- **External Pattern Enrichment** - Linkup integration for external test patterns
- **Real WebDriver Implementation** - Replaced all Mock objects with Selenium automation

**🚧 Remaining Components:**
- Production documentation (9% gap) - Comprehensive monitoring and deployment guides

**📅 Next Milestone:** Production readiness (91% → 100% completion) - 1-2 weeks

## 🚀 Quickstart

```bash
git clone <repository-url>
cd test-weaver
./start_tdd.sh  # Automated setup script
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
- **CrewAI**: Multi-agent orchestration framework with UIValidator, APIAnalyzer, PatternDiscovery agents
- **Linkup**: External search for testing best practices and patterns (fully integrated)

## Installation & Local Development

### 1. Automated Setup

```bash
# Run the complete setup script
./start_tdd.sh
```

This will:
- Create virtual environment (`venv/`)
- Install dependencies from `requirements.txt`
- Copy `.env.example` to `.env` (update with API keys)
- Start Docker services (Qdrant, Neo4j, Redis)
- Run the first failing test to begin TDD

### 2. Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### 4. Start Services

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

### 5. Run Application

```bash
# CLI entry point (installed via pip install -e .)
test-gen path/to/ui_schema.json

# Or run directly
python src/pipeline.py path/to/ui_schema.json

# Web interface
streamlit run src/web_interface.py
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
| `test-gen ui_schema.json` | CLI entry point for test generation | ✅ Working |
| `python src/pipeline.py --config config/bullpen_config.yaml` | Generate tests with specific config | ✅ Working |
| `streamlit run src/web_interface.py` | Start Streamlit web interface | ✅ Working |
| `pytest tests/ -v` | Run all tests (35 tests available) | ✅ All tests passing |
| `docker-compose up -d` | Start all services (Qdrant/Neo4j/Redis) | ✅ Working |
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

## External Test Enrichment

The system now includes comprehensive external pattern enrichment via Linkup API integration:

**Features:**
- **Intelligent Query Generation**: Creates targeted search queries from UI schemas
- **Pattern Relevance Scoring**: Advanced scoring system for external test patterns
- **Content-Based Deduplication**: Prevents duplicate patterns using similarity calculation
- **Component ID Resolution**: Handles both 'id' and 'component_id' fields with semantic fallbacks
- **Real Test Code Generation**: Produces actual Selenium WebDriver automation (no Mock objects)

**Integration Points:**
- CrewAI External Enrichment Agent for orchestration
- Redis caching for pattern usage tracking
- Vector store integration for pattern persistence
- Two-stage pattern ranking for optimal test selection

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

1. **Test Files**: Run in numerical order (test_1_*.py → test_11_*.py)
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
11. `test_11_real_test_generation_validation.py` - Real test generation validation

## Project Structure

```
test-weaver/
├── src/                     # Source code
│   ├── agents/             # CrewAI agents (UI validator, API analyzer)
│   ├── mlb_integration/    # MLB integration (cross-platform, fastball, MDS)
│   ├── bullpen_integration/    # MLB Bullpen Gateway integration
│   ├── schemas/            # Data schemas for UI and tests
│   ├── vector_store.py     # Qdrant vector storage implementation
│   ├── ai_test_generator.py # Mistral AI test generation
│   ├── intelligent_pipeline.py # AI orchestration pipeline
│   ├── external_enrichment.py # Linkup API integration for test patterns
│   ├── pipeline.py         # Main test generation pipeline (CLI entry point)
│   ├── main.py             # Legacy application entry point
│   └── web_interface.py    # Streamlit web UI
├── tests/                  # Sequential test files (test_1_*.py → test_11_*.py)
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
- `ExternalEnrichmentService`: Linkup API integration for external test patterns
- `AITestGenerator`: Mistral AI for intelligent test code generation with real WebDriver
- `IntelligentPipeline`: AI orchestration with vector similarity search
- `Vector Similarity`: Cosine similarity calculations for pattern matching
- `Component ID Resolution`: Intelligent handling of UI component identification

**Supporting Components:**
- `ServerDrivenUIVectorStore`: Qdrant-based pattern storage with two-stage ranking
- `CrewAI Agents`: Multi-agent test generation orchestration
- `Pattern Extractors`: Reusable UI pattern extraction
- `Redis Caching`: Pattern usage tracking and performance optimization

## AI Capabilities

**Real AI Features (Fully Functional):**
- **OpenAI Embeddings**: Generate 1536-dimensional vectors for UI patterns
- **Mistral Test Generation**: Context-aware Python test code generation
- **Vector Similarity Search**: Cosine similarity for finding related patterns
- **External Pattern Enrichment**: Linkup API integration for broader test coverage
- **Intelligent Component ID Generation**: Semantic ID creation with fallbacks
- **Content-Based Deduplication**: Advanced similarity calculation for pattern uniqueness
- **Two-Stage Pattern Ranking**: Enhanced relevance scoring and selection

**Generates Real Selenium/Playwright Tests:**
- Actual WebDriver automation code (no Mock objects)
- Component-specific testing based on UI schema analysis
- Performance measurements and assertions
- Error handling and state validation
- Cross-browser compatibility checks
- Accessibility and responsiveness testing

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

Entry point installed via setuptools:
```bash
pip install -e .
test-gen --help  # Verify CLI works
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

**Recent Achievements:**
- ✅ External enrichment system optimization completed (73% → 91%)
- ✅ All Mock objects replaced with real WebDriver automation
- ✅ Component ID resolution with semantic generation implemented
- ✅ Two-stage vector pattern ranking system deployed
- ✅ Content-based test deduplication system functional
- ✅ All 26 integration tests passing

Built with ❤️ for MLB's server-driven UI testing needs.