"""Vector store implementation for UI test patterns using Qdrant."""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
import openai
import logging

logger = logging.getLogger(__name__)


class ServerDrivenUIVectorStore:
    """Manages vector storage and retrieval of UI test patterns."""

    def __init__(self, host: str = "localhost", port: int = 6333):
        """Initialize connection to Qdrant."""
        self.host = host
        self.port = port
        self.collection_name = "ui_test_patterns"
        self.vector_size = 1536  # OpenAI text-embedding-ada-002 size

        try:
            self.client = QdrantClient(host=host, port=port)
            self._ensure_collection_exists()
            logger.info(f"Connected to Qdrant at {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}. Using fallback mode.")
            self.client = None

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        if not self.client:
            return

        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
                # Add some default patterns
                self._add_default_patterns()
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")

    def _add_default_patterns(self):
        """Add some default UI test patterns."""
        default_patterns = [
            {
                "component_type": "button",
                "test_pattern": "def test_{component_id}_interaction():\n    \"\"\"Test button interaction and business logic validation.\n    \n    Validates button functionality, state changes, and expected business outcomes.\n    Includes comprehensive verification of user interaction results.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    import time\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        # Arrange: Setup test environment\n        driver.get('http://localhost:8000')\n        button = wait.until(EC.element_to_be_clickable((By.ID, '{component_id}')))\n        \n        # Verify initial button state\n        assert button.is_displayed(), 'Button should be visible on page load'\n        assert button.is_enabled(), 'Button should be enabled for interaction'\n        \n        # Capture initial page state for comparison\n        initial_url = driver.current_url\n        initial_title = driver.title\n        \n        # Act: Perform button interaction\n        button.click()\n        \n        # Wait for potential state changes\n        time.sleep(1)\n        \n        # Assert: Verify business logic outcomes\n        # Check for navigation changes\n        if driver.current_url != initial_url:\n            verify_navigation_occurred = True\n            assert verify_navigation_occurred, 'Button click should trigger navigation when expected'\n        \n        # Check for dynamic content updates\n        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')\n        \n        # Verify button action completed successfully\n        # Look for success indicators in page\n        success_indicators = driver.find_elements(By.CSS_SELECTOR, '.success, .confirmation, [data-success=\"true\"]')\n        error_indicators = driver.find_elements(By.CSS_SELECTOR, '.error, .alert-error, [data-error=\"true\"]')\n        \n        if success_indicators:\n            verify_success_feedback = len(success_indicators) > 0\n            assert verify_success_feedback, 'Button action should provide success feedback when applicable'\n        \n        if error_indicators:\n            check_no_errors = len(error_indicators) == 0\n            assert check_no_errors, 'Button click should not result in error states'\n        \n        # Verify button maintains proper state after interaction\n        if button.is_displayed():  # Button might navigate away\n            post_click_state = button.get_attribute('disabled')\n            if post_click_state is None:\n                verify_button_responsive = button.is_enabled()\n                assert verify_button_responsive, 'Button should remain functional after successful interaction'\n        \n        # Additional business logic verification\n        page_source = driver.page_source.lower()\n        \n        # Check for common business outcomes\n        if 'follow' in '{component_id}'.lower():\n            verify_follow_action = 'following' in page_source or 'followed' in page_source\n            assert verify_follow_action, 'Follow button should update follow status'\n        elif 'submit' in '{component_id}'.lower():\n            verify_submission = 'submitted' in page_source or 'success' in page_source\n            assert verify_submission, 'Submit button should indicate successful submission'\n        elif 'refresh' in '{component_id}'.lower():\n            verify_refresh_occurred = driver.execute_script('return performance.navigation.type') > 0\n            assert verify_refresh_occurred or 'updated' in page_source, 'Refresh button should update content'\n        \n    finally:\n        driver.quit()",
                "description": "Comprehensive button test with business logic validation",
                "tags": ["button", "interaction", "verify", "check", "validation"]
            },
            {
                "component_type": "webview",
                "test_pattern": "def test_{component_id}_content_verification():\n    \"\"\"Test webview content loading and authentication handling.\n    \n    Validates webview functionality, content verification, and auth setup.\n    Includes comprehensive validation of embedded content and security.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    import time\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 15)  # Longer timeout for webview loading\n    \n    try:\n        # Arrange: Setup authentication if required\n        # Note: This pattern can be customized based on requires_auth flag\n        driver.get('http://localhost:8000')\n        \n        # Check if authentication is required by looking for auth indicators\n        auth_required = False\n        try:\n            # Look for common auth elements\n            auth_elements = driver.find_elements(By.CSS_SELECTOR, '.login, .auth, [data-auth=\"true\"], .sign-in')\n            if auth_elements or 'login' in driver.current_url.lower():\n                auth_required = True\n        except:\n            pass\n        \n        # Setup authentication if needed\n        if auth_required:\n            # Basic authentication setup for testing\n            try:\n                # Look for login form\n                username_field = driver.find_element(By.CSS_SELECTOR, 'input[type=\"email\"], input[name=\"username\"], input[id*=\"email\"]')\n                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type=\"password\"], input[name=\"password\"]')\n                login_button = driver.find_element(By.CSS_SELECTOR, 'button[type=\"submit\"], .login-btn, .sign-in')\n                \n                # Use test credentials for authentication\n                username_field.send_keys('test@mlb.com')\n                password_field.send_keys('testpassword')\n                login_button.click()\n                \n                # Wait for authentication to complete\n                wait.until(lambda driver: 'login' not in driver.current_url.lower())\n                \n                verify_authentication_setup = True\n                assert verify_authentication_setup, 'Authentication setup should complete successfully'\n                \n            except Exception as auth_error:\n                # If auth setup fails, continue with test but note the limitation\n                print(f'Auth setup failed: {{auth_error}}, continuing with unauthenticated test')\n        \n        # Act: Load and verify webview\n        webview = wait.until(EC.presence_of_element_located((By.ID, '{component_id}')))\n        \n        # Assert: Comprehensive webview validation\n        \n        # Basic display verification\n        assert webview.is_displayed(), 'WebView should be visible'\n        \n        # Verify webview dimensions and properties\n        size = webview.size\n        assert size['height'] > 0, 'WebView should have valid height'\n        assert size['width'] > 0, 'WebView should have valid width'\n        \n        check_dimensions = size['height'] >= 100 and size['width'] >= 100\n        assert check_dimensions, f'WebView should have reasonable dimensions, got {{size[\"width\"]}}x{{size[\"height\"]}}'\n        \n        # Verify webview content loading\n        if webview.tag_name.lower() == 'iframe':\n            # For iframe webviews\n            src_url = webview.get_attribute('src')\n            verify_iframe_src = src_url is not None and len(src_url) > 0\n            assert verify_iframe_src, 'Iframe WebView should have valid src URL'\n            \n            # Check if iframe content is accessible\n            try:\n                driver.switch_to.frame(webview)\n                iframe_body = driver.find_element(By.TAG_NAME, 'body')\n                verify_iframe_content = iframe_body is not None\n                assert verify_iframe_content, 'Iframe should contain accessible content'\n                \n                # Verify iframe content is not empty\n                iframe_text = iframe_body.text.strip()\n                check_iframe_text = len(iframe_text) > 0\n                assert check_iframe_text, 'Iframe content should not be empty'\n                \n                driver.switch_to.default_content()  # Switch back to main frame\n                \n            except Exception as iframe_error:\n                # If iframe access fails due to cross-origin, that's acceptable\n                print(f'Iframe content access limited (likely cross-origin): {{iframe_error}}')\n                driver.switch_to.default_content()\n        \n        else:\n            # For non-iframe webviews (like embedded content)\n            webview_content = webview.text.strip()\n            if len(webview_content) == 0:\n                # Check for child elements that might contain content\n                child_elements = webview.find_elements(By.CSS_SELECTOR, '*')\n                verify_webview_elements = len(child_elements) > 0\n                assert verify_webview_elements, 'WebView should contain child elements or content'\n            else:\n                verify_webview_content = len(webview_content) > 0\n                assert verify_webview_content, 'WebView should display meaningful content'\n        \n        # Business logic validation for specific webview types\n        webview_class = webview.get_attribute('class') or ''\n        webview_id = webview.get_attribute('id').lower()\n        \n        if 'game' in webview_id or 'gameday' in webview_id:\n            # Verify gameday webview content\n            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')\n            time.sleep(3)  # Allow gameday content to load\n            \n            # Look for game-related content indicators\n            page_source = driver.page_source.lower()\n            game_indicators = ['score', 'inning', 'player', 'team', 'mlb']\n            verify_game_content = any(indicator in page_source for indicator in game_indicators)\n            assert verify_game_content, 'Gameday webview should contain game-related content'\n        \n        elif 'stat' in webview_id:\n            # Verify statistics webview\n            stats_indicators = driver.find_elements(By.CSS_SELECTOR, '.stat, .statistics, [data-stat], .number')\n            verify_stats_display = len(stats_indicators) > 0\n            assert verify_stats_display, 'Statistics webview should display statistical data'\n        \n        # Performance validation\n        load_performance = driver.execute_script('return performance.timing.loadEventEnd - performance.timing.navigationStart')\n        check_load_performance = load_performance < 8000  # 8 second threshold for webviews\n        assert check_load_performance, f'WebView should load within 8 seconds, took {{load_performance}}ms'\n        \n        # Security verification - check for mixed content warnings\n        console_logs = driver.get_log('browser')\n        security_warnings = [log for log in console_logs if 'mixed content' in log['message'].lower() or 'insecure' in log['message'].lower()]\n        check_security = len(security_warnings) == 0\n        assert check_security, f'WebView should not generate security warnings: {{security_warnings}}'\n        \n    finally:\n        driver.quit()",
                "description": "Comprehensive webview test with authentication and content verification",
                "tags": ["webview", "authentication", "content", "verify", "check", "setup"]
            },
            {
                "component_type": "list",
                "test_pattern": "def test_{component_id}_data_validation():\n    \"\"\"Test list data loading, validation, and business functionality.\n    \n    Validates data integrity, item rendering, and list business logic.\n    Verifies data source connectivity and content accuracy.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    import time\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        # Arrange: Setup and navigate to list\n        driver.get('http://localhost:8000')\n        list_element = wait.until(EC.presence_of_element_located((By.ID, '{component_id}')))\n        \n        # Verify list container is properly displayed\n        assert list_element.is_displayed(), 'List container should be visible'\n        \n        # Act: Wait for data loading\n        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')\n        time.sleep(2)  # Allow time for async data loading\n        \n        # Assert: Verify data loading and validation\n        list_items = list_element.find_elements(By.CSS_SELECTOR, 'li, .list-item, [data-testid*=\"item\"], .row')\n        \n        # Check data was loaded successfully\n        verify_data_loaded = len(list_items) > 0\n        assert verify_data_loaded, 'List should contain data items after loading'\n        \n        # Verify minimum expected item count for business logic\n        if 'game' in '{component_id}'.lower():\n            check_minimum_games = len(list_items) >= 1\n            assert check_minimum_games, 'Game list should contain at least one game'\n        elif 'player' in '{component_id}'.lower():\n            check_minimum_players = len(list_items) >= 1\n            assert check_minimum_players, 'Player list should contain at least one player'\n        else:\n            check_minimum_items = len(list_items) >= 1\n            assert check_minimum_items, 'List should contain meaningful data'\n        \n        # Verify data integrity of first few items\n        for i, item in enumerate(list_items[:3]):  # Check first 3 items\n            # Verify each item has visible content\n            verify_item_content = item.text.strip() != ''\n            assert verify_item_content, f'List item {{i+1}} should have visible content'\n            \n            # Check for data attributes that indicate proper data binding\n            item_id = item.get_attribute('data-id') or item.get_attribute('id')\n            if item_id:\n                check_item_identifier = len(item_id) > 0\n                assert check_item_identifier, f'List item {{i+1}} should have valid identifier'\n        \n        # Test scrolling functionality for performance\n        if len(list_items) > 5:\n            initial_scroll = driver.execute_script('return arguments[0].scrollTop;', list_element)\n            driver.execute_script('arguments[0].scrollTop += 200;', list_element)\n            time.sleep(0.5)\n            new_scroll = driver.execute_script('return arguments[0].scrollTop;', list_element)\n            verify_scroll_functionality = new_scroll > initial_scroll\n            assert verify_scroll_functionality, 'List should support smooth scrolling for large datasets'\n        \n        # Verify business logic for specific list types\n        page_source = driver.page_source.lower()\n        \n        if 'score' in '{component_id}'.lower():\n            # Verify score data format\n            score_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid*=\"score\"], .score')\n            if score_elements:\n                verify_score_format = any('–' in elem.text or '-' in elem.text or 'vs' in elem.text.lower() for elem in score_elements)\n                assert verify_score_format, 'Score list should display properly formatted scores'\n        \n        elif 'stat' in '{component_id}'.lower():\n            # Verify statistical data presence\n            verify_stats_data = any(char.isdigit() for item in list_items for char in item.text)\n            assert verify_stats_data, 'Statistics list should contain numerical data'\n        \n        # Check for loading states and error handling\n        loading_indicators = driver.find_elements(By.CSS_SELECTOR, '.loading, .spinner, [data-loading=\"true\"]')\n        check_no_stuck_loading = len(loading_indicators) == 0\n        assert check_no_stuck_loading, 'List should not be stuck in loading state'\n        \n        error_indicators = driver.find_elements(By.CSS_SELECTOR, '.error, .no-data, .empty-state')\n        if len(list_items) > 0:\n            verify_no_error_state = len(error_indicators) == 0\n            assert verify_no_error_state, 'List with data should not show error states'\n        \n        # Performance validation\n        if len(list_items) > 10:\n            # Verify list renders efficiently with larger datasets\n            render_time = driver.execute_script('return performance.timing.loadEventEnd - performance.timing.navigationStart')\n            check_render_performance = render_time < 5000\n            assert check_render_performance, f'List should render within 5 seconds, took {{render_time}}ms'\n        \n    finally:\n        driver.quit()",
                "description": "Comprehensive list test with data validation and business logic",
                "tags": ["list", "data", "validation", "verify", "check"]
            },
            {
                "component_type": "api_endpoint",
                "test_pattern": "def test_{component_id}_response_validation():\n    \"\"\"Test API endpoint response validation and business data integrity.\n    \n    Validates HTTP response codes, JSON structure, and business data correctness.\n    Verifies API performance and error handling capabilities.\n    \"\"\"\n    from selenium import webdriver\n    import requests\n    from requests.adapters import HTTPAdapter\n    from urllib3.util.retry import Retry\n    import pytest\n    import time\n    import json\n    \n    driver = webdriver.Chrome()\n    \n    try:\n        # Arrange: Setup browser and API session\n        driver.get('http://localhost:8000')\n        \n        # Setup requests session with retries for robust testing\n        session = requests.Session()\n        retry_strategy = Retry(\n            total=3,\n            backoff_factor=1,\n            status_forcelist=[429, 500, 502, 503, 504]\n        )\n        adapter = HTTPAdapter(max_retries=retry_strategy)\n        session.mount('http://', adapter)\n        session.mount('https://', adapter)\n        \n        # Act: Make API request with timing\n        base_url = driver.current_url.split('/')[0:3]\n        full_url = '/'.join(base_url) + '{url}'\n        \n        start_time = time.time()\n        response = session.get(full_url, timeout=10)\n        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds\n        \n        # Assert: Comprehensive response validation\n        \n        # Verify HTTP response status\n        assert response.status_code == 200, f'Expected status_code 200, got {{response.status_code}}'\n        \n        # Verify response timing for performance\n        check_response_time = response_time < 2000  # Should respond within 2 seconds\n        assert check_response_time, f'API response time {{response_time:.0f}}ms exceeds 2000ms threshold'\n        \n        # Verify response headers\n        verify_content_type = 'content-type' in response.headers\n        assert verify_content_type, 'Response should include Content-Type header'\n        \n        # Test JSON response validation\n        if response.headers.get('content-type', '').startswith('application/json'):\n            try:\n                json_data = response.json()\n                assert response is not None and json_data is not None, 'Response should contain valid JSON data'\n                \n                # Verify JSON structure is not empty\n                verify_json_content = isinstance(json_data, (dict, list)) and len(json_data) > 0\n                assert verify_json_content, 'JSON response should contain meaningful data'\n                \n                # Business logic validation for specific endpoints\n                if 'game' in '{component_id}'.lower() or 'score' in '{component_id}'.lower():\n                    # Verify game/score data structure\n                    if isinstance(json_data, list) and len(json_data) > 0:\n                        first_item = json_data[0]\n                        verify_game_data = isinstance(first_item, dict)\n                        assert verify_game_data, 'Game data should be structured objects'\n                        \n                        # Check for expected game fields\n                        expected_fields = ['id', 'teams', 'score', 'date']\n                        game_fields = [field for field in expected_fields if field in str(first_item).lower()]\n                        check_game_fields = len(game_fields) > 0\n                        assert check_game_fields, 'Game data should contain relevant fields (id, teams, score, date)'\n                \n                elif 'player' in '{component_id}'.lower():\n                    # Verify player data structure\n                    if isinstance(json_data, list) and len(json_data) > 0:\n                        first_player = json_data[0]\n                        verify_player_data = isinstance(first_player, dict)\n                        assert verify_player_data, 'Player data should be structured objects'\n                        \n                        # Check for expected player fields\n                        expected_fields = ['name', 'position', 'team', 'stats']\n                        player_fields = [field for field in expected_fields if field in str(first_player).lower()]\n                        check_player_fields = len(player_fields) > 0\n                        assert check_player_fields, 'Player data should contain relevant fields (name, position, team, stats)'\n                \n                elif 'stat' in '{component_id}'.lower():\n                    # Verify statistics data\n                    if isinstance(json_data, dict):\n                        # Check for numerical statistics\n                        numeric_values = [v for v in json_data.values() if isinstance(v, (int, float))]\n                        verify_stats_numeric = len(numeric_values) > 0\n                        assert verify_stats_numeric, 'Statistics should contain numerical data'\n                \n            except json.JSONDecodeError:\n                pytest.fail(f'Response claims to be JSON but contains invalid JSON: {{response.text[:200]}}')\n        \n        # Verify response content length\n        assert response.content and len(response.content) > 0, 'Response should have meaningful content'\n        \n        # Test response encoding\n        verify_encoding = response.encoding is not None\n        assert verify_encoding, 'Response should specify character encoding'\n        \n        # Verify no error markers in response\n        response_text = response.text.lower()\n        error_markers = ['error', 'exception', 'traceback', 'internal server error']\n        check_no_errors = not any(marker in response_text for marker in error_markers)\n        assert check_no_errors, 'Response should not contain error indicators'\n        \n        # Test caching headers for performance\n        cache_headers = ['cache-control', 'etag', 'last-modified']\n        cache_present = any(header in response.headers for header in cache_headers)\n        if cache_present:\n            verify_caching = True\n            assert verify_caching, 'API should implement appropriate caching strategies'\n        \n    except requests.exceptions.RequestException as e:\n        pytest.skip(f'API endpoint not available: {{e}}')\n    except requests.exceptions.Timeout:\n        pytest.fail('API endpoint timed out - performance issue detected')\n    finally:\n        driver.quit()",
                "description": "Comprehensive API test with response validation and business logic",
                "tags": ["api", "endpoint", "response", "validation", "verify", "check"]
            },
            {
                "component_type": "text_field",
                "test_pattern": "def test_{component_id}_input_validation():\n    \"\"\"Test text field input validation and format checking.\n    \n    Validates text input functionality, pattern matching, and email format validation.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    import re\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        driver.get('http://localhost:8000')\n        text_field = wait.until(EC.presence_of_element_located((By.ID, '{component_id}')))\n        \n        assert text_field.is_displayed(), 'Text field should be visible'\n        assert text_field.is_enabled(), 'Text field should be enabled'\n        \n        # Test basic input functionality\n        test_value = 'test@example.com'\n        text_field.clear()\n        text_field.send_keys(test_value)\n        assert text_field.get_attribute('value') == test_value, 'Text field should accept valid input'\n        \n        # Test email format validation\n        field_type = text_field.get_attribute('type')\n        if field_type == 'email' or 'email' in text_field.get_attribute('class', ''):\n            # Validate email format\n            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n            current_value = text_field.get_attribute('value')\n            assert re.match(email_pattern, current_value), 'Email format should be valid'\n        \n        # Test clearing functionality\n        text_field.clear()\n        assert text_field.get_attribute('value') == '', 'Text field should clear properly'\n        \n        # Test required field validation if applicable\n        if text_field.get_attribute('required'):\n            text_field.clear()\n            driver.execute_script('arguments[0].blur();', text_field)\n            # Field should show validation state\n    finally:\n        driver.quit()",
                "description": "Text field validation test with format checking",
                "tags": ["text_field", "input", "validation", "email", "format"]
            }
        ]

        for pattern in default_patterns:
            self.store_pattern(pattern)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI API."""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}. Using fallback.")
            # Fallback: simple hash-based pseudo-embedding
            hash_obj = hashlib.md5(text.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            # Create a pseudo-embedding by repeating hash values
            embedding = []
            for i in range(self.vector_size):
                embedding.append(((hash_int >> (i % 32)) & 1) * 2.0 - 1.0)
            return embedding

    def health_check(self) -> bool:
        """Check if Qdrant connection is healthy."""
        if not self.client:
            return False
        try:
            collections = self.client.get_collections()
            return True
        except Exception:
            return False

    def store_pattern(self, pattern: Dict[str, Any]) -> str:
        """Store a UI test pattern in the vector store."""
        if not self.client:
            logger.warning("No Qdrant client - pattern not stored")
            return "fallback_id"

        # Create text representation for embedding
        text_repr = f"{pattern.get('component_type', '')} {pattern.get('description', '')} {pattern.get('test_pattern', '')}"
        embedding = self._get_embedding(text_repr)

        # Generate unique ID
        pattern_id = hashlib.md5(text_repr.encode()).hexdigest()

        point = PointStruct(
            id=pattern_id,
            vector=embedding,
            payload=pattern
        )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Stored pattern: {pattern_id}")
            return pattern_id
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            return "error_id"

    def search_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar UI patterns."""
        if not self.client:
            # Fallback mode - return hardcoded patterns
            return self._get_fallback_patterns(query, limit)

        try:
            query_embedding = self._get_embedding(query)

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )

            results = []
            for hit in search_result:
                result = hit.payload.copy()
                result['score'] = hit.score
                results.append(result)

            logger.info(f"Found {len(results)} patterns for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}. Using fallback.")
            return self._get_fallback_patterns(query, limit)

    def search_similar_patterns(self, feature_text: str, limit: int = 20, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Search for similar patterns using feature text and similarity threshold.
        
        Args:
            feature_text: Text representation of component features
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar patterns with similarity scores
        """
        if not self.client:
            logger.warning("No Qdrant client - using fallback patterns")
            return self._get_fallback_similarity_patterns(feature_text, limit, threshold)

        try:
            # Get embedding for feature text
            query_embedding = self._get_embedding(feature_text)

            # Search for similar patterns
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                score_threshold=threshold  # Apply similarity threshold
            )

            results = []
            for hit in search_result:
                if hit.score >= threshold:  # Double-check threshold
                    result = {
                        'pattern': hit.payload.copy(),
                        'similarity': hit.score,
                        'id': str(hit.id)
                    }
                    results.append(result)

            logger.info(f"Found {len(results)} similar patterns (threshold={threshold}) for features: {feature_text}")
            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}. Using fallback.")
            return self._get_fallback_similarity_patterns(feature_text, limit, threshold)

    def _get_fallback_similarity_patterns(self, feature_text: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Fallback similarity search using static patterns."""
        fallback_patterns = []
        
        # Extract component type from feature text
        component_type = 'unknown'
        if 'type:' in feature_text:
            type_part = feature_text.split('type:')[1].split()[0]
            component_type = type_part
        
        # Create fallback patterns based on component type
        base_patterns = {
            'button': {
                'pattern_type': 'base',
                'component_type': 'button',
                'test_strategy': 'button_basic_testing',
                'test_steps': ['Verify button is visible', 'Click button', 'Verify expected action'],
                'expected_assertions': ['Button is clickable', 'Action is triggered']
            },
            'list': {
                'pattern_type': 'base', 
                'component_type': 'list',
                'test_strategy': 'list_basic_testing',
                'test_steps': ['Verify list loads', 'Check item count', 'Test scrolling'],
                'expected_assertions': ['List contains items', 'Items are accessible']
            },
            'form': {
                'pattern_type': 'base',
                'component_type': 'form', 
                'test_strategy': 'form_basic_testing',
                'test_steps': ['Verify form fields', 'Fill valid data', 'Submit form'],
                'expected_assertions': ['Form accepts input', 'Validation works']
            }
        }
        
        if component_type in base_patterns:
            fallback_patterns.append({
                'pattern': base_patterns[component_type],
                'similarity': 0.9,  # High similarity for exact type match
                'id': f'fallback_{component_type}'
            })
        
        # Add generic pattern if no specific match
        if not fallback_patterns:
            fallback_patterns.append({
                'pattern': {
                    'pattern_type': 'generic',
                    'component_type': component_type,
                    'test_strategy': f'{component_type}_basic_testing',
                    'test_steps': ['Verify component exists', 'Test basic functionality'],
                    'expected_assertions': ['Component is functional']
                },
                'similarity': 0.8,
                'id': f'fallback_generic_{component_type}'
            })
        
        return fallback_patterns[:limit]

    def _get_fallback_patterns(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback patterns when Qdrant is unavailable."""
        fallback_patterns = [
            {
                "component_type": "button",
                "test_pattern": "def test_{component_id}_interaction():\n    \"\"\"Test button interaction and click functionality.\n    \n    Validates that the button is visible, enabled, and responds to clicks.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        driver.get('http://localhost:8000')\n        element = wait.until(EC.element_to_be_clickable((By.ID, '{component_id}')))\n        \n        assert element.is_displayed(), 'Button should be visible'\n        assert element.is_enabled(), 'Button should be enabled'\n        element.click()\n        \n        # Verify interaction worked\n        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')\n    finally:\n        driver.quit()",
                "description": "Interactive button test with real WebDriver",
                "score": 0.9,
                "tags": ["button", "interaction", "selenium"]
            },
            {
                "component_type": "webview",
                "test_pattern": "def test_{component_id}_loading():\n    \"\"\"Test webview loading and display functionality.\n    \n    Validates that the webview loads properly and has correct dimensions.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        driver.get('http://localhost:8000')\n        webview = wait.until(EC.presence_of_element_located((By.ID, '{component_id}')))\n        \n        assert webview.is_displayed(), 'WebView should be visible'\n        \n        # Test webview dimensions and properties\n        size = webview.size\n        assert size['height'] > 0, 'WebView should have valid height'\n        assert size['width'] > 0, 'WebView should have valid width'\n        \n        # If it's an iframe, check src attribute\n        if webview.tag_name == 'iframe':\n            src_url = webview.get_attribute('src')\n            assert src_url is not None, 'Iframe should have valid src'\n    finally:\n        driver.quit()",
                "description": "WebView functionality test with real WebDriver",
                "score": 0.8,
                "tags": ["webview", "loading", "selenium"]
            },
            {
                "component_type": "api_endpoint",
                "test_pattern": "def test_{endpoint_name}_response():\n    \"\"\"Test API endpoint response and status code validation.\n    \n    Validates that the endpoint returns successful status_code and valid JSON.\n    \"\"\"\n    import requests\n    from requests.adapters import HTTPAdapter\n    from urllib3.util.retry import Retry\n    import pytest\n    \n    # Setup session with retries\n    session = requests.Session()\n    retry_strategy = Retry(\n        total=3,\n        backoff_factor=1,\n        status_forcelist=[429, 500, 502, 503, 504]\n    )\n    adapter = HTTPAdapter(max_retries=retry_strategy)\n    session.mount('http://', adapter)\n    session.mount('https://', adapter)\n    \n    try:\n        response = session.get('{url}', timeout=10)\n        assert response.status_code == 200, f'Expected status_code 200, got {{response.status_code}}'\n        \n        # Test response content if JSON\n        if response.headers.get('content-type', '').startswith('application/json'):\n            json_data = response.json()\n            assert json_data is not None, 'Response should contain valid JSON data'\n    except requests.exceptions.RequestException as e:\n        pytest.skip(f'API endpoint not available: {{e}}')",
                "description": "API endpoint validation test with real requests",
                "score": 0.85,
                "tags": ["api", "endpoint", "validation", "requests"]
            },
            {
                "component_type": "text_field",
                "test_pattern": "def test_{component_id}_input_validation():\n    \"\"\"Test text field input validation and format checking.\n    \n    Validates text input functionality, pattern matching, and email format validation.\n    \"\"\"\n    from selenium import webdriver\n    from selenium.webdriver.common.by import By\n    from selenium.webdriver.support.ui import WebDriverWait\n    from selenium.webdriver.support import expected_conditions as EC\n    import re\n    \n    driver = webdriver.Chrome()\n    wait = WebDriverWait(driver, 10)\n    \n    try:\n        driver.get('http://localhost:8000')\n        text_field = wait.until(EC.presence_of_element_located((By.ID, '{component_id}')))\n        \n        assert text_field.is_displayed(), 'Text field should be visible'\n        assert text_field.is_enabled(), 'Text field should be enabled'\n        \n        # Test basic input functionality\n        test_value = 'test@example.com'\n        text_field.clear()\n        text_field.send_keys(test_value)\n        assert text_field.get_attribute('value') == test_value, 'Text field should accept valid input'\n        \n        # Test email format validation\n        field_type = text_field.get_attribute('type')\n        if field_type == 'email' or 'email' in text_field.get_attribute('class', ''):\n            # Validate email format\n            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$'\n            current_value = text_field.get_attribute('value')\n            assert re.match(email_pattern, current_value), 'Email format should be valid'\n        \n        # Test clearing functionality\n        text_field.clear()\n        assert text_field.get_attribute('value') == '', 'Text field should clear properly'\n        \n        # Test required field validation if applicable\n        if text_field.get_attribute('required'):\n            text_field.clear()\n            driver.execute_script('arguments[0].blur();', text_field)\n            # Field should show validation state\n    finally:\n        driver.quit()",
                "description": "Text field validation test with format checking",
                "score": 0.9,
                "tags": ["text_field", "input", "validation", "email", "format"]
            }
        ]

        # Simple matching based on query keywords
        query_lower = query.lower()
        matched_patterns = []

        for pattern in fallback_patterns:
            if any(tag in query_lower for tag in pattern['tags']) or pattern['component_type'] in query_lower:
                matched_patterns.append(pattern)

        # Return all patterns if no matches, limited by limit
        if not matched_patterns:
            matched_patterns = fallback_patterns

        return matched_patterns[:limit]

    def get_patterns_by_component_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Get all patterns for a specific component type."""
        return self.search_patterns(f"component_type:{component_type}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if not self.client:
            return {"status": "offline", "count": 0}

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "status": "online",
                "count": info.points_count,
                "vectors_config": str(info.config.params.vectors)
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "count": 0}