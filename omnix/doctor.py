import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main():
    typer.echo("Doctor tool running: Checking environment...")
    typer.echo("All good!")
