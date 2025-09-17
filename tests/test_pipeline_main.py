"""
Tests for pipeline.py main function.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import main


class TestPipelineMain:
    """Test pipeline main CLI function."""
    
    @patch('pipeline.TestGenerationPipeline')
    def test_main_with_valid_schema(self, mock_pipeline):
        """Test main function with valid UI schema."""
        # Create a temporary schema file
        schema_data = {
            "screen": "test_screen",
            "components": [
                {"type": "button", "id": "test_button"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            schema_file = f.name
        
        # Mock pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_all_test_scenarios.return_value = [
            {"test_name": "test_example", "test_type": "unit"}
        ]
        
        # Test with basic arguments
        test_args = ['test-gen', schema_file]
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                main()
        
        # Verify pipeline was called
        mock_pipeline.assert_called_once()
        mock_pipeline_instance.generate_all_test_scenarios.assert_called_once()
        
        # Clean up
        Path(schema_file).unlink()
    
    def test_main_with_missing_file(self):
        """Test main function with missing schema file."""
        test_args = ['test-gen', 'nonexistent.json']
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                with patch('builtins.print'):
                    main()
            
            assert exc_info.value.code == 1
    
    @patch('pipeline.TestGenerationPipeline')
    def test_main_with_output_file(self, mock_pipeline):
        """Test main function with output file specified."""
        # Create a temporary schema file
        schema_data = {"screen": "test", "components": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            schema_file = f.name
        
        # Mock pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_all_test_scenarios.return_value = []
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_f:
            output_file = output_f.name
        
        # Test with output file
        test_args = ['test-gen', schema_file, '--output', output_file]
        with patch('sys.argv', test_args):
            with patch('builtins.print'):
                main()
        
        # Verify output file was created
        assert Path(output_file).exists()
        
        # Clean up
        Path(schema_file).unlink()
        Path(output_file).unlink()
    
    def test_main_with_verbose_flag(self):
        """Test main function with verbose flag."""
        # Create a temporary schema file
        schema_data = {"screen": "test", "components": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            schema_file = f.name
        
        test_args = ['test-gen', schema_file, '--verbose']
        with patch('sys.argv', test_args):
            with patch('pipeline.TestGenerationPipeline') as mock_pipeline:
                mock_pipeline_instance = Mock()
                mock_pipeline.return_value = mock_pipeline_instance
                mock_pipeline_instance.generate_all_test_scenarios.return_value = []
                
                with patch('builtins.print') as mock_print:
                    main()
                
                # Verify verbose output
                assert mock_print.called
        
        # Clean up
        Path(schema_file).unlink()
    
    def test_main_with_invalid_json(self):
        """Test main function with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            invalid_file = f.name
        
        test_args = ['test-gen', invalid_file]
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                with patch('builtins.print'):
                    main()
            
            assert exc_info.value.code == 1
        
        # Clean up
        Path(invalid_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])