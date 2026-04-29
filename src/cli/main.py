import sys
import typer
from .commands.index import index 
from .commands.ask import ask
from .commands.config import config
from .commands.chat import chat

app = typer.Typer()

app.command(name="index")(index)
app.command(name="ask")(ask)
app.command(name="config")(config)
app.command(name="chat")(chat)

if __name__ == "__main__":
    app()

