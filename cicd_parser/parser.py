import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_latest_failed_run(repo: str):
    """Hits the GitHub API to find the most recent failed Actions run."""
    url = f"https://api.github.com/repos/{repo}/actions/runs?status=failure&per_page=1"
    console.print(f"[dim]Searching for failed pipelines in {repo}...[/dim]")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            console.print("[red]❌ Repository not found or is private.[/red]")
            return None
        elif response.status_code == 403:
            console.print("[red]❌ GitHub API rate limit exceeded.[/red]")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        if data.get("total_count", 0) == 0:
            console.print("[green]✅ No failed pipeline runs found in this repository![/green]")
            return None
            
        return data["workflow_runs"][0]
        
    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Failed to connect to GitHub API: {str(e)}[/red]")
        return None

def download_run_logs(repo: str, run_id: int):
    """Downloads the actual log files for the failed run (Note: this often requires auth)."""
    # The logs download endpoint redirects to a zip file. 
    # For public repos without a token, this can sometimes fail, but we'll attempt it.
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs"
    console.print(f"[dim]Attempting to download logs for run {run_id}...[/dim]")
    
    try:
        response = requests.get(url, timeout=15, allow_redirects=True)
        if response.status_code == 401 or response.status_code == 404:
            console.print("[yellow]🚧 The raw logs for this run are protected or expired. Authentication may be required.[/yellow]")
            return None
            
        response.raise_for_status()
        console.print(f"[green]✓ Successfully downloaded log archive ({len(response.content)} bytes)[/green]")
        return response.content
        
    except requests.exceptions.RequestException as e:
        console.print(f"[yellow]🚧 Failed to download raw logs: {str(e)}[/yellow]")
        return None

def run(repo_url: str):
    console.print(Panel.fit("[bold yellow]🚧 CI/CD Parser[/bold yellow]\n[dim]Extracting human-readable summaries from broken pipelines.[/dim]"))
    
    # Strip github.com if they pasted a full URL
    repo = repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
    
    failed_run = get_latest_failed_run(repo)
    
    if failed_run:
        run_id = failed_run["id"]
        run_name = failed_run.get("name", "Unknown Workflow")
        console.print(f"\n[bold red]🚨 Found Failed Pipeline:[/bold red] [cyan]{run_name}[/cyan] (Run ID: {run_id})")
        
        # In the future, this is where you will unpack the zip and parse the 500 lines.
        # For now, we prove the download pipeline works.
        log_content = download_run_logs(repo, run_id)
        
        console.print("\n[dim]Implementation of the 500-line Error Summarizer AI is pending...[/dim]")
        
    input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    run("torvalds/linux") # Example default for direct testing
