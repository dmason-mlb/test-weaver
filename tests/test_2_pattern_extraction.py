import pytest

# test_2_pattern_extraction.py
def test_extract_patterns_from_empty_schema():
    """Test that empty server-driven UI schema returns no patterns"""
    from src.pattern_extractor import UIPatternExtractor
    
    extractor = UIPatternExtractor()
    patterns = extractor.extract_from_schema({})
    assert patterns == [], "Empty schema should return no patterns"

def test_extract_patterns_missing_required_fields():
    """Test that schema missing required fields raises validation error"""
    from src.pattern_extractor import UIPatternExtractor
    
    extractor = UIPatternExtractor()
    invalid_schema = {
        "components": [
            {"type": "button"}  # Missing required 'id' and 'action' fields
        ]
    }
    with pytest.raises(ValueError, match="Missing required fields: id, action"):
        extractor.extract_from_schema(invalid_schema)

def test_unsupported_component_type():
    """Test that unsupported UI component types are not processed"""
    from src.pattern_extractor import UIPatternExtractor
    
    extractor = UIPatternExtractor()
    schema = {
        "components": [
            {"id": "1", "type": "unknown_widget", "action": "tap"}
        ]
    }
    with pytest.raises(NotImplementedError, match="Component type 'unknown_widget' not supported"):
        extractor.extract_from_schema(schema)