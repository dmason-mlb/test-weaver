import pytest

# test_9_mlb_integration.py
def test_graphql_schema_parsing_failure():
    """Test that invalid GraphQL schema from Fastball Gateway is rejected"""
    from src.mlb_integration import FastballGatewayParser
    
    parser = FastballGatewayParser()
    invalid_schema = "not a valid graphql schema"
    
    with pytest.raises(ValueError, match="Invalid GraphQL schema format"):
        parser.parse_schema(invalid_schema)

def test_my_daily_story_component_not_supported():
    """Test that unsupported MDS components are flagged"""
    from src.mlb_integration import MDSComponentAnalyzer
    
    analyzer = MDSComponentAnalyzer()
    component = {"type": "3d_stadium_view", "data": {}}
    
    with pytest.raises(NotImplementedError, match="Component type '3d_stadium_view' not in MDS specification"):
        analyzer.analyze_component(component)

def test_server_driven_ui_version_mismatch():
    """Test that version mismatches between Android and iOS are detected"""
    from src.mlb_integration import CrossPlatformValidator, VersionError
    
    validator = CrossPlatformValidator()
    android_schema = {"version": "2.1.0", "components": []}
    ios_schema = {"version": "2.0.0", "components": []}
    
    with pytest.raises(VersionError, match="Schema version mismatch: Android 2.1.0 != iOS 2.0.0"):
        validator.validate_parity(android_schema, ios_schema)