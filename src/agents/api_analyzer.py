from typing import Dict, List, Any, Optional, Union
import logging
import json
import re
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class APIAnalyzerAgent:
    """Agent responsible for analyzing API endpoints for MLB's server-driven UI.

    Analyzes:
    - GraphQL queries and mutations for Fastball Gateway
    - REST API endpoints structure and responses
    - Response schema validation
    - Performance characteristics
    - Error handling patterns
    """

    def __init__(self, base_url: Optional[str] = None, auth_config: Optional[Dict] = None):
        """Initialize the API Analyzer Agent.

        Args:
            base_url: Base URL for MLB APIs (defaults to Fastball Gateway)
            auth_config: Authentication configuration for API calls
        """
        self.base_url = base_url or "https://fastball-gateway.mlb.com"
        self.auth_config = auth_config or {}
        self.graphql_schema_cache = {}
        self.pattern_search_tool = self._initialize_pattern_search()

        # Initialize CrewAI agent
        self.agent = Agent(
            role="API Endpoint Analyzer",
            goal="Analyze API endpoints for test generation and validate response patterns",
            backstory="Expert in GraphQL, REST APIs, and MLB's Fastball Gateway with deep knowledge of sports data schemas.",
            verbose=True,
            allow_delegation=False
        )

    def analyze_endpoint(self, endpoint: Union[str, Dict], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze an API endpoint for test generation.

        Args:
            endpoint: Endpoint URL string or endpoint configuration dict
            context: Optional context about the component using this endpoint

        Returns:
            Dict containing analysis results with test patterns and recommendations
        """
        if not endpoint:
            raise ValueError("Endpoint cannot be None or empty")

        # Handle both string URLs and endpoint config dicts
        if isinstance(endpoint, str):
            endpoint_config = {'url': endpoint, 'method': 'GET'}
        elif isinstance(endpoint, dict):
            endpoint_config = endpoint
        else:
            raise ValueError("Endpoint must be string URL or configuration dict")

        analysis_result = {
            'endpoint_url': endpoint_config.get('url', ''),
            'method': endpoint_config.get('method', 'GET').upper(),
            'is_graphql': self._is_graphql_endpoint(endpoint_config.get('url', '')),
            'analysis_status': 'success',
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'test_patterns': [],
            'response_schema': {},
            'performance_metrics': {},
            'security_considerations': []
        }

        try:
            # Analyze endpoint based on type
            if analysis_result['is_graphql']:
                self._analyze_graphql_endpoint(endpoint_config, analysis_result, context)
            else:
                self._analyze_rest_endpoint(endpoint_config, analysis_result, context)

            # Generate test patterns
            self._generate_test_patterns(endpoint_config, analysis_result, context)

            # Performance analysis
            self._analyze_performance(endpoint_config, analysis_result)

            # Security analysis
            self._analyze_security(endpoint_config, analysis_result)

            logger.info(f"Analyzed endpoint {endpoint_config.get('url', 'unknown')}: {analysis_result['analysis_status']}")

        except Exception as e:
            analysis_result['analysis_status'] = 'error'
            analysis_result['errors'].append(f"Analysis error: {str(e)}")
            logger.error(f"Error analyzing endpoint {endpoint_config.get('url', 'unknown')}: {e}")

        return analysis_result

    def _analyze_graphql_endpoint(self, endpoint_config: Dict, result: Dict, context: Optional[Dict]) -> None:
        """Analyze GraphQL endpoint specifics."""
        url = endpoint_config.get('url', '')
        query = endpoint_config.get('query', '')
        variables = endpoint_config.get('variables', {})

        # Validate GraphQL query structure
        if not query and not endpoint_config.get('introspection', False):
            result['errors'].append("GraphQL endpoint missing query or introspection flag")
            return

        # Parse GraphQL query
        if query:
            query_analysis = self._parse_graphql_query(query)
            result['query_analysis'] = query_analysis

            # Validate against known MLB schema patterns
            self._validate_mlb_graphql_patterns(query_analysis, result)

        # Schema analysis
        self._analyze_graphql_schema(url, result)

        # Variable validation
        if variables:
            self._validate_graphql_variables(query, variables, result)

    def _analyze_rest_endpoint(self, endpoint_config: Dict, result: Dict, context: Optional[Dict]) -> None:
        """Analyze REST endpoint specifics."""
        url = endpoint_config.get('url', '')
        method = endpoint_config.get('method', 'GET')
        headers = endpoint_config.get('headers', {})
        params = endpoint_config.get('params', {})

        # URL structure analysis
        parsed_url = urlparse(url)
        result['url_analysis'] = {
            'scheme': parsed_url.scheme,
            'domain': parsed_url.netloc,
            'path': parsed_url.path,
            'path_segments': [seg for seg in parsed_url.path.split('/') if seg],
            'query_params': params
        }

        # Validate REST conventions
        self._validate_rest_conventions(url, method, result)

        # MLB-specific endpoint patterns
        self._validate_mlb_rest_patterns(url, result)

        # Header analysis
        if headers:
            self._analyze_headers(headers, result)

    def _generate_test_patterns(self, endpoint_config: Dict, result: Dict, context: Optional[Dict]) -> None:
        """Generate test patterns based on endpoint analysis."""
        url = endpoint_config.get('url', '')
        method = endpoint_config.get('method', 'GET')

        # Basic happy path test
        result['test_patterns'].append({
            'name': 'happy_path_test',
            'description': f"Test successful {method} request to {url}",
            'type': 'positive',
            'test_code': self._generate_happy_path_test(endpoint_config)
        })

        # Error handling tests
        error_tests = self._generate_error_tests(endpoint_config)
        result['test_patterns'].extend(error_tests)

        # Performance tests
        if context and context.get('performance_critical', False):
            perf_tests = self._generate_performance_tests(endpoint_config)
            result['test_patterns'].extend(perf_tests)

        # Security tests
        security_tests = self._generate_security_tests(endpoint_config)
        result['test_patterns'].extend(security_tests)

        # MLB-specific tests
        mlb_tests = self._generate_mlb_specific_tests(endpoint_config, context)
        result['test_patterns'].extend(mlb_tests)

    def _parse_graphql_query(self, query: str) -> Dict[str, Any]:
        """Parse GraphQL query to extract structure and fields."""
        query_analysis = {
            'operation_type': 'query',  # Default
            'operation_name': None,
            'fields': [],
            'fragments': [],
            'variables': [],
            'directives': []
        }

        # Extract operation type (query, mutation, subscription)
        operation_match = re.search(r'(query|mutation|subscription)\s+(\w+)?\s*\(', query, re.IGNORECASE)
        if operation_match:
            query_analysis['operation_type'] = operation_match.group(1).lower()
            if operation_match.group(2):
                query_analysis['operation_name'] = operation_match.group(2)

        # Extract field selections (simplified parsing)
        field_pattern = r'(\w+)\s*(?:\([^)]*\))?\s*{'
        fields = re.findall(field_pattern, query)
        query_analysis['fields'] = fields

        # Extract variables
        var_pattern = r'\$(\w+):\s*(\w+(?:\!)?)'
        variables = re.findall(var_pattern, query)
        query_analysis['variables'] = [{'name': var[0], 'type': var[1]} for var in variables]

        return query_analysis

    def _validate_mlb_graphql_patterns(self, query_analysis: Dict, result: Dict) -> None:
        """Validate GraphQL query against known MLB patterns."""
        operation_type = query_analysis.get('operation_type', '')
        fields = query_analysis.get('fields', [])

        # Check for common MLB entity fields
        mlb_entities = ['team', 'player', 'game', 'season', 'stats', 'schedule']
        has_mlb_entity = any(entity in field.lower() for field in fields for entity in mlb_entities)

        if not has_mlb_entity:
            result['warnings'].append("Query doesn't appear to request common MLB entities")

        # Validate required fields for game data
        if 'game' in ' '.join(fields).lower():
            required_game_fields = ['id', 'gameDate', 'teams']
            # This is a simplified check - real implementation would parse the full query structure
            result['recommendations'].append("Ensure game queries include id, gameDate, and teams fields")

    def _validate_rest_conventions(self, url: str, method: str, result: Dict) -> None:
        """Validate REST API conventions."""
        parsed_url = urlparse(url)
        path_segments = [seg for seg in parsed_url.path.split('/') if seg]

        # Check for versioning
        has_version = any(seg.startswith('v') and seg[1:].isdigit() for seg in path_segments)
        if not has_version:
            result['recommendations'].append("Consider including API version in URL path")

        # Check for resource naming conventions
        if len(path_segments) > 0:
            last_segment = path_segments[-1]
            # Check for plural resources for GET requests
            if method == 'GET' and not last_segment.endswith('s') and not last_segment.isdigit():
                result['recommendations'].append("Consider using plural nouns for collection resources")

        # Check HTTPS
        if parsed_url.scheme != 'https':
            result['warnings'].append("Consider using HTTPS for secure communication")

    def _validate_mlb_rest_patterns(self, url: str, result: Dict) -> None:
        """Validate REST endpoint against MLB-specific patterns."""
        # Check for MLB domain patterns
        if 'mlb.com' not in url and 'mlbstatic.com' not in url:
            result['warnings'].append("Endpoint doesn't appear to be from MLB domain")

        # Check for common MLB API patterns
        mlb_patterns = [
            r'/api/v\d+/teams?',
            r'/api/v\d+/games?',
            r'/api/v\d+/players?',
            r'/api/v\d+/stats',
            r'/api/v\d+/schedule'
        ]

        matches_pattern = any(re.search(pattern, url) for pattern in mlb_patterns)
        if not matches_pattern:
            result['recommendations'].append("Consider following MLB API path conventions")

    def _generate_happy_path_test(self, endpoint_config: Dict) -> str:
        """Generate happy path test code."""
        url = endpoint_config.get('url', '')
        method = endpoint_config.get('method', 'GET')

        if endpoint_config.get('query'):  # GraphQL
            return f'''
def test_graphql_happy_path():
    """Test successful GraphQL query execution."""
    query = """{endpoint_config.get('query', '')}"""
    variables = {endpoint_config.get('variables', {})}

    response = requests.post(
        "{url}",
        json={{"query": query, "variables": variables}},
        headers={{"Content-Type": "application/json"}}
    )

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    assert "data" in data
    assert data["data"] is not None
'''
        else:  # REST
            return f'''
def test_rest_happy_path():
    """Test successful {method} request."""
    response = requests.{method.lower()}("{url}")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")

    data = response.json()
    assert isinstance(data, (dict, list))
'''

    def _generate_error_tests(self, endpoint_config: Dict) -> List[Dict]:
        """Generate error handling test patterns."""
        url = endpoint_config.get('url', '')

        error_tests = [
            {
                'name': 'test_404_handling',
                'description': 'Test handling of not found errors',
                'type': 'negative',
                'test_code': f'''
def test_404_handling():
    """Test API response to non-existent resource."""
    invalid_url = "{url}/nonexistent"
    response = requests.get(invalid_url)

    assert response.status_code == 404
    # Verify error response format
    if response.headers.get("content-type", "").startswith("application/json"):
        error_data = response.json()
        assert "error" in error_data or "message" in error_data
'''
            },
            {
                'name': 'test_timeout_handling',
                'description': 'Test handling of request timeouts',
                'type': 'negative',
                'test_code': f'''
def test_timeout_handling():
    """Test API response timeout handling."""
    try:
        response = requests.get("{url}", timeout=0.001)
        # If we get here, the request was faster than expected
        assert response.status_code in [200, 404, 500]
    except requests.exceptions.Timeout:
        # This is expected for very short timeout
        pass
'''
            }
        ]

        return error_tests

    def _generate_performance_tests(self, endpoint_config: Dict) -> List[Dict]:
        """Generate performance test patterns."""
        url = endpoint_config.get('url', '')

        return [{
            'name': 'test_response_time',
            'description': 'Test API response time performance',
            'type': 'performance',
            'test_code': f'''
def test_response_time():
    """Test API response time is within acceptable limits."""
    import time

    start_time = time.time()
    response = requests.get("{url}")
    end_time = time.time()

    response_time = end_time - start_time

    assert response.status_code == 200
    assert response_time < 2.0, f"Response time {{response_time:.2f}}s exceeds 2s limit"

    # Log performance metrics
    print(f"Response time: {{response_time:.3f}}s")
'''
        }]

    def _generate_security_tests(self, endpoint_config: Dict) -> List[Dict]:
        """Generate security test patterns."""
        return [{
            'name': 'test_security_headers',
            'description': 'Test presence of security headers',
            'type': 'security',
            'test_code': f'''
def test_security_headers():
    """Test API includes important security headers."""
    response = requests.get("{endpoint_config.get('url', '')}")

    # Check for security headers
    security_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection"
    ]

    missing_headers = []
    for header in security_headers:
        if header not in response.headers:
            missing_headers.append(header)

    if missing_headers:
        print(f"Missing security headers: {{missing_headers}}")

    # HTTPS check
    assert response.url.startswith("https://"), "API should use HTTPS"
'''
        }]

    def _generate_mlb_specific_tests(self, endpoint_config: Dict, context: Optional[Dict]) -> List[Dict]:
        """Generate MLB-specific test patterns."""
        tests = []

        # Team data validation
        if 'team' in endpoint_config.get('url', '').lower():
            tests.append({
                'name': 'test_team_data_structure',
                'description': 'Test team data includes required MLB fields',
                'type': 'domain_specific',
                'test_code': f'''
def test_team_data_structure():
    """Test team data contains required MLB fields."""
    response = requests.get("{endpoint_config.get('url', '')}")
    assert response.status_code == 200

    data = response.json()

    # For team data, expect certain fields
    if isinstance(data, dict) and "teams" in data:
        teams = data["teams"]
    elif isinstance(data, list):
        teams = data
    else:
        teams = [data]

    for team in teams[:1]:  # Check first team
        required_fields = ["id", "name", "abbreviation"]
        for field in required_fields:
            assert field in team, f"Team missing required field: {{field}}"
'''
            })

        # Game data validation
        if 'game' in endpoint_config.get('url', '').lower() or 'schedule' in endpoint_config.get('url', '').lower():
            tests.append({
                'name': 'test_game_data_structure',
                'description': 'Test game data includes required MLB fields',
                'type': 'domain_specific',
                'test_code': f'''
def test_game_data_structure():
    """Test game data contains required MLB fields."""
    response = requests.get("{endpoint_config.get('url', '')}")
    assert response.status_code == 200

    data = response.json()

    # For game data, expect certain fields
    if isinstance(data, dict) and "games" in data:
        games = data["games"]
    elif isinstance(data, list):
        games = data
    else:
        games = [data]

    for game in games[:1]:  # Check first game
        required_fields = ["gamePk", "gameDate", "teams"]
        for field in required_fields:
            assert field in game, f"Game missing required field: {{field}}"

        # Validate teams structure
        if "teams" in game:
            assert "home" in game["teams"]
            assert "away" in game["teams"]
'''
            })

        return tests

    def _analyze_performance(self, endpoint_config: Dict, result: Dict) -> None:
        """Analyze performance characteristics of the endpoint."""
        # This would typically involve making actual requests and measuring performance
        # For now, provide static analysis based on URL patterns

        url = endpoint_config.get('url', '')

        result['performance_metrics'] = {
            'estimated_complexity': 'medium',
            'caching_recommended': True,
            'rate_limiting_needed': True
        }

        # GraphQL queries are typically more complex
        if result.get('is_graphql', False):
            result['performance_metrics']['estimated_complexity'] = 'high'
            result['recommendations'].append("Consider query complexity analysis for GraphQL")

        # Large data endpoints need special handling
        if any(keyword in url.lower() for keyword in ['stats', 'schedule', 'games']):
            result['recommendations'].append("Consider pagination for large datasets")

    def _analyze_security(self, endpoint_config: Dict, result: Dict) -> None:
        """Analyze security considerations for the endpoint."""
        url = endpoint_config.get('url', '')

        # Check URL scheme
        if not url.startswith('https://'):
            result['security_considerations'].append("Endpoint should use HTTPS")

        # Check for potential sensitive data
        sensitive_patterns = ['player', 'user', 'profile', 'personal']
        if any(pattern in url.lower() for pattern in sensitive_patterns):
            result['security_considerations'].append("Endpoint may contain sensitive data - ensure proper authentication")

        # Check authentication requirements
        if endpoint_config.get('requires_auth', False):
            result['security_considerations'].append("Endpoint requires authentication - verify token validation")

    def _analyze_graphql_schema(self, url: str, result: Dict) -> None:
        """Analyze GraphQL schema if available."""
        # This would typically involve introspection query
        # For now, provide basic schema structure expectations

        result['response_schema'] = {
            'type': 'graphql',
            'expected_structure': {
                'data': 'object',
                'errors': 'array (optional)',
                'extensions': 'object (optional)'
            }
        }

    def _validate_graphql_variables(self, query: str, variables: Dict, result: Dict) -> None:
        """Validate GraphQL variables against query requirements."""
        # Extract variable definitions from query
        var_pattern = r'\$(\w+):\s*(\w+(?:\!)?)'
        query_vars = re.findall(var_pattern, query)

        defined_vars = {var[0] for var in query_vars}
        provided_vars = set(variables.keys())

        # Check for missing required variables
        missing_vars = defined_vars - provided_vars
        if missing_vars:
            result['errors'].append(f"Missing required variables: {list(missing_vars)}")

        # Check for unused variables
        unused_vars = provided_vars - defined_vars
        if unused_vars:
            result['warnings'].append(f"Unused variables provided: {list(unused_vars)}")

    def _analyze_headers(self, headers: Dict, result: Dict) -> None:
        """Analyze request headers."""
        # Check for important headers
        important_headers = ['Content-Type', 'Authorization', 'User-Agent']

        for header in important_headers:
            if header not in headers and header.lower() not in headers:
                result['recommendations'].append(f"Consider including {header} header")

    def _is_graphql_endpoint(self, url: str) -> bool:
        """Determine if endpoint is GraphQL based on URL patterns."""
        graphql_indicators = ['/graphql', '/query', '/api/graphql']
        return any(indicator in url.lower() for indicator in graphql_indicators)

    def _initialize_pattern_search(self):
        """Initialize pattern search tool for analysis."""
        # This would typically integrate with the pattern discovery system
        return {
            'search_patterns': self._search_api_patterns,
            'validate_pattern': self._validate_api_pattern
        }

    def _search_api_patterns(self, endpoint_type: str) -> List[Dict]:
        """Search for similar API patterns."""
        # This would integrate with the pattern discovery agent
        # For now, return static patterns based on type

        if endpoint_type == 'team':
            return [{
                'pattern_name': 'mlb_team_endpoint',
                'expected_fields': ['id', 'name', 'abbreviation', 'division'],
                'test_strategy': 'validate_team_structure'
            }]
        elif endpoint_type == 'game':
            return [{
                'pattern_name': 'mlb_game_endpoint',
                'expected_fields': ['gamePk', 'gameDate', 'teams', 'status'],
                'test_strategy': 'validate_game_structure'
            }]

        return []

    def _validate_api_pattern(self, pattern: Dict, endpoint_config: Dict) -> bool:
        """Validate endpoint against a known pattern."""
        # This would perform actual pattern validation
        return True

    def analyze_batch_endpoints(self, endpoints: List[Union[str, Dict]], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze multiple endpoints and provide aggregate insights.

        Args:
            endpoints: List of endpoint URLs or configurations
            context: Optional context for the batch analysis

        Returns:
            Aggregate analysis results with patterns and recommendations
        """
        batch_result = {
            'total_endpoints': len(endpoints),
            'analyzed_endpoints': 0,
            'failed_analyses': 0,
            'endpoint_results': [],
            'aggregate_patterns': [],
            'common_issues': [],
            'batch_recommendations': []
        }

        # Analyze each endpoint
        for endpoint in endpoints:
            try:
                endpoint_result = self.analyze_endpoint(endpoint, context)
                batch_result['endpoint_results'].append(endpoint_result)
                batch_result['analyzed_endpoints'] += 1
            except Exception as e:
                batch_result['failed_analyses'] += 1
                batch_result['endpoint_results'].append({
                    'endpoint': str(endpoint),
                    'error': str(e),
                    'analysis_status': 'failed'
                })

        # Generate aggregate insights
        self._generate_aggregate_insights(batch_result)

        return batch_result

    def _generate_aggregate_insights(self, batch_result: Dict) -> None:
        """Generate insights from batch endpoint analysis."""
        successful_results = [r for r in batch_result['endpoint_results']
                            if r.get('analysis_status') == 'success']

        if not successful_results:
            return

        # Find common patterns
        all_patterns = []
        all_errors = []
        all_warnings = []

        for result in successful_results:
            all_patterns.extend(result.get('test_patterns', []))
            all_errors.extend(result.get('errors', []))
            all_warnings.extend(result.get('warnings', []))

        # Count pattern frequencies
        from collections import Counter
        pattern_types = Counter(p.get('type', 'unknown') for p in all_patterns)
        common_errors = Counter(all_errors)
        common_warnings = Counter(all_warnings)

        batch_result['aggregate_patterns'] = [
            {'pattern_type': ptype, 'frequency': count}
            for ptype, count in pattern_types.most_common()
        ]

        batch_result['common_issues'] = {
            'frequent_errors': dict(common_errors.most_common(5)),
            'frequent_warnings': dict(common_warnings.most_common(5))
        }

        # Generate batch recommendations
        if len(successful_results) > 1:
            batch_result['batch_recommendations'].extend([
                "Consider implementing consistent error handling across all endpoints",
                "Standardize response formats for better client integration",
                "Implement comprehensive logging for API monitoring"
            ])

        graphql_count = sum(1 for r in successful_results if r.get('is_graphql', False))
        if graphql_count > 0 and graphql_count < len(successful_results):
            batch_result['batch_recommendations'].append(
                "Mixed GraphQL/REST usage detected - consider API consistency strategy"
            )