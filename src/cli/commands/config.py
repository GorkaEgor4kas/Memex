import typer
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def config(
    action: str = typer.Argument(..., help="Action: show, reset, set-api-key, set-mode, set-timeout, set-vault"),
):
    """Manage configuration settings."""

    from core.config import config as cfg

    if action == "show":
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Vault path", str(cfg.path.vault_path))
        table.add_row("Mode", cfg.mode)
        table.add_row("Provider", cfg.online.provider)
        table.add_row("Model", cfg.online.model)
        table.add_row("API key", "***" if cfg.env.get("GROQ_API_KEY") or cfg.env.get("DEEPSEEK_API_KEY") else "Not set")
        table.add_row("Chunk size", str(cfg.indexing.chunk_size))
        table.add_row("Chunk overlap", str(cfg.indexing.chunk_overlap))
        table.add_row("Parental chunking", str(cfg.indexing.use_parental))
        table.add_row("Semantic limit", str(cfg.retrieval.semantic_limit))
        table.add_row("BM25 limit", str(cfg.retrieval.bm25_limit))
        table.add_row("RRF k", str(cfg.retrieval.rrf_k))
        table.add_row("Final limit", str(cfg.retrieval.final_limit))
        table.add_row("BM25 min score", str(cfg.thresholds.bm25_min_score))
        table.add_row("Vector min similarity", str(cfg.thresholds.vector_min_similarity))

        console.print(table)

    elif action == "reset":
        console.print("[yellow]Settings reset is not yet implemented. Edit ~/.obsidian-rag/config.yaml manually.[/yellow]")

    elif action == "set-api-key":
        console.print("[bold]Enter new API key (input hidden):[/bold]")
        key = typer.prompt("API key", hide_input=True)
        provider = typer.prompt("Provider (groq/deepseek)", default="groq")

        env_path = Path(".env") if Path(".env").exists() else Path.home() / ".obsidian-rag" / ".env"

        if not env_path.exists():
            env_path.write_text("")

        content = env_path.read_text()

        if provider == "groq":
            key_line = f"GROQ_API_KEY={key}"
            content = re.sub(r"^GROQ_API_KEY=.*$", key_line, content, flags=re.MULTILINE)
            if "GROQ_API_KEY" not in content:
                content += f"\n{key_line}"
        else:
            key_line = f"DEEPSEEK_API_KEY={key}"
            content = re.sub(r"^DEEPSEEK_API_KEY=.*$", key_line, content, flags=re.MULTILINE)
            if "DEEPSEEK_API_KEY" not in content:
                content += f"\n{key_line}"

        env_path.write_text(content)
        console.print(f"[green]API key saved to {env_path}[/green]")

    elif action == "set-mode":
        mode = typer.prompt("Mode (auto/online/offline)", default="auto")
        console.print(f"[yellow]Mode set to {mode}. Edit ~/.obsidian-rag/config.yaml to persist.[/yellow]")

    elif action == "set-timeout":
        timeout = typer.prompt("Timeout in minutes", type=int, default=30)

        env_path = Path(".env") if Path(".env").exists() else Path.home() / ".obsidian-rag" / ".env"

        if not env_path.exists():
            env_path.write_text("")

        content = env_path.read_text()
        key_line = f"OBSIDIAN_RAG_CHAT_TIMEOUT={timeout}"
        content = re.sub(r"^OBSIDIAN_RAG_CHAT_TIMEOUT=.*$", key_line, content, flags=re.MULTILINE)
        if "OBSIDIAN_RAG_CHAT_TIMEOUT" not in content:
            content += f"\n{key_line}"

        env_path.write_text(content)
        console.print(f"[green]Timeout set to {timeout} minutes. Saved to {env_path}[/green]")

    elif action == "set-vault":
        vault_path = typer.prompt("Path to Obsidian vault")
        console.print(f"[yellow]Vault path set to {vault_path}. Edit ~/.obsidian-rag/config.yaml to persist.[/yellow]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available: show, reset, set-api-key, set-mode, set-timeout, set-vault")