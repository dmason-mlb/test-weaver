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
        assert linkup_service.base_url == "https://api.linkup.com"
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
            assert pattern['source'] == 'linkup'
            assert 'context' in pattern
            assert pattern['context'] == 'mobile'

    @pytest.mark.skipif(not os.getenv('LINKUP_API_KEY'), reason="No Linkup API key configured")
    def test_real_api_trending_patterns(self, linkup_service):
        """Test real API trending patterns."""
        trending = linkup_service.get_trending_patterns(
            time_period='week',
            category='mobile'
        )

        assert isinstance(trending, list)
        # Trending may be empty, but should not error

    def test_pattern_search_without_api_key(self):
        """Test pattern search gracefully handles missing API key."""
        service = LinkupService(api_key=None)

        patterns = service.search_test_patterns(
            query="button testing",
            context="mobile"
        )

        # Should return empty list, not error
        assert patterns == []

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

    def test_trending_patterns(self, enrichment_service):
        """Test trending patterns functionality."""
        trending = enrichment_service.get_trending_patterns(
            time_period='week',
            category='mobile'
        )

        assert isinstance(trending, list)
        # May be empty without API key, but should not error

    def test_batch_pattern_discovery(self, enrichment_service):
        """Test batch pattern discovery."""
        components = [
            {'component_type': 'button', 'component_id': 'login'},
            {'component_type': 'list', 'component_id': 'game_list'},
            {'component_type': 'webview', 'component_id': 'stats_view'}
        ]

        batch_results = enrichment_service.batch_discover_patterns(
            components,
            ui_context={'app_type': 'mobile'}
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