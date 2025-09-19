"""
Main entry point for the Intelligent Test Case Generator.
Generates tests for MLB's actual SDUI screens using real Bullpen Gateway responses.
"""

import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from loguru import logger

from bullpen_integration.bullpen_gateway_parser import BullpenGatewayParser, SDUITestScenario
from pipeline import TestGenerationPipeline

console = Console()

# MLB's actual SDUI screens with real data file mappings
MLB_SDUI_SCREENS = {
    "gameday": {
        "name": "Gameday",
        "response_file": "data/gameday/gameday-ios-response.json",
        "request_file": "data/gameday/gameday-ios-request.txt",
        "endpoint": "/api/gameday/v1",
        "description": "WebView-based live game experience"
    },
    "scoreboard": {
        "name": "Scoreboard",
        "response_file": "data/scoreboard/scoreboard-ios.json",
        "request_file": "data/scoreboard/scoreboard-ios-request.txt",
        "endpoint": "/api/scoreboard/v1",
        "description": "Mixed native and web content scoreboard"
    },
    "browse": {
        "name": "Browse",
        "response_file": "data/browse/browse-ios-response.json",
        "request_file": "data/browse/browse-ios-request.txt",
        "endpoint": "/api/browse/v1",
        "description": "Native grid-based content discovery"
    },
    "team": {
        "name": "Team Page",
        "response_file": "data/team/teampage-guardians-ios-response.json",
        "request_file": "data/team/teampage-guardians-ios-request.txt",
        "endpoint": "/api/team/v1",
        "description": "Native team information and stats"
    }
}

async def generate_tests_for_mlb_sdui(screen_name: str, screen_config: dict) -> list:
    """Generate tests for real MLB SDUI screens from Bullpen Gateway responses."""

    console.print(f"[bold blue]⚾ MLB Test Generator - {screen_config['name']} Screen[/bold blue]")
    console.print("[yellow]Analyzing Real Bullpen Gateway SDUI Response[/yellow]\n")

    # Load real request and response data
    request_file = Path(screen_config['request_file'])
    response_file = Path(screen_config['response_file'])

    if not request_file.exists():
        console.print(f"[red]Request file not found: {request_file}[/red]")
        return []

    if not response_file.exists():
        console.print(f"[red]Response file not found: {response_file}[/red]")
        return []

    with open(request_file, 'r') as f:
        request_data = parse_request_file(f.read())

    with open(response_file, 'r') as f:
        response_data = json.load(f)

    # Parse Bullpen Gateway structure with enhanced parser
    console.print("[cyan]📋 Parsing Real Bullpen Gateway SDUI Structure...[/cyan]")
    parsed_structure = BullpenGatewayParser.parse_sdui_response(
        response_data,
        request_data
    )

    # Display parsing results
    display_parsing_results(parsed_structure, screen_config['name'])

    # Extract test scenarios from parsed structure
    test_scenarios = parsed_structure.get('test_scenarios', [])

    # Convert SDUITestScenario objects to test dictionaries
    tests = []
    for scenario in test_scenarios:
        if isinstance(scenario, SDUITestScenario):
            tests.append({
                'test_name': scenario.name,
                'test_type': scenario.type,
                'description': scenario.description,
                'priority': scenario.priority,
                'component_id': scenario.component_id,
                'test_code': scenario.test_code,
                'coverage_type': scenario.type,
                'scenario': 'real_sdui',
                'authentication_required': scenario.authentication_required
            })
        else:
            # Handle legacy format
            tests.append({
                'test_name': scenario.get('name', 'unknown_test'),
                'test_type': scenario.get('type', 'unknown'),
                'description': scenario.get('description', ''),
                'priority': scenario.get('priority', 'medium'),
                'component_id': 'unknown',
                'test_code': '# Test code not generated',
                'coverage_type': scenario.get('type', 'unknown'),
                'scenario': 'legacy'
            })

    # Display and export results
    display_test_results(tests, screen_config['name'])
    export_tests_for_platform(tests, screen_config['name'], request_data.get('platform', 'ios'))

    return tests

def has_webview_sections(structure):
    """Check if UI structure contains webview sections."""
    if not structure:
        return False

    # Check for webview components
    if 'components' in structure:
        for component in structure['components']:
            if component.get('type') == 'webview':
                return True

    # Check for URL fields indicating webview content
    if 'navigation' in structure and 'url' in structure['navigation']:
        return True

    # Check for webViews array
    if 'webViews' in structure and structure['webViews']:
        return True

    return False


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


def display_parsing_results(parsed_structure: dict, screen_name: str):
    """Display the results of parsing the Bullpen Gateway response."""
    console.print(f"\n[bold green]📊 {screen_name} SDUI Analysis Results[/bold green]")

    # Display screens information
    screens = parsed_structure.get('screens', [])
    sections = parsed_structure.get('sections', [])
    webviews = parsed_structure.get('webviews', [])
    promo_banners = parsed_structure.get('promo_banners', [])
    tile_grids = parsed_structure.get('tile_grids', [])

    analysis_table = Table(title=f"{screen_name} Structure Analysis")
    analysis_table.add_column("Component Type", style="cyan", no_wrap=True)
    analysis_table.add_column("Count", justify="right", style="magenta")
    analysis_table.add_column("Details", style="green")

    layout_variants = []
    for screen in screens:
        layout_variants.extend(screen.get('layout', {}).keys())
    layout_info = ', '.join(set(layout_variants)) if layout_variants else 'None'
    analysis_table.add_row("Screens", str(len(screens)), f"Layout variants: {layout_info}")
    analysis_table.add_row("Total Sections", str(len(sections)), f"Various component types")
    analysis_table.add_row("WebViews", str(len(webviews)), f"Interactive web content")
    analysis_table.add_row("Promo Banners", str(len(promo_banners)), f"Marketing content")
    analysis_table.add_row("Tile Grids", str(len(tile_grids)), f"Grid-based navigation")

    console.print(analysis_table)

    # Display component breakdown
    if sections:
        console.print(f"\n[bold cyan]🧩 Component Breakdown:[/bold cyan]")
        component_types = {}
        for section in sections:
            comp_type = section.get('componentType', 'Unknown')
            component_types[comp_type] = component_types.get(comp_type, 0) + 1

        for comp_type, count in component_types.items():
            console.print(f"  • {comp_type}: {count}")

    # Display authentication info
    auth_info = parsed_structure.get('authentication')
    if auth_info:
        console.print(f"\n[bold yellow]🔐 Authentication: Bearer token detected[/bold yellow]")
    else:
        console.print(f"\n[bold yellow]🔓 Authentication: No bearer token[/bold yellow]")


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




async def main():
    """Main async entry point for generating MLB SDUI tests from real Bullpen Gateway responses."""
    console.print("[bold blue]🚀 MLB SDUI Test Generator[/bold blue]")
    console.print("[yellow]Processing Real Bullpen Gateway NPD Responses[/yellow]\n")

    total_tests_generated = 0
    all_test_results = {}

    # Generate tests for each MLB screen using real Bullpen data
    for screen_name, screen_config in MLB_SDUI_SCREENS.items():
        console.print(f"\n[bold cyan]Processing {screen_config['name']} Screen...[/bold cyan]")
        console.print(f"[dim]Description: {screen_config['description']}[/dim]")

        try:
            # Generate tests using real Bullpen Gateway responses
            tests = await generate_tests_for_mlb_sdui(screen_name, screen_config)

            if tests:
                total_tests_generated += len(tests)
                all_test_results[screen_name] = tests
                console.print(f"[green]✅ Generated {len(tests)} tests for {screen_config['name']}[/green]")
            else:
                console.print(f"[yellow]⚠️  No tests generated for {screen_config['name']} (missing data files)[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Error processing {screen_config['name']}: {str(e)}[/red]")
            logger.error(f"Error processing {screen_name}: {e}")

    # Display final summary
    console.print(f"\n[bold green]📊 Final Summary[/bold green]")

    summary_table = Table(title="Test Generation Summary")
    summary_table.add_column("Screen", style="cyan", no_wrap=True)
    summary_table.add_column("Tests Generated", justify="right", style="magenta")
    summary_table.add_column("Status", style="green")

    for screen_name, screen_config in MLB_SDUI_SCREENS.items():
        test_count = len(all_test_results.get(screen_name, []))
        status = "✅ Complete" if test_count > 0 else "⚠️  No data"
        summary_table.add_row(screen_config['name'], str(test_count), status)

    console.print(summary_table)

    console.print(f"\n[bold green]✅ Total: {total_tests_generated} real SDUI tests generated![/bold green]")
    console.print("[dim]Tests are based on actual Bullpen Gateway NPD responses[/dim]")

    return all_test_results


if __name__ == "__main__":
    asyncio.run(main())