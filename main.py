import sys

def main():
    try:
        import questionary
        from rich.console import Console
        from rich.panel import Panel
    except ImportError:
        print("❌ Missing dependencies! Please run: pip install -r requirements.txt")
        sys.exit(1)

    console = Console()
    console.print(Panel.fit("[bold cyan]🛠  Hackathon Toolkit[/bold cyan]\n[dim]Select a tool to launch[/dim]", border_style="cyan"))

    choices = [
        "🔍 digger     — Correlate logs across services",
        "🔫 portkiller — Kill process bound to a port",
        "🔧 tool3      — Teammate 3 Tool",
        "📦 tool4      — Teammate 4 Tool",
        "❌ Exit"
    ]

    choice = questionary.select(
        "Select a tool to run:",
        choices=choices
    ).ask()

    if not choice or "Exit" in choice:
        console.print("[yellow]Goodbye![/yellow]")
        return

    if "digger" in choice:
        try:
            from digger.digger import run as digger_run
            digger_run()
        except ImportError:
            console.print("[red]❌ digger module not found or feature branch not merged yet.[/red]")
    elif "portkiller" in choice:
        try:
            from portkiller.portkiller import run as portkiller_run
            portkiller_run()
        except ImportError:
            console.print("[yellow]🔫 portkiller (Stub): Teammate portkiller code will run here once implemented.[/yellow]")
    elif "tool3" in choice:
        console.print("[yellow]🔧 Tool 3 (Stub): Teammate 3 code will run here.[/yellow]")
    elif "tool4" in choice:
        console.print("[yellow]📦 Tool 4 (Stub): Teammate 4 code will run here.[/yellow]")

if __name__ == "__main__":
    main()
