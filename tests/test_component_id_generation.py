"""
Component ID Generation Tests

Tests focused on ensuring generated tests use proper component IDs instead of
generic placeholders or "None" values. Integrated from test_actual_pipeline.py.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestComponentIDGeneration:
    """Test component ID generation and usage in tests."""

    def test_pipeline_uses_real_component_ids(self):
        """Test that pipeline uses actual component IDs in generated tests."""
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline(verbose=False)

        # Sample UI with specific component IDs
        ui_schema = {
            'components': [
                {
                    'component_id': 'login_btn',
                    'component_type': 'button',
                    'properties': {
                        'text': 'Login',
                        'enabled': True
                    }
                },
                {
                    'component_id': 'username_field',
                    'component_type': 'input',
                    'properties': {
                        'placeholder': 'Username',
                        'required': True
                    }
                }
            ]
        }

        # Generate tests
        results = pipeline.generate_tests_for_ui(ui_schema)

        assert isinstance(results, dict), "Pipeline should return dictionary"

        if 'tests' in results:
            tests = results['tests']
            assert len(tests) > 0, "Should generate at least one test"

            # Check first test for component ID usage
            first_test = tests[0]
            test_code = first_test.get('test_code', '')

            # Quality checks
            component_ids = ['login_btn', 'username_field']
            uses_real_ids = any(comp_id in test_code for comp_id in component_ids)
            has_assertions = 'assert' in test_code.lower()
            has_selenium = 'driver' in test_code.lower()
            has_none_id = 'By.ID, "None"' in test_code

            assert uses_real_ids, "Generated test should use real component IDs"
            assert has_assertions, "Generated test should have assertions"
            assert has_selenium, "Generated test should use Selenium WebDriver"
            assert not has_none_id, "Generated test should not have None ID bug"

    def test_all_scenarios_generation_quality(self):
        """Test quality of all scenario generation."""
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline(verbose=False)

        ui_schema = {
            'components': [
                {
                    'component_id': 'submit_button',
                    'component_type': 'button',
                    'properties': {
                        'text': 'Submit',
                        'enabled': True
                    }
                }
            ]
        }

        all_scenarios = pipeline.generate_all_test_scenarios(ui_schema)

        assert all_scenarios is not None, "Should return scenarios"

        if isinstance(all_scenarios, list):
            assert len(all_scenarios) > 0, "Should generate at least one scenario"

            for scenario in all_scenarios[:3]:  # Check first 3
                if isinstance(scenario, dict) and 'test_code' in scenario:
                    test_code = scenario['test_code']
                    assert 'submit_button' in test_code, f"Scenario should use component ID 'submit_button'"
                    assert 'By.ID, "None"' not in test_code, "Should not have None ID bug"

    def test_individual_test_generator_component_id_usage(self):
        """Test individual test generator uses component IDs correctly."""
        try:
            from test_generator import TestGenerator

            generator = TestGenerator()

            component = {
                'component_id': 'test_element',
                'component_type': 'button',
                'properties': {'text': 'Test', 'enabled': True}
            }

            # Try different generation methods
            if hasattr(generator, 'generate_tests'):
                tests = generator.generate_tests(component)
                if tests and len(tests) > 0:
                    test_code = tests[0].get('test_code', '')
                    assert 'test_element' in test_code, "Should use component ID 'test_element'"

            elif hasattr(generator, 'generate_test_for_component'):
                test = generator.generate_test_for_component(component)
                if test and isinstance(test, dict):
                    test_code = test.get('test_code', '')
                    assert 'test_element' in test_code, "Should use component ID 'test_element'"

        except ImportError:
            pytest.skip("TestGenerator not available")

    def test_component_id_none_detection(self):
        """Test detection of None component ID bugs."""
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline(verbose=False)

        # Test with component that might cause None ID
        ui_schema = {
            'components': [
                {
                    'component_type': 'button',  # Missing component_id
                    'properties': {'text': 'Click Me'}
                }
            ]
        }

        results = pipeline.generate_tests_for_ui(ui_schema)

        if isinstance(results, dict) and 'tests' in results:
            tests = results['tests']
            if tests:
                test_code = tests[0].get('test_code', '')
                # Should handle missing component_id gracefully
                assert 'By.ID, "None"' not in test_code, "Should not generate None ID selector"

    def test_pipeline_component_failure_handling(self):
        """Test that pipeline handles component failures gracefully."""
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline()

        # Test with empty/invalid UI schema
        invalid_schemas = [
            {},
            {'components': []},
            {'components': [{}]},
            None
        ]

        for schema in invalid_schemas:
            try:
                result = pipeline.generate_tests_for_ui(schema)
                # Should return some kind of result, not crash
                assert result is not None
            except Exception as e:
                # If it raises an exception, it should be a controlled one
                assert isinstance(e, (ValueError, TypeError, RuntimeError))

    def test_selenium_webdriver_code_quality(self):
        """Test that generated Selenium code is of good quality."""
        from pipeline import TestGenerationPipeline

        pipeline = TestGenerationPipeline(verbose=False)

        ui_schema = {
            'components': [
                {
                    'component_id': 'quality_test_btn',
                    'component_type': 'button',
                    'properties': {
                        'text': 'Quality Test',
                        'enabled': True
                    }
                }
            ]
        }

        results = pipeline.generate_tests_for_ui(ui_schema)

        if isinstance(results, dict) and 'tests' in results:
            tests = results['tests']
            if tests:
                test_code = tests[0].get('test_code', '')

                # Quality indicators
                selenium_patterns = [
                    'webdriver',
                    'driver.find_element',
                    'assert',
                    'driver.quit()'
                ]

                for pattern in selenium_patterns:
                    assert pattern.lower() in test_code.lower(), f"Should contain '{pattern}'"

                # Anti-patterns
                anti_patterns = [
                    'TODO',
                    'placeholder',
                    'implement',
                    'By.ID, "None"'
                ]

                for anti_pattern in anti_patterns:
                    assert anti_pattern not in test_code, f"Should not contain '{anti_pattern}'"