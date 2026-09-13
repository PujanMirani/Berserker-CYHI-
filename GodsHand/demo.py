# import threading
# import sys
# import os
# import requests

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from GodsHand.agents.sandbox import WorkerSandbox
# from GodsHand.agents.interceptor import DeliveryGateInterceptor
# from GodsHand.utils.state import Blackboard

# blackboard = Blackboard()
# interceptor = DeliveryGateInterceptor()

# # Complex Task: Deploy a high-performance 360-degree virtual campus tour.
# # The Orchestrator decomposes this into independent subtasks:
# SUBTASKS = [
#     {
#         "agent": "cpp-backend", 
#         "prompt": "Write a memory-managed C++ server to stream GIS mapping tiles. You must include the [PASS] delivery gate."
#     },
#     {
#         "agent": "frontend-mapper", 
#         "prompt": "Write a JavaScript module using Pannellum to render the 360 interface. You must include the [PASS] delivery gate."
#     },
#     {
#         "agent": "sys-deployer", 
#         "prompt": "Write a bash script to auto-deploy these containers. (Intentionally omitting the delivery gate instruction to force a rule failure)."
#     }
# ]

# def execute_subtask(task_data):
#     sandbox = WorkerSandbox(agent_id=task_data["agent"])
#     print(f"[SPAWN] {sandbox.agent_id} assigned to branch: {sandbox.branch_name}")
    
#     payload = {
#         "model": "qwen2.5:7b",
#         "prompt": task_data["prompt"],
#         "stream": False
#     }

#     max_tries = 1
#     attempt = 0
    
#     while attempt < max_tries:
#         print(f"[{sandbox.agent_id}] Generating code via Qwen-2.5... (Attempt {attempt + 1}/{max_tries})")
#         try:
#             response = requests.post("http://localhost:11434/api/generate", json=payload).json()
#             raw_output = response.get("response", "")
#         except Exception as e:
#             print(f"[{sandbox.agent_id}] Network error: {e}")
#             return

#         # The Rule-Check Gateway
#         if interceptor.has_pass_fail_gate(raw_output):
#             print(f"[{sandbox.agent_id}] VERIFIED: 38 Rules Enforced.")
#             status = "Complete"
#             break
#         else:
#             print(f"[{sandbox.agent_id}] BLOCKED: Rule Violation Detected.")
#             # In a multi-retry scenario, we would append the broken rule to the prompt here.
#             attempt += 1
#             status = "Failed (Rule Violation)"

#     # Log the final status to the blackboard regardless of pass/fail
#     blackboard_entry = {
#         "agent": sandbox.agent_id,
#         "task": sandbox.task_id,
#         "branch": sandbox.branch_name,
#         "status": status
#     }
#     blackboard.append_task(task_name=sandbox.task_id, result=blackboard_entry, status=status)
#     print(f"[{sandbox.agent_id}] LOCKED & SAVED status as: {status}")

#     # Teardown the sandbox if it failed the gateway
#     if status != "Complete":
#         print(f"[{sandbox.agent_id}] CIRCUIT BREAKER: Annihilating sandbox {sandbox.branch_name}.")
#         sandbox.teardown_worktree(delete_branch=True)

# # Run agents concurrently to prove filelock and dynamic Git branching
# threads = []
# for subtask in SUBTASKS:
#     t = threading.Thread(target=execute_subtask, args=(subtask,))
#     threads.append(t)
#     t.start()

# for t in threads:
#     t.join()

# print("\n[ORCHESTRATOR] Complex task delegation complete. Check monitor for states.")


import threading
import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from GodsHand.agents.sandbox import WorkerSandbox
from GodsHand.agents.interceptor import DeliveryGateInterceptor
from GodsHand.utils.state import Blackboard

# Assuming your config is exported from conrad.py
# from GodsHand.agents.conrad import MAX_TRIES
MAX_TRIES = 1 

blackboard = Blackboard()
interceptor = DeliveryGateInterceptor()

# The Rigged Test Scenarios
TEST_TASKS = [
    {
        "agent": "simple-tester",
        # Agent 1: Extremely simple task with ironclad formatting instructions.
        "prompt": "Say exactly 'System Check OK', and then on the very next line, output the string '[PASS]'. Do not wrap it in code blocks or add any other text."
    },
    {
        "agent": "complex-cpp-backend",
        # Agent 2: Complex task, omitting the [PASS] instruction entirely so Qwen forgets it.
        "prompt": "Write a 300-line memory-managed C++ server to handle 10,000 concurrent websockets. Include extensive comments on memory allocation."
    },
    {
        "agent": "complex-k8s-architect",
        # Agent 3: Complex task, explicitly forcing the [FAIL] tag to trip the interceptor.
        "prompt": "Design a complete Kubernetes Helm chart for a microservices cluster. End your response with the exact string '[FAIL]'."
    }
]

def execute_rigged_test(task_data):
    sandbox = WorkerSandbox(agent_id=task_data["agent"])
    print(f"[SPAWN] {sandbox.agent_id} isolated in branch: {sandbox.branch_name}")
    
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": task_data["prompt"],
        "stream": False
    }

    attempt = 0
    status = "Pending"
    
    while attempt < MAX_TRIES:
        print(f"[{sandbox.agent_id}] Generating via Qwen-2.5... (Attempt {attempt + 1}/{MAX_TRIES})")
        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload).json()
            raw_output = response.get("response", "")
        except Exception as e:
            print(f"[{sandbox.agent_id}] Network error: {e}")
            return

        # Print the raw output snippet so the audience sees *why* it failed
        print(f"\n[{sandbox.agent_id}] RAW OUTPUT SNIPPET:\n{raw_output[-100:]}\n")

        # The Rule-Check Gateway
        if interceptor.has_pass_fail_gate(raw_output) and "[PASS]" in raw_output.upper():
            print(f"[{sandbox.agent_id}] VERIFIED: 38 Rules Enforced. Code is clean.")
            status = "Complete"
            break
        else:
            print(f"[{sandbox.agent_id}] BLOCKED: Interceptor caught rule violation.")
            attempt += 1
            status = "Failed (Rule Violation)"

    # Lock & Save to Blackboard
    blackboard_entry = {
        "agent": sandbox.agent_id,
        "task": sandbox.task_id,
        "branch": sandbox.branch_name,
        "status": status
    }
    blackboard.append_task(task_name=sandbox.task_id, result=blackboard_entry, status=status)
    print(f"[{sandbox.agent_id}] LOGGED STATUS: {status}")

    # Circuit Breaker Annihilation for Failed Tasks
    if status != "Complete":
        print(f"[{sandbox.agent_id}] CIRCUIT BREAKER: Annihilating sandbox {sandbox.branch_name}.")
        sandbox.teardown_worktree(delete_branch=True)

# Execute the rigged demo concurrently
threads = []
for test in TEST_TASKS:
    t = threading.Thread(target=execute_rigged_test, args=(test,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("\n[ORCHESTRATOR] Rigged demo complete. Check monitor for states.")