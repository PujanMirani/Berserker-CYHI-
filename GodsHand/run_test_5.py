import sys
import os
import subprocess
from pathlib import Path

# Append project root
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Berserker-CYHI-"))

from GodsHand.agents.sandbox import WorkerSandbox
from GodsHand.agents.interceptor import DeliveryGateInterceptor
from GodsHand.utils.state import Blackboard
from GodsHand.agents.merger import BatchMerger

def run_test_5():
    print("\n" + "="*50)
    print("Test 5: The End-to-End Worker Task")
    print("="*50)

    prompt = "Write a memory-optimized C++ program to perform a highly efficient graph traversal for a competitive programming scenario. You must include the mandatory [PASS] or [FAIL] delivery gate block at the end of your output."
    
    sandbox = WorkerSandbox(task_name="test-005")
    interceptor = DeliveryGateInterceptor(max_retries=1) # The LLM prompt asks for it, so it should work on 1st try
    blackboard = Blackboard("state_test5.jsonl")

    # Clear state file if exists
    if blackboard.state_file.exists():
        blackboard.state_file.unlink()

    print(f"Step 1: Spawning sandbox and executing prompt...")
    sandbox.setup_worktree()
    
    try:
        is_success, output = interceptor.execute_with_gate(sandbox, prompt)
        
        # Step 2: Verification of PASS gate
        if is_success:
            print("✅ PASS: Conrad successfully detected the [PASS] gate in memory.")
            blackboard.append_task(sandbox.task_name, f"branch: task-{sandbox.task_id}", status="Complete")
            sandbox.teardown_worktree(delete_branch=False)
        else:
            print("❌ FAIL: Conrad did NOT detect the [PASS] gate.")
            print("LLM Output was:")
            try:
                print(output.markup) # Since it's a rich Markdown object, markup contains the raw text
            except:
                print(output)
            sandbox.teardown_worktree(delete_branch=True)
            return
            
        # Step 3: Verification of git branch and file
        branch_name = f"task-{sandbox.task_id}"
        cmd = ["git", "branch", "--list", branch_name]
        res = subprocess.run(cmd, cwd=sandbox.repo_root, capture_output=True, text=True)
        if branch_name in res.stdout:
            print(f"✅ PASS: Git branch '{branch_name}' was successfully spawned.")
        else:
            print(f"❌ FAIL: Git branch '{branch_name}' was NOT found.")
            
        # Optional: check if .cpp file is in the branch (checking out the branch to verify)
        subprocess.run(["git", "checkout", branch_name], cwd=sandbox.repo_root, capture_output=True)
        if (Path(sandbox.repo_root) / "graph.cpp").exists():
            print("✅ PASS: graph.cpp file successfully created in the isolated branch.")
        else:
            print("❌ FAIL: graph.cpp file NOT found in the isolated branch.")
        subprocess.run(["git", "checkout", "-"], cwd=sandbox.repo_root, capture_output=True) # Checkout back to main
            
        # Step 4: Batch Merge
        print("Step 4: Executing GodsHand CLI batch merger...")
        merger = BatchMerger(state_file="state_test5.jsonl")
        merge_success, merge_msg = merger.merge_all()
        if merge_success:
            print(f"✅ PASS: Batch Merger completed successfully! ({merge_msg})")
            if (Path(sandbox.repo_root) / "graph.cpp").exists():
                print("✅ PASS: graph.cpp successfully merged into the active repository!")
            else:
                print("❌ FAIL: graph.cpp missing from active repository after merge.")
        else:
            print(f"❌ FAIL: Batch Merger failed: {merge_msg}")
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred during Test 5: {e}")
        sandbox.teardown_worktree(delete_branch=True)

if __name__ == "__main__":
    run_test_5()
