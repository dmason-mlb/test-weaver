"""
Main entry point for the Intelligent Test Case Generator.
Showcases all Qdrant Hackathon partner technologies.
"""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from loguru import logger

from src.pipeline import TestGenerationPipeline
from src.mlb_integration import MLBSchemaLoader
from src.reporting import TestReportGenerator

console = Console()

async def generate_tests_for_mlb_app(schema_path: str):
    """Generate comprehensive test suite for MLB server-driven UI."""
    
    console.print("[bold blue]🚀 MLB Intelligent Test Generator[/bold blue]")
    console.print("[yellow]Powered by Qdrant, CrewAI, Mistral AI, and Linkup[/yellow]\n")
    
    # Initialize pipeline with partner technologies
    pipeline = TestGenerationPipeline(
        config="config/hackathon_config.yaml",
        verbose=True
    )
    
    # Load MLB server-driven UI schema
    console.print("[cyan]Loading MLB UI Schema...[/cyan]")
    schema = MLBSchemaLoader.load_from_file(schema_path)
    
    # Generate tests using multi-agent system
    console.print("[cyan]🤖 Activating CrewAI Agents...[/cyan]")
    tests = await pipeline.generate_tests_for_ui(schema)
    
    # Display results
    display_results(tests)
    
    # Export to multiple formats
    export_tests(tests, schema['screen'])
    
    return tests

def display_results(tests):
    """Display generated tests in a beautiful table."""
    table = Table(title="Generated Test Cases")
    table.add_column("Test Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Coverage", style="green")
    table.add_column("Complexity", style="yellow")
    
    for test in tests:
        table.add_row(
            test['name'],
            test['type'],
            f"{test['coverage']}%",
            test['complexity']
        )
    
    console.print(table)

if __name__ == "__main__":
    # Run with sample MLB schemas
    schemas = [
        "examples/sample_ui_schemas/my_daily_story.json",
        "examples/sample_ui_schemas/stadium_navigator.json",
        "examples/sample_ui_schemas/login_screen.json"
    ]
    
    for schema in schemas:
        asyncio.run(generate_tests_for_mlb_app(schema))