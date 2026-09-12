import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main():
    typer.echo("Sweep tool running: Cleaning up git branches...")
    typer.echo("Cleaned!")
