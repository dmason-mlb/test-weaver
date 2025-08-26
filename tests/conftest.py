"""
Pytest configuration and fixtures for TDD with Claude Code.

INSTRUCTIONS FOR CLAUDE CODE:
1. Run tests in order: test_1_*.py, test_2_*.py, etc.
2. Each test file contains failing tests that define the feature to implement
3. Implement ONLY the minimal code needed to make the current test pass
4. Do not skip ahead or implement features before their tests
5. Use the hackathon partner technologies as specified in requirements.txt
"""

import pytest
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def mock_ui_schema():
    """Sample server-driven UI schema for testing."""
    return {
        "version": "2.1.0",
        "screen": "login",
        "components": [
            {
                "id": "username_input",
                "type": "text_input",
                "properties": {
                    "placeholder": "Enter username",
                    "validation": "email"
                }
            },
            {
                "id": "password_input", 
                "type": "text_input",
                "properties": {
                    "placeholder": "Enter password",
                    "validation": "password"
                }
            },
            {
                "id": "login_button",
                "type": "button",
                "action": "submit_form",
                "properties": {
                    "text": "Login"
                }
            }
        ]
    }

@pytest.fixture
def qdrant_test_config():
    """Qdrant configuration for testing."""
    return {
        "host": os.getenv("QDRANT_HOST", "localhost"),
        "port": int(os.getenv("QDRANT_PORT", 6333)),
        "collection_name": "test_ui_patterns",
        "vector_size": 384
    }