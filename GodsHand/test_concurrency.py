import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from GodsHand.utils.state import Blackboard

# Instantiate the blackboard class
blackboard = Blackboard()

def mock_agent_write(task_id):
    # Replace .add_task with the exact method name inside your BlackBoard class
    blackboard.append_task(task_name=task_id, result="Simulated concurrent write.", status="Complete")

threads = []
for i in range(1, 21): # Simulates 20 simultaneous agents
    t = threading.Thread(target=mock_agent_write, args=(f"frontend-task-{i}",))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
    
print("Concurrency test complete. Check state.jsonl.")