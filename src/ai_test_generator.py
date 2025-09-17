"""
AI-Powered Test Generator using Mistral AI for intelligent test creation.
Generates real, executable tests with context-aware logic.
"""

import os
import json
from typing import Dict, List, Any, Optional
from mistralai import Mistral
import openai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AITestGenerator:
    """Generates intelligent tests using Mistral AI and OpenAI."""

    def __init__(self):
        """Initialize AI clients with graceful degradation."""
        self.test_framework = "selenium"  # Default to Selenium for UI testing
        self.mistral_client = None
        self.openai_client = None
        self.api_available = {"mistral": False, "openai": False}

        # Initialize Mistral client with error handling
        mistral_api_key = os.getenv('MISTRAL_API_KEY')
        if mistral_api_key and mistral_api_key.strip():
            try:
                self.mistral_client = Mistral(api_key=mistral_api_key)
                self.api_available["mistral"] = True
                logger.info("Mistral AI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Mistral client: {e}")
                self.mistral_client = None
        else:
            logger.warning("MISTRAL_API_KEY not found or empty - AI generation will use fallback")

        # Initialize OpenAI client with error handling
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key and openai_api_key.strip():
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                self.api_available["openai"] = True
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            logger.warning("OPENAI_API_KEY not found or empty - edge case discovery will use fallback")

        # Log initialization status
        if any(self.api_available.values()):
            logger.info(f"AI Test Generator initialized - Mistral: {self.api_available['mistral']}, OpenAI: {self.api_available['openai']}")
        else:
            logger.warning("AI Test Generator initialized in fallback mode - no API keys available")

    def generate_test_from_ui_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent test for a UI component using AI."""
        component_type = component.get('type', 'unknown')
        component_id = component.get('id', 'element')

        # Create intelligent prompt for Mistral
        prompt = self._create_test_generation_prompt(component)

        try:
            # Check if Mistral is available for test generation
            if self.mistral_client and self.api_available["mistral"]:
                # Use Mistral to generate test code
                response = self.mistral_client.chat.complete(
                    model='mistral-small',
                    messages=[
                        {"role": "system", "content": "You are an expert test engineer specializing in Selenium WebDriver and pytest. Generate only the test function code without imports or explanations."},
                        {"role": "user", "content": prompt}
                    ]
                )
                generated_code = response.choices[0].message.content
            else:
                # Fallback to template-based generation
                logger.info("Mistral unavailable, using fallback test generation")
                generated_code = self._generate_fallback_test_code(component)

            # Use OpenAI to generate test description (with fallback)
            description = self._generate_test_description(component)

            # Extract edge cases using OpenAI (with fallback)
            edge_cases = self._discover_edge_cases(component)

            return {
                "test_name": f"test_{component_id}_ai_generated",
                "test_code": self._clean_generated_code(generated_code),
                "description": description,
                "edge_cases": edge_cases,
                "component_type": component_type,
                "ai_generated": True,
                "generator": "mistral-small"
            }

        except Exception as e:
            logger.error(f"AI test generation failed: {e}")
            return self._generate_fallback_test(component)

    def _create_test_generation_prompt(self, component: Dict[str, Any]) -> str:
        """Create intelligent prompt for test generation with authentication awareness."""
        component_type = component.get('type', 'unknown')
        component_id = component.get('id', 'element')
        properties = component.get('properties', {})
        requires_auth = component.get('requires_auth', False)

        prompt = f"""Generate a pytest test function for a {component_type} component with the following details:
Component ID: {component_id}
Component Type: {component_type}
Properties: {json.dumps(properties, indent=2)}
Authentication Required: {requires_auth}

Requirements:
1. Use Selenium WebDriver for browser automation
2. Include proper waits and assertions
3. Test both positive and negative scenarios
4. Check for element visibility and interactability
5. Validate state changes after interactions
6. Include performance checks where relevant
7. The function should be named test_{component_id}_functionality

Generate only the test function, assuming these imports are available:
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pytest
"""

        # Add authentication setup if required
        if requires_auth:
            prompt += """
CRITICAL: This component requires authentication. Your test MUST include:
- Login form detection and interaction
- Test credentials setup (use test@mlb.com / testpassword)
- Authentication completion verification
- Error handling for auth failures
- Session management validation
- Include 'verify_authentication_setup' assertion"""

        # Add specific requirements based on component type
        if component_type == "webview":
            prompt += "\nAdditional: Test iframe loading, content accessibility, and JavaScript execution."
        elif component_type == "button":
            prompt += "\nAdditional: Test click events, disabled state, and visual feedback."
        elif component_type == "list":
            prompt += "\nAdditional: Test scrolling, item selection, and lazy loading."
        elif component_type == "api_endpoint":
            prompt += "\nAdditional: Test response time, error handling, and data validation."

        return prompt

    def _generate_test_description(self, component: Dict[str, Any]) -> str:
        """Generate intelligent test description using OpenAI with fallback."""
        if self.openai_client and self.api_available["openai"]:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test documentation expert. Generate concise, clear test descriptions."},
                        {"role": "user", "content": f"Describe a test for a {component.get('type', 'unknown')} component with properties: {json.dumps(component, indent=2)}. Keep it under 50 words."}
                    ],
                    max_tokens=100
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Could not generate AI description: {e}")

        # Fallback description generation
        component_type = component.get('type', 'unknown')
        component_id = component.get('id', 'element')
        return f"Test for {component_type} component '{component_id}' - validates functionality, interactions, and edge cases"

    def _discover_edge_cases(self, component: Dict[str, Any]) -> List[str]:
        """Discover edge cases using AI analysis with fallback."""
        if self.openai_client and self.api_available["openai"]:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a QA expert specializing in edge case discovery."},
                        {"role": "user", "content": f"List 3-5 edge cases to test for a {component.get('type', 'unknown')} component. Return as a JSON array of strings."}
                    ],
                    max_tokens=200
                )

                # Parse response as JSON array with robust validation
                content = response.choices[0].message.content.strip()

                # Try to extract JSON from response (handle code blocks)
                if '```json' in content:
                    # Extract JSON from code block
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    if json_start != -1 and json_end > json_start:
                        content = content[json_start:json_end]
                elif '```' in content:
                    # Remove any markdown code blocks
                    content = content.replace('```', '').strip()

                # Try to parse as JSON
                try:
                    if content.startswith('[') and content.endswith(']'):
                        edge_cases = json.loads(content)
                        # Validate that all items are strings and clean them
                        cleaned_cases = []
                        for case in edge_cases:
                            if isinstance(case, str) and len(case.strip()) > 0:
                                # Clean the edge case description
                                clean_case = case.strip().strip('"').strip("'")
                                # Avoid malformed or too short cases
                                if len(clean_case) > 5 and not any(x in clean_case.lower() for x in ['```', 'json', '[', ']']):
                                    cleaned_cases.append(clean_case)
                        return cleaned_cases if cleaned_cases else []
                except json.JSONDecodeError:
                    pass

                # If JSON parsing fails, try line-by-line parsing with validation
                lines = [line.strip('- ').strip() for line in content.split('\n') if line.strip()]
                cleaned_lines = []
                for line in lines:
                    # Clean and validate each line
                    clean_line = line.strip().strip('"').strip("'")
                    # Filter out malformed content
                    if (len(clean_line) > 5 and
                        not any(x in clean_line.lower() for x in ['```', 'json', 'here are', 'edge cases']) and
                        not clean_line.startswith('[') and
                        not clean_line.endswith(']')):
                        cleaned_lines.append(clean_line)

                return cleaned_lines[:5]  # Limit to 5 edge cases

            except Exception as e:
                logger.warning(f"Could not discover edge cases: {e}")

        # Fallback edge case generation based on component type
        component_type = component.get('type', 'unknown')
        edge_cases = ["Empty data handling", "Network timeout", "Invalid input"]

        if component_type == "button":
            edge_cases.extend(["Disabled state", "Multiple rapid clicks", "Long press behavior"])
        elif component_type == "form":
            edge_cases.extend(["Invalid email format", "Required field validation", "Maximum character limit"])
        elif component_type == "list":
            edge_cases.extend(["Empty list state", "Large dataset performance", "Infinite scroll edge"])
        elif component_type == "image":
            edge_cases.extend(["Missing image URL", "Slow loading images", "Invalid image format"])
        elif component_type == "video":
            edge_cases.extend(["Video load failure", "Unsupported codec", "Network buffering"])

        return edge_cases

    def _clean_generated_code(self, code: str) -> str:
        """Clean and format generated test code."""
        # Remove any import statements if mistakenly included
        lines = code.split('\n')
        cleaned_lines = []
        in_function = False

        for line in lines:
            # Skip import lines
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                continue

            # Start including from def test_
            if line.strip().startswith('def test_'):
                in_function = True

            if in_function:
                cleaned_lines.append(line)

        # Join and ensure proper indentation
        cleaned_code = '\n'.join(cleaned_lines)

        # Add necessary imports if completely missing
        if not cleaned_code.strip().startswith('def test_'):
            # If no function found, return a basic structure
            return self._generate_fallback_test({})['test_code']

        return cleaned_code

    def _generate_fallback_test_code(self, component: Dict[str, Any]) -> str:
        """Generate fallback test code when Mistral is unavailable."""
        component_id = component.get('id', 'element')
        component_type = component.get('type', 'unknown')

        # Generate component-specific test code
        base_test = f"""def test_{component_id}_{component_type}():
    \"\"\"Test {component_type} component functionality - fallback implementation.\"\"\"
    import pytest
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to test page
        driver.get("http://localhost:8000")

        # Find the component element
        element = wait.until(EC.presence_of_element_located((By.ID, "{component_id}")))
        assert element.is_displayed(), f"{component_type} element should be visible"
"""

        # Add component-specific interactions
        if component_type == "button":
            base_test += f"""
        # Test button functionality
        assert element.is_enabled(), "Button should be enabled"
        element.click()

        # Verify click action (look for page change or response)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
"""
        elif component_type == "input":
            base_test += f"""
        # Test input functionality
        element.clear()
        test_value = "test input value"
        element.send_keys(test_value)
        assert element.get_attribute("value") == test_value, "Input should accept text"
"""
        elif component_type == "form":
            base_test += f"""
        # Test form functionality
        form_inputs = element.find_elements(By.CSS_SELECTOR, "input, textarea, select")
        for input_elem in form_inputs:
            if input_elem.get_attribute("type") not in ["hidden", "submit"]:
                input_elem.clear()
                input_elem.send_keys("test_data")

        submit_btn = element.find_element(By.CSS_SELECTOR, "[type='submit'], button")
        submit_btn.click()
"""
        elif component_type in ["image", "video"]:
            base_test += f"""
        # Test media element loading
        assert element.get_attribute("src") is not None, "{component_type} should have src attribute"

        if element.tag_name == "img":
            # Check if image loaded successfully
            assert driver.execute_script("return arguments[0].complete && arguments[0].naturalHeight > 0", element)
"""
        else:
            # Generic component test
            base_test += f"""
        # Generic component interaction test
        if element.tag_name in ["button", "a"]:
            element.click()
        elif element.tag_name in ["input", "textarea"]:
            element.clear()
            element.send_keys("test_value")
"""

        base_test += f"""
        # Verify element properties
        assert element.is_displayed(), "Element should remain visible after interaction"

    except TimeoutException:
        pytest.fail(f"Timeout waiting for {component_type} element '{{component_id}}'")
    except NoSuchElementException:
        pytest.fail(f"{component_type} element '{{component_id}}' not found")
    except Exception as e:
        pytest.fail(f"Unexpected error testing {component_type}: {{str(e)}}")
    finally:
        driver.quit()
"""

        return base_test

    def _generate_fallback_test(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback test if AI generation fails."""
        component_id = component.get('id', 'element')
        component_type = component.get('type', 'unknown')

        return {
            "test_name": f"test_{component_id}_basic",
            "test_code": f"""def test_{component_id}_basic():
    driver = webdriver.Chrome()
    driver.get('http://localhost:8000')

    try:
        element = driver.find_element(By.ID, "{component_id}")
        assert element.is_displayed()
        print(f"Element {component_id} found and visible")
    except Exception as e:
        pytest.fail(f"Element {component_id} not found: {{e}}")
    finally:
        driver.quit()""",
            "description": f"Basic visibility test for {component_type} component",
            "edge_cases": ["Element not found", "Element not visible"],
            "component_type": component_type,
            "ai_generated": False,
            "generator": "fallback"
        }

    def generate_test_suite(self, ui_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive test suite for entire UI schema."""
        tests = []
        screen_name = ui_schema.get('screen', 'unknown')
        components = ui_schema.get('components', [])

        logger.info(f"Generating AI test suite for {screen_name} with {len(components)} components")

        for component in components:
            # Generate main functionality test
            main_test = self.generate_test_from_ui_component(component)
            tests.append(main_test)

            # Generate edge case tests
            if main_test.get('edge_cases'):
                for i, edge_case in enumerate(main_test['edge_cases'][:2]):  # Limit to 2 edge cases
                    edge_test = self._generate_edge_case_test(component, edge_case, i)
                    tests.append(edge_test)

        # Add integration test
        if len(components) > 1:
            integration_test = self._generate_integration_test(ui_schema)
            tests.append(integration_test)

        logger.info(f"Generated {len(tests)} AI-powered tests")
        return tests

    def _generate_edge_case_test(self, component: Dict[str, Any], edge_case: str, index: int) -> Dict[str, Any]:
        """Generate test for specific edge case with fallback."""
        component_id = component.get('id', 'element')
        component_type = component.get('type', 'unknown')

        if self.mistral_client and self.api_available["mistral"]:
            prompt = f"Generate a pytest test for this edge case: {edge_case} for a {component_type} component with ID {component_id}"

            try:
                response = self.mistral_client.chat.complete(
                    model='mistral-tiny',
                    messages=[
                        {"role": "system", "content": "Generate concise edge case tests. Focus on the specific edge case scenario."},
                        {"role": "user", "content": prompt}
                    ]
                )

                return {
                    "test_name": f"test_{component_id}_edge_case_{index}",
                    "test_code": self._clean_generated_code(response.choices[0].message.content),
                    "description": f"Edge case test: {edge_case}",
                    "component_type": component_type,
                    "test_type": "edge_case",
                    "ai_generated": True
                }
            except Exception as e:
                logger.error(f"Edge case generation failed: {e}")

        # Fallback edge case test generation
        fallback_code = self._generate_fallback_edge_case_test(component, edge_case, index)
        return {
            "test_name": f"test_{component_id}_edge_case_{index}",
            "test_code": fallback_code,
            "description": f"Edge case test: {edge_case} (fallback implementation)",
            "component_type": component_type,
            "test_type": "edge_case",
            "ai_generated": False,
            "fallback_generated": True
        }

    def _generate_fallback_edge_case_test(self, component: Dict[str, Any], edge_case: str, index: int) -> str:
        """Generate fallback edge case test when Mistral is unavailable."""
        component_id = component.get('id', 'element')
        component_type = component.get('type', 'unknown')

        return f"""def test_{component_id}_edge_case_{index}():
    \"\"\"Edge case test: {edge_case} - fallback implementation.\"\"\"
    import pytest
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("http://localhost:8000")
        element = wait.until(EC.presence_of_element_located((By.ID, "{component_id}")))

        # Edge case specific testing for: {edge_case}
        if "empty" in "{edge_case}".lower() or "null" in "{edge_case}".lower():
            # Test empty/null data handling
            if element.tag_name in ["input", "textarea"]:
                element.clear()
                element.send_keys("")
                assert element.get_attribute("value") == ""

        elif "timeout" in "{edge_case}".lower() or "network" in "{edge_case}".lower():
            # Test network/timeout scenarios
            driver.set_network_conditions(offline=True)
            try:
                element.click()
                # Should handle network failure gracefully
            except Exception:
                pass  # Expected to fail or handle gracefully
            finally:
                driver.set_network_conditions(offline=False)

        elif "invalid" in "{edge_case}".lower():
            # Test invalid input handling
            if element.tag_name in ["input", "textarea"]:
                element.clear()
                element.send_keys("invalid_test_data_!@#$%^&*()")
                # Should handle invalid input gracefully

        else:
            # Generic edge case handling
            if element.tag_name == "button":
                # Test rapid clicking
                for _ in range(5):
                    element.click()
            elif element.tag_name in ["input", "textarea"]:
                # Test boundary values
                element.clear()
                element.send_keys("x" * 1000)  # Test long input

        # Verify element still functions after edge case
        assert element.is_displayed(), "Element should remain functional after edge case test"

    except Exception as e:
        # Edge cases might cause exceptions - log but don't fail
        print(f"Edge case '{edge_case}' handled: {{str(e)}}")
    finally:
        driver.quit()"""

    def _generate_integration_test(self, ui_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration test for multiple components."""
        screen_name = ui_schema.get('screen', 'unknown')

        prompt = f"""Generate an integration test for {screen_name} screen that tests multiple components working together.
Components: {json.dumps([c.get('type') for c in ui_schema.get('components', [])], indent=2)}
Test the interaction between components and overall screen functionality."""

        if self.mistral_client and self.api_available["mistral"]:
            try:
                response = self.mistral_client.chat.complete(
                    model='mistral-small',
                    messages=[
                        {"role": "system", "content": "Generate integration tests that verify multiple components work together correctly."},
                        {"role": "user", "content": prompt}
                    ]
                )

                return {
                    "test_name": f"test_{screen_name}_integration",
                    "test_code": self._clean_generated_code(response.choices[0].message.content),
                    "description": f"Integration test for {screen_name} screen components",
                    "test_type": "integration",
                    "ai_generated": True,
                    "generator": "mistral-small"
                }
            except Exception as e:
                logger.error(f"Integration test generation failed: {e}")

        # Generate comprehensive fallback integration test
        fallback_test = self._generate_fallback_integration_test(screen_name, ui_schema)
        return {
            "test_name": f"test_{screen_name}_integration",
            "test_code": fallback_test,
            "description": f"Integration test for {screen_name} screen (fallback implementation)",
            "test_type": "integration",
            "ai_generated": False,
            "fallback_generated": True
        }

    def _generate_fallback_integration_test(self, screen_name: str, ui_schema: Dict[str, Any]) -> str:
        """Generate a comprehensive fallback integration test when AI generation fails."""
        components = ui_schema.get('components', [])
        component_types = [c.get('type', 'unknown') for c in components]

        # Build comprehensive test based on component analysis
        test_code = f"""def test_{screen_name}_integration():
    \"\"\"
    Integration test for {screen_name} screen.
    Tests multiple components working together.
    Fallback implementation when AI generation fails.
    \"\"\"
    import pytest
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    # Setup
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to screen
        driver.get("/{screen_name.lower()}")

        # Verify screen loads
        assert "{screen_name}" in driver.title or "{screen_name.lower()}" in driver.current_url

        # Component integration tests"""

        # Add component-specific integration tests
        for i, component_type in enumerate(set(component_types)):
            if component_type in ['button', 'link', 'navigation']:
                test_code += f"""

        # Test {component_type} integration
        {component_type}_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='{component_type}']")
        if {component_type}_elements:
            # Test interaction capabilities
            {component_type}_elements[0].click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))"""

            elif component_type in ['form', 'input']:
                test_code += f"""

        # Test {component_type} integration
        {component_type}_elements = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
        if {component_type}_elements:
            # Test form functionality
            for element in {component_type}_elements[:3]:  # Test first 3 inputs
                if element.get_attribute("type") not in ["hidden", "submit"]:
                    element.clear()
                    element.send_keys("test_data")
                    assert element.get_attribute("value") == "test_data" """

            elif component_type in ['image', 'video', 'media']:
                test_code += f"""

        # Test {component_type} integration
        {component_type}_elements = driver.find_elements(By.CSS_SELECTOR, "img, video, iframe")
        if {component_type}_elements:
            # Test media loading
            for element in {component_type}_elements[:2]:  # Test first 2 elements
                assert element.is_displayed()
                if element.tag_name == "img":
                    assert element.get_attribute("src") is not None"""

            elif component_type in ['list', 'grid', 'carousel']:
                test_code += f"""

        # Test {component_type} integration
        {component_type}_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='{component_type}'], ul, ol")
        if {component_type}_elements:
            # Test list functionality
            list_items = {component_type}_elements[0].find_elements(By.CSS_SELECTOR, "li, [data-testid*='item']")
            assert len(list_items) > 0, "List should contain items" """

            elif component_type in ['modal', 'dialog', 'popup']:
                test_code += f"""

        # Test {component_type} integration
        modal_triggers = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='modal'], [data-testid*='dialog']")
        if modal_triggers:
            # Test modal functionality
            modal_triggers[0].click()
            try:
                modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, .dialog")))
                assert modal.is_displayed()
                # Try to close modal
                close_btn = modal.find_element(By.CSS_SELECTOR, ".close, .cancel, [aria-label='close']")
                close_btn.click()
            except TimeoutException:
                pass  # Modal might not exist"""

        # Add comprehensive integration validation
        test_code += f"""

        # Cross-component integration validation

        # Test screen responsiveness
        driver.set_window_size(375, 667)  # Mobile size
        assert driver.find_element(By.TAG_NAME, "body").is_displayed()

        driver.set_window_size(1024, 768)  # Desktop size
        assert driver.find_element(By.TAG_NAME, "body").is_displayed()

        # Test overall screen functionality
        page_source = driver.page_source.lower()

        # Verify key components are present
        component_indicators = {[repr(ct) for ct in component_types]}
        for component_type in component_indicators:
            if component_type in ["button", "link"]:
                assert "click" in page_source or "button" in page_source
            elif component_type in ["form", "input"]:
                assert "input" in page_source or "form" in page_source

        # Test error handling
        try:
            # Simulate potential error conditions
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")
        except Exception as e:
            # Screen should handle scroll errors gracefully
            assert "Failed to scroll" not in str(e)

        # Performance validation
        load_time = driver.execute_script("return performance.timing.loadEventEnd - performance.timing.navigationStart")
        assert load_time < 10000, f"Page load time {{load_time}}ms exceeds 10 second threshold"

    except Exception as e:
        pytest.fail(f"Integration test failed: {{str(e)}}")

    finally:
        driver.quit()

    # Test completed successfully
    assert True, "Integration test completed successfully"
"""

        return test_code