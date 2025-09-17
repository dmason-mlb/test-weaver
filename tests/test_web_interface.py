"""
Tests for web_interface.py constants and basic imports.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestWebInterfaceConstants:
    """Test web interface constants and configuration."""
    
    def test_mlb_colors(self):
        """Test MLB color constants."""
        # Mock streamlit at module level to avoid import issues
        with patch.dict('sys.modules', {'streamlit': Mock()}):
            # Now we can safely import
            import web_interface
            
            assert hasattr(web_interface, 'MLB_COLORS')
            colors = web_interface.MLB_COLORS
            
            assert 'primary' in colors
            assert 'secondary' in colors
            assert 'white' in colors
            
            # Verify color values
            assert colors['primary'] == '#002D72'  # MLB Blue
            assert colors['secondary'] == '#D50032'  # MLB Red
            assert colors['white'] == '#FFFFFF'


if __name__ == "__main__":
    pytest.main([__file__])