"""
AI Generator Integration Tests

Tests focused on direct testing of AITestGenerator and core test generation
functionality. Integrated from test_core_generation.py.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestAIGeneratorIntegration:
    """Test AI test generator integration and quality."""

    def test_core_pipeline_component_generation(self):
        """Test the core pipeline functionality with specific components."""
        try:
            from pipeline import generate_tests_for_component

            # Test with a real component
            sample_component = {
                'component_id': 'login_button',
                'component_type': 'button',
                'properties': {
                    'text': 'Login',
                    'enabled': True,
                    'requires_auth': False
                }
            }

            # Generate tests
            tests = generate_tests_for_component(sample_component)

            assert isinstance(tests, list), "Should return list of tests"
            assert len(tests) > 0, "Should generate at least one test"

            # Analyze the first few tests
            for test in tests[:3]:
                assert isinstance(test, dict), "Each test should be a dictionary"

                test_code = test.get('test_code', '')
                assert len(test_code) > 0, "Test should have code"

                # Quality checks
                has_component_id = sample_component['component_id'] in test_code
                has_assertions = 'assert' in test_code.lower()
                has_selenium = 'driver' in test_code.lower()

                assert has_component_id, "Generated test should use component ID 'login_button'"
                assert has_assertions, "Generated test should have assertions"
                assert has_selenium, "Generated test should use Selenium WebDriver"

        except ImportError:
            pytest.skip("generate_tests_for_component not available")

    def test_ai_test_generator_direct(self):
        """Test the AITestGenerator directly."""
        try:
            from ai_test_generator import AITestGenerator

            generator = AITestGenerator()

            # Test generation
            component = {
                'component_id': 'score_display',
                'component_type': 'list',
                'properties': {
                    'data_source': 'mlb_api',
                    'real_time': True
                }
            }

            # Use generate_test_suite with a full UI schema
            ui_schema = {'components': [component]}
            tests = generator.generate_test_suite(ui_schema)

            assert isinstance(tests, list), "Should return list of tests"
            assert len(tests) > 0, "Should generate at least one test"

            # Check sample test
            sample_test = tests[0]
            assert isinstance(sample_test, dict), "Test should be dictionary"

            test_code = sample_test.get('test_code', '')
            assert len(test_code) > 0, "Should have test code"

            # Check if component ID is used
            assert component['component_id'] in test_code, "Should use component ID 'score_display'"

            # Check for quality indicators
            assert 'assert' in test_code.lower(), "Should have assertions"
            assert any(keyword in test_code.lower() for keyword in ['driver', 'webdriver', 'selenium']), \
                "Should use WebDriver"

        except ImportError:
            pytest.skip("AITestGenerator not available")

    def test_ai_generator_with_different_component_types(self):
        """Test AI generator with various component types."""
        try:
            from ai_test_generator import AITestGenerator

            generator = AITestGenerator()

            component_types = [
                {
                    'component_id': 'search_input',
                    'component_type': 'input',
                    'properties': {
                        'placeholder': 'Search teams...',
                        'required': True
                    }
                },
                {
                    'component_id': 'team_list',
                    'component_type': 'list',
                    'properties': {
                        'data_source': 'teams_api',
                        'sortable': True
                    }
                },
                {
                    'component_id': 'submit_btn',
                    'component_type': 'button',
                    'properties': {
                        'text': 'Submit',
                        'enabled': True
                    }
                }
            ]

            for component in component_types:
                # Use generate_test_suite with a full UI schema
                ui_schema = {'components': [component]}
                tests = generator.generate_test_suite(ui_schema)

                assert isinstance(tests, list), f"Should return list for {component['component_type']}"
                assert len(tests) > 0, f"Should generate tests for {component['component_type']}"

                # Check component ID usage
                for test in tests:
                    test_code = test.get('test_code', '')
                    assert component['component_id'] in test_code, \
                        f"Should use component ID '{component['component_id']}'"

        except ImportError:
            pytest.skip("AITestGenerator not available")

    def test_ai_generator_test_quality_metrics(self):
        """Test quality metrics of AI-generated tests."""
        try:
            from ai_test_generator import AITestGenerator

            generator = AITestGenerator()

            component = {
                'component_id': 'quality_test_element',
                'component_type': 'button',
                'properties': {
                    'text': 'Quality Test Button',
                    'accessibility_label': 'Quality test button for validation'
                }
            }

            # Use generate_test_suite with a full UI schema
            ui_schema = {'components': [component]}
            tests = generator.generate_test_suite(ui_schema)

            assert len(tests) > 0, "Should generate tests"

            for test in tests:
                test_code = test.get('test_code', '')

                # Essential quality checks
                quality_indicators = {
                    'has_webdriver': any(keyword in test_code.lower() for keyword in ['webdriver', 'driver']),
                    'has_assertions': 'assert' in test_code.lower(),
                    'has_component_id': component['component_id'] in test_code,
                    'has_proper_cleanup': 'quit()' in test_code.lower(),
                    'no_todos': 'TODO' not in test_code.upper(),
                    'no_placeholders': not any(placeholder in test_code.lower()
                                             for placeholder in ['placeholder', 'implement', 'fill in'])
                }

                # Assert quality metrics
                for metric, passed in quality_indicators.items():
                    assert passed, f"Quality metric failed: {metric} for test: {test.get('name', 'unknown')}"

        except ImportError:
            pytest.skip("AITestGenerator not available")

    def test_ai_generator_error_handling(self):
        """Test AI generator error handling with invalid inputs."""
        try:
            from ai_test_generator import AITestGenerator

            generator = AITestGenerator()

            # Test with invalid/edge case components
            invalid_components = [
                {},  # Empty component
                {'component_type': 'unknown'},  # Missing ID
                {'component_id': ''},  # Empty ID
                {'component_id': 'test', 'component_type': 'invalid_type'},  # Invalid type
            ]

            for invalid_component in invalid_components:
                try:
                    # Use generate_test_suite with a full UI schema
                    ui_schema = {'components': [invalid_component]}
                    tests = generator.generate_test_suite(ui_schema)
                    # If it doesn't raise an exception, should still return valid structure
                    assert isinstance(tests, list), "Should return list even for invalid component"

                    # If tests are generated, they should be valid
                    for test in tests:
                        assert isinstance(test, dict), "Each test should be a dictionary"
                        assert 'test_code' in test, "Each test should have test_code"

                except Exception as e:
                    # If exception is raised, it should be a controlled exception
                    assert isinstance(e, (ValueError, TypeError, KeyError)), \
                        f"Should raise controlled exception, got {type(e)}: {e}"

        except ImportError:
            pytest.skip("AITestGenerator not available")

    def test_ai_generator_integration_with_pipeline(self):
        """Test AI generator integration with the main pipeline."""
        try:
            from ai_test_generator import AITestGenerator
            from pipeline import TestGenerationPipeline

            # Test that pipeline can use AI generator
            pipeline = TestGenerationPipeline(verbose=False)

            # Check if pipeline has AI generator integration
            if hasattr(pipeline, 'ai_generator') or hasattr(pipeline, 'test_generator'):
                component = {
                    'component_id': 'integration_test_btn',
                    'component_type': 'button',
                    'properties': {'text': 'Integration Test'}
                }

                ui_schema = {'components': [component]}

                results = pipeline.generate_tests_for_ui(ui_schema)

                assert results is not None, "Pipeline should return results"

                if isinstance(results, dict) and 'tests' in results:
                    tests = results['tests']
                    if tests:
                        # Check that generated tests use AI generator quality
                        test_code = tests[0].get('test_code', '')
                        assert 'integration_test_btn' in test_code, \
                            "Pipeline should use AI generator for component ID"

        except ImportError:
            pytest.skip("AI generator or pipeline not available")

    def test_ai_generator_mlb_specific_components(self):
        """Test AI generator with MLB-specific component types."""
        try:
            from ai_test_generator import AITestGenerator

            generator = AITestGenerator()

            mlb_components = [
                {
                    'component_id': 'gameday_webview',
                    'component_type': 'webview',
                    'properties': {
                        'url': 'https://www.mlb.com/gameday/embed',
                        'requires_auth': True
                    }
                },
                {
                    'component_id': 'team_selector',
                    'component_type': 'dropdown',
                    'properties': {
                        'data_source': 'teams_api',
                        'default_team': 'yankees'
                    }
                },
                {
                    'component_id': 'score_ticker',
                    'component_type': 'ticker',
                    'properties': {
                        'real_time': True,
                        'update_interval': 30
                    }
                }
            ]

            for component in mlb_components:
                # Use generate_test_suite with a full UI schema
                ui_schema = {'components': [component]}
                tests = generator.generate_test_suite(ui_schema)

                assert len(tests) > 0, f"Should generate tests for {component['component_type']}"

                # Check MLB-specific properties are considered
                for test in tests:
                    test_code = test.get('test_code', '')

                    # Should use component ID
                    assert component['component_id'] in test_code, \
                        f"Should use component ID '{component['component_id']}'"

                    # Check for property-specific testing
                    if 'requires_auth' in component['properties']:
                        assert any(auth_keyword in test_code.lower() for auth_keyword in ['auth', 'login', 'token']), \
                            "Should test authentication requirements"

                    if 'real_time' in component['properties']:
                        assert any(realtime_keyword in test_code.lower() for realtime_keyword in ['update', 'refresh', 'real']), \
                            "Should test real-time behavior"

        except ImportError:
            pytest.skip("AITestGenerator not available")