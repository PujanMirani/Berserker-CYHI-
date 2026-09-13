import typer
from omnix import triage, doctor, sweep

app = typer.Typer(
    name="omnix",
    help="Unified Developer CLI: Hackathon Toolkit",
    add_completion=False,
)

app.add_typer(triage.app, name="triage", help="GitHub Actions log extractor and auto-remediator")
app.add_typer(doctor.app, name="doctor", help="Environment checker")
app.add_typer(sweep.app, name="sweep", help="Git branch janitor")

@app.command()
def tool4():
    """Tool 4 (To be defined)"""
    typer.echo("Tool 4 is not yet implemented.")

if __name__ == "__main__":
    app()
