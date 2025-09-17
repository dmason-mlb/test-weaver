"""
Tests for main.py functionality.
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import (
    parse_request_file,
    has_webview_sections,
    display_test_results,
    export_tests_for_platform,
    BullpenGatewayParser,
    main
)


class TestParseRequestFile:
    """Test request file parsing functionality."""
    
    def test_parse_basic_request(self):
        """Test parsing a basic request file."""
        request_content = """Request URL: https://bullpen-gateway-svc.mlbinfra.com/api/gameday-ios/v1
Request Method: GET
Authorization: Bearer token123
User-Agent: MLB/1.0 iOS
"""
        result = parse_request_file(request_content)
        
        assert result['url'] == 'https://bullpen-gateway-svc.mlbinfra.com/api/gameday-ios/v1'
        assert result['method'] == 'GET'
        assert result['platform'] == 'ios'
        assert result['headers']['Authorization'] == 'Bearer token123'
        assert result['headers']['User-Agent'] == 'MLB/1.0 iOS'
    
    def test_parse_android_request(self):
        """Test parsing Android request file."""
        request_content = """Request URL: https://bullpen-gateway-svc.mlbinfra.com/api/gameday-android/v1
Request Method: POST
Content-Type: application/json
"""
        result = parse_request_file(request_content)
        
        assert result['platform'] == 'android'
        assert result['method'] == 'POST'
        assert result['headers']['Content-Type'] == 'application/json'
    
    def test_parse_empty_request(self):
        """Test parsing empty request."""
        result = parse_request_file("")
        
        assert result['url'] == ''
        assert result['method'] == ''
        assert result['platform'] == 'ios'  # Default
        assert result['headers'] == {}


class TestHasWebviewSections:
    """Test webview detection functionality."""
    
    def test_has_webview_true(self):
        """Test detection when webview is present."""
        structure = {
            "components": [
                {"type": "webview", "url": "https://example.com"}
            ]
        }
        assert has_webview_sections(structure) is True
    
    def test_has_webview_url_present(self):
        """Test detection when URL field is present."""
        structure = {
            "navigation": {"url": "https://example.com"}
        }
        assert has_webview_sections(structure) is True
    
    def test_has_webview_false(self):
        """Test detection when no webview is present."""
        structure = {
            "components": [
                {"type": "button", "id": "test_button"}
            ]
        }
        assert has_webview_sections(structure) is False
    
    def test_has_webview_empty_structure(self):
        """Test detection with empty structure."""
        assert has_webview_sections({}) is False
        assert has_webview_sections(None) is False


class TestDisplayTestResults:
    """Test test results display functionality."""
    
    @patch('main.console')
    def test_display_basic_results(self, mock_console):
        """Test displaying basic test results."""
        tests = [
            {
                'test_name': 'test_example',
                'test_type': 'unit',
                'coverage_type': 'integration',
                'test_code': 'def test_example():\n    assert True'
            }
        ]
        
        display_test_results(tests, 'gameday')
        
        # Verify console print was called
        assert mock_console.print.called
        
        # Check that table was created and added
        mock_console.print.assert_any_call("\n[bold green]✅ Generated Tests for Gameday Screen[/bold green]")
        mock_console.print.assert_any_call("\n[bold]Total Tests Generated: 1[/bold]")
    
    @patch('main.console')
    def test_display_empty_results(self, mock_console):
        """Test displaying empty test results."""
        display_test_results([], 'browse')
        
        assert mock_console.print.called
        mock_console.print.assert_any_call("\n[bold]Total Tests Generated: 0[/bold]")


class TestExportTestsForPlatform:
    """Test test export functionality."""
    
    def test_export_tests_basic(self):
        """Test basic test export functionality."""
        tests = [
            {
                'test_name': 'test_example',
                'test_code': 'def test_example():\n    assert True'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('main.Path') as mock_path:
                mock_output_dir = Mock()
                mock_path.return_value = mock_output_dir
                mock_output_dir.mkdir = Mock()
                mock_output_file = Mock()
                mock_output_dir.__truediv__ = Mock(return_value=mock_output_file)
                
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('main.console'):
                        export_tests_for_platform(tests, 'gameday', 'ios')
                
                # Verify directory creation and file operations
                mock_output_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                mock_file.assert_called_once()
    
    def test_export_tests_empty(self):
        """Test exporting empty test list."""
        with patch('main.Path') as mock_path:
            mock_output_dir = Mock()
            mock_path.return_value = mock_output_dir
            mock_output_dir.mkdir = Mock()
            mock_output_file = Mock()
            mock_output_dir.__truediv__ = Mock(return_value=mock_output_file)
            
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('main.console'):
                    export_tests_for_platform([], 'scoreboard', 'android')
            
            # Should still create file even with empty tests
            mock_file.assert_called_once()


class TestBullpenGatewayParser:
    """Test Bullpen Gateway parser functionality."""
    
    def test_parse_sdui_response_basic(self):
        """Test basic SDUI response parsing."""
        response_data = {
            "layout": {"type": "main"},
            "webViews": [{"id": "test_webview", "url": "https://example.com"}],
            "navigation": {"items": ["home", "scores"]}
        }
        
        request_data = {
            "platform": "ios",
            "url": "https://example.com/api"
        }
        
        result = BullpenGatewayParser.parse_sdui_response(response_data, request_data)
        
        assert result["screen_type"] == "sdui"
        assert result["platform"] == "ios"
        assert len(result["components"]) == 1
        assert result["components"][0]["type"] == "layout"
        assert len(result["webview_sections"]) == 1
        assert result["metadata"]["url"] == "https://example.com/api"
    
    def test_parse_sdui_response_empty(self):
        """Test parsing empty response."""
        result = BullpenGatewayParser.parse_sdui_response({}, {})
        
        assert result["screen_type"] == "sdui"
        assert result["platform"] == "ios"  # Default
        assert len(result["components"]) == 1  # Always creates main_layout component
        assert result["components"][0]["type"] == "layout"
        assert result["webview_sections"] == []



class TestMainFunction:
    """Test main async function."""
    
    @patch('main.console')
    @patch('main.Path')
    @patch('main.TestGenerationPipeline')
    def test_main_creates_sample_data(self, mock_pipeline, mock_path, mock_console):
        """Test that main creates sample data when it doesn't exist."""
        # Mock Path behavior
        mock_examples_dir = Mock()
        mock_path.return_value = mock_examples_dir
        mock_examples_dir.exists.return_value = False
        mock_examples_dir.mkdir = Mock()
        
        # Mock file operations
        mock_sample_file = Mock()
        mock_examples_dir.__truediv__ = Mock(return_value=mock_sample_file)
        
        # Mock pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_all_test_scenarios.return_value = [
            {'test_name': 'test_example', 'test_type': 'unit', 'coverage_type': 'integration'}
        ]
        
        with patch('builtins.open', mock_open()):
            with patch('main.json.dump'):
                with patch('main.json.load', return_value={'screen': 'test', 'platform': 'ios'}):
                    with patch('main.display_test_results'):
                        with patch('main.export_tests_for_platform'):
                            # Run main function
                            asyncio.run(main())
        
        # Verify sample directory was created
        mock_examples_dir.mkdir.assert_called_with(parents=True, exist_ok=True)
        
        # Verify console output
        mock_console.print.assert_any_call("[bold blue]🚀 MLB SDUI Test Generator[/bold blue]")
    
    @patch('main.console')
    @patch('main.Path')
    @patch('main.TestGenerationPipeline')
    def test_main_with_existing_data(self, mock_pipeline, mock_path, mock_console):
        """Test main function when sample data already exists."""
        # Mock Path behavior - examples directory exists
        mock_examples_dir = Mock()
        mock_path.return_value = mock_examples_dir
        mock_examples_dir.exists.return_value = True
        
        # Mock sample files exist
        mock_sample_file = Mock()
        mock_sample_file.exists.return_value = True
        mock_examples_dir.__truediv__ = Mock(return_value=mock_sample_file)
        
        # Mock pipeline
        mock_pipeline_instance = Mock()
        mock_pipeline.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_all_test_scenarios.return_value = []
        
        with patch('builtins.open', mock_open()):
            with patch('main.json.load', return_value={'screen': 'test', 'platform': 'ios'}):
                with patch('main.display_test_results'):
                    with patch('main.export_tests_for_platform'):
                        # Run main function
                        asyncio.run(main())
        
        # Verify no sample directory creation (already exists)
        mock_examples_dir.mkdir.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])