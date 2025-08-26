import pytest

# test_3_agent_initialization.py
def test_crew_without_agents_fails():
    """Test that CrewAI crew cannot be created without agents"""
    from src.test_generation_crew import TestGenerationCrew
    
    crew = TestGenerationCrew()
    with pytest.raises(ValueError, match="Cannot create crew without agents"):
        crew.kickoff()

def test_api_analyzer_agent_missing_tools():
    """Test that API Analyzer agent fails without required tools"""
    from src.agents import APIAnalyzerAgent
    
    agent = APIAnalyzerAgent()
    with pytest.raises(AttributeError, match="API Analyzer requires 'pattern_search_tool'"):
        agent.analyze_endpoint("/api/v1/screen/home")

def test_ui_validator_agent_missing_context():
    """Test that UI Validator agent fails without UI context"""
    from src.agents import UIValidatorAgent
    
    agent = UIValidatorAgent()
    with pytest.raises(ValueError, match="UI context not provided"):
        agent.validate_component({"id": "btn_1", "type": "button"})