import re
from typing import Dict, List, Any


class FastballGatewayParser:
    """Parser for MLB Fastball Gateway GraphQL schemas and responses."""
    
    def __init__(self):
        self.type_definitions = {}
        self.queries = {}
        self.mutations = {}
    
    def parse_schema(self, schema_text: str) -> Dict[str, Any]:
        """Parse GraphQL schema text and extract type definitions."""
        if not schema_text or not schema_text.strip():
            raise ValueError("Empty schema text provided")
        
        # Check for basic GraphQL schema structure
        schema_lower = schema_text.lower()
        if not any(keyword in schema_lower for keyword in ['type', 'query', 'mutation', 'schema']):
            raise ValueError("Invalid GraphQL schema format")
        
        # Extract type definitions
        type_pattern = r'type\s+(\w+)\s*\{([^}]+)\}'
        type_matches = re.findall(type_pattern, schema_text, re.DOTALL)
        
        for type_name, type_fields in type_matches:
            self.type_definitions[type_name] = self._parse_fields(type_fields)
        
        # Extract queries
        query_pattern = r'type\s+Query\s*\{([^}]+)\}'
        query_match = re.search(query_pattern, schema_text, re.DOTALL)
        if query_match:
            self.queries = self._parse_fields(query_match.group(1))
        
        return {
            "parsed": True,
            "types": self.type_definitions,
            "queries": self.queries,
            "mutations": self.mutations
        }
    
    def _parse_fields(self, fields_text: str) -> Dict[str, str]:
        """Parse field definitions from type or query text."""
        fields = {}
        field_pattern = r'(\w+):\s*([^\n]+)'
        field_matches = re.findall(field_pattern, fields_text)
        
        for field_name, field_type in field_matches:
            fields[field_name] = field_type.strip()
        
        return fields
    
    def extract_sdui_components(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract server-driven UI components from Fastball response."""
        components = []
        
        # Look for common SDUI patterns in MLB responses
        if 'data' in response_data:
            data = response_data['data']
            
            # Extract layout components
            if 'layout' in data:
                layout = data['layout']
                if isinstance(layout, dict) and 'sections' in layout:
                    for section in layout['sections']:
                        components.append({
                            'type': 'layout_section',
                            'id': section.get('id', 'unknown'),
                            'component_type': section.get('type', 'generic'),
                            'properties': section
                        })
            
            # Extract web view components
            if 'webViews' in data:
                for webview in data['webViews']:
                    components.append({
                        'type': 'webview',
                        'id': webview.get('id', 'unknown'),
                        'url': webview.get('url', ''),
                        'requires_auth': webview.get('requiresAuth', False),
                        'properties': webview
                    })
            
            # Extract navigation components
            if 'navigation' in data:
                nav = data['navigation']
                components.append({
                    'type': 'navigation',
                    'id': 'main_navigation',
                    'items': nav.get('items', []),
                    'properties': nav
                })
        
        return components
    
    def validate_response_structure(self, response_data: Dict[str, Any]) -> bool:
        """Validate that response follows expected Fastball Gateway structure."""
        required_fields = ['data']
        
        for field in required_fields:
            if field not in response_data:
                return False
        
        # Check for errors in GraphQL response
        if 'errors' in response_data and response_data['errors']:
            return False
        
        return True