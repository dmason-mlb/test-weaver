from typing import Dict, List, Any, Optional
import logging
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

class UIValidatorAgent:
    """Agent responsible for validating UI components for MLB's server-driven UI.

    Validates components against:
    - MLB Design System standards
    - Cross-platform consistency (iOS/Android)
    - Accessibility compliance
    - Component structure and required fields
    """

    def __init__(self, design_system_rules: Optional[Dict] = None):
        """Initialize the UI Validator Agent.

        Args:
            design_system_rules: Optional MLB design system rules override
        """
        self.design_system_rules = design_system_rules or self._get_default_design_rules()
        self.accessibility_rules = self._get_accessibility_rules()
        self.platform_requirements = self._get_platform_requirements()

        # Initialize CrewAI agent
        self.agent = Agent(
            role="UI Component Validator",
            goal="Validate UI components against MLB design standards and accessibility requirements",
            backstory="Expert in MLB's design system with deep knowledge of cross-platform UI consistency and accessibility standards.",
            verbose=True,
            allow_delegation=False
        )

    def validate_component(self, component: Dict[str, Any], ui_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate a UI component against MLB standards.

        Args:
            component: UI component definition with id, type, properties
            ui_context: Optional context about the screen/page containing this component

        Returns:
            Dict containing validation results with issues, warnings, and recommendations
        """
        if not component:
            raise ValueError("Component cannot be None or empty")

        if not isinstance(component, dict):
            raise ValueError("Component must be a dictionary")

        if 'type' not in component:
            raise ValueError("Component must have a 'type' field")

        validation_result = {
            'component_id': component.get('id', 'unknown'),
            'component_type': component.get('type'),
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'accessibility_score': 100,
            'design_compliance_score': 100,
            'cross_platform_score': 100
        }

        try:
            # Core validation checks
            self._validate_required_fields(component, validation_result)
            self._validate_design_system_compliance(component, validation_result)
            self._validate_accessibility(component, validation_result)
            self._validate_cross_platform_consistency(component, validation_result)

            # Context-specific validation if UI context provided
            if ui_context:
                self._validate_with_context(component, ui_context, validation_result)

            # Calculate overall validity
            validation_result['is_valid'] = len(validation_result['errors']) == 0

            logger.info(f"Validated component {component.get('id', 'unknown')}: {'PASS' if validation_result['is_valid'] else 'FAIL'}")

        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating component {component.get('id', 'unknown')}: {e}")

        return validation_result

    def _validate_required_fields(self, component: Dict, result: Dict) -> None:
        """Validate that component has all required fields."""
        component_type = component.get('type')
        required_fields = self._get_required_fields_for_type(component_type)

        for field in required_fields:
            if field not in component:
                result['errors'].append(f"Missing required field: {field}")
                result['design_compliance_score'] -= 10

    def _validate_design_system_compliance(self, component: Dict, result: Dict) -> None:
        """Validate component against MLB Design System rules."""
        component_type = component.get('type')

        # Button validation
        if component_type == 'button':
            self._validate_button_design(component, result)
        # List validation
        elif component_type == 'list':
            self._validate_list_design(component, result)
        # Card validation
        elif component_type == 'card':
            self._validate_card_design(component, result)
        # Modal validation
        elif component_type == 'modal':
            self._validate_modal_design(component, result)
        # Form validation
        elif component_type == 'form':
            self._validate_form_design(component, result)

    def _validate_accessibility(self, component: Dict, result: Dict) -> None:
        """Validate component for accessibility compliance."""
        # Check for accessibility label
        if 'accessibility_label' not in component and 'label' not in component:
            result['warnings'].append("Missing accessibility label for screen readers")
            result['accessibility_score'] -= 15

        # Check for semantic roles
        if component.get('type') in ['button', 'input', 'select'] and 'role' not in component:
            result['warnings'].append("Missing semantic role for assistive technology")
            result['accessibility_score'] -= 10

        # Check color contrast (if color specified)
        if 'background_color' in component or 'text_color' in component:
            self._validate_color_contrast(component, result)

        # Check touch target size for mobile
        if component.get('type') in ['button', 'input', 'select']:
            self._validate_touch_target(component, result)

    def _validate_cross_platform_consistency(self, component: Dict, result: Dict) -> None:
        """Validate component for iOS/Android consistency."""
        # Check for platform-specific properties that might break consistency
        ios_only_props = ['ios_style', 'cupertino_style']
        android_only_props = ['material_style', 'android_style']

        has_ios_only = any(prop in component for prop in ios_only_props)
        has_android_only = any(prop in component for prop in android_only_props)

        if has_ios_only and has_android_only:
            result['warnings'].append("Component has both iOS and Android specific styles")
            result['cross_platform_score'] -= 10
        elif has_ios_only or has_android_only:
            result['recommendations'].append("Consider using cross-platform styling for consistency")
            result['cross_platform_score'] -= 5

        # Validate gesture support consistency
        if component.get('type') in ['list', 'card', 'image']:
            self._validate_gesture_consistency(component, result)

    def _validate_with_context(self, component: Dict, ui_context: Dict, result: Dict) -> None:
        """Validate component within its UI context."""
        screen_type = ui_context.get('screen_type', '')

        # Gameday-specific validation
        if screen_type == 'gameday':
            self._validate_gameday_component(component, result)
        # Team page validation
        elif screen_type == 'team_page':
            self._validate_team_page_component(component, result)
        # Browse menu validation
        elif screen_type == 'browse_menu':
            self._validate_browse_menu_component(component, result)

    def _validate_button_design(self, component: Dict, result: Dict) -> None:
        """Validate button-specific design rules."""
        # Must have text or icon
        if not component.get('text') and not component.get('icon'):
            result['errors'].append("Button must have either text or icon")
            result['design_compliance_score'] -= 15

        # Check button size
        min_height = 44  # iOS minimum touch target
        if component.get('height', 0) < min_height:
            result['warnings'].append(f"Button height should be at least {min_height}px")
            result['accessibility_score'] -= 10

    def _validate_list_design(self, component: Dict, result: Dict) -> None:
        """Validate list-specific design rules."""
        if 'items' not in component:
            result['errors'].append("List component must have 'items' property")
            result['design_compliance_score'] -= 20

        # Check for empty state handling
        if not component.get('empty_state_message'):
            result['recommendations'].append("Consider adding empty state message")

    def _validate_card_design(self, component: Dict, result: Dict) -> None:
        """Validate card-specific design rules."""
        # Cards should have clear content hierarchy
        if not component.get('title') and not component.get('content'):
            result['warnings'].append("Card should have title or content for clarity")
            result['design_compliance_score'] -= 10

    def _validate_modal_design(self, component: Dict, result: Dict) -> None:
        """Validate modal-specific design rules."""
        # Modals must have close mechanism
        if not component.get('dismissible') and not component.get('close_button'):
            result['errors'].append("Modal must be dismissible or have close button")
            result['accessibility_score'] -= 20

    def _validate_form_design(self, component: Dict, result: Dict) -> None:
        """Validate form-specific design rules."""
        # Forms should have validation feedback
        if 'validation' not in component:
            result['recommendations'].append("Consider adding input validation")

        # Check for submit mechanism
        if not component.get('submit_button') and not component.get('on_submit'):
            result['warnings'].append("Form should have clear submit mechanism")

    def _validate_color_contrast(self, component: Dict, result: Dict) -> None:
        """Validate color contrast for accessibility."""
        # Simplified contrast validation - in real implementation would use color analysis
        bg_color = component.get('background_color', '')
        text_color = component.get('text_color', '')

        # Basic heuristic checks
        if bg_color.lower() in ['white', '#ffffff'] and text_color.lower() in ['white', '#ffffff']:
            result['errors'].append("Insufficient color contrast: white text on white background")
            result['accessibility_score'] -= 25
        elif bg_color.lower() in ['black', '#000000'] and text_color.lower() in ['black', '#000000']:
            result['errors'].append("Insufficient color contrast: black text on black background")
            result['accessibility_score'] -= 25

    def _validate_touch_target(self, component: Dict, result: Dict) -> None:
        """Validate touch target size for mobile accessibility."""
        min_size = 44  # Apple's minimum recommended touch target

        width = component.get('width', 0)
        height = component.get('height', 0)

        if width > 0 and width < min_size:
            result['warnings'].append(f"Touch target width ({width}px) below recommended minimum ({min_size}px)")
            result['accessibility_score'] -= 10

        if height > 0 and height < min_size:
            result['warnings'].append(f"Touch target height ({height}px) below recommended minimum ({min_size}px)")
            result['accessibility_score'] -= 10

    def _validate_gesture_consistency(self, component: Dict, result: Dict) -> None:
        """Validate gesture support across platforms."""
        gestures = component.get('supported_gestures', [])

        # Check for platform-specific gestures
        ios_gestures = ['force_touch', '3d_touch']
        android_gestures = ['long_press_drag']

        has_ios_specific = any(gesture in gestures for gesture in ios_gestures)
        has_android_specific = any(gesture in gestures for gesture in android_gestures)

        if has_ios_specific or has_android_specific:
            result['recommendations'].append("Platform-specific gestures may affect cross-platform consistency")
            result['cross_platform_score'] -= 5

    def _validate_gameday_component(self, component: Dict, result: Dict) -> None:
        """Validate components specific to Gameday screen."""
        component_type = component.get('type')

        if component_type == 'scoreboard':
            if 'home_team' not in component or 'away_team' not in component:
                result['errors'].append("Scoreboard must have home_team and away_team")
        elif component_type == 'play_by_play':
            if 'events' not in component:
                result['warnings'].append("Play-by-play should have events data")

    def _validate_team_page_component(self, component: Dict, result: Dict) -> None:
        """Validate components specific to Team page."""
        component_type = component.get('type')

        if component_type == 'roster':
            if 'players' not in component:
                result['errors'].append("Roster component must have players data")
        elif component_type == 'team_stats':
            if 'season' not in component:
                result['recommendations'].append("Team stats should specify season")

    def _validate_browse_menu_component(self, component: Dict, result: Dict) -> None:
        """Validate components specific to Browse menu."""
        component_type = component.get('type')

        if component_type == 'navigation_item':
            if not component.get('destination') and not component.get('action'):
                result['errors'].append("Navigation item must have destination or action")

    def _get_required_fields_for_type(self, component_type: str) -> List[str]:
        """Get required fields for each component type."""
        required_fields = {
            'button': ['id', 'type'],
            'list': ['id', 'type', 'items'],
            'card': ['id', 'type'],
            'modal': ['id', 'type', 'content'],
            'form': ['id', 'type', 'fields'],
            'image': ['id', 'type', 'src'],
            'video': ['id', 'type', 'src'],
            'webview': ['id', 'type', 'url'],
            'api_endpoint': ['id', 'type', 'endpoint']
        }
        return required_fields.get(component_type, ['id', 'type'])

    def _get_default_design_rules(self) -> Dict[str, Any]:
        """Get default MLB design system rules."""
        return {
            'colors': {
                'primary': '#C4CED4',  # MLB primary blue
                'secondary': '#041E42',  # MLB navy
                'accent': '#B31E2C',  # MLB red
                'background': '#FFFFFF',
                'text': '#000000'
            },
            'typography': {
                'font_family': 'MLBPrimary',
                'base_size': 16,
                'line_height': 1.4
            },
            'spacing': {
                'base_unit': 8,
                'margin': 16,
                'padding': 12
            },
            'borders': {
                'radius': 4,
                'width': 1
            }
        }

    def _get_accessibility_rules(self) -> Dict[str, Any]:
        """Get accessibility compliance rules."""
        return {
            'min_contrast_ratio': 4.5,  # WCAG AA standard
            'min_touch_target': 44,  # iOS minimum
            'required_labels': True,
            'semantic_markup': True,
            'keyboard_navigation': True,
            'screen_reader_support': True
        }

    def _get_platform_requirements(self) -> Dict[str, Any]:
        """Get cross-platform consistency requirements."""
        return {
            'ios': {
                'min_touch_target': 44,
                'safe_area_support': True,
                'dynamic_type_support': True
            },
            'android': {
                'min_touch_target': 48,
                'material_design': True,
                'adaptive_icons': True
            },
            'common': {
                'responsive_design': True,
                'gesture_consistency': True,
                'performance_standards': True
            }
        }