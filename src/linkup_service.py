"""
Linkup Service for External Test Pattern Discovery

This module provides integration with the Linkup API to discover external test patterns
and best practices that can enhance the internal pattern knowledge base.
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import redis
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class LinkupService:
    """Service for discovering external test patterns via Linkup API.

    Provides caching, retry logic, and intelligent pattern discovery
    for enhancing internal test pattern knowledge base.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: str = "https://api.linkup.com",
                 cache_ttl: int = 3600,
                 max_retries: int = 3,
                 timeout: int = 30):
        """Initialize the Linkup service.

        Args:
            api_key: Linkup API key (or use LINKUP_API_KEY env var)
            base_url: Base URL for Linkup API
            cache_ttl: Cache TTL in seconds (default 1 hour)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv('LINKUP_API_KEY')
        self.base_url = base_url.rstrip('/')
        self.cache_ttl = cache_ttl
        self.timeout = timeout

        # Initialize Redis cache
        self.cache = self._initialize_cache()

        # Initialize HTTP session with retry strategy
        self.session = self._initialize_session(max_retries)

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        # Search contexts for different types of testing
        self.search_contexts = {
            'mobile': {
                'keywords': ['mobile app testing', 'iOS testing', 'Android testing', 'mobile automation'],
                'filters': ['mobile', 'app', 'device']
            },
            'web': {
                'keywords': ['web testing', 'browser automation', 'UI testing', 'frontend testing'],
                'filters': ['web', 'browser', 'frontend']
            },
            'api': {
                'keywords': ['API testing', 'REST testing', 'GraphQL testing', 'endpoint testing'],
                'filters': ['api', 'rest', 'graphql', 'endpoint']
            },
            'performance': {
                'keywords': ['performance testing', 'load testing', 'stress testing', 'performance monitoring'],
                'filters': ['performance', 'load', 'stress', 'monitoring']
            },
            'accessibility': {
                'keywords': ['accessibility testing', 'WCAG testing', 'a11y testing', 'screen reader'],
                'filters': ['accessibility', 'wcag', 'a11y', 'screenreader']
            }
        }

    def _initialize_cache(self) -> Optional[redis.Redis]:
        """Initialize Redis cache connection."""
        try:
            cache = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 1)),  # Use DB 1 for Linkup cache
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            cache.ping()
            logger.info("Redis cache initialized successfully")
            return cache
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}. Using in-memory fallback.")
            return None

    def _initialize_session(self, max_retries: int) -> requests.Session:
        """Initialize HTTP session with retry strategy."""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],  # Updated from deprecated method_whitelist
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update({
            'User-Agent': 'MLB-TestGenerator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        if self.api_key:
            session.headers['Authorization'] = f'Bearer {self.api_key}'

        return session

    def search_test_patterns(self,
                           query: str,
                           context: str = 'general',
                           limit: int = 20,
                           include_code: bool = True) -> List[Dict[str, Any]]:
        """Search for external test patterns.

        Args:
            query: Search query for test patterns
            context: Search context (mobile, web, api, performance, accessibility)
            limit: Maximum number of results to return
            include_code: Whether to include code examples

        Returns:
            List of discovered test patterns with metadata
        """
        if not self.api_key:
            logger.warning("No Linkup API key available. Returning empty results.")
            return []

        # Check cache first
        cache_key = self._generate_cache_key(query, context, limit, include_code)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for query: {query}")
            return cached_result

        try:
            # Rate limiting
            self._enforce_rate_limit()

            # Build search parameters
            search_params = self._build_search_params(query, context, limit, include_code)

            # Make API request
            response = self._make_api_request('/search/patterns', search_params)

            # Process and transform results
            patterns = self._process_search_results(response, context)

            # Cache the results
            self._cache_result(cache_key, patterns)

            logger.info(f"Found {len(patterns)} external patterns for query: {query}")
            return patterns

        except Exception as e:
            logger.error(f"Error searching external patterns: {e}")
            return []

    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific pattern.

        Args:
            pattern_id: ID of the pattern to retrieve

        Returns:
            Detailed pattern information or None if not found
        """
        if not self.api_key:
            return None

        cache_key = f"pattern_detail:{pattern_id}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            self._enforce_rate_limit()

            response = self._make_api_request(f'/patterns/{pattern_id}')
            pattern_detail = self._process_pattern_detail(response)

            self._cache_result(cache_key, pattern_detail)
            return pattern_detail

        except Exception as e:
            logger.error(f"Error getting pattern details for {pattern_id}: {e}")
            return None

    def search_by_component_type(self,
                                component_type: str,
                                mlb_specific: bool = True) -> List[Dict[str, Any]]:
        """Search for patterns specific to a component type.

        Args:
            component_type: Type of UI component (button, list, webview, etc.)
            mlb_specific: Whether to include MLB-specific patterns

        Returns:
            List of component-specific test patterns
        """
        # Build component-specific query
        query_parts = [f"{component_type} testing", "UI automation"]

        if mlb_specific:
            query_parts.extend(["sports app testing", "mobile sports", "real-time data"])

        query = " ".join(query_parts)

        # Determine context based on component type
        context = self._determine_context_for_component(component_type)

        return self.search_test_patterns(query, context, limit=15)

    def get_trending_patterns(self,
                            time_period: str = 'week',
                            category: str = 'all') -> List[Dict[str, Any]]:
        """Get trending test patterns.

        Args:
            time_period: Time period for trends (day, week, month)
            category: Pattern category filter

        Returns:
            List of trending patterns
        """
        if not self.api_key:
            return []

        cache_key = f"trending:{time_period}:{category}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            self._enforce_rate_limit()

            params = {
                'period': time_period,
                'category': category,
                'limit': 10
            }

            response = self._make_api_request('/patterns/trending', params)
            patterns = self._process_search_results(response, 'general')

            # Cache with shorter TTL for trending data
            self._cache_result(cache_key, patterns, ttl=1800)  # 30 minutes

            return patterns

        except Exception as e:
            logger.error(f"Error getting trending patterns: {e}")
            return []

    def _generate_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_data = "|".join(str(arg) for arg in args)
        return f"linkup:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available."""
        if not self.cache:
            return None

        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    def _cache_result(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache result with TTL."""
        if not self.cache:
            return

        try:
            ttl = ttl or self.cache_ttl
            self.cache.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _build_search_params(self,
                           query: str,
                           context: str,
                           limit: int,
                           include_code: bool) -> Dict[str, Any]:
        """Build search parameters for API request."""
        params = {
            'q': query,
            'limit': limit,
            'include_code': include_code,
            'format': 'json'
        }

        # Add context-specific parameters
        if context in self.search_contexts:
            context_config = self.search_contexts[context]
            params['keywords'] = ','.join(context_config['keywords'])
            params['filters'] = ','.join(context_config['filters'])

        return params

    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Linkup service."""
        url = f"{self.base_url}{endpoint}"

        if params:
            # Use GET for search endpoints
            response = self.session.get(url, params=params, timeout=self.timeout)
        else:
            # Use GET for detail endpoints
            response = self.session.get(url, timeout=self.timeout)

        response.raise_for_status()
        return response.json()

    def _process_search_results(self, response: Dict[str, Any], context: str) -> List[Dict[str, Any]]:
        """Process and transform search results."""
        patterns = []

        # Handle different response formats
        results = response.get('results', response.get('patterns', []))

        for item in results:
            pattern = {
                'pattern_id': item.get('id', ''),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'source': 'linkup',
                'context': context,
                'quality_score': item.get('score', 0.0),
                'created_at': item.get('created_at', ''),
                'tags': item.get('tags', []),
                'complexity': self._assess_pattern_complexity(item),
                'code_example': item.get('code_example', ''),
                'framework': item.get('framework', ''),
                'language': item.get('language', 'python'),
                'external_url': item.get('url', ''),
                'author': item.get('author', ''),
                'votes': item.get('votes', 0),
                'usage_count': item.get('usage_count', 0)
            }

            # Add MLB-specific scoring
            pattern['mlb_relevance'] = self._calculate_mlb_relevance(pattern)

            patterns.append(pattern)

        # Sort by quality and relevance
        patterns.sort(key=lambda p: (p['quality_score'] + p['mlb_relevance']), reverse=True)

        return patterns

    def _process_pattern_detail(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process detailed pattern information."""
        return {
            'pattern_id': response.get('id', ''),
            'title': response.get('title', ''),
            'description': response.get('description', ''),
            'full_code': response.get('full_code', ''),
            'documentation': response.get('documentation', ''),
            'dependencies': response.get('dependencies', []),
            'test_cases': response.get('test_cases', []),
            'performance_notes': response.get('performance_notes', ''),
            'best_practices': response.get('best_practices', []),
            'related_patterns': response.get('related_patterns', []),
            'external_url': response.get('url', ''),
            'last_updated': response.get('last_updated', ''),
            'version': response.get('version', '1.0')
        }

    def _assess_pattern_complexity(self, pattern: Dict[str, Any]) -> str:
        """Assess pattern complexity based on various factors."""
        # Simple heuristic based on code length, dependencies, etc.
        code_length = len(pattern.get('code_example', ''))
        dependencies = len(pattern.get('dependencies', []))

        if code_length < 100 and dependencies < 2:
            return 'simple'
        elif code_length < 500 and dependencies < 5:
            return 'medium'
        else:
            return 'complex'

    def _calculate_mlb_relevance(self, pattern: Dict[str, Any]) -> float:
        """Calculate MLB-specific relevance score."""
        relevance = 0.0

        # Check for sports-related keywords
        sports_keywords = ['sports', 'mlb', 'baseball', 'game', 'score', 'player', 'team']
        text_to_check = f"{pattern['title']} {pattern['description']}".lower()

        for keyword in sports_keywords:
            if keyword in text_to_check:
                relevance += 0.1

        # Check for mobile/real-time keywords
        mobile_keywords = ['mobile', 'real-time', 'live', 'streaming', 'push']
        for keyword in mobile_keywords:
            if keyword in text_to_check:
                relevance += 0.05

        return min(relevance, 1.0)  # Cap at 1.0

    def _determine_context_for_component(self, component_type: str) -> str:
        """Determine search context based on component type."""
        mobile_components = ['button', 'list', 'navigation', 'modal', 'form']
        web_components = ['webview', 'chart', 'map']
        api_components = ['api_endpoint']

        if component_type in mobile_components:
            return 'mobile'
        elif component_type in web_components:
            return 'web'
        elif component_type in api_components:
            return 'api'
        else:
            return 'general'

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Linkup service."""
        status = {
            'api_available': bool(self.api_key),
            'cache_available': self.cache is not None,
            'last_request': self.last_request_time,
            'base_url': self.base_url
        }

        # Test API connectivity if key is available
        if self.api_key:
            try:
                self._make_api_request('/health')
                status['api_reachable'] = True
            except Exception:
                status['api_reachable'] = False
        else:
            status['api_reachable'] = False

        return status