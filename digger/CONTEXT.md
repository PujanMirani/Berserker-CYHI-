# 🔍 Digger: Cross-Service Log Correlation

## Overview
In a microservices architecture, debugging a failure is difficult because the root cause is often in one service's logs, while the error manifests seconds later in another service's logs. **`digger`** solves this by automatically correlating logs across multiple service log files using shared transaction identifiers, without requiring the system to be pre-instrumented with complex distributed tracing.

## 🛠 Tech Stack & Dependencies
- **Language**: Python 3.8+ (Chosen for team familiarity and fast regex prototyping during the 24h hackathon)
- **Built-in Libraries**: `re` (Regex parsing), `os` (File operations)
- **External Dependencies**: 
  - `rich`: For beautiful, color-coded terminal tables and UI elements.
  - `watchdog` *(upcoming)*: For real-time live-tailing of changing log files.

## 🚀 Features

### 1. Log Parsing & Extraction
Reads unstructured logs from multiple services and uses regular expressions to extract:
- Timestamp (chronological ordering)
- Severity Level (INFO, WARN, ERROR, FATAL)
- Service Name (inferred from the log file name)

### 2. Transaction ID Extraction
Automatically scans every log line for common correlation tokens:
- **UUIDs** (e.g., `123e4567-e89b-12d3-a456-426614174000`)
- **Order IDs** (e.g., `ord_89421`)
- **Request IDs** (e.g., `req-1001`)
- **User IDs** (e.g., `usr_99`)

### 3. Chronological Correlation (The "Timeline")
When an ID is searched, `digger` merges all log lines across all microservices that mention that ID, sorts them chronologically by timestamp, and displays a unified, color-coded `rich` table. This reconstructs the exact cross-service timeline of a transaction.

### 4. Context Window *(Upcoming)*
Given an error line, `digger` will display nearby lines in the same file (e.g., ±5 lines) to provide immediate local context, alongside the cross-service timeline.

### 5. Live Tailing / Watch Mode *(Upcoming)*
A real-time mode (`digger watch`) that continuously monitors the `logs/` directory for changes and live-updates the correlation timeline as new logs stream in.

## ⚠️ Key Design Constraint & Limitation
**Non-Negotiable Principle**: `digger` never claims to know "the root cause." A shared identifier between two logs is *correlation*, not mathematical proof of *causation*. The tool's output is always framed as neutral fact ("This ID appears here at this time").
