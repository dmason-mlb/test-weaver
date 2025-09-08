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

from src.pipeline import TestGenerationPipeline
from src.bullpen_integration import BullpenGatewayParser
from src.reporting import TestReportGenerator

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