# memex/cli/commands/chat.py
import typer
import threading
from rich.console import Console
from rich.panel import Panel
from memex.core.core import MemexCore
from memex.cli.commands.index import index as index_cmd

console = Console()


class TimeoutTimer:
    """Timer with reset option."""

    def __init__(self, timeout_seconds: int):
        self.timeout = timeout_seconds
        self.timer = None
        self.expired = False

    def start(self):
        self.timer = threading.Timer(self.timeout, self._on_expire)
        self.timer.daemon = True
        self.timer.start()

    def reset(self):
        if self.timer:
            self.timer.cancel()
        self.start()

    def _on_expire(self):
        self.expired = True
        console.print("\n[yellow]Timeout reached. Exiting chat...[/yellow]")


def chat(
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout in minutes before unloading model"),
):
    """Start interactive chat session with persistent model."""

    memex = MemexCore()

    timeout_seconds = timeout * 60
    timer = TimeoutTimer(timeout_seconds)
    timer.start()

    console.print(
        f"[green]Chat started. Model loaded. Timeout: {timeout} min. "
        f"Type /exit to quit, /index to reindex.[/green]"
    )

    while True:
        if timer.expired:
            break

        try:
            query = typer.prompt(">> ")
        except (EOFError, KeyboardInterrupt):
            break

        timer.reset()

        if query == "/exit":
            break

        elif query.startswith("/index"):
            console.print("[yellow]Reindexing...[/yellow]")
            parts = query.split()
            force = "--force" in parts or "-f" in parts
            verbose = "--verbose" in parts or "-v" in parts
            dry_run = "--dry-run" in parts or "-n" in parts
            index_cmd(force=force, verbose=verbose, dry_run=dry_run)
            continue

        elif not query.strip():
            continue

        # Parse flags from query
        parts = query.split()
        offline = "--offline" in parts or "-o" in parts
        show_sources = "--show-sources" in parts or "-s" in parts
        verbose = "--verbose" in parts or "-v" in parts

        # Remove flags from query
        clean_parts = [p for p in parts if not p.startswith("-")]
        clean_query = " ".join(clean_parts)

        result = memex.search(clean_query, offline=offline)

        if result["status"] == "empty":
            console.print("[yellow]Nothing found.[/yellow]")
            continue

        if verbose:
            console.print(f"[dim]Found {len(result['chunks'])} chunks[/dim]")

        title = "Answer" if result["status"] == "llm_answer" else "Search Results"
        console.print(Panel(result["answer"], title=title))

        if show_sources:
            _print_sources(result["sources"])


def _print_sources(sources: set):
    console.print("\n[bold]Sources:[/bold]")
    for source in sorted(sources):
        console.print(f"  - {source}")