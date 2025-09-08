test-weaver/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
├── docker-compose.yml
├── pytest.ini
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── bullpen_config.yaml
│
├── src/
│   ├── __init__.py
│   ├── vector_store.py
│   ├── pattern_extractor.py
│   ├── test_generator.py
│   ├── similarity_engine.py
│   ├── edge_case_discoverer.py
│   ├── external_enrichment.py
│   ├── llm_integration.py
│   ├── pipeline.py
│   ├── reporting.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── api_analyzer.py
│   │   ├── ui_validator.py
│   │   ├── edge_case_hunter.py
│   │   └── test_writer.py
│   │
│   ├── bullpen_integration/
│   │   ├── __init__.py
│   │   ├── bullpen_gateway_parser.py
│   │   ├── mds_component_analyzer.py
│   │   └── cross_platform_validator.py
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── ui_components.py
│       └── test_patterns.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_1_vector_store_initialization.py
│   ├── test_2_pattern_extraction.py
│   ├── test_3_agent_initialization.py
│   ├── test_4_test_case_generation.py
│   ├── test_5_similarity_search.py
│   ├── test_6_edge_case_discovery.py
│   ├── test_7_external_search.py
│   ├── test_8_pipeline_integration.py
│   ├── test_9_bullpen_integration.py
│   └── test_10_output_generation.py
│
├── examples/
│   ├── sample_ui_schemas/
│   │   ├── login_screen.json
│   │   ├ението_daily_story.json
│   │   └── stadium_navigator.json
│   └── generated_tests/
│       └── .gitkeep
│
└── notebooks/
    ├── demo.ipynb
    └── hackathon_presentation.ipynb