import typer
from rich.console import Console

console = Console()

def config(
    action: str = typer.Argument(..., help="Action: show, reset, set-api-key, set-mode, set-timeout, set-vault"),
):
    """Manage configuration settings."""

    if action == "show":
        console.print("[bold]Current configuration:[/bold]")
        # ...
    elif action == "reset":
        console.print("[yellow]Reset to defaults[/yellow]")
        # ...
    elif action == "set-api-key":
        console.print("[bold]Current API key:[/bold]")
        # ...
    elif action == "set-mode":
        console.print("[bold]Current mode:[/bold]")
        # ...
    elif action == "set-timeout":
        console.print("[bold]Current timeout:[/bold]")
        # ...
    elif action == "set-vault":
        console.print("[bold]Current vault:[/bold]")
        # ...

# there will be a logic everywhere where now are '...' signs