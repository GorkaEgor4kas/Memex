import sys
import typer
from .commands.index import index 
from .commands.ask import ask
from .commands.config import config

app = typer.Typer()

app.command(name="index")(index)
app.command(name="ask")(ask)
app.command(name="config")(config)

if __name__ == "__main__":
    app()

