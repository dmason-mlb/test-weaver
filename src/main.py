"""
Main entry point for the Intelligent Test Case Generator.
Generates tests for MLB's actual SDUI screens: Scoreboard, Browse, Team Page, and Gameday.
"""

import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from loguru import logger
import httpx

from pipeline import TestGenerationPipeline
from reporting import TestReportGenerator

console = Console()

# MLB's actual SDUI screens
MLB_SDUI_SCREENS = {
    "gameday": {
        "slug": "Gameday-ios",
        "endpoint": "/api/gameday/v1",
        "params": {"gamepk": "776580", "game_view": "live"}
    },
    "scoreboard": {
        "slug": "Scoreboard-ios",
        "endpoint": "/api/scoreboard/v1",
        "params": {"date": "2025-01-27"}
    },
    "browse": {
        "slug": "Browse-ios", 
        "endpoint": "/api/browse/v1",
        "params": {"category": "video"}
    },
    "team": {
        "slug": "TeamPage-ios",
        "endpoint": "/api/team/v1",
        "params": {"teamId": "147"}  # Yankees
    }
}

async def generate_tests_for_mlb_sdui(screen_name: str, request_file: str, response_file: str):
    """Generate tests for real MLB SDUI screens from Bullpen Gateway."""
    
    console.print(f"[bold blue]⚾ MLB Test Generator - {screen_name.upper()} Screen[/bold blue]")
    console.print("[yellow]Analyzing Bullpen Gateway SDUI Response[/yellow]\n")
    
    # Load real request and response data
    with open(request_file, 'r') as f:
        request_data = parse_request_file(f.read())
    
    with open(response_file, 'r') as f:
        response_data = json.load(f)
    
    # Initialize pipeline
    pipeline = TestGenerationPipeline(
        config="config/bullpen_config.yaml",
        verbose=True
    )
    
    # Parse Bullpen Gateway structure
    console.print("[cyan]📋 Parsing Bullpen Gateway Response Structure...[/cyan]")
    parsed_structure = BullpenGatewayParser.parse_sdui_response(
        response_data,
        request_data
    )
    
    # Generate tests for each component type
    tests = []
    
    # Test WebView sections (like Gameday)
    if has_webview_sections(parsed_structure):
        console.print("[cyan]🌐 Generating WebView tests...[/cyan]")
        webview_tests = await pipeline.generate_webview_tests(parsed_structure)
        tests.extend(webview_tests)
    
    # Test layout structures
    console.print("[cyan]📐 Generating Layout tests...[/cyan]")
    layout_tests = await pipeline.generate_layout_tests(parsed_structure)
    tests.extend(layout_tests)
    
    # Test authentication requirements
    console.print("[cyan]🔐 Generating Authentication tests...[/cyan]")
    auth_tests = await pipeline.generate_auth_tests(request_data['headers'])
    tests.extend(auth_tests)
    
    # Display and export results
    display_test_results(tests, screen_name)
    export_tests_for_platform(tests, screen_name, request_data['platform'])
    
    return tests

def parse_request_file(content: str):
    """Parse the request file format into structured data."""
    lines = content.strip().split('\n')
    request_data = {
        'url': '',
        'method': '',
        'headers': {},
        'platform': 'ios'  # Default, will be detected
    }
    
    for line in lines:
        if line.startswith('Request URL:'):
            request_data['url'] = line.split('Request URL:')[1].strip()
            # Detect platform from URL
            if '-ios' in request_data['url']:
                request_data['platform'] = 'ios'
            elif '-android' in request_data['url']:
                request_data['platform'] = 'android'
        elif line.startswith('Request Method:'):
            request_data['method'] = line.split('Request Method:')[1].strip()
        elif ':' in line and not line.startswith('Status Code') and not line.startswith('Remote Address'):
            # Parse headers
            key, value = line.split(':', 1)
            request_data['headers'][key.strip()] = value.strip()
    
    return request_data


def has_webview_sections(parsed_structure):
    """Check if the parsed structure contains WebView sections."""
    if not parsed_structure:
        return False
    
    # Check for WebView indicators in the structure
    structure_str = str(parsed_structure).lower()
    webview_indicators = ['webview', 'url', 'web_view', 'browser', 'iframe']
    
    return any(indicator in structure_str for indicator in webview_indicators)


def display_test_results(tests, screen_name):
    """Display generated test results in a formatted table."""
    console.print(f"\n[bold green]✅ Generated Tests for {screen_name.title()} Screen[/bold green]")
    
    table = Table(title=f"Test Results - {screen_name.title()}")
    table.add_column("Test Name", style="cyan", no_wrap=True)
    table.add_column("Test Type", style="magenta")
    table.add_column("Coverage", style="green")
    table.add_column("Lines", justify="right", style="blue")
    
    for test in tests:
        test_name = test.get('test_name', 'Unknown')
        test_type = test.get('test_type', 'unknown')
        coverage_type = test.get('coverage_type', 'unknown')
        test_code = test.get('test_code', '')
        line_count = len(test_code.split('\n')) if test_code else 0
        
        table.add_row(test_name, test_type, coverage_type, str(line_count))
    
    console.print(table)
    console.print(f"\n[bold]Total Tests Generated: {len(tests)}[/bold]")


def export_tests_for_platform(tests, screen_name, platform):
    """Export generated tests to platform-specific files."""
    output_dir = Path("examples/generated_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create platform-specific filename
    filename = f"{screen_name}_{platform}_tests.py"
    output_file = output_dir / filename
    
    # Generate test file content
    test_content = f'''"""
Generated tests for {screen_name.title()} screen on {platform.title()} platform.
Auto-generated by Intelligent Test Case Generator.
"""

import pytest
from unittest.mock import Mock, patch


'''
    
    # Add each test to the file
    for test in tests:
        test_code = test.get('test_code', '')
        if test_code:
            test_content += test_code + '\n\n'
    
    # Add test fixtures and utilities
    test_content += '''

@pytest.fixture
def test_environment():
    """Setup test environment for MLB SDUI tests."""
    return Mock()


def setup_test_env():
    """Initialize test environment."""
    return {"initialized": True}
'''
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(test_content)
    
    console.print(f"[green]Tests exported to: {output_file}[/green]")


class BullpenGatewayParser:
    """Temporary parser for Bullpen Gateway responses until module is implemented."""
    
    @staticmethod
    def parse_sdui_response(response_data, request_data):
        """Parse Bullpen Gateway SDUI response."""
        return {
            "screen_type": "sdui",
            "platform": request_data.get('platform', 'ios'),
            "components": [
                {
                    "type": "layout",
                    "id": "main_layout",
                    "properties": response_data.get('layout', {})
                }
            ],
            "webview_sections": response_data.get('webViews', []),
            "navigation": response_data.get('navigation', {}),
            "metadata": {
                "url": request_data.get('url', ''),
                "timestamp": response_data.get('timestamp', ''),
                "version": response_data.get('version', '1.0')
            }
        }


async def main():
    """Main async entry point for generating MLB SDUI tests."""
    console.print("[bold blue]🚀 MLB SDUI Test Generator[/bold blue]")
    console.print("[yellow]Intelligent Test Case Generator for Server-Driven UI[/yellow]\n")
    
    # Check if we have sample data to work with
    examples_dir = Path("examples/sample_ui_schemas")
    if not examples_dir.exists():
        console.print("[red]No sample data found. Creating sample data directory...[/red]")
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a sample UI schema for demonstration
        sample_schema = {
            "screen": "gameday",
            "platform": "ios",
            "components": [
                {
                    "type": "webview",
                    "id": "gameday_webview",
                    "url": "https://www.mlb.com/gameday/embed",
                    "requires_auth": True
                },
                {
                    "type": "button",
                    "id": "refresh_button",
                    "action": "refresh_gameday"
                },
                {
                    "type": "list",
                    "id": "plays_list",
                    "refresh_enabled": True,
                    "max_items": 50
                }
            ]
        }
        
        sample_file = examples_dir / "gameday_sample.json"
        with open(sample_file, 'w') as f:
            json.dump(sample_schema, f, indent=2)
        
        console.print(f"[green]Created sample schema: {sample_file}[/green]")
    
    # Generate tests for each MLB screen
    for screen_name, screen_config in MLB_SDUI_SCREENS.items():
        console.print(f"\n[bold cyan]Processing {screen_name.title()} Screen...[/bold cyan]")
        
        # Use sample data for now (in real scenario, this would be actual Bullpen data)
        sample_file = examples_dir / f"{screen_name}_sample.json"
        if not sample_file.exists():
            # Create sample for this screen if it doesn't exist
            sample_schema = {
                "screen": screen_name,
                "platform": "ios",
                "endpoint": screen_config["endpoint"],
                "components": [
                    {
                        "type": "api_endpoint",
                        "url": screen_config["endpoint"],
                        "params": screen_config["params"]
                    }
                ]
            }
            with open(sample_file, 'w') as f:
                json.dump(sample_schema, f, indent=2)
        
        # Load and process the schema
        with open(sample_file, 'r') as f:
            ui_spec = json.load(f)
        
        # Initialize pipeline and generate tests
        pipeline = TestGenerationPipeline(config="config/bullpen_config.yaml")
        test_scenarios = pipeline.generate_all_test_scenarios(ui_spec)
        
        # Display results
        display_test_results(test_scenarios, screen_name)
        export_tests_for_platform(test_scenarios, screen_name, ui_spec.get('platform', 'ios'))
    
    console.print("\n[bold green]✅ All MLB SDUI tests generated successfully![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())