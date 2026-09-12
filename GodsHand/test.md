# 🧪 Testing Protocol: Conrad Gateway & Approval Workflow

## Test 1: Delivery Gate Bypass & Retry Logic
1.  **Setup:** Force the local LLM to output a valid code fix but explicitly instruct it to omit the 4-block PASS/FAIL report[cite: 3].
2.  **Verification:** The `DeliveryGateInterceptor` must silently block the stdout stream and trigger a retry[cite: 3]. Ensure the system halts exactly after 3 attempts and falls back to rendering the warning header in the terminal[cite: 3].

## Test 2: The "Complete" Tag Assignment
1.  **Setup:** Allow a worker agent to successfully generate an anti-slop compliant fix that passes Conrad's verification.
2.  **Action:** Inspect the project's active Git worktree and the `state.jsonl` file.
3.  **Verification:** The active Git worktree **must remain untouched**. The `state.jsonl` file must contain a new entry for the task with the tag `"Complete"`.

## Test 3: One-Click Batch Application
1.  **Setup:** Ensure `state.jsonl` contains multiple tasks tagged as `"Complete"`.
2.  **Action:** Trigger the final developer report UI and submit the confirmation to apply changes.
3.  **Verification:** The CLI must successfully read the completed outputs from the blackboard and merge them into the active Git worktree simultaneously.