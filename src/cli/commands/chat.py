import typer
import threading
import sys
from rich.console import Console
from rich.panel import Panel
from cli.commands.ask import ask
from cli.commands.index import index

console = Console()


class TimeoutTimer:
    """Timer with reset option"""

    def __init__(self, timeout_seconds: int):
        self.timeout = timeout_seconds
        self.timer = None
        self.expired = False

    def start(self):
        """Timer start"""
        self.timer = threading.Timer(self.timeout, self._on_expire)
        self.timer.daemon = True
        self.timer.start()

    def reset(self):
        """Timer reset"""
        if self.timer:
            self.timer.cancel()
        self.start()

    def _on_expire(self):
        """Calls after timeout"""
        self.expired = True
        console.print("\n[yellow]Timeout reached. Exiting chat...[/yellow]")


def chat(
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout in minutes before unloading model"),
):
    """Start interactive chat session with persistent model."""

    from retrieval.hybrid_search import HybridSearch
    from generation.decider import Decider
    from generation.llm_client import LLMClient
    from generation.prompt import SYSTEM_PROMPT

    hybrid_search = HybridSearch()
    decider = Decider()
    llm_client = LLMClient()

    timeout_seconds = timeout * 60
    timer = TimeoutTimer(timeout_seconds)
    timer.start()

    console.print(f"[green]Chat started. Model loaded. Timeout: {timeout} min. Type /exit to quit, /index to reindex.[/green]")

    import asyncio

    while True:
        #timeout check
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
            index(force=force, verbose=verbose, dry_run=dry_run)
            continue

        elif not query.strip():
            continue

        parts = query.split()
        offline = "--offline" in parts or "-o" in parts
        show_sources = "--show-sources" in parts or "-s" in parts
        verbose = "--verbose" in parts or "-v" in parts

        chunks = asyncio.run(hybrid_search.search(query))

        if not chunks:
            console.print("[yellow]Nothing found.[/yellow]")
            continue

        if verbose:
            console.print(f"[dim]Found {len(chunks)} chunks[/dim]")

        decision = decider.decide(chunks, offline_flag=offline)

        if decision["action"] == "return_chunks":
            console.print(Panel(decision["data"], title="Search Results"))
        else:
            if verbose:
                console.print("[dim]Sending to LLM...[/dim]")
            response = llm_client.generate(
                context=decision["data"],
                query=query,
                system_prompt=SYSTEM_PROMPT,
            )
            console.print(Panel(response, title="Answer"))

        if show_sources:
            sources = set()
            for chunk in chunks:
                source = chunk["metadata"].get("source_file", "unknown")
                sources.add(source)
            console.print("\n[bold]Sources:[/bold]")
            for source in sources:
                console.print(f"  - {source}")

    console.print("[dim]Chat ended.[/dim]")