import typer
from rich.console import Console
from rich.panel import Panel

from memex.core.core import MemexCore


console = Console()

def ask(
        query: str = typer.Argument(..., help="Your question"),
        offline: bool = typer.Option(False, "--offline", '-o', help="Force offline mode"),
        show_sources: bool = typer.Option(False, "--show-sources", '-s', help="Show source files"),
        verbose: bool = typer.Option(False, "--verbose", '-v', help="Show processes")
):
    '''Ask a question about your Obsidian notes'''

    console.print(f"[bold]Question:[/bold] {query}")

    memex = MemexCore()
    result = memex.search(query, offline)

    if result["status"] == "empty":
        console.print("[yellow]Nothing found.[/yellow]")
        return

    if verbose:
        console.print(f"[dim]Found {len(result['chunks'])} relevant chunks[/dim]")

    title = "Answer" if result["status"] == "llm_answer" else "Search Results"
    console.print(Panel(result["answer"], title=title))

    if show_sources:
        _print_sources(result["sources"])


def _print_sources(sources: set):
    console.print("\n[bold]Sources:[/bold]")
    for source in sorted(sources):
        console.print(f"  - {source}")

