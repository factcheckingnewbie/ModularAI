# MODMAN_MODCON Debug & Test Instructions (Copilot-Only Version for VS Studio)

_Last updated: 2025-05-27_

---

## 1. Task Overview

Use `interface_model_bridge.py` as the base for a debug/test harness.

**Objectives:**  
- Print/log all sent/received strings and JSON objects.
- Test basic text input/output and JSON echoing between interface and model.
- All logging must be timestamped (YYYY-MM-DD HH-MM-SS).
- Log destination (TTY, file, or both) is selectable at startup.
- No colored output.
- Platform: Fedora Linux 41, Python 3 (≥3.13.3, but “python3” is sufficient).

---

## 2. Logging/Output Rules

- **Log Format:**  
  - Each log entry must include a timestamp (YYYY-MM-DD HH-MM-SS).
  - For expected strings, log:  
    `"String expected: <string>" [timestamp]`
  - For expected JSON, log:  
    `"JSON expected: <json>" [timestamp]`
  - Log both the expectation and the actual output.
- **Log Destination:**  
  - At startup, accept a CLI argument:
    - `--log` — logs to file `progname.log` only (default if none given)
    - `--tty` — logs to tty only
    - `--both` — logs to both `progname.log` and tty

---

## 3. Instructions for Copilot

**Copilot must follow every line of these instructions exactly. Do not improvise, do not use placeholders, and do not output illustrative code.**

1. **Repo Preparation**
    - Assume repo is already local.
    - Work in the root directory.

2. **Patch `interface_model_bridge.py`**
    - Add a logging utility:
        - Timestamps using format (YYYY-MM-DD HH-MM-SS).
        - Supports TTY, file, or both (see CLI options above).
    - On every send/receive:
        - Log what is being sent/received, and what is expected (string or JSON).
    - For now, test plain text and simple JSON echo only.
    - Implement CLI argument parsing for log destination and file name.
    - Do not use or generate pull requests.
    - **Deliver the solution as a downloadable `.patch` file only.**
    - **The patch must be a standard unified diff with real context lines, suitable for `patch -p1`.**
    - **Do not use placeholders, synthetic lines, or illustrative code (e.g., `# ...existing code...`).**
    - **Do not add, remove, or change any requirements from this list.**

3. **Command-Line Usage Example**
    - Support the following:
      ```sh
      python3 interface_model_bridge.py --log      # Log to progname.log only
      python3 interface_model_bridge.py --tty      # Log to terminal only
      python3 interface_model_bridge.py --both     # Log to both
      ```

4. **Validation**
    - Ensure all sent/received messages are logged with timestamps.
    - For each message type:
        - If plain string, log as "String expected: ...".
        - If JSON, log as "JSON expected: ...".
    - Verify logs are written to the correct destinations.

5. **Future Testing Preparation**
    - Structure code so new test cases (for ping, error, capabilities, etc.) can be added easily.
    - Plan for future split test modules:
        - `test_model.py` (model only)
        - `test_interface.py` (interface only)
    - Do not implement these yet.

---

## 4. Implementation TODO

- [ ] Refactor `interface_model_bridge.py` to:
    - Add logging utility and CLI arguments.
    - Log all in/out as described.
    - Demonstrate successful round-trip message (plain string and JSON).
- [ ] Document command-line usage and log file expectations in the script’s docstring.
- [ ] Deliver the solution as a complete `.patch` file (not a PR).
- [ ] **The patch must be a standard unified diff with real context lines, suitable for `patch -p1`.**
- [ ] **Do not use placeholders, synthetic lines, or illustrative code.**
- [ ] **Copilot must follow every line of these instructions exactly.**

---

## 5. File References (Local Only)

- `interface_model_bridge.py`
- `models/gpt2/gpt2_model.py`
- `interfaces/cli_chat_interface.py`

---

## 6. Meta Instructions

- Only implement solutions as a complete downloadable `.patch` file meant to use as `patch -p1 < <stem>.patch`
- All new or modified files must be complete, standalone, and downloadable.
- Patches must work against the current main branch of the repository unless otherwise specified.
- All instructions for running or applying patches must be included in the docstring of the modified `.py` file if relevant.
- **Patches must be standard unified diffs with real context lines, not placeholders or synthetic lines.**
- **Copilot must follow every line of these instructions exactly, with no improvisation or deviation.**

---