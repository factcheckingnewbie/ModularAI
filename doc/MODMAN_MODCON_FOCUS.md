# Focus on modman.py and modcon.py

_Last updated: 2025-05-27_

## 1. Purpose & Roles

### modman.py ("Loader")
- **Entry point** during early development/prototyping.
- **Responsibility:**  
  - Hardcoded (for now) loading of backend (model) and frontend (interface) modules.
  - Import and instantiate module classes (using Python imports).
  - Pass instantiated module objects to modcon.py.
  - No complex logic or user interaction at this phase.
- **Transitional:**  
  - Will eventually be replaced by a more flexible module_manager.py.

### modcon.py ("Controller")
- **Core responsibility:**  
  - Receives ready-to-use module instances from modman.py.
  - Establishes a true asynchronous (asyncio-based) streaming connection between modules, allowing bi-directional data flow (e.g., interface <-> model).
  - Remains agnostic to module internals; just passes streams.
  - Does not own the main system loop—only manages the bridge for now.
- **Transitional:**  
  - Will eventually be superseded by a more feature-rich module_controller.py.

---

## 2. Current Workflow Overview

1. **modman.py**:
    - Has hardcoded paths to the modules you want to connect (for now).
    - Imports the relevant modules (e.g., gpt2_model.py, cli_chat_interface.py).
    - Instantiates classes for backend and frontend.
    - Passes these instances to modcon.py.

2. **modcon.py**:
    - Accepts module instances from modman.py.
    - Sets up asyncio streams for communication between them.
    - Handles all data passing (messages, prompts, responses, etc.).
    - Provides minimal error handling (expandable as needed).

---

## 3. Design Principles

- **Minimal coupling**: modcon.py does not assume anything about module logic or internals.
- **Plug-and-play**: Both modman.py and modcon.py are stepping stones towards a hot-pluggable, flexible system.
- **Proof-of-concept**: The current focus is to prove that backend and frontend modules can communicate asynchronously.
- **Keep it simple**: No advanced features, user menus, or dynamic behavior at this stage.

---

## 4. Next Steps / Actionable Tasks

- **For modman.py:**
  - Maintain hardcoded paths for now.
  - Ensure robust instantiation of backend and frontend.
  - Pass objects cleanly to modcon.py.
  - Add minimal error handling/logging just sufficient for debugging.

- **For modcon.py:**
  - Accept instances from modman.py.
  - Establish asyncio-based streams between modules.
  - Ensure clean start/stop of the bridge connection.
  - Pass data/messages without modifying or interpreting them.
  - Add minimal error handling/logging as needed.

- **Testing:**
  - Test the full flow: start modman.py, ensure the modules connect and communicate via modcon.py.
  - Use CLI interface and model as concrete test modules.

---

## 5. Transition Plan

- Once proven, use this setup as the "living spec" for the more advanced module_manager.py and module_controller.py.
- Gradually introduce:
  - Dynamic module selection.
  - Hot-plugging.
  - Compatibility checks.
  - Multi-session support.

---

## 6. Example Directory Structure

```
/project-root/
  modman.py
  modcon.py
  /models/
    gpt2_model.py
  /interfaces/
    cli_chat_interface.py
```

---

## 7. Example modman.py Skeleton

```python name=modman.py
import sys
from models.gpt2_model import GPT2Model
from interfaces.cli_chat_interface import CLIChatInterface
import modcon

def main():
    # Instantiate backend and frontend
    backend = GPT2Model()
    frontend = CLIChatInterface()
    # Pass to controller
    modcon.run_bridge(frontend, backend)

if __name__ == "__main__":
    main()
```

---

## 8. Example modcon.py Skeleton

```python name=modcon.py
import asyncio

async def bridge(frontend, backend):
    # Example: pass messages from frontend to backend and vice versa
    async for message in frontend.input_stream():
        response = await backend.process(message)
        await frontend.output_stream(response)

def run_bridge(frontend, backend):
    asyncio.run(bridge(frontend, backend))
```

---

## 9. Notes

- This is a minimal reference and not a production-ready code.
- Expand error handling, extensibility, and configuration in future iterations.
- These files are designed to be replaced or evolved into module_manager.py and module_controller.py.

---
