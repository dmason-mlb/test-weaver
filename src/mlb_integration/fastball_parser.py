class FastballGatewayParser:
    def __init__(self):
        pass
    
    def parse_schema(self, schema_text):
        if not schema_text or not schema_text.strip().startswith(('type', 'query', 'mutation', 'schema')):
            raise ValueError("Invalid GraphQL schema format")
        
        return {"parsed": True}