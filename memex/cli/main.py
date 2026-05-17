import sys
import typer
from memex.cli.commands.index import index 
from memex.cli.commands.ask import ask
from memex.cli.commands.config import config
from memex.cli.commands.chat import chat

app = typer.Typer()

app.command(name="index")(index)
app.command(name="ask")(ask)
app.command(name="config")(config)
app.command(name="chat")(chat)

if __name__ == "__main__":
    app()

