#!/bin/bash
# Make this script executable before running:
# chmod +x monitor.sh

# Resolve the absolute path to the project root's state.jsonl
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
STATE_FILE="$SCRIPT_DIR/../../state.jsonl"
REPO_ROOT="$SCRIPT_DIR/../../"

while true; do
    clear
    echo "========================================"
    echo "ACTIVE SANDBOXES"
    echo "========================================"
    # Run git worktree list from the repository root
    git -C "$REPO_ROOT" worktree list | grep "/"

    echo ""
    echo "========================================"
    echo "BLACKBOARD STATE"
    echo "========================================"
    
    if [ -f "$STATE_FILE" ]; then
        (
            # Print headers
            echo -e "AGENT\tTASK\tSTATUS"
            # Extract fields from the JSON payload (accounting for the nested 'result' structure)
            jq -r 'select(.result != null) | [.result.agent // "N/A", .task_name // "N/A", .status // "N/A"] | @tsv' "$STATE_FILE"
        ) | column -t -s $'\t'
    else
        echo "State file ($STATE_FILE) not found."
    fi

    sleep 1
done
