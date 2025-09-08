"""
Demo script showing test generation for all MLB SDUI screens.
"""

import asyncio
from rich.console import Console
from rich.table import Table

console = Console()

async def run_full_demo():
    """Run test generation for all MLB SDUI screens."""
    
    screens = ["Gameday", "Scoreboard", "Browse", "Team Page"]
    platforms = ["ios", "android"]
    
    results = []
    
    for screen in screens:
        for platform in platforms:
            console.print(f"\n[bold blue]Testing {screen} - {platform.upper()}[/bold blue]")
            
            # Generate tests
            tests = await generate_tests_for_screen(screen, platform)
            
            results.append({
                'screen': screen,
                'platform': platform,
                'test_count': len(tests),
                'coverage': calculate_coverage(tests)
            })
    
    # Display summary
    display_summary_table(results)

def display_summary_table(results):
    """Display test generation summary."""
    table = Table(title="MLB SDUI Test Generation Summary")
    
    table.add_column("Screen", style="cyan")
    table.add_column("Platform", style="magenta")
    table.add_column("Tests Generated", style="green")
    table.add_column("Coverage", style="yellow")
    
    for result in results:
        table.add_row(
            result['screen'],
            result['platform'],
            str(result['test_count']),
            f"{result['coverage']}%"
        )
    
    console.print(table)
    
    # Total metrics
    total_tests = sum(r['test_count'] for r in results)
    avg_coverage = sum(r['coverage'] for r in results) / len(results)
    
    console.print(f"\n[bold green]Total Tests Generated: {total_tests}[/bold green]")
    console.print(f"[bold yellow]Average Coverage: {avg_coverage:.1f}%[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(run_full_demo())