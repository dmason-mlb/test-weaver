"""
End-to-end pipeline validation test.
Validates that the complete test generation pipeline works without crashing.
"""

import pytest
import sys
import os

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_ai_test_generator_initialization():
    """Test that AITestGenerator can initialize without crashing."""
    try:
        from ai_test_generator import AITestGenerator
        generator = AITestGenerator()

        # Should initialize successfully even without API keys
        assert generator is not None
        assert hasattr(generator, 'api_available')

        print(f"✅ AITestGenerator initialized - Mistral: {generator.api_available.get('mistral', False)}, OpenAI: {generator.api_available.get('openai', False)}")

    except Exception as e:
        pytest.fail(f"AITestGenerator initialization failed: {str(e)}")


def test_intelligent_pipeline_initialization():
    """Test that IntelligentTestPipeline can initialize without crashing."""
    try:
        from intelligent_pipeline import IntelligentTestPipeline
        pipeline = IntelligentTestPipeline(verbose=False)

        # Should initialize successfully even without services
        assert pipeline is not None
        assert hasattr(pipeline, 'vector_store_available')
        assert hasattr(pipeline, 'test_generator_available')

        print(f"✅ IntelligentTestPipeline initialized - Vector store: {pipeline.vector_store_available}, Test generator: {pipeline.test_generator_available}")

    except Exception as e:
        pytest.fail(f"IntelligentTestPipeline initialization failed: {str(e)}")


def test_test_case_generator_initialization():
    """Test that TestCaseGenerator can initialize without crashing."""
    try:
        from test_generator import TestCaseGenerator
        generator = TestCaseGenerator()

        # Should initialize successfully even without vector store
        assert generator is not None
        assert hasattr(generator, 'supported_interactions')
        assert len(generator.supported_interactions) > 0

        print(f"✅ TestCaseGenerator initialized with {len(generator.supported_interactions)} supported interactions")

    except Exception as e:
        pytest.fail(f"TestCaseGenerator initialization failed: {str(e)}")


def test_end_to_end_test_generation():
    """Test complete test generation pipeline with sample data."""
    try:
        from intelligent_pipeline import IntelligentTestPipeline

        # Initialize pipeline
        pipeline = IntelligentTestPipeline(verbose=False)

        # Sample UI schema
        sample_schema = {
            "screen": "test_screen",
            "components": [
                {
                    "id": "test_button",
                    "type": "button",
                    "properties": {
                        "text": "Click Me",
                        "action": "navigate"
                    }
                },
                {
                    "id": "test_input",
                    "type": "input",
                    "properties": {
                        "placeholder": "Enter text",
                        "required": True
                    }
                }
            ]
        }

        # Generate tests
        tests = pipeline.generate_intelligent_tests(sample_schema)

        # Should generate some tests
        assert tests is not None
        assert isinstance(tests, list)
        assert len(tests) > 0

        # Validate test structure
        for i, test in enumerate(tests):
            assert 'test_name' in test
            assert 'test_code' in test
            assert 'description' in test
            assert test['test_code'].strip() != ""

            # Print test code for debugging
            print(f"\n--- Test {i+1} Code ---")
            print(test['test_code'][:200] + "..." if len(test['test_code']) > 200 else test['test_code'])

            # Ensure test code contains real automation code, not Mock objects
            test_code_lower = test['test_code'].lower()
            has_real_automation = any(keyword in test_code_lower for keyword in [
                'webdriver', 'selenium', 'driver.get', 'driver.find', 'by.id', 'wait.until'
            ])
            has_mock_objects = 'mock' in test_code_lower

            # Either should have real automation or be a simple test without mocks
            if has_mock_objects:
                pytest.fail(f"Test {i+1} contains Mock objects: {test['test_name']}")

            if not has_real_automation:
                print(f"⚠️  Test {i+1} doesn't contain WebDriver code but no Mock objects found")

        print(f"✅ End-to-end test generation successful - Generated {len(tests)} tests")

    except Exception as e:
        pytest.fail(f"End-to-end test generation failed: {str(e)}")


def test_fallback_functionality():
    """Test that fallback functionality works when AI services are unavailable."""
    try:
        from intelligent_pipeline import IntelligentTestPipeline

        pipeline = IntelligentTestPipeline(verbose=False)

        # Test component for fallback generation
        test_component = {
            "id": "fallback_test",
            "type": "button",
            "properties": {"text": "Test Button"}
        }

        # Generate fallback test
        fallback_test = pipeline._generate_fallback_test(test_component)

        # Validate fallback test
        assert fallback_test is not None
        assert 'test_code' in fallback_test
        assert 'fallback_generated' in fallback_test
        assert fallback_test['fallback_generated'] is True

        # Ensure fallback uses real WebDriver code
        assert 'webdriver' in fallback_test['test_code']
        assert 'selenium' in fallback_test['test_code']
        assert 'Mock' not in fallback_test['test_code']

        print("✅ Fallback functionality works correctly")

    except Exception as e:
        pytest.fail(f"Fallback functionality test failed: {str(e)}")


def test_pattern_extractor_comprehensive_support():
    """Test that PatternExtractor supports all claimed component types."""
    try:
        from pattern_extractor import UIPatternExtractor

        extractor = UIPatternExtractor()

        # Test various component types
        test_components = [
            {"type": "button", "id": "test_btn", "action": "click"},
            {"type": "webview", "id": "test_webview", "url": "https://example.com"},
            {"type": "list", "id": "test_list", "items": []},
            {"type": "form", "id": "test_form", "fields": []},
            {"type": "unknown_type", "id": "test_unknown"}  # Should handle gracefully
        ]

        for component in test_components:
            schema = {"components": [component]}

            # Should not raise NotImplementedError
            patterns = extractor.extract_from_schema(schema)
            assert patterns is not None
            assert isinstance(patterns, list)

        print("✅ PatternExtractor handles all component types without NotImplementedError")

    except Exception as e:
        pytest.fail(f"PatternExtractor comprehensive support test failed: {str(e)}")


def test_mds_analyzer_graceful_handling():
    """Test that MDSComponentAnalyzer handles unknown components gracefully."""
    try:
        from mlb_integration.mds_analyzer import MDSComponentAnalyzer

        analyzer = MDSComponentAnalyzer()

        # Test with unknown component type
        unknown_component = {
            "type": "unknown_mds_component",
            "id": "test_unknown",
            "properties": {"test": "value"}
        }

        # Should not raise NotImplementedError
        result = analyzer.analyze_component(unknown_component)

        assert result is not None
        assert 'warning' in result  # Should have warning for unknown type
        assert result['supported'] is not True  # Should not claim to be fully supported

        print("✅ MDSComponentAnalyzer handles unknown components gracefully")

    except Exception as e:
        pytest.fail(f"MDSComponentAnalyzer graceful handling test failed: {str(e)}")


if __name__ == "__main__":
    # Run tests individually for better debugging
    test_functions = [
        test_ai_test_generator_initialization,
        test_intelligent_pipeline_initialization,
        test_test_case_generator_initialization,
        test_end_to_end_test_generation,
        test_fallback_functionality,
        test_pattern_extractor_comprehensive_support,
        test_mds_analyzer_graceful_handling
    ]

    print("🧪 Running End-to-End Pipeline Validation Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            print(f"\n🔍 Running {test_func.__name__}...")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All end-to-end tests passed!")
    else:
        print("⚠️  Some tests failed - check implementation")