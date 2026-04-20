import typer
from rich.console import Console

console = Console()

def index(
        force: bool = typer.Option(False, "--force", '-f', help="Full reindexing"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help=" Detailed output"),
        dry_run: bool = typer.Option(False, "--dry-run", '-n', help="Preview without changes")
):
    '''Index Obsidian vault into vector database'''

    if dry_run:
        console.print("Files will be here")
        # dry-run logic will be here

    # main indexing logic will be here (with force and verbose argumets if it exists)

    console.print("Indexing complete!")

