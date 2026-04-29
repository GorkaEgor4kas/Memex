import typer
from rich.console import Console
from rich.panel import Panel
from cli.commands.index import index as index_cmd

console = Console()


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

    console.print("[green]Chat started. Model loaded. Type /exit to quit, /index to reindex and /ask to ask a question.[/green]")

    while True:
        try:
            query = typer.prompt(">> ")
        except (EOFError, KeyboardInterrupt):
            break

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

        parts = query.split()
        offline = "--offline" in parts or "-o" in parts
        show_sources = "--show-sources" in parts or "-s" in parts
        verbose = "--verbose" in parts or "-v" in parts

        import asyncio
        chunks = asyncio.run(hybrid_search.search(query))

        if not chunks:
            console.print("[yellow]Nothing found.[/yellow]")
            continue

        if verbose:
            console.print(f"[dim]Found {len(chunks)} chunks[/dim]")

        # Mode
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