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
    console.print(Panel.fit("[bold cyan]🛠  Berserker Hackathon Toolkit[/bold cyan]\n[dim]Select a tool to launch[/dim]", border_style="cyan"))

    choices = [
        "1️⃣  berserker   — Cross-Service Log Correlation",
        "2️⃣  griffith    — CI/CD Pipeline Error Summarizer",
        "3️⃣  GodsHand    — Local LLM Sandbox & Agent Manager",
        "❌ Exit"
    ]

    choice = questionary.select(
        "Select a tool to run:",
        choices=choices
    ).ask()

    if not choice or "Exit" in choice:
        console.print("[yellow]Goodbye![/yellow]")
        return

    if "berserker" in choice:
        try:
            from digger.digger import run as digger_run
            digger_run()
        except ImportError:
            console.print("[red]❌ digger module not found. Are you on the right branch?[/red]")
            
    elif "griffith" in choice:
        try:
            from cicd_parser.parser import run as parser_run
            repo_url = questionary.text(
                "Enter GitHub Repository (e.g., owner/repo):",
                default="owner/repo"
            ).ask()
            if repo_url and repo_url != "owner/repo":
                parser_run(repo_url)
            else:
                console.print("[yellow]Invalid repository. Exiting.[/yellow]")
        except ImportError:
            console.print("[yellow]🚧 griffith is currently under construction on the griffith branch.[/yellow]")
            
    elif "GodsHand" in choice:
        try:
            from llm_sandbox.sandbox import run as sandbox_run
            sandbox_run()
        except ImportError:
            console.print("[yellow]🚧 GodsHand is currently under construction on the conrad branch.[/yellow]")

if __name__ == "__main__":
    main()
