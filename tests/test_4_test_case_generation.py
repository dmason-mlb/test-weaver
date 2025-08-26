import pytest

# test_4_test_case_generation.py
def test_generate_test_without_pattern():
    """Test that test generation fails without input pattern"""
    from src.test_generator import TestCaseGenerator
    
    generator = TestCaseGenerator()
    with pytest.raises(ValueError, match="Pattern required for test generation"):
        generator.generate_test(pattern=None)

def test_generate_test_invalid_pattern_structure():
    """Test that invalid pattern structure raises appropriate error"""
    from src.test_generator import TestCaseGenerator
    
    generator = TestCaseGenerator()
    invalid_pattern = {"component": "button"}  # Missing required pattern fields
    with pytest.raises(ValueError, match="Invalid pattern structure: missing 'interactions'"):
        generator.generate_test(invalid_pattern)

def test_generate_test_unsupported_interaction_type():
    """Test that unsupported interaction types are rejected"""
    from src.test_generator import TestCaseGenerator
    
    generator = TestCaseGenerator()
    pattern = {
        "component": {"type": "button", "id": "btn_1"},
        "interactions": ["quantum_entangle"]  # Not a real interaction
    }
    with pytest.raises(NotImplementedError, match="Interaction 'quantum_entangle' not supported"):
        generator.generate_test(pattern)