import typer
from rich.console import Console

console = Console()

def ask(
        query: str = typer.Argument(..., help="Your question"),
        offline: bool = typer.Option(False, "--offline", '-o', help="Force online mode"),
        show_sources: bool = typer.Option(False, "--show-sources", '-s', help="Show source files"),
        verbose: bool = typer.Option(False, "--verbose", '-v', help="Show processes")
):
    '''Ask a question about your Obsidian notes'''

    console.print(f"[bold]Question:[/bold] {query}")

    # Search logic will be here (with --ofline argument if it exists)

    if verbose:
        console.print("Time of retrieval")
        # Time of the search will be here

    console.print("Your answer:")
        # Answer will be here

    if show_sources:
        console.print("first doc")
        console.print("second doc")

