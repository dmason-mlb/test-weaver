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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LinkupService:
    """Service for discovering external test patterns via Linkup API.

    Provides caching, retry logic, and intelligent pattern discovery
    for enhancing internal test pattern knowledge base.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: str = "https://api.linkup.so/v1",
                 cache_ttl: int = 3600,
                 max_retries: int = 3,
                 timeout: int = 30):
        """Initialize the Linkup service.

        Args:
            api_key: Linkup API key (or use LINKUP_API_KEY env var)
            base_url: Base URL for Linkup API (real endpoint: https://api.linkup.so/v1)
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
        """Search for external test patterns using Linkup web search.

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

            # Build web search query for test patterns
            search_query = self._build_web_search_query(query, context, include_code)

            # Build Linkup API parameters
            search_params = {
                "q": search_query,
                "depth": "standard",
                "outputType": "searchResults"
            }

            # Make API request to real Linkup search endpoint
            response = self._make_api_request('/search', search_params, method='POST')

            # Process and transform web results to test patterns
            patterns = self._process_web_search_results(response, context, limit)

            # Cache the results
            self._cache_result(cache_key, patterns)

            logger.info(f"Found {len(patterns)} external patterns for query: {query}")
            return patterns

        except Exception as e:
            logger.error(f"Error searching external patterns: {e}")
            return []

    # Note: get_pattern_details removed - was using fictional /patterns/{id} endpoint
    # Linkup API doesn't support individual pattern retrieval, only web search

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
        """Get trending test patterns using web search.

        Args:
            time_period: Time period for trends (day, week, month) - used to modify search query
            category: Pattern category filter

        Returns:
            List of trending patterns from web search
        """
        if not self.api_key:
            return []

        cache_key = f"trending:{time_period}:{category}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            self._enforce_rate_limit()

            # Build trending search query
            time_modifiers = {
                'day': 'latest',
                'week': 'recent',
                'month': 'current'
            }

            time_modifier = time_modifiers.get(time_period, 'latest')

            if category == 'all':
                search_query = f"{time_modifier} testing trends best practices automation patterns 2024"
            else:
                search_query = f"{time_modifier} {category} testing trends patterns automation"

            # Build Linkup API parameters
            search_params = {
                "q": search_query,
                "depth": "standard",
                "outputType": "searchResults"
            }

            response = self._make_api_request('/search', search_params, method='POST')
            patterns = self._process_web_search_results(response, category if category != 'all' else 'general', 10)

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

    # Note: _build_search_params removed - was for fictional pattern API
    # Now using _build_web_search_query for real Linkup web search

    def _build_web_search_query(self, query: str, context: str, include_code: bool) -> str:
        """Build web search query for finding test patterns online.

        Args:
            query: Base search query
            context: Search context (mobile, web, api, etc.)
            include_code: Whether to look for code examples

        Returns:
            Optimized search query for web search
        """
        # Start with base query
        search_terms = [query, "testing patterns", "best practices"]

        # Add context-specific keywords
        if context in self.search_contexts:
            context_keywords = self.search_contexts[context]['keywords']
            search_terms.extend(context_keywords[:2])  # Add top 2 context keywords

        # Add code-specific terms if requested
        if include_code:
            search_terms.extend(["examples", "code snippets", "automation"])

        # Add quality and source indicators
        search_terms.extend(["tutorial", "guide", "documentation"])

        return " ".join(search_terms)

    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None, method: str = 'GET') -> Dict[str, Any]:
        """Make API request to Linkup service."""
        url = f"{self.base_url}{endpoint}"

        if method.upper() == 'POST':
            # POST request with JSON body
            response = self.session.post(url, json=params, timeout=self.timeout)
        elif params:
            # GET request with query parameters
            response = self.session.get(url, params=params, timeout=self.timeout)
        else:
            # GET request without parameters
            response = self.session.get(url, timeout=self.timeout)

        response.raise_for_status()
        return response.json()

    def _process_web_search_results(self, response: Dict[str, Any], context: str, limit: int) -> List[Dict[str, Any]]:
        """Process and transform web search results to test patterns."""
        patterns = []

        # Handle Linkup search response format
        results = response.get('results', [])

        for i, item in enumerate(results[:limit]):
            # Extract relevant information from web search result
            pattern = {
                'pattern_id': f"linkup_web_{i}_{hash(item.get('url', '')) % 10000}",
                'title': item.get('name', '').strip(),  # Linkup uses 'name' not 'title'
                'description': item.get('content', '')[:500],  # Linkup uses 'content'
                'source': 'linkup_web_search',
                'context': context,
                'quality_score': self._calculate_web_relevance_score(item, context),
                'created_at': '',  # Web results don't have creation dates
                'tags': self._extract_tags_from_content(item, context),
                'complexity': self._assess_web_content_complexity(item),
                'code_example': self._extract_code_from_content(item),
                'framework': self._infer_framework_from_content(item),
                'language': self._infer_language_from_content(item),
                'external_url': item.get('url', ''),
                'url': item.get('url', ''),  # Also include for test compatibility
                'author': self._extract_author_from_url(item.get('url', '')),
                'votes': 0,  # Web results don't have vote counts
                'usage_count': 0
            }

            # Add MLB-specific scoring
            pattern['mlb_relevance'] = self._calculate_mlb_relevance(pattern)

            patterns.append(pattern)

        # Sort by quality and relevance
        patterns.sort(key=lambda p: (p['quality_score'] + p['mlb_relevance']), reverse=True)

        return patterns

    def _calculate_web_relevance_score(self, item: Dict[str, Any], context: str) -> float:
        """Calculate relevance score for web search result."""
        score = 0.5  # Base score

        title = item.get('name', '').lower()  # Linkup uses 'name'
        content = item.get('content', '').lower()  # Linkup uses 'content'
        url = item.get('url', '').lower()

        # Boost for testing-related terms
        testing_terms = ['test', 'testing', 'automation', 'qa', 'quality']
        for term in testing_terms:
            if term in title:
                score += 0.1
            if term in content:
                score += 0.05

        # Context-specific boosts
        if context in self.search_contexts:
            for keyword in self.search_contexts[context]['keywords']:
                if keyword.lower() in title:
                    score += 0.15
                if keyword.lower() in content:
                    score += 0.1

        # Authority site boost
        authority_domains = ['github.com', 'stackoverflow.com', 'medium.com', 'dev.to', 'testing-', 'qa-']
        for domain in authority_domains:
            if domain in url:
                score += 0.2
                break

        return min(score, 1.0)

    def _extract_tags_from_content(self, item: Dict[str, Any], context: str) -> List[str]:
        """Extract relevant tags from web content."""
        tags = [context]

        content = f"{item.get('name', '')} {item.get('content', '')}".lower()

        # Common testing-related tags
        tag_keywords = {
            'selenium': 'selenium',
            'cypress': 'cypress',
            'playwright': 'playwright',
            'jest': 'jest',
            'pytest': 'pytest',
            'junit': 'junit',
            'automation': 'automation',
            'ui': 'ui-testing',
            'api': 'api-testing',
            'unit': 'unit-testing',
            'integration': 'integration-testing',
            'e2e': 'e2e-testing'
        }

        for keyword, tag in tag_keywords.items():
            if keyword in content:
                tags.append(tag)

        return list(set(tags))  # Remove duplicates

    def _assess_web_content_complexity(self, item: Dict[str, Any]) -> str:
        """Assess complexity of testing content."""
        content = f"{item.get('name', '')} {item.get('content', '')}".lower()

        # Simple indicators
        simple_terms = ['basic', 'simple', 'intro', 'beginner', 'getting started']
        complex_terms = ['advanced', 'complex', 'enterprise', 'scalable', 'architecture']

        simple_count = sum(1 for term in simple_terms if term in content)
        complex_count = sum(1 for term in complex_terms if term in content)

        if complex_count > simple_count:
            return 'complex'
        elif simple_count > 0:
            return 'simple'
        else:
            return 'medium'

    def _extract_code_from_content(self, item: Dict[str, Any]) -> str:
        """Extract code examples from content if available."""
        content = item.get('content', '')

        # Look for code indicators
        if any(indicator in content.lower() for indicator in ['```', 'def ', 'function', 'class ', 'test_']):
            return content[:200]  # Return snippet that might contain code

        return ''

    def _infer_framework_from_content(self, item: Dict[str, Any]) -> str:
        """Infer testing framework from content."""
        content = f"{item.get('name', '')} {item.get('content', '')}".lower()

        frameworks = {
            'selenium': 'selenium',
            'cypress': 'cypress',
            'playwright': 'playwright',
            'jest': 'jest',
            'pytest': 'pytest',
            'junit': 'junit',
            'testng': 'testng',
            'mocha': 'mocha',
            'jasmine': 'jasmine'
        }

        for fw_name, fw_value in frameworks.items():
            if fw_name in content:
                return fw_value

        return 'unknown'

    def _infer_language_from_content(self, item: Dict[str, Any]) -> str:
        """Infer programming language from content."""
        content = f"{item.get('name', '')} {item.get('content', '')}".lower()
        url = item.get('url', '').lower()

        # Language indicators
        if any(term in content for term in ['python', 'pytest', '.py']):
            return 'python'
        elif any(term in content for term in ['javascript', 'js', 'node', 'npm']):
            return 'javascript'
        elif any(term in content for term in ['java', 'junit', '.java']):
            return 'java'
        elif any(term in content for term in ['c#', 'csharp', '.net', 'nunit']):
            return 'csharp'
        elif any(term in content for term in ['ruby', 'rspec', '.rb']):
            return 'ruby'

        return 'unknown'

    def _extract_author_from_url(self, url: str) -> str:
        """Extract author/source from URL."""
        if 'github.com' in url:
            parts = url.split('/')
            if len(parts) > 3:
                return parts[3]  # GitHub username
        elif 'stackoverflow.com' in url:
            return 'Stack Overflow Community'
        elif 'medium.com' in url:
            return 'Medium Author'

        return 'Unknown'

    # Note: _process_pattern_detail removed - was for fictional pattern detail API
    # Linkup only provides web search results, not detailed pattern objects

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
        """Get health status of Linkup service using real API endpoint."""
        status = {
            'api_available': bool(self.api_key),
            'cache_available': self.cache is not None,
            'last_request': self.last_request_time,
            'base_url': self.base_url
        }

        # Test API connectivity using real /credits/balance endpoint
        if self.api_key:
            try:
                self._make_api_request('/credits/balance')
                status['api_reachable'] = True
            except Exception:
                status['api_reachable'] = False
        else:
            status['api_reachable'] = False

        return status