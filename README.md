# 🛠 Berserker Hackathon Toolkit

**Berserker** is a 3-part comprehensive developer toolkit designed to effortlessly parse chaotic logs, automatically summarize 500+ line CI/CD pipeline crashes, and manage an intelligent Local LLM Sandbox for rule validation.

This repository serves as the central integration point for the hackathon team.

---

## 🏗 The Architecture & Branching Strategy

The project is split into a **Master UI Shell** (currently on the `main` branch) and three independent feature branches built by different teammates. All features will automatically snap into the Master UI when their branches are merged into `main`.

### The Master UI Shell (`main` branch)
This branch contains the packaging logic (`setup.py`) and the interactive terminal menu (`main.py`). It acts as the glue that ties the three features together into a single global `berserker` CLI command.

### Feature 1: The Digger Engine (Branch: `Void`)
- **Tool Name**: `berserker`
- **Purpose**: Cross-Service Log Correlation. It auto-sniffs log formats (JSON, ISO8601, Bracket, Syslog), standardizes chaotic logs into strict `LogEntry` formats, scans for `ERROR` and `FATAL` severity, and instantly builds a relative-time correlation timeline across different services based on shared transaction identifiers.

### Feature 2: CI/CD Pipeline Parser (Branch: `griffith`)
- **Tool Name**: `griffith`
- **Purpose**: Auto-discovers broken CI/CD pipelines via the public GitHub API and downloads the raw logs. It is designed to extract human-readable error summaries from massive 500+ line pipeline breakages.

### Feature 3: Local LLM Sandbox (Branch: `conrad`)
- **Tool Name**: `GodsHand`
- **Purpose**: A local LLM Sandbox & Agent Manager. Runs a local LLM strictly within the terminal sandbox and evaluates the output of two sub-agents against specific rule sets, monitored by a larger overarching model.

---

## 🚀 How to Install and Run

The master shell is packaged as a real Python CLI tool. 

### 1. Installation
Clone the repository and install it in editable mode (so the tool updates instantly when you pull new branch merges):
```bash
cd berserker
pip install -e .
```

### 2. Execution
You do not need to run python scripts manually. The installation automatically registers a global command. Simply type this anywhere in your terminal:
```bash
berserker
```

This will launch the master terminal UI. 
*(Note: If you select a tool that has not been merged into `main` yet, the UI will safely warn you that the tool is currently under construction on its respective branch).*

---

## 🤝 How to Integrate Teammate Code

When a teammate finishes building their tool on the `griffith` or `conrad` branch, do **not** edit `main.py`.

1. Place the entry function inside `cicd_parser/parser.py` (for Griffith) or `llm_sandbox/sandbox.py` (for GodsHand).
2. Ensure the entry function is named exactly `run()`.
3. Open a Pull Request on GitHub and merge the teammate's branch into `main`.
4. The Master UI will automatically detect the merged code and launch it perfectly!
