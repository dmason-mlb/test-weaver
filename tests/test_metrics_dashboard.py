"""
Tests for metrics_dashboard.py.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from metrics_dashboard import MetricsDashboard


class TestMetricsDashboard:
    """Test metrics dashboard functionality."""
    
    def test_init(self):
        """Test dashboard initialization."""
        dashboard = MetricsDashboard()
        assert dashboard is not None
    
    def test_calculate_roi(self):
        """Test ROI calculation."""
        dashboard = MetricsDashboard()
        roi = dashboard.calculate_roi()
        
        assert isinstance(roi, dict)
        assert "time_saved_hours" in roi
        assert "tests_generated" in roi
        assert "bugs_prevented" in roi
        assert "coverage_increase" in roi
        assert "cost_savings" in roi
        assert "generation_speed" in roi
        
        # Verify data types and reasonable values
        assert isinstance(roi["time_saved_hours"], int)
        assert isinstance(roi["tests_generated"], int)
        assert isinstance(roi["bugs_prevented"], int)
        assert roi["time_saved_hours"] > 0
        assert roi["tests_generated"] > 0
        assert roi["bugs_prevented"] > 0
    
    def test_compare_before_after(self):
        """Test before/after comparison."""
        dashboard = MetricsDashboard()
        comparison = dashboard.compare_before_after()
        
        assert isinstance(comparison, dict)
        assert "before" in comparison
        assert "after" in comparison
        
        before = comparison["before"]
        after = comparison["after"]
        
        # Verify structure
        expected_fields = ["test_creation_time", "coverage", "edge_cases_found", "maintenance_burden"]
        for field in expected_fields:
            assert field in before
            assert field in after
        
        # Verify improvements (basic sanity checks)
        assert before["coverage"] != after["coverage"]
        assert before["maintenance_burden"] != after["maintenance_burden"]


if __name__ == "__main__":
    pytest.main([__file__])