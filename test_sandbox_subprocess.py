from GodsHand.agents.sandbox import WorkerSandbox
import traceback
import sys

try:
    sandbox = WorkerSandbox("test_task")
    sandbox.setup_worktree()
    print("Worktree setup complete.")
    result = sandbox.run_task("Hello world", error_feedback=None)
    print("Result:", result)
    sandbox.teardown_worktree(delete_branch=True)
except Exception as e:
    print("Error:", e)
    traceback.print_exc()
