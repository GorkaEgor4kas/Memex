import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from memex.indexing.orchestrator import IndexOrchestrator


console = Console()


def index(
        force: bool = typer.Option(False, "--force", '-f', help="Full reindexing"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help=" Detailed output"),
        dry_run: bool = typer.Option(False, "--dry-run", '-n', help="Preview without changes")
):
    '''Index Obsidian vault into vector database'''

    orchestrator = IndexOrchestrator(
        force=force,
        verbose=verbose,
        dry_run=dry_run
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Indexing vault...", total=None)

        result = asyncio.run(orchestrator.run())

        progress.update(task, completed=True, description="[green]Indexing complete!")

    if dry_run:
        _print_dry_run_report(result)

    else:
        _print_stats(result)


def _print_stats(stats: dict):
    """Print indexing statistics."""
    console.print("\n[bold green]✅ Indexing complete![/bold green]")
    console.print(f"  Files processed: {stats['processed']}")
    console.print(f"  Files deleted: {stats['deleted']}")
    console.print(f"  Total chunks: {stats['chunks']}")

def _print_dry_run_report(report: dict):
    """Print dry run report as a table."""
    table = Table(title="Dry Run Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total files", str(report["total_files"]))
    table.add_row("To process", str(report["to_process"]))
    table.add_row("  └─ New files", str(len(report.get("new_files", []))))
    table.add_row("  └─ Modified files", str(len(report.get("modified_files", []))))
    table.add_row("To delete", str(report["to_delete"]))
    table.add_row("Unchanged", str(report["unchanged"]))

    console.print(table)

    if report.get("new_files"):
        console.print("\n[bold]New files:[/bold]")
        for f in report["new_files"]:
            console.print(f"  [green]+ {f}[/green]")
    
    if report.get("modified_files"):
        console.print("\n[bold]Modified files:[/bold]")
        for f in report["modified_files"]:
            console.print(f"  [yellow]~ {f}[/yellow]")
    
    if report.get("deleted_files"):
        console.print("\n[bold]Deleted files:[/bold]")
        for f in report["deleted_files"]:
            console.print(f"  [red]- {f}[/red]")