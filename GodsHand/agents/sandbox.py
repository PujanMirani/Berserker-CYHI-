import subprocess
import os
import shutil
import uuid
from pathlib import Path

class WorkerSandbox:
    def __init__(self, agent_id, task_id=None, base_image="docker.io/library/python:3.11-slim"):
        self.agent_id = agent_id
        self.task_id = task_id if task_id else f"task-{str(uuid.uuid4())[:8]}"
        self.branch_name = f"{self.agent_id}/{self.task_id}"
        self.base_image = base_image
        self.worktree_dir = Path(f"/tmp/godshand_worktrees/{self.task_id}")
        
        
        # Determine repo root (where this file's parent's parent is)
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    def setup_worktree(self):
        """
        Creates a temporary branch and an isolated detached worktree for the task.
        """
        self.worktree_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # git worktree add -b <branch_name> <path>
        cmd = ["git", "worktree", "add", "-b", self.branch_name, str(self.worktree_dir)]
        subprocess.run(cmd, cwd=self.repo_root, check=True, capture_output=True)
        print(f"Created isolated worktree at {self.worktree_dir} on branch {self.branch_name}")

    def teardown_worktree(self, delete_branch=False):
        """
        Removes the worktree. Optionally deletes the branch.
        """
        # git worktree remove <path>
        if self.worktree_dir.exists():
            cmd = ["git", "worktree", "remove", "-f", str(self.worktree_dir)]
            subprocess.run(cmd, cwd=self.repo_root, check=False, capture_output=True)
            
        if delete_branch:
            # git branch -D <branch_name>
            cmd = ["git", "branch", "-D", self.branch_name]
            subprocess.run(cmd, cwd=self.repo_root, check=False, capture_output=True)
            
    def run_task(self, prompt, error_feedback=None):
        """
        Spawns a --rm daemonless container, mounts the worktree, and runs a mock worker script.
        Pipes error feedback via stdin if provided.
        """
        # In a real scenario, this script would invoke the actual LLM agent inside the container.
        # We will create a dummy script inside the worktree to simulate the worker agent.
        worker_script_path = self.worktree_dir / "worker_script.py"
        worker_script = f'''import sys
import json
import urllib.request

prompt = """{prompt}"""
payload = json.dumps({{
    "model": "qwen2.5-coder:7b",
    "prompt": prompt,
    "stream": False
}}).encode("utf-8")

req = urllib.request.Request("http://localhost:11434/api/generate", data=payload, headers={{"Content-Type": "application/json"}})
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        output = res["response"]
        
        # Write the cpp code to a file in the workspace
        with open("/workspace/graph.cpp", "w") as f:
            f.write(output)
            
        # Print the output so the interceptor captures it in memory
        print(output)
except Exception as e:
    print(f"Error calling local LLM: {{e}}")
'''
        with open(worker_script_path, "w") as f:
            f.write(worker_script)

        # Subprocess fallback for robust stdin piping to ephemeral containers
        podman_cmd = [
            "podman", "run", "--rm", "-i", "--network", "host", "--userns=keep-id",
            "-v", f"{str(self.worktree_dir)}:/workspace:Z",
            self.base_image,
            "python", "/workspace/worker_script.py"
        ]
        
        result = subprocess.run(
            podman_cmd,
            input=error_feedback.encode('utf-8') if error_feedback else b"",
            capture_output=True,
        )
        
        stdout_text = result.stdout.decode('utf-8')
        if not stdout_text:
            return result.stderr.decode('utf-8')
            
        # Mock worker behavior: commit the generated files to the worktree branch
        subprocess.run(["git", "add", "graph.cpp"], cwd=self.worktree_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "worker task complete"], cwd=self.worktree_dir, capture_output=True)
        
        return stdout_text
