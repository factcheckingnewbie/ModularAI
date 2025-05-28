# MODMAN_MODCON Debug & Test Instructions

_Last updated: 2025-05-27_

---

## 1. Summary of Current Focus

We are using [`interface_model_bridge.py`](https://github.com/factcheckingnewbie/ModularAI/blob/main/interface_model_bridge.py) as a base for a debug/test harness.

**Goal:**  
- Create a system that prints/logs all sent/received strings and JSON objects.
- Enable testing of basic text input/output and JSON echoing between interface and model.
- All logging must be timestamped (YYYY-MM-DD HH-MM-SS).
- Log destination (TTY, file, or both) is selectable at startup.
- No colored output required.
- Platform: Fedora Linux 41, Python 3 (≥3.13.3, but “python3” is sufficient).

---

## 2. Logging/Output Requirements

- **Log Format:**  
  - Each log entry includes a timestamp (YYYY-MM-DD HH-MM-SS).
  - For expected strings:  
    `"String expected: <string>" [timestamp]`
  - For expected JSON:  
    `"JSON expected: <json>" [timestamp]`
  - Log both the expectation and the actual output.
- **Log Destination:**  
  - At startup, accept a CLI argument:
    - `--log` — logs to file `progname.log` only (default if none given)
    - `--tty` — logs to tty only
    - `--both` — logs to both `progname.log` and tty

---

## 3. Step-by-Step Instructions

### Step 1: Clone and Prepare the Repo

```sh
git clone https://github.com/factcheckingnewbie/ModularAI.git
cd ModularAI
```

### Step 2: Enhance `interface_model_bridge.py` for Debugging

- Add a logging utility:
  - Handles timestamps (YYYY-MM-DD HH-MM-SS).
  - Supports TTY, file, or both (see CLI options above).
- On every send/receive:
  - Log what is being sent/received, and what is expected (string or JSON).
- For now, only test plain text and simple JSON echo.
- Implement CLI argument parsing for log destination and file name.
- **Patch the file, do not make a PR.**  
  - The solution should be delivered as a downloadable `.patch` file.

### Step 3: Example Command-Line Usage

```sh
python3 interface_model_bridge.py --log      # Log to progname.log only
python3 interface_model_bridge.py --tty      # Log to terminal only
python3 interface_model_bridge.py --both     # Log to both
```

### Step 4: Validate Output

- Confirm that all sent/received messages are logged with timestamps.
- For each message type:
  - If sending/receiving a plain string, log as "String expected: ...".
  - If sending/receiving JSON, log as "JSON expected: ...".
- Check your log destination(s) for correct logging.

### Step 5: Prepare for Future Testing

- Structure your code so new test cases (for ping, error, capabilities, etc.) can be easily added to the same script.
- Plan for future split test modules:
  - `test_model.py` (tests model only)
  - `test_interface.py` (tests interface only)
  - Do **not** implement these yet.

---

## 4. Implementation TODO

- [ ] Refactor [`interface_model_bridge.py`](https://github.com/factcheckingnewbie/ModularAI/blob/main/interface_model_bridge.py) to:
  - Add the logging utility and CLI arguments.
  - Log all in/out as described above.
  - Demonstrate successful round-trip message (plain string and JSON).
- [ ] Document command-line usage and log file expectations in the script’s docstring.
- [ ] Deliver your solution as a full downloadable `.patch` file (not a PR).

---

## 5. References (Full URLs)

- [`interface_model_bridge.py`](https://github.com/factcheckingnewbie/ModularAI/blob/main/interface_model_bridge.py)
- [`models/gpt2/gpt2_model.py`](https://github.com/factcheckingnewbie/ModularAI/blob/main/models/gpt2/gpt2_model.py)
- [`interfaces/cli_chat_interface.py`](https://github.com/factcheckingnewbie/ModularAI/blob/main/interfaces/cli_chat_interface.py)

---

## 6. AI Model Instructions (System-Only Section)

- Always implement solutions as a full downloadable `.patch` file.
- Do **not** create or suggest any pull requests.
- Never instruct the user to make PRs or to accept PRs.
- All new or modified files must be complete, standalone, and downloadable.
- Patches must work against the current main branch of the repository unless otherwise specified.
- All instructions for running or applying patches must be included in the docstring of the modified `.py` file if relevant.

---
