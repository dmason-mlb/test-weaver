"""
External Test Enrichment Service

This module provides comprehensive external test pattern discovery and enrichment
using the Linkup service to enhance internal test generation capabilities.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

try:
    from .linkup_service import LinkupService
    LINKUP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LinkupService not available: {e}")
    try:
        # Try absolute import for testing
        from linkup_service import LinkupService
        LINKUP_AVAILABLE = True
    except ImportError:
        LinkupService = None
        LINKUP_AVAILABLE = False


class ExternalTestEnrichment:
    """External test pattern enrichment service.

    Provides comprehensive integration with external pattern sources
    to enhance internal test generation with industry best practices.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 timeout: int = 30,
                 max_patterns_per_search: int = 20,
                 quality_threshold: float = 0.6):
        """Initialize external test enrichment service.

        Args:
            api_key: Linkup API key (or use LINKUP_API_KEY env var)
            timeout: Request timeout in seconds
            max_patterns_per_search: Maximum patterns to retrieve per search
            quality_threshold: Minimum quality score for patterns
        """
        self.api_key = api_key or os.getenv('LINKUP_API_KEY')
        self.timeout = timeout
        self.max_patterns_per_search = max_patterns_per_search
        self.quality_threshold = quality_threshold

        # Initialize Linkup service if available
        if LINKUP_AVAILABLE and LinkupService:
            self.linkup_service = LinkupService(
                api_key=self.api_key,
                timeout=timeout
            )
        else:
            logger.warning("LinkupService not available - external enrichment will use fallback mode")
            self.linkup_service = None

        # Pattern transformation mappings
        self.pattern_mappings = {
            'mobile': self._transform_mobile_pattern,
            'web': self._transform_web_pattern,
            'api': self._transform_api_pattern,
            'performance': self._transform_performance_pattern,
            'accessibility': self._transform_accessibility_pattern
        }

        # Internal pattern templates
        self.internal_templates = {
            'button_test': self._create_button_test_template,
            'list_test': self._create_list_test_template,
            'api_test': self._create_api_test_template,
            'performance_test': self._create_performance_test_template,
            'accessibility_test': self._create_accessibility_test_template
        }

    def search_test_patterns(self,
                           query: str,
                           context: str = 'general') -> List[Dict[str, Any]]:
        """Search for external test patterns with improved error handling.

        Args:
            query: Search query for test patterns
            context: Search context (mobile, web, api, etc.)

        Returns:
            List of enriched test patterns

        Raises:
            EnvironmentError: If LINKUP_API_KEY not set
            TimeoutError: If search times out
        """
        if not self.linkup_service:
            logger.warning("LinkupService not available - returning empty results")
            return []

        if not self.api_key:
            raise EnvironmentError("LINKUP_API_KEY not set")

        try:
            # Search using Linkup service
            raw_patterns = self.linkup_service.search_test_patterns(
                query=query,
                context=context,
                limit=self.max_patterns_per_search
            )

            # Transform and enrich patterns
            enriched_patterns = []
            for pattern in raw_patterns:
                if pattern.get('quality_score', 0) >= self.quality_threshold:
                    enriched_pattern = self._enrich_pattern(pattern, context)
                    if enriched_pattern:
                        enriched_patterns.append(enriched_pattern)

            logger.info(f"Successfully enriched {len(enriched_patterns)} patterns for query: {query}")
            return enriched_patterns

        except Exception as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"External search timed out after {self.timeout} seconds")
            else:
                logger.error(f"Error in external pattern search: {e}")
                raise

    def discover_patterns_for_component(self,
                                      component: Dict[str, Any],
                                      ui_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Discover external patterns specifically for a UI component.

        Args:
            component: UI component definition
            ui_context: Optional UI context information

        Returns:
            List of component-specific external patterns
        """
        if not component or 'type' not in component:
            return []

        component_type = component['type']
        discovered_patterns = []

        try:
            # Search by component type
            if self.linkup_service:
                component_patterns = self.linkup_service.search_by_component_type(
                    component_type=component_type,
                    mlb_specific=True
                )
            else:
                component_patterns = []

            # Add context-specific searches
            contexts = self._determine_search_contexts(component, ui_context)
            for context in contexts:
                query = self._build_context_query(component, context)
                context_patterns = self.search_test_patterns(query, context)
                component_patterns.extend(context_patterns)

            # Transform patterns to internal format
            for pattern in component_patterns:
                transformed_pattern = self._transform_to_internal_format(pattern, component)
                if transformed_pattern:
                    discovered_patterns.append(transformed_pattern)

            # Remove duplicates and sort by relevance
            discovered_patterns = self._deduplicate_and_sort(discovered_patterns)

            logger.info(f"Discovered {len(discovered_patterns)} external patterns for component {component.get('id', 'unknown')}")

        except Exception as e:
            logger.error(f"Error discovering patterns for component {component.get('id', 'unknown')}: {e}")

        return discovered_patterns

    def enrich_test_suite(self,
                         test_suite: Dict[str, Any],
                         component: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich an existing test suite with external patterns.

        Args:
            test_suite: Existing test suite to enrich
            component: Component being tested

        Returns:
            Enriched test suite with external patterns integrated
        """
        enriched_suite = test_suite.copy()

        try:
            # Discover relevant external patterns
            external_patterns = self.discover_patterns_for_component(component)

            if not external_patterns:
                return enriched_suite

            # Integrate external patterns into test suite
            enriched_suite['external_patterns'] = external_patterns
            enriched_suite['enrichment_metadata'] = {
                'enrichment_timestamp': datetime.now().isoformat(),
                'external_patterns_count': len(external_patterns),
                'enrichment_source': 'linkup',
                'quality_threshold': self.quality_threshold
            }

            # Merge test cases
            existing_tests = enriched_suite.get('test_cases', [])
            external_tests = []

            for pattern in external_patterns:
                if 'test_template' in pattern:
                    external_test = self._generate_test_from_pattern(pattern, component)
                    if external_test:
                        external_tests.append(external_test)

            # Add external tests with proper categorization
            enriched_suite['test_cases'] = existing_tests + external_tests
            enriched_suite['test_categories'] = enriched_suite.get('test_categories', {})
            enriched_suite['test_categories']['external_enriched'] = len(external_tests)

            logger.info(f"Enriched test suite with {len(external_tests)} external test cases")

        except Exception as e:
            logger.error(f"Error enriching test suite: {e}")

        return enriched_suite

    def get_trending_patterns(self,
                            time_period: str = 'week',
                            category: str = 'all') -> List[Dict[str, Any]]:
        """Get trending test patterns from external sources.

        Args:
            time_period: Time period for trends (day, week, month)
            category: Pattern category filter

        Returns:
            List of trending patterns
        """
        try:
            if self.linkup_service:
                trending_patterns = self.linkup_service.get_trending_patterns(
                    time_period=time_period,
                    category=category
                )
            else:
                trending_patterns = []

            # Transform to internal format
            enriched_patterns = []
            for pattern in trending_patterns:
                enriched_pattern = self._enrich_pattern(pattern, 'trending')
                if enriched_pattern:
                    enriched_patterns.append(enriched_pattern)

            return enriched_patterns

        except Exception as e:
            logger.error(f"Error getting trending patterns: {e}")
            return []

    def batch_discover_patterns(self,
                              components: List[Dict[str, Any]],
                              max_workers: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Discover patterns for multiple components in parallel.

        Args:
            components: List of UI components
            max_workers: Maximum number of parallel workers

        Returns:
            Dictionary mapping component IDs to their discovered patterns
        """
        results = {}

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tasks
                future_to_component = {
                    executor.submit(self.discover_patterns_for_component, comp): comp
                    for comp in components
                }

                # Collect results
                for future in as_completed(future_to_component):
                    component = future_to_component[future]
                    component_id = component.get('id', f'component_{id(component)}')

                    try:
                        patterns = future.result()
                        results[component_id] = patterns
                    except Exception as e:
                        logger.error(f"Error discovering patterns for component {component_id}: {e}")
                        results[component_id] = []

        except Exception as e:
            logger.error(f"Error in batch pattern discovery: {e}")

        return results

    def _enrich_pattern(self,
                       pattern: Dict[str, Any],
                       context: str) -> Optional[Dict[str, Any]]:
        """Enrich a raw external pattern with additional metadata and transformations."""
        try:
            enriched = pattern.copy()

            # Add enrichment metadata
            enriched['enrichment'] = {
                'source': 'external',
                'enriched_at': datetime.now().isoformat(),
                'context': context,
                'original_score': pattern.get('quality_score', 0)
            }

            # Apply context-specific transformations
            if context in self.pattern_mappings:
                enriched = self.pattern_mappings[context](enriched)

            # Add MLB-specific enhancements
            enriched = self._add_mlb_enhancements(enriched)

            # Calculate final enrichment score
            enriched['enrichment_score'] = self._calculate_enrichment_score(enriched)

            return enriched

        except Exception as e:
            logger.error(f"Error enriching pattern: {e}")
            return None

    def _transform_mobile_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern for mobile testing context."""
        pattern['mobile_specific'] = {
            'device_compatibility': ['iOS', 'Android'],
            'orientation_testing': True,
            'touch_gestures': ['tap', 'swipe', 'pinch'],
            'performance_considerations': ['memory_usage', 'battery_impact']
        }
        return pattern

    def _transform_web_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern for web testing context."""
        pattern['web_specific'] = {
            'browser_compatibility': ['chrome', 'firefox', 'safari'],
            'responsive_design': True,
            'accessibility_checks': True,
            'performance_metrics': ['load_time', 'first_paint']
        }
        return pattern

    def _transform_api_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern for API testing context."""
        pattern['api_specific'] = {
            'methods_supported': ['GET', 'POST', 'PUT', 'DELETE'],
            'authentication_types': ['bearer', 'oauth2'],
            'response_validation': True,
            'error_handling': ['4xx', '5xx', 'timeout']
        }
        return pattern

    def _transform_performance_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern for performance testing context."""
        pattern['performance_specific'] = {
            'metrics': ['response_time', 'throughput', 'memory_usage'],
            'load_testing': True,
            'stress_testing': True,
            'thresholds': {
                'response_time_ms': 2000,
                'memory_mb': 100
            }
        }
        return pattern

    def _transform_accessibility_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern for accessibility testing context."""
        pattern['accessibility_specific'] = {
            'wcag_compliance': '2.1 AA',
            'screen_reader_support': True,
            'keyboard_navigation': True,
            'color_contrast': True,
            'focus_management': True
        }
        return pattern

    def _add_mlb_enhancements(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Add MLB-specific enhancements to pattern."""
        pattern['mlb_enhancements'] = {
            'sports_data_testing': True,
            'real_time_updates': True,
            'live_score_validation': True,
            'player_statistics': True,
            'game_state_changes': True
        }
        return pattern

    def _calculate_enrichment_score(self, pattern: Dict[str, Any]) -> float:
        """Calculate final enrichment score for pattern."""
        base_score = pattern.get('quality_score', 0.5)
        mlb_relevance = pattern.get('mlb_relevance', 0.0)

        # Boost for MLB-specific content
        mlb_boost = mlb_relevance * 0.3

        # Boost for code examples
        code_boost = 0.1 if pattern.get('code_example') else 0.0

        # Boost for documentation
        doc_boost = 0.1 if pattern.get('documentation') else 0.0

        return min(base_score + mlb_boost + code_boost + doc_boost, 1.0)

    def _determine_search_contexts(self,
                                 component: Dict[str, Any],
                                 ui_context: Optional[Dict]) -> List[str]:
        """Determine appropriate search contexts for component."""
        contexts = ['mobile']  # Default for MLB mobile app

        component_type = component.get('type', '')

        if component_type in ['webview', 'chart', 'map']:
            contexts.append('web')

        if component_type == 'api_endpoint':
            contexts.append('api')

        if component.get('requires_auth'):
            contexts.append('security')

        if ui_context and ui_context.get('requires_performance_testing'):
            contexts.append('performance')

        return contexts

    def _build_context_query(self, component: Dict[str, Any], context: str) -> str:
        """Build search query based on component and context."""
        component_type = component.get('type', 'component')

        base_query = f"{component_type} testing"

        context_queries = {
            'mobile': f"{base_query} mobile app automation",
            'web': f"{base_query} web browser automation",
            'api': f"{base_query} API endpoint validation",
            'performance': f"{base_query} performance load testing",
            'accessibility': f"{base_query} accessibility WCAG testing",
            'security': f"{base_query} authentication security testing"
        }

        return context_queries.get(context, base_query)

    def _transform_to_internal_format(self,
                                    pattern: Dict[str, Any],
                                    component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform external pattern to internal format."""
        try:
            internal_pattern = {
                'pattern_id': pattern.get('pattern_id', ''),
                'title': pattern.get('title', ''),
                'description': pattern.get('description', ''),
                'category': 'external_enriched',
                'source': 'linkup',
                'confidence_score': pattern.get('enrichment_score', 0.5),
                'component_type': component.get('type', ''),
                'test_template': self._generate_test_template(pattern, component),
                'metadata': {
                    'external_url': pattern.get('external_url', ''),
                    'author': pattern.get('author', ''),
                    'framework': pattern.get('framework', ''),
                    'language': pattern.get('language', 'python'),
                    'tags': pattern.get('tags', []),
                    'created_at': pattern.get('created_at', ''),
                    'votes': pattern.get('votes', 0)
                }
            }

            return internal_pattern

        except Exception as e:
            logger.error(f"Error transforming pattern to internal format: {e}")
            return None

    def _generate_test_template(self,
                              pattern: Dict[str, Any],
                              component: Dict[str, Any]) -> str:
        """Generate test template from external pattern."""
        component_type = component.get('type', 'unknown')

        if component_type in self.internal_templates:
            return self.internal_templates[component_type](pattern, component)
        else:
            return self._create_generic_test_template(pattern, component)

    def _create_button_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create button test template."""
        return f"""
def test_{component.get('id', 'button')}_external_pattern():
    '''External pattern: {pattern.get('title', 'Button test')}'''
    # {pattern.get('description', 'Test button functionality')}

    driver.find_element(By.ID, "{component.get('id')}").click()
    assert driver.current_url != initial_url  # Navigation occurred
    """

    def _create_list_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create list test template."""
        return f"""
def test_{component.get('id', 'list')}_external_pattern():
    '''External pattern: {pattern.get('title', 'List test')}'''
    # {pattern.get('description', 'Test list functionality')}

    list_element = driver.find_element(By.ID, "{component.get('id')}")
    items = list_element.find_elements(By.CLASS_NAME, "list-item")
    assert len(items) > 0  # List has items
    """

    def _create_api_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create API test template."""
        return f"""
def test_{component.get('id', 'api')}_external_pattern():
    '''External pattern: {pattern.get('title', 'API test')}'''
    # {pattern.get('description', 'Test API endpoint')}

    response = requests.get("{component.get('url', '')}")
    assert response.status_code == 200
    assert response.json() is not None
    """

    def _create_performance_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create performance test template."""
        return f"""
def test_{component.get('id', 'performance')}_external_pattern():
    '''External pattern: {pattern.get('title', 'Performance test')}'''
    # {pattern.get('description', 'Test performance metrics')}

    start_time = time.time()
    driver.find_element(By.ID, "{component.get('id')}").click()
    load_time = time.time() - start_time
    assert load_time < 2.0  # Max 2 second load time
    """

    def _create_accessibility_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create accessibility test template."""
        return f"""
def test_{component.get('id', 'accessibility')}_external_pattern():
    '''External pattern: {pattern.get('title', 'Accessibility test')}'''
    # {pattern.get('description', 'Test accessibility compliance')}

    element = driver.find_element(By.ID, "{component.get('id')}")
    assert element.get_attribute("aria-label") is not None
    assert element.is_enabled()
    """

    def _create_generic_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create generic test template."""
        return f"""
def test_{component.get('id', 'component')}_external_pattern():
    '''External pattern: {pattern.get('title', 'Component test')}'''
    # {pattern.get('description', 'Test component functionality')}

    element = driver.find_element(By.ID, "{component.get('id')}")
    assert element.is_displayed()
    """

    def _generate_test_from_pattern(self,
                                  pattern: Dict[str, Any],
                                  component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate test case from pattern."""
        try:
            test_case = {
                'test_id': f"external_{pattern.get('pattern_id', '')[:8]}",
                'name': f"Test {component.get('id', 'component')} - {pattern.get('title', 'External Pattern')}",
                'description': pattern.get('description', ''),
                'category': 'external_enriched',
                'priority': 'medium',
                'source': 'external_pattern',
                'test_code': pattern.get('test_template', ''),
                'metadata': {
                    'external_pattern_id': pattern.get('pattern_id', ''),
                    'external_source': pattern.get('source', ''),
                    'confidence_score': pattern.get('confidence_score', 0.5)
                }
            }

            return test_case

        except Exception as e:
            logger.error(f"Error generating test from pattern: {e}")
            return None

    def _deduplicate_and_sort(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and sort patterns by relevance."""
        # Remove duplicates based on pattern_id
        seen_ids = set()
        unique_patterns = []

        for pattern in patterns:
            pattern_id = pattern.get('pattern_id', '')
            if pattern_id and pattern_id not in seen_ids:
                seen_ids.add(pattern_id)
                unique_patterns.append(pattern)

        # Sort by enrichment score
        unique_patterns.sort(
            key=lambda p: p.get('enrichment_score', 0),
            reverse=True
        )

        return unique_patterns

    def get_service_status(self) -> Dict[str, Any]:
        """Get external enrichment service status."""
        return {
            'service_name': 'ExternalTestEnrichment',
            'linkup_available': LINKUP_AVAILABLE,
            'linkup_status': self.linkup_service.get_health_status() if self.linkup_service else {'available': False},
            'api_key_configured': bool(self.api_key),
            'quality_threshold': self.quality_threshold,
            'max_patterns_per_search': self.max_patterns_per_search,
            'supported_contexts': list(self.pattern_mappings.keys())
        }