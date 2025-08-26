import pytest

# test_6_edge_case_discovery.py
def test_edge_case_discovery_no_historical_data():
    """Test that edge case discovery fails without historical test data"""
    from src.edge_case_discoverer import EdgeCaseDiscoverer
    
    discoverer = EdgeCaseDiscoverer()
    with pytest.raises(RuntimeError, match="No historical test data available"):
        discoverer.discover_edge_cases({"type": "form", "fields": ["email", "password"]})

def test_edge_case_discovery_invalid_component():
    """Test that edge case discovery rejects invalid components"""
    from src.edge_case_discoverer import EdgeCaseDiscoverer
    
    discoverer = EdgeCaseDiscoverer()
    discoverer.load_historical_data(["test_1", "test_2"])
    
    with pytest.raises(ValueError, match="Component missing required 'type' field"):
        discoverer.discover_edge_cases({"id": "comp_1"})

def test_boundary_condition_generation_non_numeric():
    """Test that boundary conditions fail for non-numeric fields"""
    from src.edge_case_discoverer import EdgeCaseDiscoverer
    
    discoverer = EdgeCaseDiscoverer()
    with pytest.raises(TypeError, match="Cannot generate boundary conditions for non-numeric field"):
        discoverer.generate_boundary_conditions({"field": "username", "type": "string"})