class EdgeCaseDiscoverer:
    def __init__(self):
        self.historical_data = []
    
    def load_historical_data(self, test_data):
        self.historical_data = test_data
    
    def discover_edge_cases(self, component):
        if not self.historical_data:
            raise RuntimeError("No historical test data available")
        
        if 'type' not in component:
            raise ValueError("Component missing required 'type' field")
        
        return []
    
    def generate_boundary_conditions(self, field):
        if field.get('type') == 'string':
            raise TypeError("Cannot generate boundary conditions for non-numeric field")
        
        return []