"""
Parser for MLB's Bullpen Gateway SDUI responses.
Handles screens, sections, layouts, and WebView components.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from loguru import logger

@dataclass
class SDUIComponent:
    """Represents a component in the SDUI response."""
    id: str
    type: str
    properties: Dict[str, Any]
    test_requirements: List[str]

class BullpenGatewayParser:
    """Parse and analyze Bullpen Gateway SDUI responses."""
    
    @staticmethod
    def parse_sdui_response(response: Dict, request_data: Dict) -> Dict:
        """Parse the SDUI response structure."""
        structure = {
            'screens': [],
            'sections': [],
            'layouts': [],
            'webviews': [],
            'authentication': request_data.get('headers', {}).get('Authorization'),
            'platform': request_data.get('platform', 'ios'),
            'test_scenarios': []
        }
        
        # Parse screens
        for screen in response.get('screens', []):
            screen_info = {
                'id': screen['id'],
                'type': screen['screenProperties']['type'],
                'layout': screen.get('layout', {}),
                'analytics': screen.get('screenLoadAction', {}).get('analyticsTrackingData', {})
            }
            structure['screens'].append(screen_info)
            
            # Identify test scenarios for screen
            structure['test_scenarios'].extend(
                BullpenGatewayParser._generate_screen_test_scenarios(screen_info)
            )
        
        # Parse sections (especially WebView sections)
        for section in response.get('sections', []):
            section_info = {
                'id': section['id'],
                'componentType': section['sectionComponentType'],
                'details': section.get('section', {})
            }
            
            if section['sectionComponentType'] == 'WEBVIEW':
                webview = section['section']
                structure['webviews'].append({
                    'url': webview['url'],
                    'authentication': webview.get('authentication'),
                    'allowScrolling': webview.get('allowScrolling'),
                    'pullToRefresh': webview.get('pullToRefreshEnabled'),
                    'blockedDomains': webview.get('blockedDomain', [])
                })
            
            structure['sections'].append(section_info)
        
        return structure
    
    @staticmethod
    def _generate_screen_test_scenarios(screen_info: Dict) -> List[Dict]:
        """Generate test scenarios for a screen."""
        scenarios = []
        
        # Layout tests
        if 'layout' in screen_info:
            for view_type in ['wide', 'compact']:
                if view_type in screen_info['layout']:
                    scenarios.append({
                        'type': 'layout',
                        'name': f"test_{screen_info['id']}_{view_type}_layout",
                        'description': f"Verify {view_type} layout renders correctly",
                        'priority': 'high'
                    })
        
        # Analytics tests
        if 'analytics' in screen_info and screen_info['analytics']:
            scenarios.append({
                'type': 'analytics',
                'name': f"test_{screen_info['id']}_analytics_tracking",
                'description': f"Verify analytics pageTag '{screen_info['analytics'].get('pageTag')}' is tracked",
                'priority': 'medium'
            })
        
        return scenarios