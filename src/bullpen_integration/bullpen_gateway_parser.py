"""
Parser for MLB's Bullpen Gateway SDUI responses.
Handles screens, sections, layouts, and all component types.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class SDUIComponent:
    """Represents a component in the SDUI response."""
    id: str
    type: str
    properties: Dict[str, Any]
    test_requirements: List[str]
    test_code: Optional[str] = None

@dataclass
class SDUITestScenario:
    """Represents a test scenario for an SDUI component."""
    name: str
    type: str
    description: str
    priority: str
    component_id: str
    test_code: str
    authentication_required: bool = False

class BullpenGatewayParser:
    """Parse and analyze Bullpen Gateway SDUI responses."""

    # Supported SDUI component types
    COMPONENT_TYPES = {
        'WEBVIEW': 'webview',
        'PROMO_BANNER': 'promo_banner',
        'TILE_GRID': 'tile_grid',
        'CARD_GRID': 'card_grid',
        'LIST': 'list',
        'HERO_BANNER': 'hero_banner',
        'NAVIGATION': 'navigation'
    }

    @staticmethod
    def parse_sdui_response(response: Dict, request_data: Dict = None) -> Dict:
        """Parse the SDUI response structure."""
        if request_data is None:
            request_data = {}

        structure = {
            'screens': [],
            'sections': [],
            'layouts': [],
            'webviews': [],
            'promo_banners': [],
            'tile_grids': [],
            'authentication': request_data.get('headers', {}).get('Authorization'),
            'platform': request_data.get('platform', 'ios'),
            'test_scenarios': [],
            'components': []
        }

        # Parse screens
        for screen in response.get('screens', []):
            screen_info = BullpenGatewayParser._parse_screen(screen)
            structure['screens'].append(screen_info)

            # Generate test scenarios for screen layout
            structure['test_scenarios'].extend(
                BullpenGatewayParser._generate_screen_test_scenarios(screen_info)
            )

        # Parse sections with enhanced component handling
        for section in response.get('sections', []):
            section_info = BullpenGatewayParser._parse_section(section)
            structure['sections'].append(section_info)

            # Create component object
            component = SDUIComponent(
                id=section_info['id'],
                type=section_info['componentType'],
                properties=section_info['details'],
                test_requirements=section_info.get('test_requirements', [])
            )
            structure['components'].append(component)

            # Generate component-specific test scenarios
            test_scenarios = BullpenGatewayParser._generate_component_test_scenarios(section_info)
            structure['test_scenarios'].extend(test_scenarios)

            # Categorize by component type
            component_type = section_info['componentType']
            if component_type == 'WEBVIEW':
                webview = section_info['details']
                structure['webviews'].append({
                    'id': section_info['id'],
                    'url': webview.get('url'),
                    'authentication': webview.get('authentication'),
                    'allowScrolling': webview.get('allowScrolling'),
                    'pullToRefresh': webview.get('pullToRefreshEnabled'),
                    'blockedDomains': webview.get('blockedDomain', [])
                })
            elif component_type == 'PROMO_BANNER':
                structure['promo_banners'].append(section_info['details'])
            elif component_type == 'TILE_GRID':
                structure['tile_grids'].append(section_info['details'])

        return structure

    @staticmethod
    def _parse_screen(screen: Dict) -> Dict:
        """Parse a single screen object."""
        screen_info = {
            'id': screen['id'],
            'type': screen['screenProperties']['type'],
            'layout': screen.get('layout', {}),
            'analytics': screen.get('screenLoadAction', {}).get('analyticsTrackingData', {}),
            'section_ids': []
        }

        # Extract section IDs from layout
        for layout_type in ['wide', 'compact']:
            layout = screen_info['layout'].get(layout_type, {})
            main_placement = layout.get('main', {})
            if main_placement.get('type') == 'MultipleSectionsPlacement':
                section_details = main_placement.get('sectionDetails', [])
                screen_info['section_ids'] = [detail['sectionId'] for detail in section_details]
                break

        return screen_info

    @staticmethod
    def _parse_section(section: Dict) -> Dict:
        """Parse a single section object."""
        section_info = {
            'id': section['id'],
            'componentType': section['sectionComponentType'],
            'details': section.get('section', {}),
            'test_requirements': []
        }

        # Add component-specific test requirements
        component_type = section['sectionComponentType']
        section_details = section.get('section', {})

        if component_type == 'WEBVIEW':
            section_info['test_requirements'] = [
                'url_loading',
                'authentication_handling',
                'scroll_behavior',
                'pull_to_refresh'
            ]
        elif component_type == 'PROMO_BANNER':
            section_info['test_requirements'] = [
                'image_loading',
                'deeplink_navigation',
                'analytics_tracking',
                'accessibility'
            ]
        elif component_type == 'TILE_GRID':
            section_info['test_requirements'] = [
                'grid_layout',
                'tile_interactions',
                'deeplink_navigation',
                'analytics_tracking',
                'accessibility'
            ]

        return section_info
    
    @staticmethod
    def _generate_screen_test_scenarios(screen_info: Dict) -> List[SDUITestScenario]:
        """Generate test scenarios for a screen."""
        scenarios = []

        # Layout tests
        if 'layout' in screen_info:
            for view_type in ['wide', 'compact']:
                if view_type in screen_info['layout']:
                    test_code = BullpenGatewayParser._generate_layout_test_code(
                        screen_info['id'], view_type, screen_info['layout'][view_type]
                    )
                    scenarios.append(SDUITestScenario(
                        name=f"test_{screen_info['id']}_{view_type}_layout",
                        type='layout',
                        description=f"Verify {view_type} layout renders correctly",
                        priority='high',
                        component_id=screen_info['id'],
                        test_code=test_code
                    ))

        # Analytics tests
        if 'analytics' in screen_info and screen_info['analytics']:
            page_tag = screen_info['analytics'].get('pageTag', 'unknown')
            test_code = BullpenGatewayParser._generate_analytics_test_code(
                screen_info['id'], page_tag
            )
            scenarios.append(SDUITestScenario(
                name=f"test_{screen_info['id']}_analytics_tracking",
                type='analytics',
                description=f"Verify analytics pageTag '{page_tag}' is tracked",
                priority='medium',
                component_id=screen_info['id'],
                test_code=test_code
            ))

        return scenarios

    @staticmethod
    def _generate_component_test_scenarios(section_info: Dict) -> List[SDUITestScenario]:
        """Generate test scenarios for a component section."""
        scenarios = []
        component_type = section_info['componentType']
        component_id = section_info['id']
        details = section_info['details']

        if component_type == 'WEBVIEW':
            scenarios.extend(BullpenGatewayParser._generate_webview_test_scenarios(component_id, details))
        elif component_type == 'PROMO_BANNER':
            scenarios.extend(BullpenGatewayParser._generate_promo_banner_test_scenarios(component_id, details))
        elif component_type == 'TILE_GRID':
            scenarios.extend(BullpenGatewayParser._generate_tile_grid_test_scenarios(component_id, details))

        return scenarios

    @staticmethod
    def _generate_webview_test_scenarios(component_id: str, details: Dict) -> List[SDUITestScenario]:
        """Generate test scenarios for WebView components."""
        scenarios = []
        url = details.get('url', '')
        requires_auth = details.get('authentication') in ['COOKIE', 'BEARER']

        # URL loading test
        test_code = f'''def test_webview_{component_id}_url_loading():
    """Test WebView URL loading for component {component_id}."""
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import pytest

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to WebView URL
        driver.get("{url}")

        # Wait for page to load
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

        # Verify URL loaded successfully
        assert driver.current_url == "{url}", "WebView should load correct URL"

        # Verify page is not showing error
        page_text = driver.page_source.lower()
        assert "404" not in page_text, "WebView should not show 404 error"
        assert "error" not in page_text, "WebView should not show error page"

    finally:
        driver.quit()'''

        scenarios.append(SDUITestScenario(
            name=f"test_webview_{component_id}_url_loading",
            type='webview_url',
            description=f"Test WebView URL loading for {url}",
            priority='high',
            component_id=component_id,
            test_code=test_code,
            authentication_required=requires_auth
        ))

        # Pull to refresh test if enabled
        if details.get('pullToRefreshEnabled'):
            pull_refresh_code = f'''def test_webview_{component_id}_pull_to_refresh():
    """Test WebView pull-to-refresh functionality."""
    from selenium import webdriver
    from selenium.webdriver.common.action_chains import ActionChains
    import time

    driver = webdriver.Chrome()

    try:
        driver.get("{url}")
        time.sleep(2)

        # Simulate pull-to-refresh gesture
        actions = ActionChains(driver)
        actions.move_by_offset(0, 100)
        actions.click_and_hold()
        actions.move_by_offset(0, -200)
        actions.release()
        actions.perform()

        # Wait for refresh to complete
        time.sleep(3)

        # Verify page still loads correctly after refresh
        assert driver.current_url == "{url}", "URL should remain same after refresh"

    finally:
        driver.quit()'''

            scenarios.append(SDUITestScenario(
                name=f"test_webview_{component_id}_pull_to_refresh",
                type='webview_refresh',
                description="Test WebView pull-to-refresh functionality",
                priority='medium',
                component_id=component_id,
                test_code=pull_refresh_code
            ))

        return scenarios

    @staticmethod
    def _generate_promo_banner_test_scenarios(component_id: str, details: Dict) -> List[SDUITestScenario]:
        """Generate test scenarios for PromoBanner components."""
        scenarios = []
        action = details.get('action', {})
        deeplink_url = action.get('deeplinkURL', '')

        # Image loading test
        background_image = details.get('backgroundImageUrl', '')
        if background_image:
            image_test_code = f'''def test_promo_banner_{component_id}_image_loading():
    """Test PromoBanner image loading."""
    import requests

    # Test background image URL accessibility
    response = requests.head("{background_image}")
    assert response.status_code == 200, "Background image should be accessible"

    # Verify image content type
    content_type = response.headers.get('content-type', '')
    assert 'image' in content_type, "URL should return image content"'''

            scenarios.append(SDUITestScenario(
                name=f"test_promo_banner_{component_id}_image_loading",
                type='image_loading',
                description="Test PromoBanner background image loading",
                priority='medium',
                component_id=component_id,
                test_code=image_test_code
            ))

        # Deeplink navigation test
        if deeplink_url:
            deeplink_test_code = f'''def test_promo_banner_{component_id}_deeplink_navigation():
    """Test PromoBanner deeplink navigation."""
    # Note: This would need platform-specific implementation
    # For iOS: XCTest with URL scheme handling
    # For Android: Espresso with Intent verification

    deeplink_url = "{deeplink_url}"

    # Verify deeplink format
    assert deeplink_url.startswith('mlbatbat://'), "Deeplink should use MLB app scheme"

    # Test deeplink components
    if 'webview' in deeplink_url:
        assert 'url=' in deeplink_url, "WebView deeplink should contain URL parameter"

    # This test would need platform-specific implementation'''

            scenarios.append(SDUITestScenario(
                name=f"test_promo_banner_{component_id}_deeplink_navigation",
                type='deeplink',
                description=f"Test PromoBanner deeplink to {deeplink_url}",
                priority='high',
                component_id=component_id,
                test_code=deeplink_test_code
            ))

        return scenarios

    @staticmethod
    def _generate_tile_grid_test_scenarios(component_id: str, details: Dict) -> List[SDUITestScenario]:
        """Generate test scenarios for TileGrid components."""
        scenarios = []
        items = details.get('items', [])

        # Grid layout test
        grid_test_code = f'''def test_tile_grid_{component_id}_layout():
    """Test TileGrid layout and items."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    driver = webdriver.Chrome()

    try:
        # This would need to be the actual app screen containing the grid
        # For now, testing grid properties

        expected_items = {len(items)}

        # Verify grid has expected number of items
        grid_items = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='tile-grid-item']")
        assert len(grid_items) == expected_items, f"Grid should contain {{expected_items}} items"

        # Verify each item is visible
        for item in grid_items:
            assert item.is_displayed(), "Each grid item should be visible"

    finally:
        driver.quit()'''

        scenarios.append(SDUITestScenario(
            name=f"test_tile_grid_{component_id}_layout",
            type='grid_layout',
            description=f"Test TileGrid layout with {len(items)} items",
            priority='medium',
            component_id=component_id,
            test_code=grid_test_code
        ))

        return scenarios

    @staticmethod
    def _generate_layout_test_code(screen_id: str, layout_type: str, layout_config: Dict) -> str:
        """Generate test code for layout verification."""
        return f'''def test_screen_{screen_id}_{layout_type}_layout():
    """Test {layout_type} layout rendering for screen {screen_id}."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    driver = webdriver.Chrome()

    try:
        # Set viewport for {layout_type} layout
        if "{layout_type}" == "wide":
            driver.set_window_size(1024, 768)  # Wide layout viewport
        else:
            driver.set_window_size(375, 667)   # Compact layout viewport

        # Navigate to screen
        driver.get("http://localhost:8000/screen/{screen_id}")

        # Verify layout type is applied
        layout_element = driver.find_element(By.CSS_SELECTOR, "[data-layout-type='{layout_type}']")
        assert layout_element.is_displayed(), "{layout_type.title()} layout should be visible"

        # Verify main content area
        main_content = driver.find_element(By.CSS_SELECTOR, "[data-placement='main']")
        assert main_content.is_displayed(), "Main content area should be visible"

    finally:
        driver.quit()'''

    @staticmethod
    def _generate_analytics_test_code(screen_id: str, page_tag: str) -> str:
        """Generate test code for analytics verification."""
        return f'''def test_screen_{screen_id}_analytics_tracking():
    """Test analytics tracking for screen {screen_id}."""
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    import json

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to screen
        driver.get("http://localhost:8000/screen/{screen_id}")

        # Wait for analytics to fire
        wait.until(lambda driver: driver.execute_script(
            "return window.analytics && window.analytics.queue.length > 0"
        ))

        # Check analytics data
        analytics_data = driver.execute_script("return window.analytics.queue")

        # Verify page tag is tracked
        page_events = [event for event in analytics_data if event.get('pageTag') == '{page_tag}']
        assert len(page_events) > 0, f"Analytics should track pageTag '{page_tag}'"

    finally:
        driver.quit()'''