# Project Overview

## Project Name
MLB Intelligent Test Generator (test-weaver)

## Current Status: 45% Complete (September 16, 2025)
**Validated by Karen agent assessment through comprehensive gap analysis**

## Purpose
An internal MLB tool that automatically generates comprehensive test suites for server-driven UI components. The system uses AI-powered vector similarity search, OpenAI embeddings, and Mistral AI to create intelligent, context-aware test cases. It aims to improve test coverage and reduce manual test creation effort for MLB's mobile applications (iOS/Android).

## Key Features (Working)
- **Real AI Integration**: OpenAI embeddings (1536 dimensions) with cosine similarity search ✅
- **Intelligent Test Generation**: Mistral AI creates context-aware Selenium tests (no Mock objects) ✅
- **Vector Pattern Matching**: Enhanced ServerDrivenUIVectorStore with business logic validation ✅
- **Authentication Handling**: Full auth setup for `requires_auth: true` components ✅
- **MLB-Specific Components**: Team Page, Browse Menu, Gameday, Scoreboard support ✅
- **Comprehensive Coverage**: Happy Path, Edge Cases, Error Handling tests ✅
- **Real Test Code**: Generates executable WebDriver tests with component IDs ✅

## Key Features (Missing - 35% Gap)
- **Multi-agent orchestration**: CrewAI framework implementation (15% gap) ❌
- **Persistent storage**: Qdrant vector database integration (8% gap) ❌
- **Advanced scenarios**: Performance/accessibility automation (7% gap) ❌
- **External search**: Linkup integration for testing patterns (3% gap) ❌
- **Advanced MLB features**: Extended MDS component handling (2% gap) ❌

## Tech Stack
### AI Technologies (Fully Functional)
- **OpenAI**: Real embeddings API for 1536-dimensional vectors ✅
- **Mistral AI**: Context-aware test code generation ✅
- **Vector Similarity**: Cosine similarity calculations ✅
- **Enhanced Vector Store**: Business logic validation patterns ✅

### Core Technologies
- **Python 3.9+** (tested with Python 3.12.6)
- **Qdrant**: Vector database (Docker configured, not integrated)
- **CrewAI**: Multi-agent orchestration framework (stub implementations only)
- **Selenium**: WebDriver automation (working)

### Additional Technologies
- **FastAPI**: Web framework for API endpoints
- **Pydantic**: Data validation and schemas
- **Docker**: Container services for Qdrant, Neo4j, and Redis
- **Pytest**: Testing framework with 7/7 end-to-end tests passing

## Project Structure
- `src/`: Main source code (15 of 28 files substantially implemented)
  - `intelligent_pipeline.py`: AI orchestration pipeline (✅ with auth)
  - `vector_store.py`: Enhanced vector storage with business logic (✅)
  - `ai_test_generator.py`: Mistral AI test generation (✅ auth-aware)
  - `test_generator.py`: 17 interaction handlers (✅ fixed)
  - `pattern_extractor.py`: 12 component handlers (✅ fixed)
  - `test_generation_crew.py`: 7-line stub class (❌ needs implementation)
  - `agents/`: CrewAI agents (❌ stub implementations)
  - `mlb_integration/`: MLB-specific integrations (✅ basic working)
  - `bullpen_integration/`: MLB Bullpen Gateway integration (✅ working)
  - `pipeline.py`: Main orchestration pipeline (✅ edge cases fixed)
- `tests/`: Sequential TDD test files (7/7 end-to-end tests passing)
- `config/`: Configuration files including bullpen_config.yaml
- `examples/`: Sample UI schemas and generated tests

## Development Environment
- Platform: Darwin (macOS)
- Virtual environment: venv
- Package management: pip with requirements.in -> requirements.txt
- Docker services: Qdrant (6333), Neo4j (7474/7687), Redis (6379)

## Phase 2 Plan (45% → 75% in 2-3 weeks)
1. **CrewAI Agent Implementation** (15% impact): Real agent intelligence and orchestration
2. **Qdrant Integration** (8% impact): Persistent vector storage with learning
3. **Advanced Test Scenarios** (7% impact): Performance and accessibility automation
4. **External Enrichment** (3% impact): Linkup integration for pattern discovery

## Recent Major Achievements
- All 5 NotImplementedError exceptions resolved
- Mock objects eliminated from generated tests  
- Authentication handling for secure components implemented
- Vector store enhanced with business logic validation
- Karen's critical findings addressed and validated
- End-to-end pipeline working with real WebDriver automation