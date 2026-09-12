import re
import os
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class LogLine:
    def __init__(self, raw: str, service: str, timestamp: str, level: str, message: str, identifiers: List[str]):
        self.raw = raw
        self.service = service
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.identifiers = identifiers

class DiggerEngine:
    def __init__(self):
        self.lines: List[LogLine] = []
        self.index: Dict[str, List[LogLine]] = {}

    def parse_log_line(self, raw_line: str, service_name: str) -> LogLine:
        """Extract timestamp, level, message, and transaction IDs (UUIDs, order IDs, request IDs)"""
        # Example pattern: 2026-09-12 14:00:01 [INFO] ...
        ts_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', raw_line)
        timestamp = ts_match.group(0) if ts_match else "UNKNOWN_TIME"

        lvl_match = re.search(r'\[(INFO|WARN|WARNING|ERROR|FATAL)\]', raw_line, re.IGNORECASE)
        level = lvl_match.group(1).upper() if lvl_match else "INFO"

        # Regex for common transaction identifiers (UUIDs, order_xxx, req-xxx, transaction IDs)
        id_pattern = r'\b(?:ord_[a-zA-Z0-9]+|req-[a-zA-Z0-9]+|usr_[a-zA-Z0-9]+|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b'
        identifiers = list(set(re.findall(id_pattern, raw_line)))

        return LogLine(
            raw=raw_line.strip(),
            service=service_name,
            timestamp=timestamp,
            level=level,
            message=raw_line.strip(),
            identifiers=identifiers
        )

    def load_logs_from_dir(self, log_dir: str):
        """Read all log files in a directory and index them"""
        if not os.path.exists(log_dir):
            console.print(f"[red]Directory '{log_dir}' not found![/red]")
            return

        for fname in sorted(os.listdir(log_dir)):
            if fname.endswith('.log') or fname.endswith('.txt'):
                service_name = fname.replace('.log', '').replace('.txt', '')
                fpath = os.path.join(log_dir, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        log_obj = self.parse_log_line(line, service_name)
                        self.lines.append(log_obj)
                        for token in log_obj.identifiers:
                            if token not in self.index:
                                self.index[token] = []
                            self.index[token].append(log_obj)

        # Sort all lines chronologically
        self.lines.sort(key=lambda x: x.timestamp)
        console.print(f"[green]✓ Successfully indexed {len(self.lines)} log lines across {len(self.index)} unique identifiers.[/green]")

    def get_context_for_id(self, token: str):
        """Show all cross-service correlated logs matching an identifier"""
        matched = self.index.get(token, [])
        if not matched:
            console.print(f"[yellow]No correlation records found for ID: {token}[/yellow]")
            return

        table = Table(title=f"🔍 Correlated Timeline for Identifier: [bold cyan]{token}[/bold cyan]")
        table.add_column("Timestamp", style="dim", no_wrap=True)
        table.add_column("Service", style="bold cyan")
        table.add_column("Level", style="bold")
        table.add_column("Log Message")

        for entry in matched:
            lvl_style = "red" if entry.level in ["ERROR", "FATAL"] else ("yellow" if "WARN" in entry.level else "green")
            table.add_row(entry.timestamp, entry.service, f"[{lvl_style}]{entry.level}[/{lvl_style}]", entry.message)

        console.print(table)
        console.print("\n[dim]Note: Correlation shows shared transaction identifiers, not proven causality.[/dim]\n")

def run():
    console.print(Panel.fit("[bold magenta]🔍 digger — Cross-Service Log Correlation[/bold magenta]"))

    log_dir = input("Enter directory containing log files (default: './logs'): ").strip() or "./logs"
    
    engine = DiggerEngine()
    engine.load_logs_from_dir(log_dir)

    if not engine.index:
        console.print("[yellow]No identifiers indexed yet. Add some log files with order IDs (ord_123) or UUIDs.[/yellow]")
        return

    console.print("\n[bold]Available Sample Identifiers:[/bold]")
    for token in list(engine.index.keys())[:10]:
        console.print(f" • [cyan]{token}[/cyan] ({len(engine.index[token])} logs)")

    search_id = input("\nEnter transaction/correlation ID to inspect (or press Enter to exit): ").strip()
    if search_id:
        engine.get_context_for_id(search_id)

if __name__ == "__main__":
    run()
