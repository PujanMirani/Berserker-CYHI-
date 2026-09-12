# 🚀 Implementation Plan: Conrad Gateway & User Approval Integration

## Phase 1: Static Parsing & Blackboard Setup
1.  **Rule Ingestion:** Utilize the existing `utils/parser.py` to extract 'R-XX' rule blocks from `ANTISLOP.md` using regex[cite: 3].
2.  **State Initialization:** Implement `state.jsonl` using the `filelock` library to safely manage concurrent writes from isolated sandboxes. 

## Phase 2: Containerization & Worker Orchestration
1.  **Podman SDK:** Integrate the `podman` Python library to dynamically spawn `--rm` containers for atomic tasks.
2.  **Isolated Execution:** Mount specific sub-directories or temporary copies into the containers so workers never directly touch the active Git worktree.

## Phase 3: The Interception Loop
1.  **Gate Verification:** Route the Podman container's `stdout` directly into the `DeliveryGateInterceptor` middleware[cite: 3]. Scan for the non-negotiable `[PASS]` or `[FAIL]` tags[cite: 3].
2.  **Adaptive Feedback:** If Conrad detects a rule violation, push the exact violation back to the container's `stdin` to force a rewrite.
3.  **State Tagging:** If the output passes, append the task to `state.jsonl` with `"status": "Complete"`. **Do not apply to the Git worktree.**

## Phase 4: Batch Review & Developer UI
1.  **Report Generation:** After the agents finish, parse `state.jsonl` to collect all `"Complete"` tasks. Pipe the results through the `rich.Markdown` module to display a highly visible terminal panel[cite: 3].
2.  **One-Click Apply:** Use `questionary` or `prompt_toolkit` to prompt the user to accept the completed batch. Upon confirmation, the CLI sequentially applies the verified patches to the active Git worktree.