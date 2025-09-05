# Codebase Structure

## Root Directory Files
- `.env.example` - Template for environment variables (currently empty)
- `.gitignore` - Git ignore patterns
- `README.md` - Project readme (minimal content)
- `requirements.txt` - pip-compiled dependencies (auto-generated)
- `requirements.in` - Source dependency list for pip-compile
- `setup.py` - Package setup with CLI entry point `test-gen`
- `docker-compose.yml` - Docker services configuration
- `pytest.ini` - Pytest configuration with coverage settings
- `PROJECT_LAYOUT.md` - Visual directory structure
- `CLAUDE.md` - Instructions for Claude AI assistant
- `LICENSE.md` - Project license

## Source Code (`src/`)
### Main Modules
- `vector_store.py` - ServerDrivenUIVectorStore class for Qdrant operations
- `pattern_extractor.py` - Extract patterns from UI schemas
- `test_generator.py` - TestGenerator class for test case generation
- `test_generation_crew.py` - CrewAI orchestration
- `similarity_engine.py` - TestSimilarityEngine for pattern matching
- `edge_case_discoverer.py` - EdgeCaseDiscoverer class
- `external_enrichment.py` - ExternalTestEnrichment with MistralTestEnhancer
- `llm_integration.py` - Language model integrations
- `pipeline.py` - TestGenerationPipeline main orchestration
- `main.py` - CLI entry point and demo functions
- `reporting.py` - TestReportGenerator, TestExporter, CoverageCalculator
- `metrics_dashboard.py` - Metrics visualization
- `web_interface.py` - Web UI components

### Sub-packages
#### `agents/` - CrewAI Agents
- `api_analyzer.py` - API analysis agent
- `ui_validator.py` - UI validation agent  
- `edge_case_hunter.py` - Edge case discovery agent
- `test_writer.py` - Test writing agent

#### `mlb_integration/` - MLB Specific
- `fastball_gateway_parser.py` - Parse Fastball Gateway responses
- `mds_component_analyzer.py` - My Daily Story component analysis
- `cross_platform_validator.py` - iOS/Android consistency checks

#### `schemas/` - Data Models
- `ui_components.py` - UI component schemas
- `test_patterns.py` - Test pattern definitions

## Tests (`tests/`)
- `conftest.py` - Pytest fixtures and configuration
- `test_1_*.py` through `test_10_*.py` - Sequential TDD test files
- Each test file tests specific functionality in order

## Configuration (`config/`)
- `settings.py` - Application settings
- `hackathon_config.yaml` - Hackathon and partner configuration

## Examples (`examples/`)
- `sample_ui_schemas/` - Sample UI schema JSON files
  - `login_screen.json`
  - `mention_daily_story.json`
  - `stadium_navigator.json`
- `generated_tests/` - Output directory for generated tests

## Demo (`demo/`)
- Demo and presentation materials for hackathon

## Notebooks (`notebooks/`)
- `demo.ipynb` - Demo notebook
- `hackathon_presentation.ipynb` - Presentation notebook

## Docker Services
Defined in `docker-compose.yml`:
- **Qdrant** (port 6333) - Vector database
- **Neo4j** (ports 7474, 7687) - Graph database  
- **Redis** (port 6379) - Caching layer

## Entry Points
- CLI: `test-gen` command (installed via setup.py)
- Direct: `python -m src.pipeline`
- Demo: Functions in `src/main.py`

## Key Implementation Files
Based on TDD tests, the core implementations are:
1. `vector_store.py` - Qdrant vector storage
2. `pattern_extractor.py` - Pattern extraction
3. `agents/*.py` - CrewAI agents
4. `test_generator.py` - Test generation
5. `similarity_engine.py` - Similarity search
6. `edge_case_discoverer.py` - Edge case discovery
7. `external_enrichment.py` - External search
8. `pipeline.py` - Full pipeline
9. `mlb_integration/*.py` - MLB specifics
10. `reporting.py` - Output generation