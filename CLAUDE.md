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
- `IMPLEMENTATION_STATUS.md` tracks real-time implementation progress (primary status file)
- Must be updated immediately after completing any significant task
- Contains critical metrics: files modified, NotImplementedErrors fixed, test coverage
- Includes detailed timeline with specific timestamps and descriptions
- **Cross-Reference**: Also update `PROJECT_PROGRESS.md` for historical record
- **Cross-Reference**: Update `ARCHITECTURE.md` for technical/architectural changes
- **Cross-Reference**: Keep `REMAINING_WORK.md` synchronized with priorities

### When to Update Status Document
1. **After fixing any NotImplementedError or placeholder code**
   - Also update `REMAINING_WORK.md` to remove from outstanding issues
2. **After completing any major feature or component**
   - Also update `PROJECT_PROGRESS.md` with milestone entry
   - Update `ARCHITECTURE.md` if component relationships changed
3. **After making architectural changes**
   - **CRITICAL**: Update `ARCHITECTURE.md` with technical details
   - Update diagrams and component descriptions
4. **After achieving significant milestones**
   - Add detailed entry to `PROJECT_PROGRESS.md` historical timeline
5. **When starting or completing implementation phases**
   - Update all relevant documentation files for consistency

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

### Example Multi-File Documentation Update
```markdown
IMPLEMENTATION_STATUS.md:
- **12:45 PM**: ✅ **FIXED** ai_test_generator.py integration placeholder - Added comprehensive fallback test generator
  - Replaced placeholder pass statement with full Selenium WebDriver integration tests
  - Added component-specific testing based on UI schema analysis
  - Includes responsiveness testing, error handling, and performance validation
- **Next**: Begin Phase 2 implementation

PROJECT_PROGRESS.md:
- **12:45 PM**: ✅ **MILESTONE** ai_test_generator.py integration completed
  - Comprehensive fallback test generator implemented with real WebDriver code
  - Component-specific testing logic based on UI schema analysis
  - Integration with existing pipeline and authentication handling

REMAINING_WORK.md:
- Remove "ai_test_generator.py line 295 integration placeholder" from known issues
- Update completion percentage from previous milestone
- Adjust Phase 2 priorities based on completed foundation

ARCHITECTURE.md:
- Update AI Test Generation component description to reflect actual implementation
- Update data flow diagram to show real integration paths vs placeholders
```

**Note**: The implementation status document serves as the single source of truth for project progress and must always reflect the current state of the codebase.

## Documentation Maintenance

**CRITICAL**: Maintain ALL documentation files when completing tasks. The project uses multiple documentation files that must be kept synchronized and accurate to provide a reliable source of truth for project state.

### Required Documentation Files

When making changes, you MUST update the following files as appropriate:

1. **IMPLEMENTATION_STATUS.md** - Real-time implementation progress with executive summary
2. **PROJECT_PROGRESS.md** - Complete historical timeline of all work completed
3. **PROJECT_LAYOUT.md** - File structure and directory organization
4. **ARCHITECTURE.md** - System architecture, technical design, and component relationships
5. **REMAINING_WORK.md** - Outstanding tasks, priorities, and realistic timelines
6. **README.md** - Project overview, current status, and quickstart guide

### When to Update Documentation

#### After ANY Code Changes:
- **IMPLEMENTATION_STATUS.md**: Update metrics table, add timestamped entry to recent updates
- **PROJECT_PROGRESS.md**: Add to timeline if significant milestone achieved
- **ARCHITECTURE.md**: Update component descriptions if functionality changed

#### After Adding/Removing Files:
- **PROJECT_LAYOUT.md**: Update file tree structure to match actual directory
- **ARCHITECTURE.md**: Update file structure section if architectural file added/removed
- **IMPLEMENTATION_STATUS.md**: Update "Files Modified" count in metrics table

#### After Fixing Issues:
- **IMPLEMENTATION_STATUS.md**: Mark as ✅ **FIXED** with timestamp and details
- **PROJECT_PROGRESS.md**: Add to progress timeline with technical specifics
- **REMAINING_WORK.md**: Remove from outstanding tasks list
- **ARCHITECTURE.md**: Update component status if architectural fix

#### After Architectural Changes:
- **ARCHITECTURE.md**: Update diagrams, data flow, component descriptions, integration points
- **IMPLEMENTATION_STATUS.md**: Note architectural change with timestamp
- **PROJECT_PROGRESS.md**: Document architectural milestone
- **README.md**: Update architecture overview if user-facing

#### After Completing Features:
- **All relevant files**: Update completion percentages consistently
- **REMAINING_WORK.md**: Remove completed items from priority lists
- **IMPLEMENTATION_STATUS.md**: Add to completed sections
- **PROJECT_PROGRESS.md**: Document feature completion milestone

### Documentation Update Checklist

Before considering any task complete, verify:
- [ ] **IMPLEMENTATION_STATUS.md** updated with timestamp and technical details
- [ ] **PROJECT_PROGRESS.md** updated if milestone achieved (major fixes, feature completions)
- [ ] **PROJECT_LAYOUT.md** updated if files added/removed/reorganized
- [ ] **ARCHITECTURE.md** updated if component relationships or technical design changed
- [ ] **REMAINING_WORK.md** updated to remove completed items and adjust priorities
- [ ] **README.md** updated if user-facing changes or status changed
- [ ] **Completion percentages** accurate and consistent across all files
- [ ] **Timeline entries** include specific technical details and file names
- [ ] **Serena memories** updated if major progress made

### Documentation Synchronization Rules

1. **Completion Percentages**: Must match across all files
   - IMPLEMENTATION_STATUS.md, README.md, PROJECT_PROGRESS.md, and Serena memories must show same percentage

2. **Timeline Consistency**:
   - PROJECT_PROGRESS.md is the authoritative historical record
   - IMPLEMENTATION_STATUS.md shows current state and recent updates
   - All timestamps must be accurate and detailed

3. **Architecture Accuracy**:
   - ARCHITECTURE.md must reflect actual implementation, not planned features
   - Update component diagrams when integration relationships change
   - Mark missing components clearly vs working components

4. **File Structure Accuracy**:
   - PROJECT_LAYOUT.md must match actual directory structure exactly
   - Run `tree` command to verify accuracy when files added/removed

5. **Priority Alignment**:
   - REMAINING_WORK.md priorities must align with IMPLEMENTATION_STATUS.md next steps
   - Remove completed items immediately to avoid confusion

### Documentation Templates

#### Feature Completion Template:
```markdown
IMPLEMENTATION_STATUS.md:
- **[TIME]**: ✅ **COMPLETED** [feature name] - [brief description]
  - [Specific technical details of implementation]
  - [Files modified and key changes made]
  - [Test coverage or validation performed]

PROJECT_PROGRESS.md:
- **[TIME]**: ✅ **MILESTONE** [feature name] completed
  - [Technical implementation details]
  - [Integration points and dependencies]

REMAINING_WORK.md:
- Remove completed feature from priority lists
- Update completion percentages
- Adjust timeline estimates
```

#### Bug Fix Template:
```markdown
IMPLEMENTATION_STATUS.md:
- **[TIME]**: ✅ **FIXED** [file]:[line] [issue description] - [solution summary]
  - [Root cause analysis]
  - [Technical fix implemented]
  - [Validation performed]

ARCHITECTURE.md (if architectural):
- Update component diagram if integration fixed
- Update data flow if process corrected
```

#### File Addition/Removal Template:
```markdown
PROJECT_LAYOUT.md:
- Update directory tree structure
- Add/remove file entries with descriptions

ARCHITECTURE.md:
- Update file structure section
- Update component relationships if new architectural file

IMPLEMENTATION_STATUS.md:
- Update "Files Modified" count
- Add timestamped entry for file changes
```