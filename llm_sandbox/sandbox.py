def run():
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    console.print(Panel.fit("[bold magenta]🧠 LLM Sandbox & Agent Manager[/bold magenta]\n[dim]This tool manages local LLMs and tests sub-agents against rules.[/dim]"))
    console.print("\n[dim]Implementation pending...[/dim]")
    input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    run()
