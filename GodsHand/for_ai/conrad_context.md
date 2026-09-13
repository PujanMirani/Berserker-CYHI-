# 🏛 GodsHand & Conrad: Multi-Agent Blackboard Architecture

## 1. System Overview
The `GodsHand` framework orchestrates a multi-agent ecosystem using a Blackboard design pattern secured by ephemeral sandboxes. The **Conrad** agent acts as a dedicated, natively-run auditor persona[cite: 3]. Conrad does not generate code directly; instead, it enforces the 38-rules `anti-slop` framework against the output of specialized worker agents[cite: 3]. Crucially, passing Conrad's rule check does not automatically modify the active Git worktree.

## 2. Core Components
*   **The Blackboard (`state.jsonl`):** A centralized, append-only JSON Lines file acting as the single source of truth. When an agent's output passes Conrad's verification, the task is updated here with a `"Complete"` tag rather than instantly applied to the project.
*   **Worker Sandboxes (Podman):** Atomic tasks are isolated in daemonless Podman containers. Workers operate on temporary file copies or isolated mounts, preventing untrusted LLM hallucinations from directly modifying the main codebase.
*   **The Conrad Gateway (Generator-Verifier):** Before any worker's output is marked as complete, it is intercepted in memory[cite: 3]. Conrad verifies the code against the 38 anti-slop rules and demands the mandatory 4-block PASS/FAIL gate report[cite: 3].
*   **User Approval Dashboard:** The CLI renders a final report of all tasks tagged as `"Complete"` in `state.jsonl`. The user reviews the validated tasks and can apply them to the active Git worktree in a single click.

## 3. Directional Boundaries
Conrad operates as a filter, not a style guide, and does not prescribe fonts, colors, or layouts[cite: 3]. It strictly requires a `DESIGN.md` file in the local directory; if missing, Conrad forces the output to be flagged as a "draft without direction"[cite: 3].