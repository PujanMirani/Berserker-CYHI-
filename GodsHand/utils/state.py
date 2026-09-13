import json
import os
from filelock import FileLock
from pathlib import Path

class Blackboard:
    def __init__(self, state_file="state.jsonl"):
        # Resolve the repository root to prevent duplicating state.jsonl across directories
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.state_file = Path(repo_root) / state_file
        self.lock_file = Path(f"{self.state_file}.lock")
        
        # Ensure the file exists
        if not self.state_file.exists():
            self.state_file.touch()

    def append_task(self, task_name, result, status="Complete"):
        """
        Thread-safe method to append a completed task to the blackboard.
        """
        data = {
            "task_name": task_name,
            "status": status,
            "result": result
        }
        
        lock = FileLock(str(self.lock_file), timeout=10)
        
        with lock:
            with open(self.state_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
                
    def get_all_tasks(self):
        """
        Thread-safe method to read all tasks.
        """
        if not self.state_file.exists():
            return []
            
        lock = FileLock(str(self.lock_file), timeout=10)
        tasks = []
        
        with lock:
            with open(self.state_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        tasks.append(json.loads(line))
        return tasks
