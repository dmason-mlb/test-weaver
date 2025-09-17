"""
Tests for MLB integration modules.
"""

import pytest
import json
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_integration.fastball_parser import FastballGatewayParser
from mlb_integration.cross_platform_validator import (
    CrossPlatformValidator, 
    VersionError, 
    ComponentMismatchError
)
from mlb_integration.mds_analyzer import MDSComponentAnalyzer


class TestFastballGatewayParser:
    """Test Fastball Gateway parser functionality."""
    
    def test_init(self):
        """Test parser initialization."""
        parser = FastballGatewayParser()
        assert parser.type_definitions == {}
        assert parser.queries == {}
        assert parser.mutations == {}
    
    def test_parse_schema_valid(self):
        """Test parsing valid GraphQL schema."""
        schema_text = """
        type User {
            id: String!
            name: String
            email: String
        }
        
        type Query {
            user(id: String!): User
            users: [User]
        }
        """
        
        parser = FastballGatewayParser()
        result = parser.parse_schema(schema_text)
        
        assert result["parsed"] is True
        assert "User" in result["types"]
        # The regex captures the full line, so check for the field names
        assert any("user" in field for field in result["queries"].keys())
        assert any("users" in field for field in result["queries"].keys())
    
    def test_parse_schema_empty(self):
        """Test parsing empty schema."""
        parser = FastballGatewayParser()
        
        with pytest.raises(ValueError, match="Empty schema text provided"):
            parser.parse_schema("")
    
    def test_parse_schema_invalid(self):
        """Test parsing invalid schema."""
        parser = FastballGatewayParser()
        
        with pytest.raises(ValueError, match="Invalid GraphQL schema format"):
            parser.parse_schema("completely invalid content with no keywords")
    
    def test_extract_sdui_components_full(self):
        """Test extracting SDUI components from full response."""
        response_data = {
            "data": {
                "layout": {
                    "sections": [
                        {"id": "header", "type": "header_section"},
                        {"id": "content", "type": "content_section"}
                    ]
                },
                "webViews": [
                    {"id": "gameday_view", "url": "https://mlb.com/gameday", "requiresAuth": True}
                ],
                "navigation": {
                    "items": ["home", "scores", "teams"]
                }
            }
        }
        
        parser = FastballGatewayParser()
        components = parser.extract_sdui_components(response_data)
        
        assert len(components) == 4  # 2 layout sections + 1 webview + 1 navigation
        
        # Check layout components
        layout_components = [c for c in components if c["type"] == "layout_section"]
        assert len(layout_components) == 2
        
        # Check webview components
        webview_components = [c for c in components if c["type"] == "webview"]
        assert len(webview_components) == 1
        assert webview_components[0]["requires_auth"] is True
        
        # Check navigation components
        nav_components = [c for c in components if c["type"] == "navigation"]
        assert len(nav_components) == 1
    
    def test_extract_sdui_components_empty(self):
        """Test extracting components from empty response."""
        parser = FastballGatewayParser()
        components = parser.extract_sdui_components({})
        
        assert components == []
    
    def test_validate_response_structure_valid(self):
        """Test validating valid response structure."""
        response_data = {"data": {"user": {"id": "123"}}}
        
        parser = FastballGatewayParser()
        assert parser.validate_response_structure(response_data) is True
    
    def test_validate_response_structure_missing_data(self):
        """Test validating response missing data field."""
        response_data = {"user": {"id": "123"}}
        
        parser = FastballGatewayParser()
        assert parser.validate_response_structure(response_data) is False
    
    def test_validate_response_structure_with_errors(self):
        """Test validating response with GraphQL errors."""
        response_data = {
            "data": {"user": None},
            "errors": [{"message": "User not found"}]
        }
        
        parser = FastballGatewayParser()
        assert parser.validate_response_structure(response_data) is False


class TestCrossPlatformValidator:
    """Test cross-platform validation functionality."""
    
    def test_init(self):
        """Test validator initialization."""
        validator = CrossPlatformValidator()
        assert len(validator.critical_fields) > 0
        assert 'id' in validator.critical_fields
        assert 'type' in validator.critical_fields
    
    def test_validate_parity_matching_versions(self):
        """Test validation with matching versions."""
        android_schema = {"version": "1.0", "components": []}
        ios_schema = {"version": "1.0", "components": []}
        
        validator = CrossPlatformValidator()
        result = validator.validate_parity(android_schema, ios_schema)
        
        assert result["parity"] is True
        assert result["version_match"] is True
        assert result["component_match"] is True
        assert len(result["differences"]) == 0
    
    def test_validate_parity_version_mismatch(self):
        """Test validation with version mismatch."""
        android_schema = {"version": "1.0"}
        ios_schema = {"version": "1.1"}
        
        validator = CrossPlatformValidator()
        
        with pytest.raises(VersionError):
            validator.validate_parity(android_schema, ios_schema)
    
    def test_validate_parity_component_mismatch(self):
        """Test validation with component mismatch."""
        android_schema = {
            "version": "1.0",
            "components": [
                {"id": "button1", "type": "button"},
                {"id": "list1", "type": "list"}
            ]
        }
        ios_schema = {
            "version": "1.0",
            "components": [
                {"id": "button1", "type": "button"}
                # missing list1
            ]
        }
        
        validator = CrossPlatformValidator()
        result = validator.validate_parity(android_schema, ios_schema)
        
        assert result["parity"] is False
        assert result["component_match"] is False
        assert len(result["differences"]) > 0
        
        # Check for missing component difference
        missing_diff = next(
            (d for d in result["differences"] if d["type"] == "missing_ios_component"), 
            None
        )
        assert missing_diff is not None
        assert missing_diff["component_id"] == "list1"
    
    def test_compare_critical_fields(self):
        """Test critical field comparison."""
        android_schema = {"id": "test", "type": "button", "visible": True}
        ios_schema = {"id": "test", "type": "list", "visible": True}  # Different type
        
        validator = CrossPlatformValidator()
        result = validator._compare_critical_fields(android_schema, ios_schema)
        
        assert result["match"] is False
        assert len(result["differences"]) > 0
        
        # Check for field mismatch
        type_diff = next(
            (d for d in result["differences"] if d["field"] == "type"), 
            None
        )
        assert type_diff is not None
        assert type_diff["android_value"] == "button"
        assert type_diff["ios_value"] == "list"
    
    def test_generate_test_recommendations(self):
        """Test test recommendation generation."""
        validation_results = {
            "parity": False,
            "version_match": False,
            "component_match": True,
            "field_match": False,
            "warnings": [{"type": "auth_method_difference"}]
        }
        
        validator = CrossPlatformValidator()
        recommendations = validator.generate_test_recommendations(validation_results)
        
        assert len(recommendations) > 0
        assert "Add cross-platform consistency tests" in recommendations
        assert "Add version synchronization tests" in recommendations
        assert "Add field validation tests for critical properties" in recommendations


class TestMDSComponentAnalyzer:
    """Test MDS component analyzer functionality."""
    
    def test_init(self):
        """Test analyzer initialization."""
        analyzer = MDSComponentAnalyzer()
        assert len(analyzer.supported_components) > 0
        assert 'scoreboard' in analyzer.supported_components
        assert 'player_card' in analyzer.supported_components
    
    def test_analyze_component_supported(self):
        """Test analyzing supported component."""
        component = {
            "type": "player_card",
            "player_id": "123",
            "name": "Test Player",
            "team": "Test Team",
            "favorite": True
        }
        
        analyzer = MDSComponentAnalyzer()
        result = analyzer.analyze_component(component)
        
        assert result["supported"] is True
        assert result["component"] == "player_card"
        assert result["personalization_score"] > 0  # Has 'favorite'
        assert result["supports_favorites"] is True
        assert len(result["test_recommendations"]) > 0
    
    def test_analyze_component_unsupported(self):
        """Test analyzing unsupported component."""
        component = {"type": "unsupported_type"}
        
        analyzer = MDSComponentAnalyzer()
        
        with pytest.raises(NotImplementedError):
            analyzer.analyze_component(component)
    
    def test_analyze_personalization_features(self):
        """Test personalization feature analysis."""
        component = {
            "type": "news_card",
            "content": "personalized news",
            "user_preferences": ["favorite", "location"],
            "recommendation_score": 0.9
        }
        
        analyzer = MDSComponentAnalyzer()
        result = analyzer._analyze_personalization(component)
        
        assert result["personalization_score"] > 50  # Should be high
        assert result["supports_favorites"] is True
        assert "favorites" in result["personalization_features"]
        assert "recommendations" in result["personalization_features"]
    
    def test_analyze_content_requirements(self):
        """Test content requirements analysis."""
        component = {
            "type": "video_card",
            "video_url": "https://example.com/video.mp4",
            "title": "Test Video",
            "thumbnail": "https://example.com/thumb.jpg"
            # Missing duration (optional)
        }
        
        analyzer = MDSComponentAnalyzer()
        requirements = analyzer._analyze_content_requirements(component)
        
        assert len(requirements) > 0
        
        # Check required fields are present
        video_url_req = next((r for r in requirements if r["field"] == "video_url"), None)
        assert video_url_req is not None
        assert video_url_req["present"] is True
        assert video_url_req["required"] is True
        
        # Check optional field handling
        duration_req = next((r for r in requirements if r["field"] == "duration"), None)
        assert duration_req is not None
        assert duration_req["present"] is False
        assert duration_req["required"] is False
    
    def test_check_analytics_compliance(self):
        """Test analytics compliance checking."""
        component = {
            "type": "scoreboard",
            "analytics": {
                "events": ["component_view"]  # Missing component_interaction
            }
        }
        
        analyzer = MDSComponentAnalyzer()
        result = analyzer._check_analytics_compliance(component)
        
        assert result["compliant"] is False
        assert "component_interaction" in result["missing"]
        assert "component_view" in result["required_events"]
    
    def test_analyze_mds_screen(self):
        """Test analyzing entire MDS screen."""
        screen_data = {
            "name": "home_screen",
            "components": [
                {
                    "type": "scoreboard",
                    "analytics": {"events": ["component_view", "component_interaction"]}
                },
                {
                    "type": "player_card",
                    "player_id": "123",
                    "analytics": {"events": ["component_view"]}  # Missing events
                }
            ]
        }
        
        analyzer = MDSComponentAnalyzer()
        result = analyzer.analyze_mds_screen(screen_data)
        
        assert result["screen_name"] == "home_screen"
        assert result["total_components"] == 2
        assert result["supported_components"] == 2
        assert result["analytics_compliance_rate"] < 100  # One component not compliant
        assert len(result["components"]) == 2
        assert len(result["overall_recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])