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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

        # Internal pattern templates mapped to component types
        self.internal_templates = {
            'button': self._create_button_test_template,
            'list': self._create_list_test_template,
            'api': self._create_api_test_template,
            'api_endpoint': self._create_api_test_template,
            'webview': self._create_generic_test_template,
            'chart': self._create_generic_test_template,
            'map': self._create_generic_test_template,
            'performance': self._create_performance_test_template,
            'accessibility': self._create_accessibility_test_template
        }

    def _calculate_test_similarity(self, test1: Dict[str, Any], test2: Dict[str, Any]) -> float:
        """Calculate similarity between two test cases based on content.
        
        Args:
            test1: First test case
            test2: Second test case
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Extract testable content from both tests
            content1 = self._extract_test_content(test1)
            content2 = self._extract_test_content(test2)
            
            # Calculate similarity based on multiple factors
            name_similarity = self._string_similarity(content1['name'], content2['name'])
            description_similarity = self._string_similarity(content1['description'], content2['description'])
            code_similarity = self._string_similarity(content1['code'], content2['code'])
            type_similarity = 1.0 if content1['type'] == content2['type'] else 0.0
            
            # Weighted average (code has highest weight as it's most important)
            similarity = (
                name_similarity * 0.25 + 
                description_similarity * 0.25 + 
                code_similarity * 0.40 + 
                type_similarity * 0.10
            )
            
            return similarity
            
        except Exception as e:
            logger.warning(f"Error calculating test similarity: {e}")
            return 0.0
    
    def _extract_test_content(self, test: Any) -> Dict[str, str]:
        """Extract comparable content from a test case, handling various input formats."""
        # Handle non-dictionary inputs safely
        if not test:
            return {
                'name': '',
                'description': '',
                'code': '',
                'type': 'unknown'
            }
        
        # If test is a string, treat it as a test name
        if isinstance(test, str):
            return {
                'name': test.lower().strip(),
                'description': '',
                'code': '',
                'type': 'unknown'
            }
        
        # If test is not a dictionary, convert to string representation
        if not isinstance(test, dict):
            test_str = str(test).lower().strip()
            return {
                'name': test_str,
                'description': '',
                'code': '',
                'type': 'unknown'
            }
        
        # Extract content from dictionary format
        return {
            'name': str(test.get('name', test.get('test_name', ''))).lower().strip(),
            'description': str(test.get('description', test.get('test_description', ''))).lower().strip(),
            'code': self._normalize_test_code(str(test.get('test_code', test.get('code', '')))),
            'type': str(test.get('type', test.get('test_type', 'unknown'))).lower().strip()
        }
    
    def _normalize_test_code(self, code: str) -> str:
        """Normalize test code for comparison by removing whitespace and formatting differences."""
        import re
        
        # Remove extra whitespace, comments, and normalize common patterns
        normalized = re.sub(r'#.*$', '', code, flags=re.MULTILINE)  # Remove comments
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = re.sub(r'[\'"]([^\'"]*)[\'"]', r'STRING', normalized)  # Normalize string literals
        normalized = re.sub(r'\b\d+\b', 'NUMBER', normalized)  # Normalize numbers
        normalized = normalized.lower().strip()
        
        return normalized
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using simple character-based comparison."""
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
            
        # Simple Jaccard similarity using character bigrams
        def get_bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        
        bigrams1 = get_bigrams(str1)
        bigrams2 = get_bigrams(str2)
        
        if not bigrams1 and not bigrams2:
            return 1.0
        if not bigrams1 or not bigrams2:
            return 0.0
            
        intersection = len(bigrams1.intersection(bigrams2))
        union = len(bigrams1.union(bigrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _deduplicate_tests(self, tests: List[Dict[str, Any]], similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Remove duplicate tests based on content similarity.
        
        Args:
            tests: List of test cases to deduplicate
            similarity_threshold: Threshold above which tests are considered duplicates
            
        Returns:
            Deduplicated list of tests
        """
        if not tests:
            return tests
            
        deduplicated = []
        removed_count = 0
        
        for test in tests:
            is_duplicate = False
            
            # Check against already selected tests
            for existing_test in deduplicated:
                similarity = self._calculate_test_similarity(test, existing_test)
                
                if similarity >= similarity_threshold:
                    # This is a duplicate - merge any unique information
                    self._merge_test_metadata(existing_test, test)
                    is_duplicate = True
                    removed_count += 1
                    logger.debug(f"Removed duplicate test (similarity: {similarity:.3f}): {test.get('name', 'unnamed')}")
                    break
            
            if not is_duplicate:
                deduplicated.append(test)
        
        logger.info(f"Deduplication removed {removed_count} duplicate tests out of {len(tests)} total tests")
        return deduplicated
    
    def _merge_test_metadata(self, target_test: Dict[str, Any], source_test: Dict[str, Any]):
        """Merge metadata from source test into target test for enhanced information."""
        # Merge sources if both tests have source information
        target_sources = target_test.get('sources', [])
        source_sources = source_test.get('sources', [])
        
        if source_sources:
            if not isinstance(target_sources, list):
                target_sources = [target_sources] if target_sources else []
            
            # Add unique sources
            for source in source_sources:
                if source not in target_sources:
                    target_sources.append(source)
            
            target_test['sources'] = target_sources
        
        # Merge tags or categories
        target_tags = set(target_test.get('tags', []))
        source_tags = set(source_test.get('tags', []))
        if source_tags:
            target_test['tags'] = list(target_tags.union(source_tags))
        
        # Add deduplication metadata
        if 'deduplication_info' not in target_test:
            target_test['deduplication_info'] = []
        
        target_test['deduplication_info'].append({
            'merged_test': source_test.get('name', 'unnamed'),
            'similarity_source': source_test.get('source', 'unknown')
        })

    def search_test_patterns(self,
                           query: str,
                           context: str = 'general',
                           limit: int = None) -> List[Dict[str, Any]]:
        """Search for external test patterns with improved error handling.

        Args:
            query: Search query for test patterns
            context: Search context (mobile, web, api, etc.)
            limit: Maximum number of patterns to return (optional)

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
            # Use provided limit or default
            search_limit = limit if limit is not None else self.max_patterns_per_search
            
            # Search using Linkup service
            raw_patterns = self.linkup_service.search_test_patterns(
                query=query,
                context=context,
                limit=search_limit
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
        """Discover external patterns specifically for a UI component with relevance scoring.

        Args:
            component: UI component definition
            ui_context: Optional UI context information

        Returns:
            List of component-specific external patterns sorted by relevance
        """
        if not component:
            return []

        # Handle both 'type' and 'component_type' field names
        component_type = component.get('type') or component.get('component_type')
        if not component_type:
            return []

        discovered_patterns = []

        try:
            # Search by component type using enhanced query generation
            component_patterns = []
            if self.linkup_service:
                # Build enhanced search query for component type
                query = f"{component_type} testing automation"

                # Add MLB context if available
                if ui_context and ui_context.get('app_type') == 'mlb_mobile':
                    query += " mobile app sports"

                component_patterns = self.linkup_service.search_test_patterns(
                    query=query,
                    context='mobile',
                    limit=self.max_patterns_per_search
                )

            # Add context-specific searches with enhanced queries
            contexts = self._determine_search_contexts(component, ui_context)
            for context in contexts:
                enhanced_query = self._build_context_query(component, context)
                context_patterns = self.search_test_patterns(enhanced_query, context)
                component_patterns.extend(context_patterns)

            # Apply relevance scoring and filtering
            if component_patterns:
                # Filter patterns by relevance score (minimum 0.3)
                relevant_patterns = self._filter_patterns_by_relevance(
                    component_patterns, 
                    component, 
                    contexts[0] if contexts else 'mobile',
                    min_score=0.3
                )
                
                # Transform top relevant patterns to internal format
                for pattern in relevant_patterns[:self.max_patterns_per_search]:
                    transformed_pattern = self._transform_to_internal_format(pattern, component)
                    if transformed_pattern:
                        # Preserve relevance score in transformed pattern
                        transformed_pattern['relevance_score'] = pattern.get('relevance_score', 0.0)
                        discovered_patterns.append(transformed_pattern)

            # Apply final deduplication and sorting
            discovered_patterns = self._deduplicate_and_sort_by_relevance(discovered_patterns)

            logger.info(f"Discovered {len(discovered_patterns)} high-relevance external patterns for component {component.get('id', component.get('component_id', 'unknown'))}")

        except Exception as e:
            logger.error(f"Error discovering patterns for component {component.get('id', component.get('component_id', 'unknown'))}: {e}")

        return discovered_patterns

    def enrich_test_suite(self,
                         test_suite,
                         component: Dict[str, Any]):
        """Enrich an existing test suite with external patterns and track usage.

        Args:
            test_suite: Existing test suite to enrich (list of tests or dict with test_cases)
            component: Component being tested

        Returns:
            Enriched test suite with external patterns integrated and duplicates removed
        """
        try:
            # Handle both list and dict formats
            if isinstance(test_suite, list):
                # Convert list format to dict format
                enriched_suite = {
                    'test_cases': test_suite.copy(),
                    'test_categories': {}
                }
                return_as_list = True
            else:
                enriched_suite = test_suite.copy()
                return_as_list = False

            # Get component type for tracking
            component_type = component.get('type') or component.get('component_type', 'unknown')

            # Discover relevant external patterns with usage-boosted scoring
            external_patterns = self.discover_patterns_for_component(component)
            
            # Track pattern views
            for pattern in external_patterns:
                pattern_id = pattern.get('pattern_id')
                if pattern_id:
                    self.track_pattern_usage(pattern_id, 'viewed', component_type)

            if not external_patterns:
                if return_as_list:
                    return enriched_suite['test_cases']
                return enriched_suite

            # Integrate external patterns into test suite
            enriched_suite['external_patterns'] = external_patterns
            enriched_suite['enrichment_metadata'] = {
                'enrichment_timestamp': datetime.now().isoformat(),
                'external_patterns_count': len(external_patterns),
                'enrichment_source': 'linkup',
                'quality_threshold': self.quality_threshold,
                'usage_tracking_enabled': True
            }

            # Merge test cases
            existing_tests = enriched_suite.get('test_cases', [])
            external_tests = []
            selected_patterns = []

            for pattern in external_patterns:
                if 'test_template' in pattern:
                    external_test = self._generate_test_from_pattern(pattern, component)
                    if external_test:
                        external_tests.append(external_test)
                        selected_patterns.append(pattern)
                        
                        # Track pattern selection
                        pattern_id = pattern.get('pattern_id')
                        if pattern_id:
                            self.track_pattern_usage(pattern_id, 'selected', component_type)

            # Track ignored patterns (viewed but not selected)
            selected_pattern_ids = {p.get('pattern_id') for p in selected_patterns if p.get('pattern_id')}
            for pattern in external_patterns:
                pattern_id = pattern.get('pattern_id')
                if pattern_id and pattern_id not in selected_pattern_ids:
                    self.track_pattern_usage(pattern_id, 'ignored', component_type)

            # Apply usage-based scoring to patterns before deduplication
            for test in external_tests:
                if 'pattern_id' in test:
                    original_score = test.get('relevance_score', 0.5)
                    boosted_score = self.get_usage_boosted_score(test['pattern_id'], original_score)
                    test['usage_boosted_score'] = boosted_score

            # Combine all tests before deduplication
            all_tests = existing_tests + external_tests
            
            # Apply content-based deduplication to remove similar tests
            logger.info(f"Deduplicating {len(all_tests)} tests (before: {len(existing_tests)} existing + {len(external_tests)} external)")
            deduplicated_tests = self._deduplicate_tests(all_tests, similarity_threshold=0.7)
            
            # Update enrichment metadata with deduplication info
            enriched_suite['enrichment_metadata']['tests_before_deduplication'] = len(all_tests)
            enriched_suite['enrichment_metadata']['tests_after_deduplication'] = len(deduplicated_tests)
            enriched_suite['enrichment_metadata']['duplicates_removed'] = len(all_tests) - len(deduplicated_tests)
            enriched_suite['enrichment_metadata']['deduplication_threshold'] = 0.7
            enriched_suite['enrichment_metadata']['patterns_selected'] = len(selected_patterns)
            enriched_suite['enrichment_metadata']['patterns_ignored'] = len(external_patterns) - len(selected_patterns)
            
            # Categorize final tests
            enriched_suite['test_cases'] = deduplicated_tests
            enriched_suite['test_categories'] = enriched_suite.get('test_categories', {})
            enriched_suite['test_categories']['external_enriched'] = len(external_tests)
            enriched_suite['test_categories']['deduplicated_final'] = len(deduplicated_tests)

            logger.info(f"Enriched test suite: {len(existing_tests)} → {len(deduplicated_tests)} tests (added {len(external_tests)}, removed {len(all_tests) - len(deduplicated_tests)} duplicates)")

            # Return in the same format as input
            if return_as_list:
                return deduplicated_tests
            else:
                return enriched_suite

        except Exception as e:
            logger.error(f"Error enriching test suite: {e}")
            # Return original input on error
            return test_suite

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
        """Discover patterns for multiple components in parallel with deduplication.

        Args:
            components: List of UI components
            max_workers: Maximum number of parallel workers

        Returns:
            Dictionary mapping component IDs to their discovered patterns (deduplicated)
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
                all_patterns = []
                component_pattern_map = {}
                
                for future in as_completed(future_to_component):
                    component = future_to_component[future]
                    component_id = component.get('id') or component.get('component_id', f'component_{id(component)}')

                    try:
                        patterns = future.result()
                        results[component_id] = patterns
                        
                        # Track patterns for cross-component deduplication
                        for pattern in patterns:
                            pattern['_source_component'] = component_id
                            all_patterns.append(pattern)
                            
                        component_pattern_map[component_id] = len(patterns)
                        
                    except Exception as e:
                        logger.error(f"Error discovering patterns for component {component_id}: {e}")
                        results[component_id] = []
                        component_pattern_map[component_id] = 0

                # Apply cross-component deduplication if we have multiple components
                if len(components) > 1 and all_patterns:
                    logger.info(f"Applying cross-component deduplication to {len(all_patterns)} patterns from {len(components)} components")
                    
                    # Convert patterns to test format for deduplication
                    pattern_tests = []
                    for pattern in all_patterns:
                        test_item = {
                            'name': pattern.get('title', pattern.get('pattern_id', 'unnamed_pattern')),
                            'description': pattern.get('description', ''),
                            'test_code': pattern.get('test_template', ''),
                            'type': pattern.get('category', 'unknown'),
                            'source': pattern.get('source', 'external'),
                            '_source_component': pattern.get('_source_component'),
                            '_original_pattern': pattern
                        }
                        pattern_tests.append(test_item)
                    
                    # Deduplicate with slightly higher threshold for cross-component patterns
                    deduplicated_pattern_tests = self._deduplicate_tests(pattern_tests, similarity_threshold=0.8)
                    
                    # Rebuild results with deduplicated patterns
                    results = {}
                    for component in components:
                        component_id = component.get('id') or component.get('component_id', f'component_{id(component)}')
                        results[component_id] = []
                    
                    # Distribute deduplicated patterns back to components
                    for test_item in deduplicated_pattern_tests:
                        source_component = test_item['_source_component']
                        original_pattern = test_item['_original_pattern']
                        
                        # Add deduplication metadata to pattern
                        if 'deduplication_info' in test_item:
                            original_pattern['deduplication_info'] = test_item['deduplication_info']
                        
                        results[source_component].append(original_pattern)
                    
                    duplicates_removed = len(all_patterns) - len(deduplicated_pattern_tests)
                    logger.info(f"Cross-component deduplication: {len(all_patterns)} → {len(deduplicated_pattern_tests)} patterns (removed {duplicates_removed} duplicates)")

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
        """Intelligently determine appropriate search contexts for component."""
        contexts = []
        
        # Handle both 'type' and 'component_type' field names
        component_type = component.get('type') or component.get('component_type', '')
        component_id = component.get('id') or component.get('component_id', '')
        properties = component.get('properties', {})

        # Primary context based on UI context
        if ui_context:
            app_type = ui_context.get('app_type', '')
            platform = ui_context.get('platform', '')
            
            if 'mobile' in app_type.lower() or platform.lower() in ['ios', 'android']:
                contexts.append('mobile')
            elif 'web' in app_type.lower() or platform.lower() in ['web', 'browser']:
                contexts.append('web')
            else:
                contexts.append('mobile')  # Default for MLB mobile app
        else:
            contexts.append('mobile')  # Default

        # Component-type-specific contexts
        component_context_mapping = {
            'webview': ['web', 'mobile'],
            'iframe': ['web'],
            'chart': ['web', 'performance'],
            'map': ['web', 'mobile'],
            'api_endpoint': ['api', 'performance'],
            'list': ['mobile', 'performance'],  # Lists often need performance testing
            'form': ['mobile', 'web', 'accessibility'],  # Forms need accessibility testing
            'text_field': ['accessibility', 'mobile'],
            'video': ['mobile', 'web', 'performance'],
            'image': ['mobile', 'web', 'performance'],
            'modal': ['accessibility', 'mobile', 'web'],
            'dropdown': ['accessibility', 'mobile']
        }

        if component_type in component_context_mapping:
            for ctx in component_context_mapping[component_type]:
                if ctx not in contexts:
                    contexts.append(ctx)

        # Business logic-based context determination
        # Security context for authentication-related components
        security_indicators = [
            component.get('requires_auth'),
            'login' in component_id.lower(),
            'auth' in component_id.lower(),
            'password' in component_id.lower(),
            'signin' in component_id.lower(),
            properties.get('secure', False),
            properties.get('authentication_required', False)
        ]
        
        if any(security_indicators):
            contexts.append('security')

        # Performance context for data-heavy components
        performance_indicators = [
            'large_dataset' in str(properties).lower(),
            'real_time' in str(properties).lower(),
            properties.get('real_time', False),
            'live' in component_id.lower(),
            'stream' in component_id.lower(),
            component_type in ['list', 'api_endpoint', 'webview'],
            len(str(properties)) > 200,  # Large property set suggests complex component
            ui_context and ui_context.get('requires_performance_testing')
        ]
        
        if any(performance_indicators):
            contexts.append('performance')

        # Accessibility context for interactive components
        accessibility_indicators = [
            component_type in ['button', 'form', 'text_field', 'modal', 'dropdown'],
            properties.get('accessibility_label'),
            properties.get('aria_label'),
            'accessible' in str(properties).lower(),
            ui_context and ui_context.get('accessibility_required', True)  # Default to true
        ]
        
        if any(accessibility_indicators):
            contexts.append('accessibility')

        # MLB-specific context enhancement
        mlb_indicators = [
            'game' in component_id.lower(),
            'team' in component_id.lower(),
            'player' in component_id.lower(),
            'score' in component_id.lower(),
            'stat' in component_id.lower(),
            'mlb' in component_id.lower(),
            properties.get('data_source') == 'mlb_api',
            ui_context and 'mlb' in ui_context.get('app_type', '').lower()
        ]

        if any(mlb_indicators):
            # For MLB components, prioritize mobile and performance
            if 'mobile' not in contexts:
                contexts.insert(0, 'mobile')
            if 'performance' not in contexts:
                contexts.append('performance')

        # API context for endpoints and data-driven components
        api_indicators = [
            component_type == 'api_endpoint',
            properties.get('url'),
            properties.get('endpoint'),
            properties.get('data_source'),
            'api' in component_id.lower(),
            'endpoint' in component_id.lower()
        ]
        
        if any(api_indicators):
            contexts.append('api')

        # Remove duplicates while preserving order
        unique_contexts = []
        for ctx in contexts:
            if ctx not in unique_contexts:
                unique_contexts.append(ctx)

        # Limit to top 4 contexts to avoid over-searching
        return unique_contexts[:4]

    def _calculate_pattern_relevance_score(self, 
                                           pattern: Dict[str, Any], 
                                           component: Dict[str, Any],
                                           context: str) -> float:
        """Calculate relevance score for a pattern based on multiple factors.
        
        Scoring breakdown:
        - Component type match: 40%
        - Context match: 30%
        - Source credibility: 20%
        - Pattern completeness: 10%
        
        Returns:
            Relevance score between 0.0 and 1.0
        """
        total_score = 0.0
        
        # Get component information
        component_type = component.get('type') or component.get('component_type', '')
        component_id = component.get('id') or component.get('component_id', '')
        properties = component.get('properties', {})
        
        # 1. Component type match (40% weight)
        component_match_score = self._score_component_type_match(pattern, component_type, component_id)
        total_score += component_match_score * 0.4
        
        # 2. Context match (30% weight)
        context_match_score = self._score_context_match(pattern, context, properties)
        total_score += context_match_score * 0.3
        
        # 3. Source credibility (20% weight)
        source_credibility_score = self._score_source_credibility(pattern)
        total_score += source_credibility_score * 0.2
        
        # 4. Pattern completeness (10% weight)
        completeness_score = self._score_pattern_completeness(pattern)
        total_score += completeness_score * 0.1
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _score_component_type_match(self, pattern: Dict[str, Any], component_type: str, component_id: str) -> float:
        """Score how well the pattern matches the component type."""
        score = 0.0
        
        pattern_title = pattern.get('title', '').lower()
        pattern_description = pattern.get('description', '').lower()
        pattern_content = f"{pattern_title} {pattern_description}"
        
        # Exact component type match
        if component_type.lower() in pattern_content:
            score += 0.5
        
        # Specific component ID terms
        component_terms = component_id.lower().split('_')
        for term in component_terms:
            if len(term) > 2 and term in pattern_content:
                score += 0.1
        
        # Component-specific keyword matching
        component_keywords = {
            'button': ['click', 'press', 'tap', 'button', 'cta', 'action'],
            'list': ['list', 'scroll', 'item', 'collection', 'table', 'grid'],
            'webview': ['webview', 'iframe', 'embed', 'web', 'browser'],
            'form': ['form', 'input', 'field', 'validation', 'submit'],
            'api_endpoint': ['api', 'endpoint', 'request', 'response', 'http'],
            'text_field': ['input', 'field', 'text', 'typing', 'entry'],
            'modal': ['modal', 'dialog', 'popup', 'overlay'],
            'image': ['image', 'picture', 'photo', 'visual'],
            'video': ['video', 'player', 'stream', 'media']
        }
        
        if component_type in component_keywords:
            keywords = component_keywords[component_type]
            matched_keywords = sum(1 for keyword in keywords if keyword in pattern_content)
            score += (matched_keywords / len(keywords)) * 0.3
        
        return min(score, 1.0)
    
    def _score_context_match(self, pattern: Dict[str, Any], context: str, properties: Dict[str, Any]) -> float:
        """Score how well the pattern matches the testing context."""
        score = 0.0
        
        pattern_content = f"{pattern.get('title', '')} {pattern.get('description', '')}".lower()
        
        # Context-specific keywords
        context_keywords = {
            'mobile': ['mobile', 'app', 'touch', 'gesture', 'ios', 'android', 'responsive'],
            'web': ['web', 'browser', 'desktop', 'chrome', 'firefox', 'safari'],
            'api': ['api', 'rest', 'json', 'http', 'endpoint', 'request', 'response'],
            'performance': ['performance', 'speed', 'load', 'time', 'optimization', 'fast'],
            'accessibility': ['accessibility', 'a11y', 'screen reader', 'wcag', 'aria', 'keyboard'],
            'security': ['security', 'auth', 'login', 'permission', 'secure', 'authentication']
        }
        
        if context in context_keywords:
            keywords = context_keywords[context]
            matched_keywords = sum(1 for keyword in keywords if keyword in pattern_content)
            score += (matched_keywords / len(keywords)) * 0.6
        
        # Business domain matching (MLB-specific)
        mlb_keywords = ['sport', 'game', 'team', 'player', 'score', 'baseball', 'mlb', 'stats']
        if properties.get('data_source') == 'mlb_api' or any(keyword in pattern_content for keyword in mlb_keywords):
            mlb_matches = sum(1 for keyword in mlb_keywords if keyword in pattern_content)
            score += (mlb_matches / len(mlb_keywords)) * 0.4
        
        return min(score, 1.0)
    
    def _score_source_credibility(self, pattern: Dict[str, Any]) -> float:
        """Score the credibility of the pattern source."""
        score = 0.5  # Base score
        
        source = pattern.get('source', '').lower()
        url = pattern.get('url', '').lower()
        
        # High credibility sources
        high_credibility_domains = [
            'developer.mozilla.org',
            'selenium.dev',
            'testing-library.com',
            'cypress.io',
            'playwright.dev',
            'stackoverflow.com',
            'github.com',
            'medium.com',
            'dev.to'
        ]
        
        if any(domain in url for domain in high_credibility_domains):
            score += 0.3
        
        # Medium credibility indicators
        medium_credibility_indicators = [
            'official' in source,
            'documentation' in source,
            'guide' in source,
            'tutorial' in source,
            'best practices' in pattern.get('title', '').lower()
        ]
        
        if any(medium_credibility_indicators):
            score += 0.2
        
        # Quality indicators from content
        pattern_title = pattern.get('title', '').lower()
        quality_indicators = [
            'comprehensive' in pattern_title,
            'complete' in pattern_title,
            'guide' in pattern_title,
            'best practice' in pattern_title,
            'testing' in pattern_title,
            'automation' in pattern_title
        ]
        
        quality_score = sum(1 for indicator in quality_indicators if indicator)
        score += (quality_score / len(quality_indicators)) * 0.2
        
        return min(score, 1.0)
    
    def _score_pattern_completeness(self, pattern: Dict[str, Any]) -> float:
        """Score the completeness and quality of the pattern."""
        score = 0.0
        
        # Required fields
        required_fields = ['title', 'description']
        present_fields = sum(1 for field in required_fields if pattern.get(field))
        score += (present_fields / len(required_fields)) * 0.4
        
        # Content quality indicators
        title = pattern.get('title', '')
        description = pattern.get('description', '')
        
        # Title quality
        if len(title) >= 10:
            score += 0.1
        if len(title) >= 30:
            score += 0.1
        
        # Description quality  
        if len(description) >= 50:
            score += 0.1
        if len(description) >= 200:
            score += 0.1
        
        # Test-specific content
        test_indicators = [
            'test' in title.lower(),
            'assert' in description.lower(),
            'verify' in description.lower(),
            'validate' in description.lower(),
            'check' in description.lower()
        ]
        
        test_score = sum(1 for indicator in test_indicators if indicator)
        score += (test_score / len(test_indicators)) * 0.2
        
        return min(score, 1.0)
    
    def _filter_patterns_by_relevance(self,
                                       patterns: List[Dict[str, Any]],
                                       component: Dict[str, Any],
                                       context: str,
                                       min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Filter and sort patterns by relevance score."""
        scored_patterns = []
        
        for pattern in patterns:
            relevance_score = self._calculate_pattern_relevance_score(pattern, component, context)
            
            if relevance_score >= min_score:
                pattern_copy = pattern.copy()
                pattern_copy['relevance_score'] = relevance_score
                scored_patterns.append(pattern_copy)
        
        # Sort by relevance score (highest first)
        scored_patterns.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Filtered {len(patterns)} patterns to {len(scored_patterns)} relevant patterns (min_score={min_score})")
        
        return scored_patterns

    def _deduplicate_and_sort_by_relevance(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and sort patterns by relevance score."""
        # Remove duplicates based on pattern_id and title similarity
        seen_ids = set()
        seen_titles = set()
        unique_patterns = []

        for pattern in patterns:
            pattern_id = pattern.get('pattern_id', '')
            pattern_title = pattern.get('title', '').lower().strip()
            
            # Check for ID-based duplicates
            is_duplicate = False
            if pattern_id and pattern_id in seen_ids:
                is_duplicate = True
            
            # Check for title-based duplicates (similar titles)
            if not is_duplicate and pattern_title:
                for seen_title in seen_titles:
                    # Simple similarity check for titles
                    if (len(pattern_title) > 10 and len(seen_title) > 10 and 
                        abs(len(pattern_title) - len(seen_title)) < 10):
                        # Check if titles are very similar (>80% character overlap)
                        common_chars = set(pattern_title.lower()) & set(seen_title.lower())
                        total_chars = set(pattern_title.lower()) | set(seen_title.lower())
                        if len(common_chars) / len(total_chars) > 0.8:
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                if pattern_id:
                    seen_ids.add(pattern_id)
                if pattern_title:
                    seen_titles.add(pattern_title)
                unique_patterns.append(pattern)

        # Sort by relevance score (highest first), then by enrichment score as fallback
        unique_patterns.sort(
            key=lambda p: (
                p.get('relevance_score', 0),
                p.get('enrichment_score', 0),
                p.get('quality_score', 0)
            ),
            reverse=True
        )

        logger.info(f"Deduplicated {len(patterns)} patterns to {len(unique_patterns)} unique patterns")
        return unique_patterns

    def track_pattern_usage(self, pattern_id: str, action: str, component_type: str = None):
        """Track pattern usage for learning and optimization.
        
        Args:
            pattern_id: Unique identifier for the pattern
            action: 'selected', 'ignored', 'successful', 'failed'
            component_type: Type of component the pattern was used with
        """
        if not pattern_id or not self.linkup_service or not self.linkup_service.cache:
            return
        
        try:
            timestamp = datetime.now().isoformat()
            usage_key = f"pattern_usage:{pattern_id}"
            
            # Get existing usage data
            existing_data = self.linkup_service.cache.get(usage_key)
            if existing_data:
                usage_data = json.loads(existing_data)
            else:
                usage_data = {
                    'pattern_id': pattern_id,
                    'total_views': 0,
                    'total_selected': 0,
                    'total_ignored': 0,
                    'total_successful': 0,
                    'total_failed': 0,
                    'component_types': {},
                    'first_seen': timestamp,
                    'last_updated': timestamp,
                    'usage_history': []
                }
            
            # Update counters
            if action == 'viewed':
                usage_data['total_views'] += 1
            elif action == 'selected':
                usage_data['total_selected'] += 1
            elif action == 'ignored':
                usage_data['total_ignored'] += 1
            elif action == 'successful':
                usage_data['total_successful'] += 1
            elif action == 'failed':
                usage_data['total_failed'] += 1
            
            # Track component type usage
            if component_type:
                if component_type not in usage_data['component_types']:
                    usage_data['component_types'][component_type] = 0
                usage_data['component_types'][component_type] += 1
            
            # Add to usage history (keep last 50 entries)
            usage_data['usage_history'].append({
                'timestamp': timestamp,
                'action': action,
                'component_type': component_type
            })
            if len(usage_data['usage_history']) > 50:
                usage_data['usage_history'] = usage_data['usage_history'][-50:]
            
            usage_data['last_updated'] = timestamp
            
            # Store back to cache with 30-day TTL
            self.linkup_service.cache.setex(
                usage_key,
                30 * 24 * 60 * 60,  # 30 days
                json.dumps(usage_data)
            )
            
            logger.debug(f"Tracked pattern usage: {pattern_id} -> {action}")
            
        except Exception as e:
            logger.error(f"Error tracking pattern usage: {e}")
    
    def get_pattern_usage_stats(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a specific pattern."""
        if not pattern_id or not self.linkup_service or not self.linkup_service.cache:
            return None
        
        try:
            usage_key = f"pattern_usage:{pattern_id}"
            existing_data = self.linkup_service.cache.get(usage_key)
            
            if existing_data:
                usage_data = json.loads(existing_data)
                
                # Calculate derived metrics
                total_interactions = usage_data['total_selected'] + usage_data['total_ignored']
                selection_rate = (usage_data['total_selected'] / total_interactions) if total_interactions > 0 else 0
                success_rate = (usage_data['total_successful'] / usage_data['total_selected']) if usage_data['total_selected'] > 0 else 0
                
                usage_data['selection_rate'] = selection_rate
                usage_data['success_rate'] = success_rate
                usage_data['effectiveness_score'] = selection_rate * success_rate
                
                return usage_data
            
        except Exception as e:
            logger.error(f"Error getting pattern usage stats: {e}")
        
        return None
    
    def get_usage_boosted_score(self, pattern_id: str, base_score: float) -> float:
        """Apply usage-based boost to pattern score."""
        usage_stats = self.get_pattern_usage_stats(pattern_id)
        if not usage_stats:
            return base_score
        
        # Calculate usage boost based on effectiveness
        effectiveness_score = usage_stats.get('effectiveness_score', 0)
        total_selected = usage_stats.get('total_selected', 0)
        
        # Boost based on effectiveness (0-50% boost)
        effectiveness_boost = effectiveness_score * 0.5
        
        # Additional boost for frequently used patterns (0-20% boost)
        if total_selected > 0:
            import math
            usage_boost = min(math.log(total_selected + 1) * 0.05, 0.2)
        else:
            usage_boost = 0
        
        # Apply combined boost
        boosted_score = base_score * (1 + effectiveness_boost + usage_boost)
        
        return min(boosted_score, 1.0)  # Cap at 1.0
    
    def get_top_performing_patterns(self, component_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top performing patterns based on usage data."""
        if not self.linkup_service or not self.linkup_service.cache:
            return []
        
        try:
            # Scan for all pattern usage keys
            pattern_keys = []
            cursor = 0
            while True:
                cursor, keys = self.linkup_service.cache.scan(cursor, match="pattern_usage:*", count=100)
                pattern_keys.extend(keys)
                if cursor == 0:
                    break
            
            patterns_with_stats = []
            
            for key in pattern_keys:
                try:
                    pattern_id = key.decode('utf-8').replace('pattern_usage:', '')
                    usage_stats = self.get_pattern_usage_stats(pattern_id)
                    
                    if usage_stats:
                        # Filter by component type if specified
                        if component_type:
                            component_types = usage_stats.get('component_types', {})
                            if component_type not in component_types:
                                continue
                        
                        patterns_with_stats.append({
                            'pattern_id': pattern_id,
                            'effectiveness_score': usage_stats.get('effectiveness_score', 0),
                            'selection_rate': usage_stats.get('selection_rate', 0),
                            'success_rate': usage_stats.get('success_rate', 0),
                            'total_selected': usage_stats.get('total_selected', 0),
                            'total_views': usage_stats.get('total_views', 0),
                            'component_types': usage_stats.get('component_types', {})
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing pattern stats for {key}: {e}")
                    continue
            
            # Sort by effectiveness score
            patterns_with_stats.sort(key=lambda x: x['effectiveness_score'], reverse=True)
            
            return patterns_with_stats[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top performing patterns: {e}")
            return []
    
    def cleanup_old_usage_data(self, days_old: int = 90):
        """Clean up usage data older than specified days."""
        if not self.linkup_service or not self.linkup_service.cache:
            return
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Scan for all pattern usage keys
            pattern_keys = []
            cursor = 0
            while True:
                cursor, keys = self.linkup_service.cache.scan(cursor, match="pattern_usage:*", count=100)
                pattern_keys.extend(keys)
                if cursor == 0:
                    break
            
            cleaned_count = 0
            
            for key in pattern_keys:
                try:
                    data = self.linkup_service.cache.get(key)
                    if data:
                        usage_data = json.loads(data)
                        last_updated = datetime.fromisoformat(usage_data.get('last_updated', ''))
                        
                        if last_updated < cutoff_date:
                            self.linkup_service.cache.delete(key)
                            cleaned_count += 1
                            
                except Exception as e:
                    logger.warning(f"Error processing cleanup for {key}: {e}")
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} old usage records")
            
        except Exception as e:
            logger.error(f"Error during usage data cleanup: {e}")
    
    def generate_usage_report(self) -> Dict[str, Any]:
        """Generate a comprehensive usage report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_patterns_tracked': 0,
            'top_component_types': {},
            'overall_stats': {
                'total_views': 0,
                'total_selected': 0,
                'total_ignored': 0,
                'total_successful': 0,
                'total_failed': 0
            },
            'top_patterns': [],
            'insights': []
        }
        
        try:
            # Get all pattern stats
            all_patterns = self.get_top_performing_patterns(limit=100)
            report['total_patterns_tracked'] = len(all_patterns)
            
            # Aggregate overall stats
            for pattern in all_patterns:
                report['overall_stats']['total_views'] += pattern.get('total_views', 0)
                report['overall_stats']['total_selected'] += pattern.get('total_selected', 0)
                
                # Aggregate component type stats
                for comp_type, count in pattern.get('component_types', {}).items():
                    if comp_type not in report['top_component_types']:
                        report['top_component_types'][comp_type] = 0
                    report['top_component_types'][comp_type] += count
            
            # Top 10 patterns
            report['top_patterns'] = all_patterns[:10]
            
            # Generate insights
            total_interactions = report['overall_stats']['total_selected'] + report['overall_stats']['total_ignored']
            if total_interactions > 0:
                overall_selection_rate = report['overall_stats']['total_selected'] / total_interactions
                report['insights'].append(f"Overall selection rate: {overall_selection_rate:.2%}")
            
            if report['top_component_types']:
                most_used_component = max(report['top_component_types'].items(), key=lambda x: x[1])
                report['insights'].append(f"Most used component type: {most_used_component[0]} ({most_used_component[1]} uses)")
            
            if len(all_patterns) > 0:
                avg_effectiveness = sum(p['effectiveness_score'] for p in all_patterns) / len(all_patterns)
                report['insights'].append(f"Average pattern effectiveness: {avg_effectiveness:.2%}")
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            report['error'] = str(e)
        
        return report

    def _build_context_query(self, component: Dict[str, Any], context: str) -> str:
        """Build sophisticated search query based on component type and context."""
        # Handle both 'type' and 'component_type' field names
        component_type = component.get('type') or component.get('component_type', 'component')
        component_id = component.get('id') or component.get('component_id', '')
        properties = component.get('properties', {})

        # Component-specific search terms with business logic keywords
        component_keywords = {
            'button': [
                'click interaction', 'disabled state', 'loading state', 'accessibility',
                'touch targets', 'form submission', 'navigation trigger', 'CTA testing',
                'button states', 'click handlers', 'responsive design', 'hover effects'
            ],
            'list': [
                'infinite scroll', 'pagination', 'lazy loading', 'item rendering',
                'performance optimization', 'virtual scrolling', 'data binding',
                'empty states', 'loading indicators', 'refresh functionality',
                'sorting filters', 'search integration'
            ],
            'webview': [
                'iframe testing', 'embedded content', 'cross-origin policies',
                'authentication integration', 'security validation', 'content loading',
                'resize handling', 'navigation events', 'cookie handling',
                'JavaScript execution', 'responsive iframe'
            ],
            'form': [
                'field validation', 'error handling', 'input patterns', 'email validation',
                'required fields', 'form submission', 'client-side validation',
                'server-side validation', 'accessibility labels', 'autocomplete',
                'form persistence', 'multi-step forms'
            ],
            'api_endpoint': [
                'HTTP status codes', 'JSON validation', 'response time', 'error handling',
                'authentication headers', 'rate limiting', 'caching strategies',
                'request/response logging', 'API versioning', 'error responses',
                'timeout handling', 'retry logic'
            ],
            'text_field': [
                'input validation', 'format checking', 'email patterns', 'phone patterns',
                'character limits', 'autocomplete', 'placeholder text', 'focus states',
                'accessibility labels', 'keyboard navigation', 'input masking',
                'real-time validation'
            ],
            'modal': [
                'overlay behavior', 'escape key handling', 'focus management',
                'backdrop clicks', 'accessibility traps', 'scroll locking',
                'animation states', 'responsive design', 'nested modals',
                'keyboard navigation'
            ],
            'dropdown': [
                'option selection', 'keyboard navigation', 'accessibility compliance',
                'search filtering', 'multi-select', 'option groups',
                'loading states', 'error states', 'custom styling'
            ],
            'image': [
                'loading states', 'lazy loading', 'responsive images', 'alt text',
                'error handling', 'placeholder images', 'image optimization',
                'retina support', 'progressive loading'
            ],
            'video': [
                'playback controls', 'autoplay policies', 'responsive player',
                'accessibility controls', 'caption support', 'fullscreen mode',
                'loading states', 'error handling', 'streaming quality'
            ]
        }

        # Get component-specific keywords
        keywords = component_keywords.get(component_type, ['functionality', 'user interaction', 'validation'])

        # Build base query with component type and primary keywords
        primary_keywords = keywords[:3]  # Use top 3 most relevant keywords
        base_query = f"{component_type} {' '.join(primary_keywords)} testing"

        # Add MLB-specific context if applicable
        mlb_context = ''
        if any(term in component_id.lower() for term in ['game', 'team', 'player', 'score', 'stat', 'mlb']):
            mlb_context = ' sports mobile app'
        elif properties.get('data_source') == 'mlb_api':
            mlb_context = ' real-time sports data'

        # Context-specific query enhancement
        context_enhancements = {
            'mobile': {
                'suffix': ' mobile app automation touch gestures',
                'additional': ['responsive design', 'touch targets', 'mobile performance']
            },
            'web': {
                'suffix': ' web browser automation cross-browser',
                'additional': ['browser compatibility', 'responsive web', 'desktop interaction']
            },
            'api': {
                'suffix': ' REST API validation JSON response',
                'additional': ['HTTP methods', 'status codes', 'data validation']
            },
            'performance': {
                'suffix': ' performance testing load optimization',
                'additional': ['response time', 'memory usage', 'scalability']
            },
            'accessibility': {
                'suffix': ' accessibility WCAG compliance screen readers',
                'additional': ['keyboard navigation', 'aria labels', 'color contrast']
            },
            'security': {
                'suffix': ' security testing authentication authorization',
                'additional': ['input sanitization', 'XSS protection', 'CSRF protection']
            }
        }

        enhancement = context_enhancements.get(context, {
            'suffix': ' automated testing best practices',
            'additional': ['test automation', 'quality assurance']
        })

        # Build final query
        final_query = base_query + enhancement['suffix'] + mlb_context

        # Add component-specific business logic terms
        if component_type == 'button' and any(term in component_id.lower() for term in ['follow', 'subscribe']):
            final_query += ' follow button subscription state management'
        elif component_type == 'list' and 'game' in component_id.lower():
            final_query += ' game schedule live scores real-time updates'
        elif component_type == 'webview' and any(term in component_id.lower() for term in ['gameday', 'live']):
            final_query += ' live sports streaming embedded video'
        elif component_type == 'api_endpoint' and 'stat' in component_id.lower():
            final_query += ' baseball statistics aggregation real-time data'

        return final_query

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
                'component_type': component.get('type') or component.get('component_type', ''),
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

    def _get_component_id(self, component: Dict[str, Any]) -> str:
        """Intelligently generate component ID, handling multiple field names and creating meaningful fallbacks."""
        # Try direct ID fields first
        component_id = component.get('id') or component.get('component_id')
        if component_id and component_id.strip():
            return component_id.strip()
        
        # Extract semantic information for intelligent fallback generation
        component_type = component.get('type') or component.get('component_type', 'unknown')
        properties = component.get('properties', {})
        
        # Strategy 1: Generate ID from text content
        text_sources = [
            properties.get('text'),
            properties.get('label'),
            properties.get('title'),
            properties.get('placeholder'),
            properties.get('accessibility_label'),
            properties.get('aria_label'),
            properties.get('name'),
            component.get('label'),  # Check component level too
            component.get('text')
        ]
        
        meaningful_text = None
        for text_source in text_sources:
            if text_source and isinstance(text_source, str) and len(text_source.strip()) > 0:
                meaningful_text = text_source.strip()
                break
        
        if meaningful_text:
            # Convert text to valid ID format
            # Remove special characters, convert to lowercase, replace spaces with underscores
            import re
            sanitized_text = re.sub(r'[^\w\s]', '', meaningful_text.lower())
            sanitized_text = re.sub(r'\s+', '_', sanitized_text.strip())
            # Limit length and ensure it's not too generic
            sanitized_text = sanitized_text[:20]
            
            if len(sanitized_text) >= 3 and sanitized_text not in ['button', 'click', 'submit', 'input', 'text']:
                component_id = f"{sanitized_text}_{component_type}"
                logger.info(f"Generated semantic component ID from text: {component_id}")
                return component_id
        
        # Strategy 2: Generate ID from component purpose/context
        purpose_indicators = []
        
        # Check for common action patterns
        action_patterns = {
            'follow': ['follow'],
            'login': ['login', 'sign_in', 'signin'],
            'logout': ['logout', 'sign_out', 'signout'],
            'submit': ['submit', 'send'],
            'cancel': ['cancel', 'close'],
            'save': ['save', 'store'],
            'edit': ['edit', 'modify'],
            'delete': ['delete', 'remove'],
            'refresh': ['refresh', 'reload'],
            'search': ['search', 'find'],
            'filter': ['filter'],
            'sort': ['sort'],
            'next': ['next', 'forward'],
            'prev': ['previous', 'back'],
            'play': ['play', 'start'],
            'pause': ['pause', 'stop']
        }
        
        # Check all component data for action indicators
        component_str = str(component).lower()
        for action, patterns in action_patterns.items():
            if any(pattern in component_str for pattern in patterns):
                purpose_indicators.append(action)
        
        # Strategy 3: Check for MLB/domain-specific context
        mlb_context = []
        mlb_patterns = {
            'game': ['game', 'match'],
            'team': ['team', 'club'],
            'player': ['player', 'athlete'],
            'score': ['score', 'points'],
            'stats': ['stats', 'statistics', 'stat'],
            'schedule': ['schedule', 'calendar'],
            'live': ['live', 'realtime', 'real_time'],
            'video': ['video', 'stream', 'media']
        }
        
        for context, patterns in mlb_patterns.items():
            if any(pattern in component_str for pattern in patterns):
                mlb_context.append(context)
        
        # Strategy 4: Check data source context
        data_context = []
        data_source = properties.get('data_source', '')
        if 'mlb' in data_source.lower():
            data_context.append('mlb')
        if 'api' in data_source.lower():
            data_context.append('api')
        
        # Build intelligent ID from collected context
        id_parts = []
        
        # Add MLB context first (highest priority)
        if mlb_context:
            id_parts.extend(mlb_context[:2])  # Max 2 MLB context terms
        
        # Add purpose/action context
        if purpose_indicators:
            id_parts.extend(purpose_indicators[:1])  # Max 1 action term
        
        # Add component type
        id_parts.append(component_type)
        
        if len(id_parts) > 1:  # More than just component type
            component_id = '_'.join(id_parts)
            logger.info(f"Generated contextual component ID: {component_id}")
            return component_id
        
        # Strategy 5: Enhanced fallback with sequence numbering
        # Use a class-level counter to ensure unique IDs within session
        if not hasattr(self, '_component_id_counter'):
            self._component_id_counter = {}
        
        fallback_key = component_type
        if fallback_key not in self._component_id_counter:
            self._component_id_counter[fallback_key] = 1
        else:
            self._component_id_counter[fallback_key] += 1
        
        sequence_num = self._component_id_counter[fallback_key]
        component_id = f"{component_type}_{sequence_num}"
        
        logger.warning(f"Using enhanced fallback component ID: {component_id} (no semantic context found)")
        return component_id

    def _generate_test_template(self,
                              pattern: Dict[str, Any],
                              component: Dict[str, Any]) -> str:
        """Generate test template from external pattern."""
        # Handle both 'type' and 'component_type' field names
        component_type = component.get('type') or component.get('component_type', 'unknown')

        if component_type in self.internal_templates:
            return self.internal_templates[component_type](pattern, component)
        else:
            return self._create_generic_test_template(pattern, component)

    def _create_button_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create button test template."""
        component_id = self._get_component_id(component)
        button_text = component.get('properties', {}).get('text', 'button')
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'Button test')}'''
    # {pattern.get('description', 'Test button functionality')}

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    initial_url = driver.current_url
    button = driver.find_element(By.ID, "{component_id}")
    
    # Comprehensive button validation
    assert button.is_displayed(), "Button should be visible to users"
    assert button.is_enabled(), "Button should be enabled for interaction"
    
    # Verify button text content
    button_text = button.text or button.get_attribute('value') or button.get_attribute('aria-label')
    assert button_text, "Button should have accessible text content"
    
    # Test click interaction
    button.click()

    # Verify navigation or state change occurred
    WebDriverWait(driver, 5).until(
        lambda d: d.current_url != initial_url or
                 len(d.find_elements(By.CSS_SELECTOR, "[data-testid='success']")) > 0
    )
    """

    def _create_list_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create list test template."""
        component_id = self._get_component_id(component)
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'List test')}'''
    # {pattern.get('description', 'Test list functionality')}

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Wait for list to be present and visible
    list_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "{component_id}"))
    )

    # Check for list items using multiple selectors
    items = (list_element.find_elements(By.CLASS_NAME, "list-item") or
             list_element.find_elements(By.CSS_SELECTOR, "li") or
             list_element.find_elements(By.CSS_SELECTOR, "[role='listitem']"))

    assert len(items) > 0, f"List {{component_id}} should contain items"
    assert list_element.is_displayed(), "List should be visible"

    # Test first item is clickable
    if items:
        first_item = items[0]
        assert first_item.is_displayed(), "First list item should be visible"
    """

    def _create_api_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create API test template."""
        component_id = self._get_component_id(component)
        api_url = component.get('url') or component.get('endpoint', '/api/test')
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'API test')}'''
    # {pattern.get('description', 'Test API endpoint')}

    import requests
    import json

    # Test API endpoint functionality
    response = requests.get("{api_url}", timeout=10)

    assert response.status_code == 200, f"API endpoint should return 200, got {{response.status_code}}"
    assert response.headers.get('content-type', '').startswith('application/json'), "Response should be JSON"

    data = response.json()
    assert data is not None, "Response should contain valid JSON data"
    assert isinstance(data, (dict, list)), "Response should be a valid JSON object or array"

    # Test response structure
    if isinstance(data, dict) and 'error' in data:
        assert data['error'] is False or data['error'] == '', "API should not return error"
    """

    def _create_performance_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create performance test template."""
        component_id = self._get_component_id(component)
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'Performance test')}'''
    # {pattern.get('description', 'Test performance metrics')}

    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Test element load time
    start_time = time.time()
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "{component_id}"))
    )
    load_time = time.time() - start_time
    assert load_time < 2.0, f"Element should load within 2 seconds, took {{load_time:.2f}}s"

    # Test interaction response time
    if element.is_enabled():
        interaction_start = time.time()
        element.click()
        interaction_time = time.time() - interaction_start
        assert interaction_time < 1.0, f"Interaction should respond within 1 second, took {{interaction_time:.2f}}s"

    # Test element visibility performance
    assert element.is_displayed(), "Element should be visible"
    assert element.size['height'] > 0, "Element should have valid dimensions"
    """

    def _create_accessibility_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create accessibility test template."""
        component_id = self._get_component_id(component)
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'Accessibility test')}'''
    # {pattern.get('description', 'Test accessibility compliance')}

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "{component_id}"))
    )

    # Test WCAG compliance requirements
    assert element.is_enabled(), "Interactive element should be enabled"
    assert element.is_displayed(), "Element should be visible"

    # Test accessibility attributes
    aria_label = element.get_attribute("aria-label")
    aria_labelledby = element.get_attribute("aria-labelledby")
    role = element.get_attribute("role")

    # Element should have accessible name
    assert (aria_label or aria_labelledby or element.text.strip()), \
           "Element should have accessible name (aria-label, aria-labelledby, or text content)"

    # Test keyboard accessibility
    if element.tag_name.lower() in ['button', 'a', 'input', 'select', 'textarea']:
        tabindex = element.get_attribute("tabindex")
        assert tabindex != "-1", "Interactive element should be keyboard accessible"

    # Test color contrast (basic check)
    color = driver.execute_script("return window.getComputedStyle(arguments[0]).color", element)
    bg_color = driver.execute_script("return window.getComputedStyle(arguments[0]).backgroundColor", element)
    assert color and bg_color, "Element should have visible color styling"
    """

    def _create_generic_test_template(self, pattern: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Create generic test template."""
        component_id = self._get_component_id(component)
        return f"""
def test_{component_id}_external_pattern():
    '''External pattern: {pattern.get('title', 'Component test')}'''
    # {pattern.get('description', 'Test component functionality')}

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Wait for element to be present and visible
    element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "{component_id}"))
    )

    # Basic functionality tests
    assert element.is_displayed(), f"Element {{component_id}} should be visible"
    assert element.size['height'] > 0 and element.size['width'] > 0, "Element should have valid dimensions"

    # Test interactivity if applicable
    if element.is_enabled() and element.tag_name.lower() in ['button', 'a', 'input', 'select']:
        # Element appears interactive, test basic interaction
        element.click()
    """

    def _generate_test_from_pattern(self,
                                  pattern: Dict[str, Any],
                                  component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate test case from pattern."""
        try:
            # Get the template type from the pattern
            test_template_type = pattern.get('test_template', '')
            
            # Generate actual test code using template system
            if test_template_type and test_template_type in self.internal_templates:
                # Use specific template method if pattern specifies a known template type
                template_method = self.internal_templates[test_template_type]
                test_code = template_method(pattern, component)
            else:
                # Fall back to component-type based routing via _generate_test_template
                test_code = self._generate_test_template(pattern, component)

            test_case = {
                'test_id': f"external_{pattern.get('pattern_id', '')[:8]}",
                'name': f"Test {component.get('id', 'component')} - {pattern.get('title', 'External Pattern')}",
                'description': pattern.get('description', ''),
                'category': 'external_enriched',
                'priority': 'medium',
                'source': 'external_pattern',
                'test_code': test_code,
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