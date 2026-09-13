# GodsHand Conrad Agent: Project Context & History

This document serves as a historical context and architectural summary of the work done to implement the **Conrad Agent** (originally referred to as "Guts") within the `GodsHand` CLI framework.

## 1. Core Concept & Objectives
The **Conrad** agent is designed as a dedicated, natively-run auditor persona. Its sole purpose is to enforce the 38-rules `anti-slop` framework, preventing generic AI output, sterile copywriting, and hallucinatory fixes without relying on external web requests. 

**Key Principles:**
- **Filter, Not a Style Guide:** Conrad evaluates purpose and technique but does not prescribe fonts, colors, or layouts.
- **Directional Boundary:** Conrad expects a `DESIGN.md` in the local directory. Without it, output is explicitly flagged as a "draft without direction."
- **Operational Isolation:** Conrad runs sandboxed via a REPL session, preventing contamination with other agents in the `GodsHand` ecosystem.
- **Mandatory Interception:** All LLM outputs are intercepted in-memory to look for a non-negotiable 4-block PASS/FAIL gate report.

## 2. Implemented Architecture

We scaffolded the `GodsHand` Python package from scratch within this repository. The resulting file structure is as follows:

```text
GodsHand/
├── __init__.py
├── rules/
│   ├── ANTISLOP.md       # Static store for the core 38 anti-slop rules
│   └── SKILL_CODE.md     # Modular rule extensions for code writing
├── utils/
│   ├── __init__.py
│   └── parser.py         # Parses markdown files and extracts 'R-XX' rule blocks using Regex
└── agents/
    ├── __init__.py
    ├── compiler.py       # SystemPromptCompiler: Injects rules, Liveliness Toolkit, and DESIGN.md context
    ├── interceptor.py    # DeliveryGateInterceptor: Middleware that blocks streaming, enforces PASS/FAIL gate, and handles silent retries
    └── conrad.py         # The interactive prompt_toolkit REPL session
```

## 3. Key Mechanisms Built

### A. Static Parsing (`utils/parser.py`)
To ensure offline compatibility and speed, rules are loaded directly from the static Markdown files in `GodsHand/rules/`. The parser strips out the relevant text blocks so they can be injected into the system prompt.

### B. Context Compilation (`agents/compiler.py`)
The `SystemPromptCompiler` brings together:
1. The extracted 38 Rules.
2. The Liveliness Toolkit (currently intentionally left empty).
3. The contents of `DESIGN.md`. If `DESIGN.md` is missing, it dynamically appends a explicit warning indicating that generation lacks direction.

### C. Delivery Gate & Retry Logic (`agents/interceptor.py`)
The `DeliveryGateInterceptor` scans the final LLM text response using regex for `[PASS]` or `[FAIL]`. 
- **Retry Mechanism:** If the gate is absent, it silently retries the generation. 
- **Fallback:** To prevent infinite loops, retries are capped at `3`. If the 3rd attempt also lacks a gate, the interceptor falls back by appending a warning header and returning the raw string to the user.
- **Rendering:** All validated text is piped through the `rich.Markdown` module for beautiful terminal formatting.

### D. The Interactive REPL (`agents/conrad.py`)
Provides an interactive command-line loop via `prompt_toolkit`. A mocked LLM generation function is currently mapped to it for local testing and debugging.

## 4. Dependencies & Testing
All dependencies required to run the agent (`prompt_toolkit`, `rich`, `psutil`, `watchdog`, `questionary`) are pinned in the root `requirements.txt`. The REPL can be manually started and tested via:

```bash
python -m GodsHand.agents.conrad
```
