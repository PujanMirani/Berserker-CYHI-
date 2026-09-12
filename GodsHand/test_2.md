**Test 4: Blackboard Concurrency Stress Test**
This test simulates multiple agents finishing their tasks at the exact same millisecond to ensure OS-level file locking (`filelock`) prevents JSON schema corruption in the global blackboard.

*   **Setup:** Create `test_concurrency.py` in your project root.
*   **The Code:**
    ```python
    import threading
    import sys
    import os

    # Append project root to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Adjust capitalization of Blackboard and the write method based on your exact state.py implementation
    from GodsHand.utils.state import Blackboard 
    
    blackboard = Blackboard()

    def mock_agent_write(task_id):
        payload = {"task": task_id, "status": "Complete", "details": "Simulated concurrent write."}
        blackboard.add_task(payload) # Replace .add_task with your exact method name

    threads = []
    for i in range(1, 21): 
        t = threading.Thread(target=mock_agent_write, args=(f"frontend-task-{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        
    print("Concurrency test complete. Check state.jsonl.")
    ```
*   **Verification:** Run the script (`python test_concurrency.py`). Open `state.jsonl`. You must see exactly 20 perfectly formatted JSON lines. Overlapping brackets or corrupted strings indicate a failed `filelock` implementation.

---

**Test 5: The End-to-End Worker Task**
This validates the full daemonless pipeline, interceptor, and isolated sandbox using a complex, domain-specific generation task.

*   **Action:** Modify your worker script to pass this exact prompt to your local Qwen-2.5 instance. 
*   **The Prompt:** *"Write a memory-optimized C++ program to perform a highly efficient graph traversal for a competitive programming scenario. You must include the mandatory [PASS] or [FAIL] delivery gate block at the end of your output."*
*   **Execution:** Run the task through the `WorkerSandbox`. 
*   **Verification:** 
    1. The container should spawn and capture the C++ output silently.
    2. Conrad must detect the `[PASS]` gate in memory.
    3. Run `git branch` to ensure the temporary `task-<id>` branch is spawned and safely holding the generated `.cpp` file.
    4. Run the GodsHand CLI batch merger to review the C++ code and execute the one-click merge into your active repository.