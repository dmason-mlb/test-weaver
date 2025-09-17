class UIPatternExtractor:
    def __init__(self):
        # Define required fields for each supported component type
        self.component_requirements = {
            'button': ['id', 'action'],
            'webview': ['id', 'url'],
            'list': ['id', 'items'],
            'api_endpoint': ['id', 'url', 'method'],
            'card': ['id', 'content'],
            'modal': ['id', 'title'],
            'navigation': ['id', 'items'],
            'form': ['id', 'fields'],
            'image': ['id', 'src'],
            'video': ['id', 'src'],
            'chart': ['id', 'data'],
            'map': ['id', 'coordinates']
        }

        self.supported_components = set(self.component_requirements.keys())

    def extract_from_schema(self, schema):
        if not schema:
            return []

        components = schema.get("components", [])
        patterns = []

        for component in components:
            component_type = component.get("type")

            if component_type in self.supported_components:
                required_fields = self.component_requirements[component_type]
                missing_fields = [field for field in required_fields if field not in component]

                if missing_fields:
                    raise ValueError(f"Missing required fields for {component_type}: {', '.join(missing_fields)}")

                # Extract pattern from validated component
                pattern = self._extract_component_pattern(component)
                if pattern:
                    patterns.append(pattern)
            else:
                # Graceful fallback for unsupported component types
                pattern = self._extract_generic_pattern(component)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _extract_component_pattern(self, component):
        """Extract pattern from a validated component"""
        component_type = component.get("type")
        component_id = component.get("id", "unknown")

        # Create a pattern based on component type and properties
        pattern = {
            "type": component_type,
            "id": component_id,
            "properties": {},
            "test_strategies": self._get_test_strategies(component_type)
        }

        # Add type-specific properties
        if component_type == "button":
            pattern["properties"]["action"] = component.get("action")
            pattern["properties"]["text"] = component.get("text", "")
        elif component_type == "webview":
            pattern["properties"]["url"] = component.get("url")
            pattern["properties"]["content_type"] = component.get("content_type", "html")
        elif component_type == "list":
            pattern["properties"]["items"] = component.get("items", [])
            pattern["properties"]["scroll_direction"] = component.get("scroll_direction", "vertical")
        elif component_type == "api_endpoint":
            pattern["properties"]["url"] = component.get("url")
            pattern["properties"]["method"] = component.get("method")
            pattern["properties"]["headers"] = component.get("headers", {})
        elif component_type == "card":
            pattern["properties"]["content"] = component.get("content")
            pattern["properties"]["layout"] = component.get("layout", "standard")
        elif component_type == "modal":
            pattern["properties"]["title"] = component.get("title")
            pattern["properties"]["closable"] = component.get("closable", True)
        elif component_type == "navigation":
            pattern["properties"]["items"] = component.get("items", [])
            pattern["properties"]["orientation"] = component.get("orientation", "horizontal")
        elif component_type == "form":
            pattern["properties"]["fields"] = component.get("fields", [])
            pattern["properties"]["validation"] = component.get("validation", {})
        elif component_type == "image":
            pattern["properties"]["src"] = component.get("src")
            pattern["properties"]["alt_text"] = component.get("alt_text", "")
        elif component_type == "video":
            pattern["properties"]["src"] = component.get("src")
            pattern["properties"]["controls"] = component.get("controls", True)
        elif component_type == "chart":
            pattern["properties"]["data"] = component.get("data")
            pattern["properties"]["chart_type"] = component.get("chart_type", "line")
        elif component_type == "map":
            pattern["properties"]["coordinates"] = component.get("coordinates")
            pattern["properties"]["zoom_level"] = component.get("zoom_level", 10)

        return pattern

    def _extract_generic_pattern(self, component):
        """Extract generic pattern for unsupported component types"""
        component_type = component.get("type", "unknown")
        component_id = component.get("id", f"unknown_{component_type}")

        return {
            "type": component_type,
            "id": component_id,
            "properties": component,  # Include all properties for unknown types
            "test_strategies": ["basic_rendering", "visibility_check"]
        }

    def _get_test_strategies(self, component_type):
        """Get recommended test strategies for component type"""
        strategies = {
            'button': ['click_interaction', 'state_validation', 'accessibility_check'],
            'webview': ['load_validation', 'content_check', 'performance_test'],
            'list': ['scroll_test', 'item_interaction', 'performance_test'],
            'api_endpoint': ['response_validation', 'error_handling', 'performance_test'],
            'card': ['content_validation', 'interaction_test', 'layout_check'],
            'modal': ['show_hide_test', 'interaction_test', 'accessibility_check'],
            'navigation': ['item_selection', 'state_validation', 'accessibility_check'],
            'form': ['input_validation', 'submission_test', 'error_handling'],
            'image': ['load_validation', 'accessibility_check', 'responsive_test'],
            'video': ['playback_test', 'controls_test', 'performance_test'],
            'chart': ['data_rendering', 'interaction_test', 'responsive_test'],
            'map': ['location_display', 'interaction_test', 'performance_test']
        }

        return strategies.get(component_type, ['basic_rendering', 'visibility_check'])