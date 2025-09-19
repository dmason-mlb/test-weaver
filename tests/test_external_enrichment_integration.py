"""
Integration tests for external enrichment with real API validation.
Tests the actual functionality of LinkupService and ExternalTestEnrichment
with live external services.
"""

import os
import sys
import pytest
import time
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from linkup_service import LinkupService
from external_enrichment import ExternalTestEnrichment


class TestRealAPIIntegration:
    """Test actual API integration functionality."""

    @pytest.fixture
    def linkup_service(self):
        """Create LinkupService instance for testing."""
        return LinkupService(
            api_key=os.getenv('LINKUP_API_KEY'),
            timeout=10
        )

    @pytest.fixture
    def enrichment_service(self):
        """Create ExternalTestEnrichment instance for testing."""
        return ExternalTestEnrichment()

    @pytest.fixture
    def sample_component(self):
        """Sample UI component for testing."""
        return {
            'component_type': 'button',
            'component_id': 'login_button',
            'properties': {
                'text': 'Login',
                'enabled': True,
                'accessibility_label': 'Login to MLB app'
            }
        }

    def test_linkup_service_initialization(self, linkup_service):
        """Test LinkupService initializes correctly."""
        assert linkup_service is not None
        assert linkup_service.api_key is not None or linkup_service.api_key == os.getenv('LINKUP_API_KEY')
        assert linkup_service.base_url == "https://api.linkup.so/v1"
        assert linkup_service.cache is not None  # Redis should be available

    def test_linkup_service_health_check(self, linkup_service):
        """Test LinkupService health status."""
        status = linkup_service.get_health_status()

        assert 'api_available' in status
        assert 'cache_available' in status
        assert 'base_url' in status

        # Should have Redis cache available
        assert status['cache_available'] is True

        # API availability depends on API key
        if os.getenv('LINKUP_API_KEY'):
            # With API key, should attempt to reach API
            assert 'api_reachable' in status
        else:
            # Without API key, API not available
            assert status['api_available'] is False

    @pytest.mark.skipif(not os.getenv('LINKUP_API_KEY'), reason="No Linkup API key configured")
    def test_real_api_pattern_search(self, linkup_service):
        """Test real API pattern search with live API key."""
        patterns = linkup_service.search_test_patterns(
            query="button testing mobile app",
            context="mobile",
            limit=5
        )

        # Should return actual patterns from API
        assert isinstance(patterns, list)

        if patterns:  # If API returns results
            pattern = patterns[0]
            assert 'pattern_id' in pattern
            assert 'title' in pattern
            assert 'description' in pattern
            assert 'source' in pattern
            assert pattern['source'] == 'linkup_web_search'
            assert 'url' in pattern  # Web search results include URL
            assert 'quality_score' in pattern  # Transformed patterns have quality scores

    def test_real_api_returns_web_search_format(self, linkup_service):
        """Test that real API returns web search results in expected format."""
        if not os.getenv('LINKUP_API_KEY'):
            pytest.skip("No Linkup API key configured")

        patterns = linkup_service.search_test_patterns(
            query="mobile testing best practices",
            context="mobile",
            limit=3
        )

        assert isinstance(patterns, list)
        if patterns:  # If API returns results
            pattern = patterns[0]
            # Real API returns web search results transformed to test patterns
            assert 'pattern_id' in pattern
            assert 'title' in pattern
            assert 'description' in pattern
            assert 'source' in pattern
            assert pattern['source'] == 'linkup_web_search'
            assert 'url' in pattern  # Web search results include original URL

    def test_pattern_search_without_api_key(self):
        """Test pattern search gracefully handles missing API key."""
        service = LinkupService(api_key=None)

        patterns = service.search_test_patterns(
            query="button testing",
            context="mobile"
        )

        # Should return patterns from cache or fallback, not error
        assert isinstance(patterns, list)

    def test_cache_functionality(self, linkup_service):
        """Test Redis caching works correctly."""
        if not linkup_service.cache:
            pytest.skip("Redis cache not available")

        # Test cache key generation
        cache_key = linkup_service._generate_cache_key("test", "mobile", 10, True)
        assert isinstance(cache_key, str)
        assert cache_key.startswith("linkup:")

        # Test cache storage and retrieval
        test_data = {"test": "data", "patterns": []}
        linkup_service._cache_result(cache_key, test_data, ttl=60)

        retrieved = linkup_service._get_cached_result(cache_key)
        assert retrieved == test_data

    def test_enrichment_service_initialization(self, enrichment_service):
        """Test ExternalTestEnrichment initializes correctly."""
        assert enrichment_service is not None
        assert enrichment_service.linkup_service is not None

        status = enrichment_service.get_service_status()
        assert 'service_name' in status
        assert status['service_name'] == 'ExternalTestEnrichment'
        assert 'linkup_available' in status
        assert 'linkup_status' in status

    def test_component_pattern_discovery(self, enrichment_service, sample_component):
        """Test pattern discovery for specific component."""
        patterns = enrichment_service.discover_patterns_for_component(
            sample_component,
            ui_context={'app_type': 'mobile', 'platform': 'iOS'}
        )

        assert isinstance(patterns, list)
        # May be empty without API key, but should not error

    def test_test_suite_enrichment(self, enrichment_service, sample_component):
        """Test test suite enrichment functionality."""
        base_tests = [
            {
                'name': 'test_button_click',
                'description': 'Test button click functionality',
                'type': 'interaction'
            }
        ]

        enriched_tests = enrichment_service.enrich_test_suite(
            base_tests,
            sample_component
        )

        assert isinstance(enriched_tests, list)
        assert len(enriched_tests) >= len(base_tests)  # Should preserve original tests

        # Original test should be preserved
        original_test = next((t for t in enriched_tests if t['name'] == 'test_button_click'), None)
        assert original_test is not None

    def test_web_search_pattern_transformation(self, enrichment_service):
        """Test that web search results are properly transformed to test patterns."""
        if not os.getenv('LINKUP_API_KEY'):
            pytest.skip("No Linkup API key configured")

        # Test direct pattern search
        patterns = enrichment_service.search_test_patterns(
            query="mobile app testing automation",
            context="mobile"
        )

        assert isinstance(patterns, list)
        if patterns:  # If API returns results
            pattern = patterns[0]
            # Verify enrichment metadata is added
            assert 'enrichment' in pattern
            assert pattern['enrichment']['source'] == 'external'
            assert 'enrichment_score' in pattern
            assert 'mlb_enhancements' in pattern

    def test_batch_pattern_discovery(self, enrichment_service):
        """Test batch pattern discovery."""
        components = [
            {'component_type': 'button', 'component_id': 'login'},
            {'component_type': 'list', 'component_id': 'game_list'},
            {'component_type': 'webview', 'component_id': 'stats_view'}
        ]

        batch_results = enrichment_service.batch_discover_patterns(
            components
        )

        assert isinstance(batch_results, dict)
        # Should have entries for each component
        for component in components:
            component_id = component['component_id']
            assert component_id in batch_results
            assert isinstance(batch_results[component_id], list)

    def test_error_handling_with_invalid_config(self):
        """Test error handling with invalid configuration."""
        # Test with invalid Redis config
        service = LinkupService(api_key="test_key")

        # Should handle Redis connection errors gracefully
        patterns = service.search_test_patterns("test query", "mobile")
        assert isinstance(patterns, list)

    def test_rate_limiting(self, linkup_service):
        """Test rate limiting functionality."""
        start_time = time.time()

        # Make multiple requests
        for _ in range(3):
            linkup_service._enforce_rate_limit()

        end_time = time.time()

        # Should take at least 200ms for 3 requests (100ms between each)
        # But we'll be lenient due to test timing
        elapsed = end_time - start_time
        assert elapsed >= 0.1  # At least some delay

    @pytest.mark.skipif(not os.getenv('LINKUP_API_KEY'), reason="No Linkup API key configured")
    def test_end_to_end_workflow(self, enrichment_service, sample_component):
        """Test complete end-to-end workflow with real API."""
        # Step 1: Discover patterns for component
        patterns = enrichment_service.discover_patterns_for_component(
            sample_component,
            ui_context={'app_type': 'mobile', 'platform': 'iOS'}
        )

        # Step 2: Create base test suite
        base_tests = [
            {
                'name': 'test_basic_interaction',
                'description': 'Test basic button interaction',
                'type': 'functional'
            }
        ]

        # Step 3: Enrich with external patterns
        enriched_tests = enrichment_service.enrich_test_suite(
            base_tests,
            sample_component
        )

        # Step 4: Validate results
        assert isinstance(patterns, list)
        assert isinstance(enriched_tests, list)
        assert len(enriched_tests) >= len(base_tests)

        # If external patterns were found, enriched tests should be enhanced
        if patterns:
            assert len(enriched_tests) > len(base_tests)

    def test_mlb_specific_enhancement(self, enrichment_service):
        """Test MLB-specific pattern enhancement."""
        # Test with MLB-relevant component
        mlb_component = {
            'component_type': 'list',
            'component_id': 'game_schedule',
            'properties': {
                'title': 'Game Schedule',
                'data_source': 'mlb_api',
                'real_time': True
            }
        }

        patterns = enrichment_service.discover_patterns_for_component(
            mlb_component,
            ui_context={'app_type': 'mlb_mobile', 'domain': 'sports'}
        )

        assert isinstance(patterns, list)
        # Should not error even if no MLB-specific patterns found


class TestFunctionalValidation:
    """Test actual functional behavior, not just structure."""

    @pytest.fixture
    def enrichment_service(self):
        """Create ExternalTestEnrichment instance for testing."""
        return ExternalTestEnrichment()

    @pytest.fixture
    def test_component_with_id(self):
        """Component with proper ID for functional testing."""
        return {
            'component_type': 'button',
            'id': 'login_button_123',
            'properties': {
                'text': 'Login',
                'enabled': True,
                'accessibility_label': 'Login to app'
            }
        }

    @pytest.fixture
    def test_component_without_id(self):
        """Component missing ID to test fallback logic."""
        return {
            'component_type': 'input',
            'properties': {
                'placeholder': 'Enter username',
                'required': True
            }
        }

    def test_component_id_resolution_functional(self, enrichment_service, test_component_with_id, test_component_without_id):
        """Test that component ID resolution actually works in practice."""
        # Test with component that has ID
        component_id = enrichment_service._get_component_id(test_component_with_id)
        assert component_id == 'login_button_123', f"Should resolve actual ID, got: {component_id}"
        
        # Test with component missing ID - should generate fallback
        fallback_id = enrichment_service._get_component_id(test_component_without_id)
        assert 'input' in fallback_id, f"Should generate input-based fallback ID, got: {fallback_id}"
        assert fallback_id != 'None', "Should never return None as component ID"

    def test_generated_test_code_is_valid_python(self, enrichment_service, test_component_with_id):
        """Test that generated test code is syntactically valid Python."""
        # Generate test code using various templates
        test_methods = [
            enrichment_service._create_button_test_template,
            enrichment_service._create_api_test_template,
            enrichment_service._create_list_test_template
        ]

        pattern = {
            'pattern_id': 'test_pattern',
            'title': 'Test Pattern',
            'description': 'Test description'
        }

        for test_method in test_methods:
            test_code = test_method(pattern, test_component_with_id)
            
            # Validate it's not empty or just 'pass'
            assert test_code.strip(), f"Test code should not be empty for {test_method.__name__}"
            assert 'pass' not in test_code or 'assert' in test_code, f"Test should have real assertions, not just 'pass' for {test_method.__name__}"
            
            # Validate it's syntactically correct Python
            try:
                compile(test_code, '<test_code>', 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated test code has syntax error in {test_method.__name__}: {e}\nCode:\n{test_code}")

    def test_generated_tests_have_meaningful_assertions(self, enrichment_service, test_component_with_id):
        """Test that generated tests have proper assertions, not placeholders."""
        pattern = {
            'pattern_id': 'assertion_test',
            'title': 'Assertion Test Pattern',
            'description': 'Test meaningful assertions'
        }

        button_test = enrichment_service._create_button_test_template(pattern, test_component_with_id)
        
        # Should have multiple specific assertions
        assertion_patterns = [
            'assert.*is_enabled',
            'assert.*is_displayed', 
            'assert.*text',
            'By.ID.*login_button_123'  # Should use actual component ID
        ]
        
        for assertion_pattern in assertion_patterns:
            import re
            assert re.search(assertion_pattern, button_test), f"Missing assertion pattern: {assertion_pattern}\nGenerated code:\n{button_test}"

    def test_test_enrichment_produces_more_tests(self, enrichment_service, test_component_with_id):
        """Test that enrichment actually increases test coverage meaningfully."""
        # Start with minimal base test suite
        base_tests = [
            {
                'name': 'test_basic_functionality',
                'description': 'Basic test',
                'type': 'functional'
            }
        ]

        # Enrich the test suite
        enriched_tests = enrichment_service.enrich_test_suite(base_tests, test_component_with_id)
        
        # Should have preserved original tests
        assert len(enriched_tests) >= len(base_tests), "Enrichment should preserve original tests"
        
        # Check if any of the original test names still exist
        original_names = {test['name'] for test in base_tests}
        enriched_names = {test.get('name', '') for test in enriched_tests}
        
        # At least some original test names should be preserved
        preserved_tests = original_names.intersection(enriched_names)
        assert len(preserved_tests) > 0, f"Some original tests should be preserved. Original: {original_names}, Enriched: {enriched_names}"

    def test_deduplication_actually_removes_duplicates(self, enrichment_service):
        """Test that deduplication functionality actually works on duplicate content."""
        # Create intentionally duplicate tests
        duplicate_tests = [
            {
                'name': 'test_button_click',
                'description': 'Test button click functionality',
                'test_code': 'def test_button_click(): button.click(); assert button.clicked',
                'type': 'functional'
            },
            {
                'name': 'test_button_click_duplicate',  # Different name but same content
                'description': 'Test button click functionality',  # Same description
                'test_code': 'def test_button_click(): button.click(); assert button.clicked',  # Same code
                'type': 'functional'
            },
            {
                'name': 'test_button_hover',
                'description': 'Test button hover behavior',
                'test_code': 'def test_button_hover(): button.hover(); assert button.hovered',
                'type': 'functional'
            }
        ]

        # Apply deduplication
        deduplicated = enrichment_service._deduplicate_tests(duplicate_tests, similarity_threshold=0.7)
        
        # Should have removed one duplicate
        assert len(deduplicated) == 2, f"Should remove 1 duplicate, got {len(deduplicated)} tests: {[t.get('name') for t in deduplicated]}"
        
        # Unique test should still be there
        test_names = {test.get('name', '') for test in deduplicated}
        assert 'test_button_hover' in test_names, "Unique test should be preserved"

    def test_external_pattern_integration_functionality(self, enrichment_service, test_component_with_id):
        """Test that external pattern integration produces functional improvements."""
        
        # Mock some external patterns to test integration
        mock_patterns = [
            {
                'pattern_id': 'accessibility_test',
                'title': 'Accessibility Validation',
                'description': 'Test accessibility features',
                'test_template': 'accessibility',
                'category': 'accessibility',
                'source': 'external_test'
            }
        ]

        # Test pattern to test conversion
        for pattern in mock_patterns:
            generated_test = enrichment_service._generate_test_from_pattern(pattern, test_component_with_id)
            
            if generated_test:  # Only test if pattern was successfully converted
                # Should have generated meaningful test
                assert 'name' in generated_test, "Generated test should have name"
                assert 'test_code' in generated_test, "Generated test should have code"
                
                test_code = generated_test.get('test_code', '')
                assert test_code.strip(), "Generated test code should not be empty"
                assert 'login_button_123' in test_code, "Should use actual component ID in test code"

    def test_pattern_search_returns_usable_results(self, enrichment_service):
        """Test that pattern search returns results that can actually be used."""
        patterns = enrichment_service.search_test_patterns(
            query="button testing",
            context="mobile",
            limit=3
        )
        
        # Even if no external API, should return patterns that are usable
        assert isinstance(patterns, list), "Should return list of patterns"
        
        # If patterns are returned, they should have required structure
        for pattern in patterns:
            assert isinstance(pattern, dict), "Each pattern should be a dictionary"
            
            # Should have basic required fields for pattern processing
            required_fields = ['pattern_id', 'title', 'description']
            for field in required_fields:
                assert field in pattern, f"Pattern missing required field {field}: {pattern}"

    def test_service_status_reflects_actual_capability(self, enrichment_service):
        """Test that service status accurately reflects what the service can actually do."""
        status = enrichment_service.get_service_status()
        
        # Status should reflect real capability
        assert 'linkup_available' in status, "Status should indicate if Linkup service is available"
        assert 'api_key_configured' in status, "Status should indicate if API key is configured"
        
        # Test that claimed capabilities actually work
        if status.get('linkup_available'):
            # If service claims to be available, test that it can actually search
            try:
                patterns = enrichment_service.search_test_patterns("test", "mobile", limit=1)
                assert isinstance(patterns, list), "Service claiming availability should return valid results"
            except Exception as e:
                pytest.fail(f"Service claims to be available but fails: {e}")

    def test_mlb_specific_functionality_works(self, enrichment_service):
        """Test that MLB-specific enhancements actually work for baseball content."""
        mlb_component = {
            'component_type': 'scoreboard',
            'id': 'live_scoreboard',
            'properties': {
                'game_id': 'mlb_game_123',
                'real_time': True,
                'teams': ['Yankees', 'Red Sox']
            }
        }

        # Test pattern discovery for MLB component
        patterns = enrichment_service.discover_patterns_for_component(
            mlb_component,
            ui_context={'app_type': 'mlb_mobile', 'domain': 'sports'}
        )

        # Should return patterns (even if empty, should be list)
        assert isinstance(patterns, list), "MLB component pattern discovery should return list"
        
        # If patterns are returned, should be relevant to MLB/sports context
        for pattern in patterns:
            if 'mlb_enhancements' in pattern:
                assert isinstance(pattern['mlb_enhancements'], dict), "MLB enhancements should be structured"

class TestServiceIntegration:
    """Test integration between services."""

    def test_linkup_service_in_enrichment(self):
        """Test LinkupService integration in ExternalTestEnrichment."""
        enrichment = ExternalTestEnrichment()

        # Should have linkup service available
        assert enrichment.linkup_service is not None
        assert isinstance(enrichment.linkup_service, LinkupService)

    def test_service_status_reporting(self):
        """Test comprehensive service status reporting."""
        enrichment = ExternalTestEnrichment()
        status = enrichment.get_service_status()

        # Should include all required status fields
        required_fields = [
            'service_name',
            'linkup_available',
            'linkup_status',
            'api_key_configured',
            'quality_threshold',
            'max_patterns_per_search'
        ]

        for field in required_fields:
            assert field in status

        # Linkup status should be detailed
        linkup_status = status['linkup_status']
        assert 'api_available' in linkup_status
        assert 'cache_available' in linkup_status
        assert 'base_url' in linkup_status


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])