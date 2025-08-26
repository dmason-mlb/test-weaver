import pytest

# test_8_pipeline_integration.py
def test_pipeline_missing_configuration():
    """Test that pipeline fails without proper configuration"""
    from src.pipeline import TestGenerationPipeline
    
    pipeline = TestGenerationPipeline()
    with pytest.raises(RuntimeError, match="Pipeline not configured"):
        pipeline.generate_tests_for_ui({"screen": "home"})

def test_pipeline_component_failure_handling():
    """Test that pipeline handles component failures gracefully"""
    from src.pipeline import TestGenerationPipeline
    
    pipeline = TestGenerationPipeline(config="config.yaml")
    pipeline.vector_store = None  # Simulate component failure
    
    with pytest.raises(RuntimeError, match="Pipeline component 'vector_store' failed"):
        pipeline.generate_tests_for_ui({"screen": "home"})

def test_pipeline_output_validation():
    """Test that pipeline output meets expected structure"""
    from src.pipeline import TestGenerationPipeline
    
    pipeline = TestGenerationPipeline(config="config.yaml")
    # Mock a broken generator that returns invalid output
    pipeline.test_generator.generate = lambda x: {"invalid": "structure"}
    
    with pytest.raises(ValueError, match="Generated tests missing required fields: test_name, test_code, coverage_type"):
        pipeline.generate_tests_for_ui({"screen": "home", "components": []})