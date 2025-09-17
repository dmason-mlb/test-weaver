from typing import Dict, List, Any, Tuple
import json


class VersionError(Exception):
    pass


class ComponentMismatchError(Exception):
    pass


class CrossPlatformValidator:
    """Validates consistency between iOS and Android SDUI implementations."""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_fields = [
            'id', 'type', 'url', 'title', 'required', 
            'visible', 'enabled', 'navigation', 'authentication'
        ]
    
    def validate_parity(self, android_schema: Dict[str, Any], ios_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parity between Android and iOS schemas."""
        results = {
            "parity": True,
            "version_match": True,
            "component_match": True,
            "field_match": True,
            "differences": [],
            "warnings": []
        }
        
        # Version validation
        android_version = android_schema.get('version')
        ios_version = ios_schema.get('version')
        
        if android_version != ios_version:
            results["version_match"] = False
            results["parity"] = False
            results["differences"].append({
                "type": "version_mismatch",
                "android": android_version,
                "ios": ios_version
            })
            raise VersionError(f"Schema version mismatch: Android {android_version} != iOS {ios_version}")
        
        # Component structure validation
        android_components = self._extract_components(android_schema)
        ios_components = self._extract_components(ios_schema)
        
        component_comparison = self._compare_components(android_components, ios_components)
        if not component_comparison["match"]:
            results["component_match"] = False
            results["parity"] = False
            results["differences"].extend(component_comparison["differences"])
        
        # Field-level validation for critical fields
        field_comparison = self._compare_critical_fields(android_schema, ios_schema)
        if not field_comparison["match"]:
            results["field_match"] = False
            results["parity"] = False
            results["differences"].extend(field_comparison["differences"])
        
        # Platform-specific features validation
        platform_validation = self._validate_platform_features(android_schema, ios_schema)
        results["warnings"].extend(platform_validation["warnings"])
        
        return results
    
    def _extract_components(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract components from schema for comparison."""
        components = []
        
        if 'components' in schema:
            components.extend(schema['components'])
        
        if 'layout' in schema and isinstance(schema['layout'], dict):
            if 'sections' in schema['layout']:
                components.extend(schema['layout']['sections'])
        
        if 'navigation' in schema:
            components.append({
                'type': 'navigation',
                'id': 'main_navigation',
                'properties': schema['navigation']
            })
        
        return components
    
    def _compare_components(self, android_components: List[Dict], ios_components: List[Dict]) -> Dict[str, Any]:
        """Compare components between platforms."""
        result = {"match": True, "differences": []}
        
        # Create component maps by ID for comparison
        android_map = {comp.get('id', 'unknown'): comp for comp in android_components}
        ios_map = {comp.get('id', 'unknown'): comp for comp in ios_components}
        
        all_component_ids = set(android_map.keys()) | set(ios_map.keys())
        
        for comp_id in all_component_ids:
            android_comp = android_map.get(comp_id)
            ios_comp = ios_map.get(comp_id)
            
            if android_comp and not ios_comp:
                result["match"] = False
                result["differences"].append({
                    "type": "missing_ios_component",
                    "component_id": comp_id,
                    "android_component": android_comp
                })
            elif ios_comp and not android_comp:
                result["match"] = False
                result["differences"].append({
                    "type": "missing_android_component",
                    "component_id": comp_id,
                    "ios_component": ios_comp
                })
            elif android_comp and ios_comp:
                # Compare component types
                android_type = android_comp.get('type')
                ios_type = ios_comp.get('type')
                
                if android_type != ios_type:
                    result["match"] = False
                    result["differences"].append({
                        "type": "component_type_mismatch",
                        "component_id": comp_id,
                        "android_type": android_type,
                        "ios_type": ios_type
                    })
        
        return result
    
    def _compare_critical_fields(self, android_schema: Dict, ios_schema: Dict) -> Dict[str, Any]:
        """Compare critical fields between platforms."""
        result = {"match": True, "differences": []}
        
        for field in self.critical_fields:
            android_value = self._deep_get(android_schema, field)
            ios_value = self._deep_get(ios_schema, field)
            
            if android_value != ios_value:
                # Only consider it a mismatch if both platforms have the field
                if android_value is not None and ios_value is not None:
                    result["match"] = False
                    result["differences"].append({
                        "type": "field_value_mismatch",
                        "field": field,
                        "android_value": android_value,
                        "ios_value": ios_value
                    })
        
        return result
    
    def _validate_platform_features(self, android_schema: Dict, ios_schema: Dict) -> Dict[str, Any]:
        """Validate platform-specific features and capabilities."""
        result = {"warnings": []}
        
        # Check for platform-specific authentication methods
        android_auth = android_schema.get('authentication', {})
        ios_auth = ios_schema.get('authentication', {})
        
        android_methods = android_auth.get('methods', [])
        ios_methods = ios_auth.get('methods', [])
        
        if set(android_methods) != set(ios_methods):
            result["warnings"].append({
                "type": "auth_method_difference",
                "message": "Authentication methods differ between platforms",
                "android_methods": android_methods,
                "ios_methods": ios_methods
            })
        
        # Check for platform-specific UI capabilities
        android_ui = android_schema.get('ui_capabilities', {})
        ios_ui = ios_schema.get('ui_capabilities', {})
        
        if android_ui != ios_ui:
            result["warnings"].append({
                "type": "ui_capability_difference",
                "message": "UI capabilities differ between platforms",
                "details": {
                    "android": android_ui,
                    "ios": ios_ui
                }
            })
        
        return result
    
    def _deep_get(self, data: Dict, key: str) -> Any:
        """Get value from nested dictionary structure."""
        if not isinstance(data, dict):
            return None
        
        # Direct key lookup
        if key in data:
            return data[key]
        
        # Search in nested structures
        for value in data.values():
            if isinstance(value, dict):
                result = self._deep_get(value, key)
                if result is not None:
                    return result
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result = self._deep_get(item, key)
                        if result is not None:
                            return result
        
        return None
    
    def generate_test_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate test recommendations based on validation results."""
        recommendations = []
        
        if not validation_results["parity"]:
            recommendations.append("Add cross-platform consistency tests")
        
        if not validation_results["version_match"]:
            recommendations.append("Add version synchronization tests")
        
        if not validation_results["component_match"]:
            recommendations.append("Add component availability tests for both platforms")
        
        if not validation_results["field_match"]:
            recommendations.append("Add field validation tests for critical properties")
        
        if validation_results["warnings"]:
            recommendations.append("Add platform-specific feature tests")
        
        return recommendations