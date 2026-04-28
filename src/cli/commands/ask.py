import typer
import asyncio
from rich.console import Console
from rich.panel import Panel

from retrieval.hybrid_search import HybridSearch
from generation.decider import Decider
from generation.llm_client import LLMClient
from generation.prompt import SYSTEM_PROMPT


console = Console()

def ask(
        query: str = typer.Argument(..., help="Your question"),
        offline: bool = typer.Option(False, "--offline", '-o', help="Force offline mode"),
        show_sources: bool = typer.Option(False, "--show-sources", '-s', help="Show source files"),
        verbose: bool = typer.Option(False, "--verbose", '-v', help="Show processes")
):
    '''Ask a question about your Obsidian notes'''

    console.print(f"[bold]Question:[/bold] {query}")

    #init
    hybrid_search = HybridSearch()
    decider = Decider()

    #retrieval
    chunks = asyncio.run(hybrid_search.search(query))

    if not chunks:
        console.print("[yellow]Nothing found.[/yellow]")
        return
    
    if verbose:
        console.print(f"[dim]Found {len(chunks)} relevant chunks[/dim]")

    #mode decision
    decision = decider.decide(chunks, offline_flag=offline)

    #offline
    if decision["action"] == "return_chunks":
        console.print(Panel(decision["data"], title="Search Results"))
        if show_sources:
            _print_sources(chunks)
    
    #online
    else:
        if verbose:
            console.print("[dim]Sending to LLM...[/dim]")
        
        llm_client = LLMClient()
        response = llm_client.generate(
            context=decision["data"],
            query=query,
            system_prompt=SYSTEM_PROMPT,
        )

        console.print(Panel(response, title="Answer"))
        if show_sources:
            _print_sources(chunks)

def _print_sources(chunks: list):
    """Print source files."""

    sources = set()
    for chunk in chunks:
        source = chunk["metadata"].get("source_file", "unknown")
        sources.add(source)
    
    console.print("\n[bold]Sources:[/bold]")
    for source in sources:
        console.print(f" - {source}")

