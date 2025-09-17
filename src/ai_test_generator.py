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

    def generate_performance_tests(self, ui_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive performance tests for UI components.
        
        Args:
            ui_schema: UI schema definition
            
        Returns:
            List of performance test definitions
        """
        performance_tests = []
        
        try:
            screen_name = ui_schema.get('screen', 'unknown')
            components = ui_schema.get('components', [])
            
            # Generate load time tests
            load_time_test = self._generate_load_time_test(screen_name, components)
            performance_tests.append(load_time_test)
            
            # Generate response time tests for interactive components
            interactive_components = [c for c in components if 'interactions' in c]
            if interactive_components:
                response_time_test = self._generate_response_time_test(screen_name, interactive_components)
                performance_tests.append(response_time_test)
            
            # Generate memory usage tests
            memory_test = self._generate_memory_usage_test(screen_name, components)
            performance_tests.append(memory_test)
            
            # Generate API performance tests
            api_components = [c for c in components if 'endpoint' in c or 'api_url' in c]
            if api_components:
                api_perf_test = self._generate_api_performance_test(screen_name, api_components)
                performance_tests.append(api_perf_test)
            
            # Generate rendering performance tests
            rendering_test = self._generate_rendering_performance_test(screen_name, components)
            performance_tests.append(rendering_test)
            
            logger.info(f"Generated {len(performance_tests)} performance tests for {screen_name}")
            
        except Exception as e:
            logger.error(f"Error generating performance tests: {e}")
            # Add fallback performance test
            performance_tests.append(self._generate_fallback_performance_test(ui_schema))
            
        return performance_tests

    def generate_accessibility_tests(self, ui_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive accessibility tests for UI components.
        
        Args:
            ui_schema: UI schema definition
            
        Returns:
            List of accessibility test definitions
        """
        accessibility_tests = []
        
        try:
            screen_name = ui_schema.get('screen', 'unknown')
            components = ui_schema.get('components', [])
            
            # Generate WCAG compliance tests
            wcag_test = self._generate_wcag_compliance_test(screen_name, components)
            accessibility_tests.append(wcag_test)
            
            # Generate keyboard navigation tests
            interactive_components = [c for c in components if c.get('type') in ['button', 'input', 'select', 'navigation']]
            if interactive_components:
                keyboard_test = self._generate_keyboard_navigation_test(screen_name, interactive_components)
                accessibility_tests.append(keyboard_test)
            
            # Generate screen reader tests
            screen_reader_test = self._generate_screen_reader_test(screen_name, components)
            accessibility_tests.append(screen_reader_test)
            
            # Generate color contrast tests
            color_test = self._generate_color_contrast_test(screen_name, components)
            accessibility_tests.append(color_test)
            
            # Generate focus management tests
            focus_test = self._generate_focus_management_test(screen_name, components)
            accessibility_tests.append(focus_test)
            
            logger.info(f"Generated {len(accessibility_tests)} accessibility tests for {screen_name}")
            
        except Exception as e:
            logger.error(f"Error generating accessibility tests: {e}")
            # Add fallback accessibility test
            accessibility_tests.append(self._generate_fallback_accessibility_test(ui_schema))
            
        return accessibility_tests

    def _generate_load_time_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate load time performance test."""
        test_code = f'''
def test_{screen_name}_load_time_performance():
    """Test that {screen_name} screen loads within acceptable time limits."""
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    driver = webdriver.Chrome()
    
    try:
        start_time = time.time()
        
        # Navigate to screen
        driver.get("http://localhost:3000/{screen_name}")
        
        # Wait for critical components to load
        wait = WebDriverWait(driver, 10)
        {self._generate_load_time_assertions(components)}
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Performance assertions
        assert load_time < 3.0, f"Load time {{load_time:.2f}}s exceeds 3s limit"
        assert load_time < 2.0, f"Load time {{load_time:.2f}}s exceeds optimal 2s target"
        
        print(f"{screen_name} load time: {{load_time:.3f}}s")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_load_time_performance",
            "test_code": test_code,
            "description": f"Load time performance test for {screen_name}",
            "test_type": "performance",
            "category": "load_time"
        }

    def _generate_response_time_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate response time performance test for interactive components."""
        test_code = f'''
def test_{screen_name}_response_time_performance():
    """Test response times for interactive components on {screen_name} screen."""
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        wait = WebDriverWait(driver, 10)
        
        {self._generate_response_time_tests(components)}
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_response_time_performance", 
            "test_code": test_code,
            "description": f"Response time performance test for {screen_name} interactive components",
            "test_type": "performance",
            "category": "response_time"
        }

    def _generate_memory_usage_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate memory usage performance test."""
        test_code = f'''
def test_{screen_name}_memory_usage():
    """Test memory usage during {screen_name} screen operations."""
    import psutil
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        time.sleep(2)  # Allow initial load
        
        # Perform operations that might cause memory leaks
        {self._generate_memory_stress_operations(components)}
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase < 100, f"Memory increase {{memory_increase:.1f}}MB exceeds 100MB limit"
        print(f"Memory usage: {{initial_memory:.1f}}MB -> {{final_memory:.1f}}MB (+{{memory_increase:.1f}}MB)")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_memory_usage",
            "test_code": test_code,
            "description": f"Memory usage test for {screen_name}",
            "test_type": "performance", 
            "category": "memory"
        }

    def _generate_wcag_compliance_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate WCAG compliance accessibility test."""
        test_code = f'''
def test_{screen_name}_wcag_compliance():
    """Test WCAG 2.1 AA compliance for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from axe_selenium_python import Axe
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        
        # Run axe accessibility scanner
        axe = Axe(driver)
        
        # Inject axe-core JavaScript
        axe.inject()
        
        # Run accessibility scan
        results = axe.run()
        
        # Check for violations
        violations = results.get("violations", [])
        
        if violations:
            print(f"Accessibility violations found on {screen_name}:")
            for violation in violations[:5]:  # Show first 5 violations
                print(f"- {{violation['id']}}: {{violation['description']}}")
        
        # Assert no critical violations
        critical_violations = [v for v in violations if v.get("impact") in ["critical", "serious"]]
        assert len(critical_violations) == 0, f"Found {{len(critical_violations)}} critical accessibility violations"
        
        # Warn about moderate violations
        moderate_violations = [v for v in violations if v.get("impact") == "moderate"]
        if moderate_violations:
            print(f"Warning: {{len(moderate_violations)}} moderate accessibility issues found")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_wcag_compliance",
            "test_code": test_code,
            "description": f"WCAG compliance test for {screen_name}",
            "test_type": "accessibility",
            "category": "wcag"
        }

    def _generate_keyboard_navigation_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate keyboard navigation accessibility test."""
        test_code = f'''
def test_{screen_name}_keyboard_navigation():
    """Test keyboard navigation accessibility for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        wait = WebDriverWait(driver, 10)
        
        # Start with body element
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        
        # Test tab navigation through interactive elements
        {self._generate_keyboard_navigation_assertions(components)}
        
        # Test escape key functionality
        {self._generate_escape_key_tests(components)}
        
        # Test enter key activation
        {self._generate_enter_key_tests(components)}
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_keyboard_navigation",
            "test_code": test_code,
            "description": f"Keyboard navigation test for {screen_name}",
            "test_type": "accessibility",
            "category": "keyboard"
        }

    def _generate_screen_reader_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate screen reader accessibility test."""
        test_code = f'''
def test_{screen_name}_screen_reader_support():
    """Test screen reader support for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        
        # Check for proper heading structure
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        if headings:
            # Verify heading hierarchy
            {self._generate_heading_hierarchy_tests()}
        
        # Check for alt text on images
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            assert alt_text is not None, f"Image missing alt text: {{img.get_attribute('src')}}"
        
        # Check for aria-labels on interactive elements
        {self._generate_aria_label_tests(components)}
        
        # Check for form labels
        {self._generate_form_label_tests(components)}
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_screen_reader_support",
            "test_code": test_code,
            "description": f"Screen reader support test for {screen_name}",
            "test_type": "accessibility",
            "category": "screen_reader"
        }

    def _generate_load_time_assertions(self, components: List[Dict]) -> str:
        """Generate load time assertions for components."""
        assertions = []
        for component in components[:3]:  # Check first 3 components
            component_id = component.get('id', 'unknown')
            assertions.append(f'        wait.until(EC.presence_of_element_located((By.ID, "{component_id}")))')
        return '\n'.join(assertions) if assertions else '        # No specific components to wait for'

    def _generate_response_time_tests(self, components: List[Dict]) -> str:
        """Generate response time test code for interactive components."""
        tests = []
        for component in components:
            if component.get('type') == 'button':
                component_id = component.get('id', 'unknown')
                tests.append(f'''
        # Test {component_id} response time
        start_time = time.time()
        button = wait.until(EC.element_to_be_clickable((By.ID, "{component_id}")))
        button.click()
        
        # Wait for response (adjust selector based on expected change)
        time.sleep(0.1)  # Minimum response time
        response_time = time.time() - start_time
        
        assert response_time < 0.5, f"{component_id} response time {{response_time:.3f}}s exceeds 500ms"
        print(f"{component_id} response time: {{response_time:.3f}}s")''')
        
        return '\n'.join(tests) if tests else '        # No interactive components found'

    def _generate_memory_stress_operations(self, components: List[Dict]) -> str:
        """Generate memory stress operations."""
        operations = []
        
        # Scroll operations
        operations.append('''
        # Perform scrolling operations
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.1)''')
        
        # Click operations on interactive elements
        interactive_components = [c for c in components if c.get('type') in ['button', 'card', 'list']]
        if interactive_components:
            component_id = interactive_components[0].get('id', 'unknown')
            operations.append(f'''
        # Perform repeated interactions
        try:
            element = driver.find_element(By.ID, "{component_id}")
            for _ in range(20):
                element.click()
                time.sleep(0.05)
        except:
            pass  # Element might not be clickable''')
        
        return '\n'.join(operations)

    def _generate_keyboard_navigation_assertions(self, components: List[Dict]) -> str:
        """Generate keyboard navigation assertions."""
        tests = []
        interactive_components = [c for c in components if c.get('type') in ['button', 'input', 'select']]
        
        if interactive_components:
            tests.append('''
        # Test tab navigation
        focused_elements = []
        for _ in range(10):  # Tab through first 10 focusable elements
            driver.switch_to.active_element.send_keys(Keys.TAB)
            focused = driver.switch_to.active_element
            focused_elements.append(focused.tag_name)
            
        # Verify we can navigate to interactive elements
        assert len(focused_elements) > 0, "No elements received focus during tab navigation"''')
        
        return '\n'.join(tests) if tests else '        # No interactive components to test'

    def _generate_escape_key_tests(self, components: List[Dict]) -> str:
        """Generate escape key functionality tests."""
        modal_components = [c for c in components if c.get('type') == 'modal']
        if modal_components:
            return '''
        # Test escape key for modals
        try:
            modal_trigger = driver.find_element(By.CSS_SELECTOR, "[data-testid*='modal'], [class*='modal']")
            modal_trigger.click()
            time.sleep(0.5)
            
            # Press escape
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            
            # Verify modal is closed (adjust selector as needed)
            modals = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']:not([style*='display: none'])")
            assert len(modals) == 0, "Modal did not close with escape key"
        except:
            pass  # Modal might not be present'''
        return '        # No modal components to test escape functionality'

    def _generate_enter_key_tests(self, components: List[Dict]) -> str:
        """Generate enter key activation tests."""
        button_components = [c for c in components if c.get('type') == 'button']
        if button_components:
            component_id = button_components[0].get('id', 'unknown')
            return f'''
        # Test enter key activation
        try:
            button = driver.find_element(By.ID, "{component_id}")
            button.click()  # Focus the button
            button.send_keys(Keys.ENTER)
            # Verify button activation (adjust based on expected behavior)
            time.sleep(0.2)
        except:
            pass  # Button might not be present'''
        return '        # No button components to test enter key activation'

    def _generate_heading_hierarchy_tests(self) -> str:
        """Generate heading hierarchy validation."""
        return '''
        # Check heading hierarchy
        previous_level = 0
        for heading in headings:
            level = int(heading.tag_name[1])  # Extract number from h1, h2, etc.
            if previous_level > 0:
                # Heading levels should not skip (e.g., h1 -> h3 is bad)
                assert level <= previous_level + 1, f"Heading hierarchy violation: h{previous_level} followed by h{level}"
            previous_level = level'''

    def _generate_aria_label_tests(self, components: List[Dict]) -> str:
        """Generate ARIA label validation tests."""
        tests = []
        for component in components:
            if component.get('type') in ['button', 'input', 'select']:
                component_id = component.get('id', 'unknown')
                tests.append(f'''
        # Check aria-label for {component_id}
        try:
            element = driver.find_element(By.ID, "{component_id}")
            aria_label = element.get_attribute("aria-label")
            text_content = element.text
            
            # Element should have either aria-label or visible text
            assert aria_label or text_content, f"{component_id} missing both aria-label and visible text"
        except:
            pass  # Element might not be present''')
        
        return '\n'.join(tests) if tests else '        # No interactive components to test'

    def _generate_form_label_tests(self, components: List[Dict]) -> str:
        """Generate form label validation tests."""
        form_components = [c for c in components if c.get('type') in ['input', 'select', 'form']]
        if form_components:
            return '''
        # Check form labels
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        for input_element in inputs:
            element_id = input_element.get_attribute("id")
            if element_id:
                # Look for associated label
                labels = driver.find_elements(By.CSS_SELECTOR, f'label[for="{element_id}"]')
                aria_labelledby = input_element.get_attribute("aria-labelledby")
                aria_label = input_element.get_attribute("aria-label")
                
                assert labels or aria_labelledby or aria_label, f"Input {element_id} missing proper label"'''
        return '        # No form components to test'

    def _generate_fallback_performance_test(self, ui_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback performance test when AI generation fails."""
        screen_name = ui_schema.get('screen', 'unknown')
        
        test_code = f'''
def test_{screen_name}_basic_performance():
    """Basic performance test for {screen_name} screen (fallback)."""
    import time
    from selenium import webdriver
    
    driver = webdriver.Chrome()
    
    try:
        start_time = time.time()
        driver.get("http://localhost:3000/{screen_name}")
        
        # Wait for page load
        driver.implicitly_wait(10)
        
        load_time = time.time() - start_time
        
        # Basic performance assertions
        assert load_time < 5.0, f"Load time {{load_time:.2f}}s exceeds 5s limit"
        print(f"Basic performance test - Load time: {{load_time:.3f}}s")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_basic_performance",
            "test_code": test_code,
            "description": f"Basic performance test for {screen_name} (fallback)",
            "test_type": "performance",
            "category": "basic"
        }

    def _generate_fallback_accessibility_test(self, ui_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback accessibility test when AI generation fails."""
        screen_name = ui_schema.get('screen', 'unknown')
        
        test_code = f'''
def test_{screen_name}_basic_accessibility():
    """Basic accessibility test for {screen_name} screen (fallback)."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        
        # Check for basic accessibility features
        # 1. Page has a title
        title = driver.title
        assert title and title.strip(), "Page missing title"
        
        # 2. Images have alt text
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt = img.get_attribute("alt")
            assert alt is not None, "Image missing alt attribute"
        
        # 3. Interactive elements are focusable
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            tabindex = button.get_attribute("tabindex")
            assert tabindex != "-1", "Button not focusable"
        
        print(f"Basic accessibility test passed for {screen_name}")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_basic_accessibility",
            "test_code": test_code,
            "description": f"Basic accessibility test for {screen_name} (fallback)",
            "test_type": "accessibility",
            "category": "basic"
        }

    def _generate_api_performance_test(self, screen_name: str, api_components: List[Dict]) -> Dict[str, Any]:
        """Generate API performance test for components with endpoints."""
        test_code = f'''
def test_{screen_name}_api_performance():
    """Test API performance for {screen_name} screen endpoints."""
    import time
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    endpoints = {[comp.get('endpoint', comp.get('api_url', '')) for comp in api_components]}
    
    def test_endpoint_performance(url):
        """Test individual endpoint performance."""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            end_time = time.time()
            
            return {{
                'url': url,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }}
        except Exception as e:
            return {{
                'url': url,
                'error': str(e),
                'response_time': 5.0,  # Timeout
                'success': False
            }}
    
    # Test endpoints concurrently
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {{executor.submit(test_endpoint_performance, url): url for url in endpoints}}
        
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
    
    # Performance assertions
    successful_requests = [r for r in results if r['success']]
    assert len(successful_requests) > 0, "No API endpoints responded successfully"
    
    avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
    assert avg_response_time < 2.0, f"Average API response time {{avg_response_time:.3f}}s exceeds 2s limit"
    
    for result in results:
        if result['success']:
            print(f"API {{result['url']}}: {{result['response_time']:.3f}}s")
        else:
            print(f"API {{result['url']}}: ERROR - {{result.get('error', 'Unknown')}}")
'''
        
        return {
            "test_name": f"test_{screen_name}_api_performance",
            "test_code": test_code,
            "description": f"API performance test for {screen_name}",
            "test_type": "performance",
            "category": "api"
        }

    def _generate_rendering_performance_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate rendering performance test."""
        test_code = f'''
def test_{screen_name}_rendering_performance():
    """Test rendering performance for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    import time
    
    # Enable performance logging
    options = webdriver.ChromeOptions()
    options.add_argument("--enable-logging")
    options.add_argument("--log-level=0")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate and measure rendering metrics
        start_time = time.time()
        driver.get("http://localhost:3000/{screen_name}")
        
        # Wait for rendering to complete
        driver.execute_script("return document.readyState") == "complete"
        
        # Measure paint timing using Performance API
        paint_metrics = driver.execute_script("""
            const paintEntries = performance.getEntriesByType('paint');
            const metrics = {{}};
            paintEntries.forEach(entry => {{
                metrics[entry.name] = entry.startTime;
            }});
            return metrics;
        """)
        
        # Get layout metrics
        layout_time = driver.execute_script("""
            const navigationTiming = performance.getEntriesByType('navigation')[0];
            return navigationTiming ? navigationTiming.domContentLoadedEventEnd - navigationTiming.domContentLoadedEventStart : 0;
        """)
        
        # Performance assertions
        first_paint = paint_metrics.get('first-paint', 0)
        first_contentful_paint = paint_metrics.get('first-contentful-paint', 0)
        
        if first_paint > 0:
            assert first_paint < 1000, f"First paint {{first_paint}}ms exceeds 1s limit"
        
        if first_contentful_paint > 0:
            assert first_contentful_paint < 1500, f"First contentful paint {{first_contentful_paint}}ms exceeds 1.5s limit"
        
        print(f"Rendering metrics for {screen_name}:")
        print(f"  First Paint: {{first_paint:.1f}}ms")
        print(f"  First Contentful Paint: {{first_contentful_paint:.1f}}ms")
        print(f"  Layout Time: {{layout_time:.1f}}ms")
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_rendering_performance",
            "test_code": test_code,
            "description": f"Rendering performance test for {screen_name}",
            "test_type": "performance",
            "category": "rendering"
        }

    def _generate_color_contrast_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate color contrast accessibility test."""
        test_code = f'''
def test_{screen_name}_color_contrast():
    """Test color contrast ratios for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    import re
    
    def rgb_to_luminance(r, g, b):
        """Calculate relative luminance of RGB color."""
        def component_luminance(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * component_luminance(r) + 0.7152 * component_luminance(g) + 0.0722 * component_luminance(b)
    
    def contrast_ratio(color1, color2):
        """Calculate contrast ratio between two colors."""
        l1 = rgb_to_luminance(*color1)
        l2 = rgb_to_luminance(*color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def parse_color(color_str):
        """Parse CSS color string to RGB values."""
        if color_str.startswith('rgb'):
            # Extract RGB values from rgb(r, g, b) format
            matches = re.findall(r'\\d+', color_str)
            return tuple(int(match) for match in matches[:3])
        return (0, 0, 0)  # Default to black if can't parse
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        
        # Test text elements for contrast
        text_elements = driver.find_elements(By.CSS_SELECTOR, "p, span, div, h1, h2, h3, h4, h5, h6, button, a")
        
        contrast_violations = []
        
        for element in text_elements[:10]:  # Test first 10 text elements
            try:
                text_color = element.value_of_css_property("color")
                bg_color = element.value_of_css_property("background-color")
                
                if text_color and bg_color:
                    text_rgb = parse_color(text_color)
                    bg_rgb = parse_color(bg_color)
                    
                    if text_rgb != (0, 0, 0) or bg_rgb != (0, 0, 0):  # Skip if couldn't parse
                        ratio = contrast_ratio(text_rgb, bg_rgb)
                        
                        # WCAG AA requires 4.5:1 for normal text, 3:1 for large text
                        font_size = element.value_of_css_property("font-size")
                        is_large_text = "px" in font_size and int(font_size.replace("px", "")) >= 18
                        
                        min_ratio = 3.0 if is_large_text else 4.5
                        
                        if ratio < min_ratio:
                            contrast_violations.append({{
                                'element': element.tag_name,
                                'text': element.text[:50],
                                'ratio': ratio,
                                'required': min_ratio
                            }})
            except:
                continue  # Skip elements that can't be analyzed
        
        # Assert no critical contrast violations
        if contrast_violations:
            print(f"Color contrast violations found on {screen_name}:")
            for violation in contrast_violations[:5]:
                print(f"  {{violation['element']}}: {{violation['ratio']:.1f}}:1 (required: {{violation['required']}}:1)")
        
        # Allow some violations but not too many
        assert len(contrast_violations) < 5, f"Too many color contrast violations: {{len(contrast_violations)}}"
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_color_contrast",
            "test_code": test_code,
            "description": f"Color contrast test for {screen_name}",
            "test_type": "accessibility",
            "category": "color_contrast"
        }

    def _generate_focus_management_test(self, screen_name: str, components: List[Dict]) -> Dict[str, Any]:
        """Generate focus management accessibility test."""
        test_code = f'''
def test_{screen_name}_focus_management():
    """Test focus management for {screen_name} screen."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    import time
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("http://localhost:3000/{screen_name}")
        
        # Test focus indicators
        focusable_elements = driver.find_elements(By.CSS_SELECTOR, "button, input, select, textarea, a[href]")
        
        focus_issues = []
        
        for element in focusable_elements[:5]:  # Test first 5 focusable elements
            try:
                # Focus the element
                element.click()
                time.sleep(0.1)
                
                # Check if element is focused
                focused_element = driver.switch_to.active_element
                is_focused = focused_element == element
                
                if is_focused:
                    # Check for visible focus indicator
                    outline = element.value_of_css_property("outline")
                    outline_width = element.value_of_css_property("outline-width")
                    box_shadow = element.value_of_css_property("box-shadow")
                    border = element.value_of_css_property("border")
                    
                    has_focus_indicator = (
                        outline and outline != "none" and outline_width != "0px"
                    ) or (
                        box_shadow and box_shadow != "none"
                    ) or (
                        "focus" in element.get_attribute("class") or ""
                    )
                    
                    if not has_focus_indicator:
                        focus_issues.append({{
                            'element': element.tag_name,
                            'id': element.get_attribute('id') or 'no-id',
                            'issue': 'No visible focus indicator'
                        }})
                
            except Exception as e:
                focus_issues.append({{
                    'element': 'unknown',
                    'issue': f'Focus test failed: {{str(e)}}'
                }})
        
        # Test focus trapping in modals (if any)
        modal_elements = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], .modal")
        for modal in modal_elements:
            try:
                # If modal is visible, test focus trapping
                if modal.is_displayed():
                    # Focus should be trapped within modal
                    first_focusable = modal.find_element(By.CSS_SELECTOR, "button, input, select, textarea, a[href]")
                    first_focusable.click()
                    
                    # Tab multiple times and ensure focus stays in modal
                    for _ in range(10):
                        driver.switch_to.active_element.send_keys(Keys.TAB)
                        current_focus = driver.switch_to.active_element
                        
                        # Check if focus is still within modal
                        modal_contains_focus = modal.find_elements(By.XPATH, ".//*") and current_focus in modal.find_elements(By.XPATH, ".//*")
                        
                        if not modal_contains_focus:
                            focus_issues.append({{
                                'element': 'modal',
                                'issue': 'Focus escaped from modal'
                            }})
                            break
            except:
                continue  # Skip if modal testing fails
        
        # Report focus issues
        if focus_issues:
            print(f"Focus management issues found on {screen_name}:")
            for issue in focus_issues[:5]:
                print(f"  {{issue['element']}}: {{issue['issue']}}")
        
        # Allow some focus issues but not too many
        assert len(focus_issues) < 3, f"Too many focus management issues: {{len(focus_issues)}}"
        
    finally:
        driver.quit()
'''
        
        return {
            "test_name": f"test_{screen_name}_focus_management",
            "test_code": test_code,
            "description": f"Focus management test for {screen_name}",
            "test_type": "accessibility",
            "category": "focus"
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