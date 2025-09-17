# System Architecture - MLB Intelligent Test Generator

**Project**: AI-powered test generation for MLB's server-driven UI components
**Current Status**: 45% Complete - Functional foundation with major components missing
**Last Updated**: September 16, 2025

## 📋 **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    MLB Test Generation System                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Schema     │    │   AI Services   │    │  Vector Store   │
│   Input Layer   │───▶│     Layer       │───▶│     Layer       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pattern       │    │    Test         │    │    Output       │
│  Extraction     │───▶│  Generation     │───▶│   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CrewAI        │    │   Authentication│    │   Executable    │
│   Agents        │───▶│    Handling     │───▶│   Test Files    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏗️ **Component Architecture**

### Core Pipeline (✅ Working - 45%)

```
Input UI Schema
       │
       ▼
┌─────────────────┐
│ IntelligentTest │ ✅ WORKING
│    Pipeline     │ (with auth handling)
└─────────────────┘
       │
       ▼
┌─────────────────┐    ┌─────────────────┐
│  Vector Store   │───▶│  AI Test Gen    │ ✅ WORKING
│   (Enhanced)    │    │   (Mistral)     │ (with fallbacks)
└─────────────────┘    └─────────────────┘
       │                        │
       ▼                        ▼
┌─────────────────┐    ┌─────────────────┐
│  Pattern Match  │    │ WebDriver Code  │ ✅ WORKING
│  (Similarity)   │    │  Generation     │ (no Mock objects)
└─────────────────┘    └─────────────────┘
```

### Missing Components (❌ 35% Gap)

```
CrewAI Multi-Agent System (❌ 15% gap)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ UIValidator     │    │ APIAnalyzer     │    │ PatternDisc     │
│   Agent         │───▶│     Agent       │───▶│     Agent       │
│ (ValueError)    │    │  (minimal)      │    │  (missing)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│TestGeneration   │    │   Agent         │    │   Consensus     │
│     Crew        │───▶│ Orchestration   │───▶│   Building      │
│  (7-line stub)  │    │   (missing)     │    │   (missing)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Qdrant Integration (❌ 8% gap)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   In-Memory     │    │     Qdrant      │    │   Persistent    │
│   Storage       │───▶│    Docker       │───▶│    Learning     │
│  (current)      │    │ (configured)    │    │   (missing)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Technical Stack**

### ✅ Working Components

#### AI Services Layer
- **OpenAI Embeddings**: 1536-dimensional vectors with cosine similarity
- **Mistral AI**: Context-aware test code generation with prompt engineering
- **Vector Similarity**: Enhanced pattern matching with business logic validation
- **Graceful Degradation**: Fallback mechanisms when APIs unavailable

#### Data Processing Layer
- **Pattern Extraction**: 12 component types (button, webview, list, api_endpoint, etc.)
- **Interaction Handling**: 17 interaction types (click, tap, swipe, scroll, etc.)
- **Authentication Support**: Full auth setup for `requires_auth: true` components
- **Component ID Usage**: Real component IDs in generated tests

#### Test Generation Layer
- **Real WebDriver Code**: Selenium automation (no Mock objects)
- **Business Logic Validation**: Tests verify functionality, not just presence
- **Error Handling**: Comprehensive try/catch blocks and fallbacks
- **MLB Context**: Team Page, Browse, Gameday, Scoreboard components

### ❌ Missing Components

#### CrewAI Agent System
```python
# Current state (❌ Non-functional)
class UIValidatorAgent:
    def validate_component(self, component):
        raise ValueError("UI context not provided")  # 💥 STUB

class TestGenerationCrew:
    def __init__(self):
        self.agents = []  # Empty list

    def kickoff(self):
        if not self.agents:
            raise ValueError("Cannot create crew without agents")  # 💥 STUB

# Needed implementation (✅ Target)
class UIValidatorAgent:
    def validate_component(self, component):
        # Real validation logic
        # Cross-platform consistency checks
        # Accessibility compliance validation
        # MLB design system compliance
```

#### Qdrant Integration
```python
# Current state (⚠️ In-memory only)
class ServerDrivenUIVectorStore:
    def __init__(self):
        self.patterns = {}  # In-memory dictionary
        self.embeddings = {}  # Lost on restart

# Needed implementation (✅ Target)
class ServerDrivenUIVectorStore:
    def __init__(self):
        self.qdrant_client = QdrantClient("localhost", port=6333)
        # Persistent storage with learning capabilities
```

## 📊 **Data Flow**

### Current Working Flow (✅ 45%)

```
1. UI Schema Input
   ↓
2. Component Analysis (pattern_extractor.py)
   ↓
3. Vector Similarity Search (ServerDrivenUIVectorStore)
   ↓
4. Pattern Matching & Adaptation (with auth handling)
   ↓
5. AI Test Generation (Mistral AI with context)
   ↓
6. WebDriver Code Output (real automation)
```

### Missing Flow Components (❌ 35%)

```
1. UI Schema Input
   ↓
2. CrewAI Agent Analysis (❌ MISSING)
   ├── UIValidator validates component design
   ├── APIAnalyzer examines endpoints
   └── PatternDiscovery finds similar patterns
   ↓
3. Agent Consensus Building (❌ MISSING)
   ↓
4. Enhanced Pattern Storage (❌ IN-MEMORY ONLY)
   ↓
5. Advanced Test Scenarios (❌ BASIC ONLY)
   ├── Performance testing
   ├── Accessibility validation
   └── Error handling scenarios
   ↓
6. External Enrichment (❌ STUBBED)
   └── Linkup pattern discovery
```

## 🔗 **Integration Points**

### ✅ Working Integrations

#### MLB Bullpen Gateway
- Basic integration implemented
- Component parsing and analysis
- GraphQL response handling

#### AI Services
- OpenAI: Real API integration with error handling
- Mistral: Context-aware generation with fallbacks
- Vector embeddings: 1536-dimensional with similarity search

#### Authentication
- Login form detection and setup
- Test credential injection
- Auth validation in generated tests

### ❌ Missing Integrations

#### Docker Services
- Qdrant: Service running but not connected
- Neo4j: Available but unused
- Redis: Available but unused

#### External Services
- Linkup SDK: Integration stubbed
- Pattern enrichment: Not implemented

## 📁 **File Structure & Responsibilities**

### Core Implementation Files (✅ Working)
```
src/
├── intelligent_pipeline.py      # Main orchestration (✅ with auth)
├── vector_store.py             # Enhanced patterns (✅ business logic)
├── ai_test_generator.py        # Mistral generation (✅ auth-aware)
├── test_generator.py           # 17 interactions (✅ fixed)
├── pattern_extractor.py        # 12 components (✅ fixed)
├── pipeline.py                 # Main pipeline (✅ edge cases fixed)
└── main.py                     # Entry point (✅ working)
```

### Stub/Missing Files (❌ Need Implementation)
```
src/
├── test_generation_crew.py     # 7-line stub class (❌)
├── agents/
│   ├── ui_validator.py         # ValueError only (❌)
│   └── api_analyzer.py         # Minimal impl (❌)
├── external_enrichment.py      # Linkup stubbed (❌)
└── (Qdrant integration)        # In-memory only (❌)
```

## 🚀 **Phase 2 Architecture Plan**

### Week 1: CrewAI Agent System (15% impact)
```
Implement:
├── UIValidatorAgent
│   ├── Component validation logic
│   ├── Cross-platform consistency checks
│   └── Accessibility compliance
├── APIAnalyzerAgent
│   ├── Endpoint analysis
│   ├── GraphQL query parsing
│   └── Response validation
├── PatternDiscoveryAgent
│   ├── Pattern learning
│   ├── Similarity analysis
│   └── Evolution tracking
└── TestGenerationCrew
    ├── Agent orchestration
    ├── Task distribution
    └── Result aggregation
```

### Week 2: Qdrant + Advanced Scenarios (15% impact)
```
Implement:
├── Qdrant Integration
│   ├── Replace in-memory storage
│   ├── Persistent pattern storage
│   └── Learning capabilities
└── Advanced Test Scenarios
    ├── Performance testing automation
    ├── Accessibility validation
    └── Error handling scenarios
```

## 🔍 **Dependencies & External Services**

### Required Services
- **Qdrant**: Vector database (Docker: localhost:6333)
- **OpenAI**: Embeddings API (functional)
- **Mistral**: Test generation API (functional)
- **Neo4j**: Graph database (configured but unused)
- **Redis**: Caching (configured but unused)

### Python Dependencies
- `qdrant-client`: Vector database client
- `openai`: OpenAI API client
- `mistralai`: Mistral API client
- `crewai`: Multi-agent framework (partially implemented)
- `linkup-sdk`: External search (stubbed)
- `selenium`: WebDriver automation (working)
- `pytest`: Testing framework (working)

## 📈 **Performance Characteristics**

### Current Performance (✅ Working)
- **Test Generation**: ~2-5 seconds per component
- **Vector Search**: In-memory, ~100ms per query
- **AI Generation**: Depends on API availability (fallback ready)
- **End-to-End**: 7/7 validation tests passing

### Target Performance (Phase 2)
- **Agent Coordination**: ~5-10 seconds for complex analysis
- **Qdrant Queries**: ~50ms per vector search
- **Pattern Learning**: Continuous improvement over time
- **Batch Processing**: Multiple components in parallel

---

*This architecture document reflects the current 45% complete state and provides the technical foundation for Phase 2 implementation.*