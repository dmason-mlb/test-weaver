from typing import Dict, List, Any, Set
import json


class MDSComponentAnalyzer:
    """Analyzer for MLB My Daily Story (MDS) components and personalization features."""
    
    def __init__(self):
        self.supported_components = {
            'scoreboard', 'standings', 'player_card', 
            'news_card', 'video_card', 'team_logo',
            'game_card', 'highlight_card', 'stats_card',
            'roster_card', 'schedule_card', 'social_card'
        }
        
        self.personalization_features = {
            'favorite_team', 'favorite_players', 'follow_teams',
            'preferred_content_types', 'viewing_history',
            'notification_preferences', 'location_based'
        }
        
        self.analytics_events = {
            'component_view', 'component_interaction', 'content_engagement',
            'personalization_change', 'share_content', 'bookmark_content'
        }
    
    def analyze_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single MDS component for compliance and personalization."""
        component_type = component.get('type')

        # Determine if component is officially supported or needs generic analysis
        is_officially_supported = component_type in self.supported_components

        analysis = {
            "component": component_type,
            "supported": is_officially_supported,
            "officially_supported": is_officially_supported,
            "personalization_score": 0,
            "analytics_compliance": False,
            "content_requirements": [],
            "test_recommendations": []
        }

        # Add warning for non-standard components
        if not is_officially_supported:
            analysis["warning"] = f"Component type '{component_type}' not in official MDS specification - using generic analysis"
        
        # Analyze personalization features
        personalization_analysis = self._analyze_personalization(component)
        analysis.update(personalization_analysis)
        
        # Analyze content requirements
        content_analysis = self._analyze_content_requirements(component)
        analysis["content_requirements"] = content_analysis
        
        # Check analytics compliance
        analytics_analysis = self._check_analytics_compliance(component)
        analysis["analytics_compliance"] = analytics_analysis["compliant"]
        analysis["missing_analytics"] = analytics_analysis.get("missing", [])
        
        # Generate test recommendations
        analysis["test_recommendations"] = self._generate_test_recommendations(component, analysis)
        
        return analysis
    
    def _analyze_personalization(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze personalization features in the component."""
        result = {
            "personalization_score": 0,
            "personalization_features": [],
            "supports_favorites": False,
            "supports_location": False,
            "supports_history": False
        }
        
        # Check for personalization indicators
        component_str = json.dumps(component, default=str).lower()
        
        score = 0
        features = []
        
        if any(term in component_str for term in ['favorite', 'follow', 'preferred']):
            score += 25
            features.append('favorites')
            result["supports_favorites"] = True
        
        if any(term in component_str for term in ['location', 'geo', 'nearby', 'local']):
            score += 20
            features.append('location')
            result["supports_location"] = True
        
        if any(term in component_str for term in ['history', 'recent', 'viewed', 'watched']):
            score += 15
            features.append('history')
            result["supports_history"] = True
        
        if any(term in component_str for term in ['recommend', 'suggest', 'personalized']):
            score += 30
            features.append('recommendations')
        
        if any(term in component_str for term in ['notification', 'alert', 'remind']):
            score += 10
            features.append('notifications')
        
        result["personalization_score"] = score
        result["personalization_features"] = features
        
        return result
    
    def _analyze_content_requirements(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze content requirements for the component."""
        component_type = component.get('type')
        requirements = []
        
        # Define content requirements by component type
        content_specs = {
            'scoreboard': [
                {'field': 'games', 'type': 'array', 'required': True},
                {'field': 'date', 'type': 'string', 'required': True},
                {'field': 'league', 'type': 'string', 'required': False}
            ],
            'player_card': [
                {'field': 'player_id', 'type': 'string', 'required': True},
                {'field': 'name', 'type': 'string', 'required': True},
                {'field': 'team', 'type': 'string', 'required': True},
                {'field': 'stats', 'type': 'object', 'required': False}
            ],
            'news_card': [
                {'field': 'headline', 'type': 'string', 'required': True},
                {'field': 'summary', 'type': 'string', 'required': False},
                {'field': 'image_url', 'type': 'string', 'required': False},
                {'field': 'publish_date', 'type': 'string', 'required': True}
            ],
            'video_card': [
                {'field': 'video_url', 'type': 'string', 'required': True},
                {'field': 'thumbnail', 'type': 'string', 'required': True},
                {'field': 'duration', 'type': 'number', 'required': False},
                {'field': 'title', 'type': 'string', 'required': True}
            ]
        }
        
        if component_type in content_specs:
            requirements = content_specs[component_type]
        else:
            # Generic requirements for unknown component types
            requirements = self._generate_generic_requirements(component)

        # Validate requirements against actual component data
        for req in requirements:
            field = req['field']
            if field in component:
                req['present'] = True
                req['actual_type'] = type(component[field]).__name__
            else:
                req['present'] = False
                req['actual_type'] = None

        return requirements

    def _generate_generic_requirements(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic content requirements for unknown component types."""
        requirements = []

        # Always require basic fields for any MLB component
        basic_requirements = [
            {'field': 'id', 'type': 'string', 'required': True},
            {'field': 'type', 'type': 'string', 'required': True}
        ]

        # Inspect component to infer additional requirements
        for field, value in component.items():
            if field not in ['id', 'type']:  # Skip basic fields already added
                requirements.append({
                    'field': field,
                    'type': type(value).__name__,
                    'required': False,  # Unknown components have flexible requirements
                    'inferred': True
                })

        return basic_requirements + requirements

    def _check_analytics_compliance(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Check if component meets analytics requirements."""
        result = {
            "compliant": True,
            "required_events": [],
            "missing": []
        }
        
        component_type = component.get('type')
        
        # Define required analytics events by component type
        required_events = {
            'scoreboard': ['component_view', 'component_interaction'],
            'player_card': ['component_view', 'component_interaction', 'content_engagement'],
            'news_card': ['component_view', 'content_engagement', 'share_content'],
            'video_card': ['component_view', 'content_engagement', 'share_content'],
            'game_card': ['component_view', 'component_interaction'],
        }
        
        if component_type in required_events:
            result["required_events"] = required_events[component_type]
        else:
            # Generic analytics requirements for unknown component types
            result["required_events"] = ['component_view']  # Minimum requirement
            result["generic_requirements"] = True

        # Check if analytics configuration exists
        analytics_config = component.get('analytics', {})
        configured_events = analytics_config.get('events', [])

        missing = set(result["required_events"]) - set(configured_events)
        if missing:
            result["compliant"] = False
            result["missing"] = list(missing)
        
        return result
    
    def _generate_test_recommendations(self, component: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate test recommendations based on component analysis."""
        recommendations = []
        
        # Personalization tests
        if analysis["personalization_score"] > 0:
            recommendations.append("Add personalization feature tests")
            
            if analysis["supports_favorites"]:
                recommendations.append("Test favorite team/player functionality")
            
            if analysis["supports_location"]:
                recommendations.append("Test location-based content filtering")
            
            if analysis["supports_history"]:
                recommendations.append("Test user history and recommendations")
        
        # Content validation tests
        if analysis["content_requirements"]:
            recommendations.append("Add content structure validation tests")
            
            missing_required = [req for req in analysis["content_requirements"] 
                              if req["required"] and not req.get("present", False)]
            if missing_required:
                recommendations.append("Test error handling for missing required fields")
        
        # Analytics tests
        if not analysis["analytics_compliance"]:
            recommendations.append("Add analytics event tracking tests")
        
        # Component-specific tests
        component_type = component.get('type')
        if component_type == 'video_card':
            recommendations.append("Test video playback functionality")
            recommendations.append("Test video quality adaptation")
        elif component_type == 'scoreboard':
            recommendations.append("Test real-time score updates")
            recommendations.append("Test game state transitions")
        elif component_type == 'player_card':
            recommendations.append("Test player statistics accuracy")
            recommendations.append("Test player image loading")
        else:
            # Generic recommendations for unknown component types
            if not analysis.get("officially_supported", True):
                recommendations.append("Test basic component rendering and visibility")
                recommendations.append("Test component responsiveness and interaction")
                recommendations.append("Verify component data structure compliance")

                # Add recommendations based on component properties
                if any(prop in str(component).lower() for prop in ['image', 'img', 'photo']):
                    recommendations.append("Test image loading and accessibility")
                if any(prop in str(component).lower() for prop in ['video', 'play', 'stream']):
                    recommendations.append("Test media playback functionality")
                if any(prop in str(component).lower() for prop in ['link', 'url', 'navigation']):
                    recommendations.append("Test navigation and linking functionality")

        return recommendations
    
    def analyze_mds_screen(self, screen_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an entire MDS screen containing multiple components."""
        screen_analysis = {
            "screen_name": screen_data.get('name', 'unknown'),
            "total_components": 0,
            "supported_components": 0,
            "personalization_score": 0,
            "analytics_compliance_rate": 0,
            "components": [],
            "overall_recommendations": []
        }
        
        components = screen_data.get('components', [])
        screen_analysis["total_components"] = len(components)
        
        compliant_components = 0
        total_personalization = 0
        
        for component in components:
            try:
                component_analysis = self.analyze_component(component)
                screen_analysis["components"].append(component_analysis)
                
                if component_analysis["supported"]:
                    screen_analysis["supported_components"] += 1
                
                if component_analysis["analytics_compliance"]:
                    compliant_components += 1
                
                total_personalization += component_analysis["personalization_score"]
                
            except NotImplementedError as e:
                screen_analysis["components"].append({
                    "component": component.get('type', 'unknown'),
                    "supported": False,
                    "error": str(e)
                })
        
        # Calculate rates
        if screen_analysis["total_components"] > 0:
            screen_analysis["analytics_compliance_rate"] = (
                compliant_components / screen_analysis["total_components"] * 100
            )
            screen_analysis["personalization_score"] = (
                total_personalization / screen_analysis["total_components"]
            )
        
        # Generate overall recommendations
        if screen_analysis["analytics_compliance_rate"] < 100:
            screen_analysis["overall_recommendations"].append("Improve analytics coverage across components")
        
        if screen_analysis["personalization_score"] < 50:
            screen_analysis["overall_recommendations"].append("Enhance personalization features")
        
        if screen_analysis["supported_components"] < screen_analysis["total_components"]:
            screen_analysis["overall_recommendations"].append("Update unsupported components to MDS specification")
        
        return screen_analysis