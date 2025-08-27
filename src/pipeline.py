class TestGenerationPipeline:
    def __init__(self, config=None):
        self.config = config
        self.vector_store = "initialized" if config else None
        self.test_generator = TestGenerator() if config else None
    
    def generate_tests_for_ui(self, ui_spec):
        if not self.config:
            raise RuntimeError("Pipeline not configured")
        
        if self.vector_store is None:
            raise RuntimeError("Pipeline component 'vector_store' failed")
        
        # Generate tests using the test generator
        if hasattr(self.test_generator, 'generate'):
            result = self.test_generator.generate(ui_spec)
        else:
            result = {"test_name": "sample_test", "test_code": "assert True", "coverage_type": "unit"}
        
        # Validate output structure
        required_fields = ["test_name", "test_code", "coverage_type"]
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            raise ValueError(f"Generated tests missing required fields: {', '.join(missing_fields)}")
        
        return result


class TestGenerator:
    def generate(self, ui_spec):
        return {"test_name": "sample_test", "test_code": "assert True", "coverage_type": "unit"}