import subprocess
import os
from GodsHand.utils.state import Blackboard

class BatchMerger:
    def __init__(self, state_file="state.jsonl"):
        self.blackboard = Blackboard(state_file)
        # Determine repo root
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def get_completed_branches(self):
        tasks = self.blackboard.get_all_tasks()
        branches = []
        for t in tasks:
            if t.get("status") == "Complete":
                result = t.get("result")
                if isinstance(result, dict) and "branch" in result:
                    branches.append(result["branch"])
                elif isinstance(result, str) and result.startswith("branch: "):
                    branches.append(result.split("branch: ")[1])
        return branches

    def merge_all(self):
        branches = self.get_completed_branches()
        if not branches:
            return False, "No completed tasks to merge."
        
        merged = []
        for branch in branches:
            cmd = ["git", "merge", "--no-ff", branch, "-m", f"Auto-merge completed task branch {branch}"]
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True)
            if res.returncode == 0:
                merged.append(branch)
                # Cleanup branch after merge
                subprocess.run(["git", "branch", "-D", branch], cwd=self.repo_root, capture_output=True)
            else:
                return False, f"Failed to merge {branch}: {res.stderr.decode()}"
                
        return True, f"Successfully merged branches: {', '.join(merged)}"
