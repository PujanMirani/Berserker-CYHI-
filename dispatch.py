import sys
import os

# Append project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GodsHand.agents.sandbox import WorkerSandbox
from GodsHand.utils.state import Blackboard

def main():
    agent_id = "cpp-optimizer"
    print(f"Initializing {agent_id} sandbox...")
    
    sandbox = WorkerSandbox(agent_id=agent_id)
    blackboard = Blackboard()
    
    sandbox.setup_worktree()
    
    prompt = "Write a minimal memory-optimized C++ program. Include the mandatory [PASS] or [FAIL] delivery gate block at the end of your output."
    
    try:
        print(f"Executing mock C++ generation task in Podman container...")
        output = sandbox.run_task(prompt)
        
        print("Worker Output Received:")
        print(output)
        
        # Append payload to blackboard
        payload = {
            "agent": sandbox.agent_id,
            "task": sandbox.task_id,
            "branch": sandbox.branch_name
        }
        
        blackboard.append_task(task_name=sandbox.task_id, result=payload, status="Complete")
        print("✅ Task recorded successfully in state.jsonl")
        
    except Exception as e:
        print(f"❌ Error during mock generation: {e}")
    finally:
        # Tear down worktree but keep the branch alive for any future merging
        sandbox.teardown_worktree(delete_branch=False)

if __name__ == "__main__":
    main()
