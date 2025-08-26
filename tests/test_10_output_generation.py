import pytest

# test_10_output_generation.py
def test_test_report_missing_metrics():
    """Test that test report generation fails without metrics"""
    from src.reporting import TestReportGenerator
    
    generator = TestReportGenerator()
    with pytest.raises(ValueError, match="Cannot generate report without test metrics"):
        generator.generate_report(tests=[], metrics=None)

def test_export_invalid_format():
    """Test that invalid export formats are rejected"""
    from src.reporting import TestExporter
    
    exporter = TestExporter()
    tests = [{"name": "test_1", "code": "assert True"}]
    
    with pytest.raises(ValueError, match="Export format 'quantum' not supported"):
        exporter.export(tests, format="quantum")

def test_coverage_calculation_no_tests():
    """Test that coverage calculation fails without tests"""
    from src.reporting import CoverageCalculator
    
    calculator = CoverageCalculator()
    with pytest.raises(RuntimeError, match="Cannot calculate coverage: no tests provided"):
        calculator.calculate_coverage(ui_schema={"components": [1, 2, 3]}, tests=[])