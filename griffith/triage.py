import os
import re
import sys
import time
import subprocess
import zipfile
import io
import requests
import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()

def get_github_token():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            # Fallback to GitHub CLI if available
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
            token = result.stdout.strip()
        except Exception:
            pass
    return token

def get_git_info():
    try:
        # Get remote URL
        remote_out = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True).stdout.strip()
        # Parse owner/repo
        # Handles https://github.com/owner/repo.git or git@github.com:owner/repo.git
        if "github.com" not in remote_out:
            console.print("[red]Not a GitHub repository.[/red]")
            raise typer.Exit(1)
        
        match = re.search(r'github\.com[:/](.+?)/(.+?)(\.git)?$', remote_out)
        if not match:
            console.print("[red]Could not parse GitHub repository owner/repo.[/red]")
            raise typer.Exit(1)
        owner, repo = match.group(1), match.group(2)
        
        # Get current branch
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True).stdout.strip()
        
        return owner, repo, branch
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to get git info: {e}[/red]")
        raise typer.Exit(1)

def api_request(url, token, stream=False):
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers, stream=stream)
    response.raise_for_status()
    if stream:
        return response
    return response.json()

def fetch_latest_run(owner, repo, branch, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?branch={branch}&per_page=1"
    data = api_request(url, token)
    if not data.get("workflow_runs"):
        return None
    return data["workflow_runs"][0]

def fetch_failed_jobs(owner, repo, run_id, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    data = api_request(url, token)
    failed_jobs = [job for job in data.get("jobs", []) if job["conclusion"] == "failure"]
    return failed_jobs

def download_job_logs(owner, repo, job_id, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # Log endpoint redirects to the raw log text file
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    response.raise_for_status()
    return ""

def parse_logs(log_text):
    # Noise reduction: remove standard timestamps (e.g., 2026-09-12T12:00:00.0000000Z)
    log_lines = log_text.splitlines()
    clean_lines = []
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z (.*)')
    for line in log_lines:
        match = timestamp_pattern.match(line)
        if match:
            clean_lines.append(match.group(1))
        else:
            clean_lines.append(line)
    
    clean_text = "\n".join(clean_lines)
    
    # Isolate stack trace or failing command output
    # Very basic isolation: look for traceback or failing test output
    error_block = []
    in_error = False
    
    failing_test_cmd = None
    missing_module = None
    linter_failure = False
    
    for i, line in enumerate(clean_lines):
        if "Traceback (most recent call last):" in line or "FAILED " in line or "FAIL: " in line or "ERROR: " in line or "ModuleNotFoundError" in line:
            in_error = True
            error_block.append(line)
            continue
        
        if in_error:
            error_block.append(line)
            if "ModuleNotFoundError" in line or "ImportError" in line:
                m = re.search(r"No module named '(.+?)'", line)
                if m:
                    missing_module = m.group(1)
            if "ruff" in line.lower() and "failed" in line.lower():
                linter_failure = True
            
            # Find pytest command
            if "pytest" in line and "::" in line:
                m = re.search(r'(pytest\s+\S+::\S+)', line)
                if m:
                    failing_test_cmd = m.group(1)
            
            # Stop if we hit the GitHub Actions process completion error or trailing noise
            if "##[error]Process completed with exit code" in line:
                break
            
            # Or stop if we hit multiple empty lines
            if not line.strip() and len(error_block) > 5:
                break

    if not error_block:
        # Fallback to last 50 lines
        error_block = clean_lines[-50:]
        
    return "\n".join(error_block), failing_test_cmd, missing_module, linter_failure

def trigger_alert(passed):
    # Desktop notification or sound alert
    if passed:
        console.print("[bold green]✅ CI Passed![/bold green]")
        # Standard bell
        print("\a", end="")
    else:
        console.print("[bold red]❌ CI Failed![/bold red]")
        print("\a\a\a", end="")

def check_and_setup_ci():
    workflows_dir = ".github/workflows"
    has_workflows = os.path.exists(workflows_dir) and any(f.endswith(".yml") or f.endswith(".yaml") for f in os.listdir(workflows_dir))
    if not has_workflows:
        if questionary.confirm("No GitHub Actions CI pipeline found. Would you like Griffith to automatically create one for you?").ask():
            os.makedirs(workflows_dir, exist_ok=True)
            ci_content = """name: Griffith Auto CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Run Tests
        run: |
          # Add your test commands here
          echo "Griffith Auto CI configured."
"""
            with open(os.path.join(workflows_dir, "griffith_ci.yml"), "w") as f:
                f.write(ci_content)
            console.print("[green]✅ CI pipeline created at .github/workflows/griffith_ci.yml[/green]")
            console.print("Please run [bold cyan]git add . && git commit -m 'Add CI' && git push[/bold cyan] to trigger it.")
            raise typer.Exit(0)

def run_triage(watch: bool = False):
    check_and_setup_ci()
    token = get_github_token()
    if not token:
        console.print("[yellow]ℹ️ No GitHub token found. Operating in public-repo mode (rate limits apply).[/yellow]")

    
    owner, repo, branch = get_git_info()
    console.print(f"Tracking repository: [bold cyan]{owner}/{repo}[/bold cyan] on branch: [bold cyan]{branch}[/bold cyan]")
    
    last_run_id = None
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Checking GitHub Actions...", total=None)
        
        while True:
            try:
                run = fetch_latest_run(owner, repo, branch, token)
                if not run:
                    progress.stop()
                    console.print("[yellow]No workflow runs found for this branch.[/yellow]")
                    if not watch:
                        break
                    time.sleep(10)
                    continue
                
                if watch and last_run_id == run["id"] and run["status"] == "completed":
                    # Already processed this run
                    time.sleep(5)
                    continue
                
                last_run_id = run["id"]
                
                if run["status"] != "completed":
                    progress.update(task, description=f"Run {run['id']} is {run['status']}. Waiting...")
                    if not watch:
                        progress.stop()
                        console.print(f"[yellow]Current run is {run['status']}. Use --watch to wait for completion.[/yellow]")
                        break
                    time.sleep(5)
                    continue
                
                progress.stop()
                
                if run["conclusion"] == "success":
                    trigger_alert(passed=True)
                    if not watch:
                        break
                else:
                    trigger_alert(passed=False)
                    console.print(f"Run {run['id']} failed. Fetching logs...")
                    jobs = fetch_failed_jobs(owner, repo, run["id"], token)
                    for job in jobs:
                        console.print(f"Analyzing job: [bold red]{job['name']}[/bold red]")
                        logs = download_job_logs(owner, repo, job["id"], token)
                        
                        error_text, failing_test, missing_module, linter_failure = parse_logs(logs)
                        
                        # Syntax highlighting
                        syntax = Syntax(error_text, "python", theme="monokai", line_numbers=True)
                        console.print(Panel(syntax, title="Extracted Error Log", border_style="red"))
                        
                        # Auto Remediation
                        if failing_test:
                            if questionary.confirm(f"Run failing test locally? ({failing_test})").ask():
                                subprocess.run(failing_test, shell=True)
                        
                        if missing_module:
                            if questionary.confirm(f"Detected missing module '{missing_module}'. Install and add to requirements.txt?").ask():
                                subprocess.run(["pip", "install", missing_module])
                                with open("requirements.txt", "a") as f:
                                    f.write(f"\n{missing_module}\n")
                                console.print(f"[green]Successfully installed {missing_module}[/green]")
                                
                        if linter_failure:
                            if questionary.confirm("Detected linter failure. Run 'ruff format .' locally?").ask():
                                subprocess.run(["ruff", "format", "."])
                                
                    if not watch:
                        break
                        
            except Exception as e:
                progress.stop()
                console.print(f"[red]Error fetching CI data: {e}[/red]")
                if not watch:
                    raise typer.Exit(1)
                time.sleep(10)

@app.callback(invoke_without_command=True)
def main(watch: bool = typer.Option(False, "--watch", "-w", help="Poll GitHub API and alert on completion")):
    run_triage(watch)

if __name__ == "__main__":
    app()
