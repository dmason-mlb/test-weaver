class UIPatternExtractor:
    def extract_from_schema(self, schema):
        if not schema:
            return []
        
        components = schema.get("components", [])
        for component in components:
            component_type = component.get("type")
            
            if component_type == "button":
                required_fields = ["id", "action"]
                missing_fields = [field for field in required_fields if field not in component]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            else:
                raise NotImplementedError(f"Component type '{component_type}' not supported")
        
        return []