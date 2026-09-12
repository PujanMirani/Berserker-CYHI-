import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from GodsHand.agents.compiler import SystemPromptCompiler
from GodsHand.agents.interceptor import DeliveryGateInterceptor

from GodsHand.utils.state import Blackboard
from GodsHand.agents.sandbox import WorkerSandbox

def run_conrad_repl():
    """
    Main REPL session for the Conrad Agent.
    """
    print("Initializing GodsHand Conrad Agent...")
    
    compiler = SystemPromptCompiler()
    system_prompt = compiler.compile_prompt()
    
    interceptor = DeliveryGateInterceptor(max_retries=3)
    blackboard = Blackboard()
    
    session = PromptSession()
    
    print("\n--- System Prompt Context ---")
    print(system_prompt[:500] + "...\n(Truncated for display)")
    print("-----------------------------\n")
    print("Conrad Agent is ready. Type your request (or 'exit' to quit).")
    
    while True:
        try:
            user_input = session.prompt("conrad> ")
            
            if user_input.strip().lower() in ['exit', 'quit']:
                break
                
            if not user_input.strip():
                continue
                
            # Combine system prompt and user input
            full_prompt = f"{system_prompt}\n\nUser Request: {user_input}"
            
            # Execute with interception via Sandbox
            # task_name can just be the first few words of the prompt
            task_name = user_input.strip()[:20].replace(" ", "_")
            sandbox = WorkerSandbox(task_name=task_name)
            
            print(f"Setting up sandbox for task: {task_name}...")
            sandbox.setup_worktree()
            
            try:
                is_success, final_markdown = interceptor.execute_with_gate(sandbox, full_prompt)
                
                # Render the final output
                print("\n--- Output ---")
                interceptor.render(final_markdown)
                print("--------------\n")
                
                if is_success:
                    print("Task verified successfully. Appending to blackboard.")
                    blackboard.append_task(task_name=task_name, result=f"branch: task-{sandbox.task_id}")
                    # Teardown but keep branch for later review/merge
                    sandbox.teardown_worktree(delete_branch=False)
                else:
                    print("Task failed verification. Cleaning up temporary branch.")
                    # Cleanup the failed branch
                    sandbox.teardown_worktree(delete_branch=True)
            except Exception as e:
                print(f"Error executing task: {e}")
                sandbox.teardown_worktree(delete_branch=True)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    run_conrad_repl()
