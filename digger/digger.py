import re
import os
import json
from datetime import datetime, timezone, date
from dataclasses import dataclass
from typing import List, Dict, Optional
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

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

SEVERITY_PATTERN = re.compile(r'\b(INFO|WARN|WARNING|ERROR|FATAL|DEBUG|TRACE)\b', re.IGNORECASE)
ID_PATTERN = re.compile(r'\b(?:ord_[a-zA-Z0-9]+|req-[a-zA-Z0-9]+|usr_[a-zA-Z0-9]+|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[a-zA-Z_]+=[a-zA-Z0-9_-]+)\b')


def _parse_regex_timestamp(fmt: str, matched_text: str, file_mtime: datetime) -> Optional[datetime]:
    """Turn a matched timestamp SUBSTRING into a real datetime object.
    This is the piece that was previously faked with file_mtime for every line."""
    try:
        if fmt == "ISO8601":
            text = matched_text.replace("Z", "+00:00")
            if "T" not in text and " " in text:
                text = text.replace(" ", "T", 1)
            dt = datetime.fromisoformat(text)
            # Strip timezone so every LogEntry in the system is consistently
            # naive. Without this, ISO8601/JSON timestamps (aware) and
            # BRACKET/SYSLOG timestamps (always naive) can't be safely
            # compared: subtracting them crashes, and sorting them silently
            # mis-orders entries depending on the host machine's local
            # timezone (naive .timestamp() assumes local time; aware
            # .timestamp() doesn't) — a bug that wouldn't throw an error,
            # just quietly produce the wrong cross-service order.
            return dt.replace(tzinfo=None)

        if fmt == "BRACKET":
            inner = matched_text.strip("[]")
            fmt_str = "%H:%M:%S.%f" if "." in inner else "%H:%M:%S"
            t = datetime.strptime(inner, fmt_str).time()
            # No date in a time-only bracket log — borrow the date from the
            # file's mtime. Known limitation: wrong if the file spans midnight.
            return datetime.combine(file_mtime.date(), t)

        if fmt == "SYSLOG":
            # e.g. "Sep 12 10:02:14" — syslog gives month+day but no year,
            # so the year is borrowed from file_mtime. Known limitation:
            # wrong if the file spans a year boundary (e.g. Dec 31 -> Jan 1).
            parts = matched_text.split()
            month = MONTH_MAP.get(parts[0])
            day = int(parts[1])
            t = datetime.strptime(parts[2], "%H:%M:%S").time()
            if month is None:
                return None
            return datetime.combine(date(file_mtime.year, month, day), t)
    except (ValueError, IndexError):
        return None
    return None


class DiggerEngine:
    def __init__(self):
        self.entries: List[LogEntry] = []
        self.index: Dict[str, List[LogEntry]] = {}

    def extract_identifiers(self, raw_text: str) -> List[str]:
        # dict.fromkeys instead of set(): dedupes while preserving the
        # order identifiers first appear in the line. A plain set() here
        # made "which identifier is 'first'" non-deterministic across runs
        # (Python string hash randomization), which matters because
        # get_context_for_id() uses identifiers[0] to drive correlation.
        return list(dict.fromkeys(ID_PATTERN.findall(raw_text)))

    def extract_severity(self, raw_text: str) -> str:
        match = SEVERITY_PATTERN.search(raw_text)
        return match.group(1).upper() if match else "INFO"

    def try_parse_json_line(self, line: str) -> Optional[datetime]:
        try:
            data = json.loads(line)
        except Exception:
            return None
        for key in ["ts", "timestamp", "time", "date"]:
            if key in data:
                val = str(data[key])
                try:
                    text = val.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(text)
                    return dt.replace(tzinfo=None)  # keep naive, see note in _parse_regex_timestamp
                except ValueError:
                    continue
        return None

    def get_file_mtime_date(self, file_path: str) -> datetime:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime)

    def sniff_format(self, lines: List[str]) -> str:
        """Sniffs the dominant format for a file (Fast Path). Returns format name or 'MIXED'."""
        if not lines:
            return "UNPARSEABLE"

        total = len(lines)

        json_matches = sum(1 for line in lines if self.try_parse_json_line(line) is not None)
        if json_matches / total >= 0.8:
            return "JSON"

        pattern_counts = {name: 0 for name in REGEX_PATTERNS}
        for line in lines:
            for name, pattern in REGEX_PATTERNS.items():
                if pattern.search(line):
                    pattern_counts[name] += 1

        best_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        if best_pattern[1] / total >= 0.7:
            return best_pattern[0]

        return "MIXED"

    def parse_line(self, line: str, file_path: str, line_number: int, service: str,
                    file_mtime: datetime, forced_format: str) -> LogEntry:
        raw = line.strip()
        ts_obj = None

        if forced_format == "JSON":
            formats_to_try = ["JSON"]
        elif forced_format in REGEX_PATTERNS:
            formats_to_try = [forced_format]
        elif forced_format == "MIXED":
            formats_to_try = ["JSON", "ISO8601", "BRACKET", "SYSLOG"]
        else:
            formats_to_try = []

        for fmt in formats_to_try:
            if fmt == "JSON":
                ts_obj = self.try_parse_json_line(line)
                if ts_obj is not None:
                    break
            else:
                match = REGEX_PATTERNS[fmt].search(line)
                if match:
                    ts_obj = _parse_regex_timestamp(fmt, match.group(0), file_mtime)
                    if ts_obj is not None:
                        break
                    # matched the shape but failed to actually parse (rare) —
                    # keep trying other formats when in MIXED mode

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
            if not fname.endswith('.log'):
                continue

            fpath = os.path.join(log_dir, fname)
            service = fname.replace('.log', '')
            file_mtime = self.get_file_mtime_date(fpath)

            with open(fpath, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()

            sample = [l for l in all_lines[:20] if l.strip()]
            fmt = self.sniff_format(sample)
            console.print(f"[dim]Sniffed {fname} -> {fmt}[/dim]")

            file_entry_count = 0
            file_unparsed_count = 0
            for idx, line in enumerate(all_lines):
                if not line.strip():
                    continue
                entry = self.parse_line(line, fpath, idx + 1, service, file_mtime, fmt)
                self.entries.append(entry)
                file_entry_count += 1
                if entry.timestamp is None:
                    file_unparsed_count += 1
                for token in entry.identifiers:
                    self.index.setdefault(token, []).append(entry)

            if file_entry_count > 0 and file_unparsed_count == file_entry_count:
                console.print(
                    f"[yellow]Warning: no lines in {fname} could be timestamp-parsed — "
                    f"its entries will not be reliably ordered against other services.[/yellow]"
                )
            elif file_unparsed_count > 0:
                console.print(
                    f"[yellow]Note: {file_unparsed_count}/{file_entry_count} lines in {fname} "
                    f"had no parseable timestamp.[/yellow]"
                )

        # Real timestamps now exist per-line, so this sort actually reflects
        # true chronological order across services, not just file order.
        self.entries.sort(key=lambda x: (x.timestamp is not None, x.timestamp.timestamp() if x.timestamp else 0))
        console.print(f"[green]Successfully parsed {len(self.entries)} entries into standardized LogEntry format.[/green]")

    def digger_scan(self):
        """Auto-lists every ERROR/FATAL line"""
        errors = [e for e in self.entries if e.severity in ["ERROR", "FATAL"]]
        if not errors:
            console.print("[green]No ERROR or FATAL logs found![/green]")
            return None

        table = Table(title="Digger Scan: Detected Errors")
        table.add_column("File:Line", style="dim")
        table.add_column("Service", style="cyan")
        table.add_column("Message", style="red")

        for idx, err in enumerate(errors):
            msg = err.raw_text[:80] + "..." if len(err.raw_text) > 80 else err.raw_text
            table.add_row(f"{os.path.basename(err.file_path)}:{err.line_number}", err.service, f"[{idx+1}] {msg}")

        console.print(table)
        return errors

    def get_context_for_ids(self, tokens: List[str], anchor: Optional[LogEntry] = None):
        """Auto-correlate on EVERY identifier found on the selected line,
        not just one — a line can carry an order ID, a request ID, etc.
        simultaneously, and each is independently useful evidence."""
        matched_by_id: Dict[int, LogEntry] = {}
        shared_tokens_by_id: Dict[int, List[str]] = {}

        for token in tokens:
            for entry in self.index.get(token, []):
                if anchor is not None and entry is anchor:
                    continue  # don't list the error against itself
                key = id(entry)
                matched_by_id[key] = entry
                shared_tokens_by_id.setdefault(key, []).append(token)

        matched = list(matched_by_id.values())
        if not matched:
            return

        matched.sort(key=lambda x: x.timestamp.timestamp() if x.timestamp else 0)

        table = Table(title=f"Correlation Timeline for: [bold cyan]{', '.join(tokens)}[/bold cyan]")
        table.add_column("Time", style="dim")
        table.add_column("Service", style="cyan")
        table.add_column("Level")
        table.add_column("Shared ID(s)", style="green")
        table.add_column("Message")

        for entry in matched:
            lvl_style = "red" if entry.severity in ["ERROR", "FATAL"] else "yellow" if "WARN" in entry.severity else "green"
            # Timestamps are normalized to naive at parse time (see
            # _parse_regex_timestamp / try_parse_json_line), so this
            # subtraction is always safe now — no per-call tz stripping needed.
            if entry.timestamp and anchor and anchor.timestamp:
                gap = (anchor.timestamp - entry.timestamp).total_seconds()
                time_display = f"{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]} ({gap:+.2f}s)"
            elif entry.timestamp:
                time_display = entry.timestamp.strftime('%H:%M:%S.%f')[:-3]
            else:
                time_display = "unknown"
            shared = ", ".join(shared_tokens_by_id.get(id(entry), []))
            table.add_row(time_display, entry.service, f"[{lvl_style}]{entry.severity}[/{lvl_style}]", shared, entry.raw_text)

        console.print(table)
        console.print("[dim]Note: Correlation shows shared transaction identifiers, not proven causality.[/dim]")


def run():
    console.print(Panel.fit("[bold magenta]digger — Cross-Service Log Correlation[/bold magenta]"))

    while True:
        try:
            log_dir = input("\nEnter path to logs directory [./logs]: ").strip()
        except (KeyboardInterrupt, EOFError):
            return
            
        if not log_dir:
            log_dir = "./logs"
            
        if not os.path.exists(log_dir) or not os.path.isdir(log_dir):
            console.print(f"[red]Directory '{log_dir}' not found. Please try again.[/red]")
            continue
            
        break

    engine = DiggerEngine()
    engine.load_logs_from_dir(log_dir)



    console.print("[dim]Type 'help' for commands, or 'exit' to quit.[/dim]")
    while True:
        try:
            cmd = input("\ndigger> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
            
        if not cmd:
            continue
            
        parts = cmd.split()
        base_cmd = parts[0].lower()
        
        if base_cmd in ["exit", "quit"]:
            break
        elif base_cmd in ["errors", "error"]:
            engine.digger_scan()
        elif base_cmd in ["trace", "uuid"]:
            if len(parts) < 2:
                console.print("[red]Usage: trace <UID>[/red]")
            else:
                uid = parts[1]
                engine.get_context_for_ids([uid])
        elif base_cmd == "merge":
            if len(parts) < 2:
                console.print("[red]Usage: merge all OR merge <service1> <service2>...[/red]")
                continue
            
            target_services = parts[1:]
            merge_all = "all" in [s.lower() for s in target_services]
            
            entries_to_merge = []
            if merge_all:
                entries_to_merge = engine.entries
            else:
                entries_to_merge = [e for e in engine.entries if e.service in target_services]
                if not entries_to_merge:
                    console.print(f"[red]No entries found for services: {', '.join(target_services)}[/red]")
                    continue
            
            with open("combined.log", "w", encoding="utf-8") as f:
                for entry in entries_to_merge:
                    time_str = entry.timestamp.strftime('%H:%M:%S.%f')[:-3] if entry.timestamp else "unknown"
                    f.write(f"[{time_str}] [{entry.severity}] {entry.service}: {entry.raw_text}\n")
            
            svc_list = "all services" if merge_all else ", ".join(target_services)
            console.print(f"[green]Saved chronological combined log for {svc_list} to combined.log[/green]")
            
        elif base_cmd == "help":
            table = Table(title="Digger Commands", show_header=True, header_style="bold magenta")
            table.add_column("Command")
            table.add_column("Description")
            table.add_row("help", "Show this help message")
            table.add_row("errors", "Scan all logs and extract ERROR/FATAL events")
            table.add_row("trace <UUID>", "Correlate and build a timeline across all microservices for a specific UUID (alias: uuid)")
            table.add_row("merge all", "Combine all logs chronologically into combined.log")
            table.add_row("merge <s1> <s2>", "Combine specific service logs (e.g., 'merge web payment')")
            table.add_row("exit, quit", "Exit the Digger shell")
            console.print(table)
        else:
            console.print(f"[red]Unknown command: {base_cmd}[/red] Type 'help' to see available commands.")

if __name__ == "__main__":
    run()
