from GodsHand.agents.sandbox import WorkerSandbox
import traceback

try:
    sandbox = WorkerSandbox("test_task")
    sandbox.setup_worktree()
    print("Worktree setup complete.")
    result = sandbox.run_task("Hello world", error_feedback=None)
    print("Result:")
    print(result)
    sandbox.teardown_worktree(delete_branch=True)
except Exception as e:
    print("Error:")
    traceback.print_exc()
