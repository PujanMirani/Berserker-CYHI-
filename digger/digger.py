import re
import os
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class LogEntry:
    timestamp: Optional[datetime]
    severity: str
    service: str
    raw_text: str
    identifiers: List[str]
    file_path: str
    line_number: int

# Strict order for tie-breaking: JSON (handled separately), ISO8601, BRACKET, SYSLOG
REGEX_PATTERNS = {
    "ISO8601": re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?'),
    "BRACKET": re.compile(r'\[\d{2}:\d{2}:\d{2}(?:\.\d+)?\]'),
    "SYSLOG":  re.compile(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s+\d{2}:\d{2}:\d{2}')
}

SEVERITY_PATTERN = re.compile(r'\b(INFO|WARN|WARNING|ERROR|FATAL|DEBUG|TRACE)\b', re.IGNORECASE)
ID_PATTERN = re.compile(r'\b(?:ord_[a-zA-Z0-9]+|req-[a-zA-Z0-9]+|usr_[a-zA-Z0-9]+|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[a-zA-Z_]+=[a-zA-Z0-9_-]+)\b')

class DiggerEngine:
    def __init__(self):
        self.entries: List[LogEntry] = []
        self.index: Dict[str, List[LogEntry]] = {}

    def extract_identifiers(self, raw_text: str) -> List[str]:
        # Simple extraction for identifiers and key=value pairs
        return list(set(ID_PATTERN.findall(raw_text)))

    def extract_severity(self, raw_text: str) -> str:
        match = SEVERITY_PATTERN.search(raw_text)
        return match.group(1).upper() if match else "INFO"

    def try_parse_json_line(self, line: str) -> Optional[datetime]:
        try:
            data = json.loads(line)
            # Check common timestamp keys
            for key in ["ts", "timestamp", "time", "date"]:
                if key in data:
                    # Very rough parsing just to prove it works as a timestamp
                    # In a real app we'd use dateutil.parser
                    # For MVP we will just return a dummy datetime to prove it matched, or parse ISO
                    # We will parse basic ISO here since JSON usually has ISO
                    val = str(data[key])
                    # Try to parse it if it looks like ISO
                    iso_match = REGEX_PATTERNS["ISO8601"].search(val)
                    if iso_match:
                        # Success
                        return datetime.now(timezone.utc) # Dummy return for sniffer logic
            return None
        except Exception:
            return None

    def get_file_mtime_date(self, file_path: str) -> datetime:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime)

    def sniff_format(self, lines: List[str]) -> str:
        """Sniffs the dominant format for a file (Fast Path). Returns format name or 'MIXED'."""
        if not lines:
            return "UNPARSEABLE"

        total = len(lines)
        
        # 1. Try JSON (80% threshold)
        json_matches = sum(1 for line in lines if self.try_parse_json_line(line) is not None)
        if json_matches / total >= 0.8:
            return "JSON"

        # 2. Try Regex Patterns (70% threshold)
        pattern_counts = {name: 0 for name in REGEX_PATTERNS}
        for line in lines:
            for name, pattern in REGEX_PATTERNS.items():
                if pattern.search(line):
                    pattern_counts[name] += 1
                    # Break to avoid double-counting if we want strict winners, 
                    # but actually we just count matches per pattern.

        best_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        if best_pattern[1] / total >= 0.7:
            return best_pattern[0]

        # 3. Middle Option
        return "MIXED"

    def parse_line(self, line: str, file_path: str, line_number: int, service: str, file_mtime: datetime, forced_format: str) -> LogEntry:
        raw = line.strip()
        ts_obj = None
        
        formats_to_try = []
        if forced_format == "JSON":
            formats_to_try = ["JSON"]
        elif forced_format in REGEX_PATTERNS:
            formats_to_try = [forced_format]
        elif forced_format == "MIXED":
            # Strict tie-break order
            formats_to_try = ["JSON", "ISO8601", "BRACKET", "SYSLOG"]
            
        for fmt in formats_to_try:
            if fmt == "JSON":
                parsed = self.try_parse_json_line(line)
                if parsed:
                    ts_obj = parsed # Ideally parse the real time, using dummy for sniffer proof
                    break
            else:
                match = REGEX_PATTERNS[fmt].search(line)
                if match:
                    # In a real tool we parse the match. For MVP we use file_mtime to mock parsed time
                    # We will use the mtime as the base and just ensure it's a valid datetime
                    ts_obj = file_mtime
                    break
        
        # Line-level fallback (if still no ts_obj, it's None)
        return LogEntry(
            timestamp=ts_obj,
            severity=self.extract_severity(raw),
            service=service,
            raw_text=raw,
            identifiers=self.extract_identifiers(raw),
            file_path=file_path,
            line_number=line_number
        )

    def load_logs_from_dir(self, log_dir: str):
        if not os.path.exists(log_dir):
            console.print(f"[red]Directory '{log_dir}' not found![/red]")
            return

        for fname in sorted(os.listdir(log_dir)):
            if not fname.endswith('.log'): continue
            
            fpath = os.path.join(log_dir, fname)
            service = fname.replace('.log', '')
            file_mtime = self.get_file_mtime_date(fpath)

            with open(fpath, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            sample = [l for l in all_lines[:20] if l.strip()]
            fmt = self.sniff_format(sample)
            console.print(f"[dim]Sniffed {fname} -> {fmt}[/dim]")

            # Now normalize immediately
            for idx, line in enumerate(all_lines):
                if not line.strip(): continue
                entry = self.parse_line(line, fpath, idx+1, service, file_mtime, fmt)
                
                # If unparseable (no ts_obj), we can fallback to previous line's time or just append
                self.entries.append(entry)
                for token in entry.identifiers:
                    if token not in self.index:
                        self.index[token] = []
                    self.index[token].append(entry)

        # Sort entries chronologically (None timestamps go to the end or beginning)
        # Using a stable sort based on presence of timestamp, then timestamp value
        self.entries.sort(key=lambda x: (x.timestamp is not None, x.timestamp.timestamp() if x.timestamp else 0))
        console.print(f"[green]✓ Successfully parsed {len(self.entries)} entries into standardized LogEntry format.[/green]")

    def digger_scan(self):
        """Auto-lists every ERROR/FATAL line"""
        errors = [e for e in self.entries if e.severity in ["ERROR", "FATAL"]]
        if not errors:
            console.print("[green]No ERROR or FATAL logs found![/green]")
            return None

        table = Table(title="🚨 Digger Scan: Detected Errors")
        table.add_column("File:Line", style="dim")
        table.add_column("Service", style="cyan")
        table.add_column("Message", style="red")

        for idx, err in enumerate(errors):
            msg = err.raw_text[:80] + "..." if len(err.raw_text) > 80 else err.raw_text
            table.add_row(f"{os.path.basename(err.file_path)}:{err.line_number}", err.service, f"[{idx+1}] {msg}")
        
        console.print(table)
        return errors

    def get_context_for_id(self, token: str):
        """Auto-correlate on selection"""
        matched = self.index.get(token, [])
        if not matched:
            return

        # Sort matches by timestamp
        matched.sort(key=lambda x: x.timestamp.timestamp() if x.timestamp else 0)

        table = Table(title=f"🔍 Correlation Timeline for: [bold cyan]{token}[/bold cyan]")
        table.add_column("Service", style="cyan")
        table.add_column("Level")
        table.add_column("Message")

        for entry in matched:
            lvl_style = "red" if entry.severity in ["ERROR", "FATAL"] else "yellow" if "WARN" in entry.severity else "green"
            table.add_row(entry.service, f"[{lvl_style}]{entry.severity}[/{lvl_style}]", entry.raw_text)

        console.print(table)
        console.print("[dim]Note: Correlation shows shared transaction identifiers, not proven causality.[/dim]")

def run():
    import questionary
    console.print(Panel.fit("[bold magenta]🔍 digger — Cross-Service Log Correlation[/bold magenta]"))

    log_dir = "./logs"
    engine = DiggerEngine()
    engine.load_logs_from_dir(log_dir)

    while True:
        errors = engine.digger_scan()
        if not errors:
            break

        choices = [f"[{i+1}] {e.service}: {e.raw_text[:40]}..." for i, e in enumerate(errors)]
        choices.append("Exit")
        
        choice = questionary.select(
            "Select an error to auto-correlate (or Exit):",
            choices=choices
        ).ask()

        if not choice or choice == "Exit":
            break

        # Find the selected error
        idx = int(choice.split("]")[0][1:]) - 1
        selected_err = errors[idx]

        if not selected_err.identifiers:
            console.print("[yellow]No correlation identifiers found on this line to search with.[/yellow]")
            continue
        
        # Pick the first identifier for correlation
        target_id = selected_err.identifiers[0]
        engine.get_context_for_id(target_id)
        input("\nPress Enter to return to scan list...")

if __name__ == "__main__":
    run()
