# ModularAI: Expanded Planning Summary

_Last updated: 2025-05-27_

---

## 1. Architecture & Control Flow

- **module_manager.py** (“loader”)
  - Initial entry point; eventually will be a GUI (with CLI fallback).
  - Discovers and loads available backend (model) and frontend (interface) modules.
  - Passes module instances to module_controller.py.

- **module_controller.py** (“controller”)
  - Mediates all data streams between modules.
  - Remains agnostic about module internal logic.
  - Owns the async event loop for coordinating module connections and communication.
  - Designed as a “flexible state machine” for dynamic bridging.

- **Modules**
  - Can be backends (models) or frontends (interfaces).
  - Supported formats: Python packages, executables, shared libraries, script modules, etc.
  - Each module is as independent as possible and can define its own requirements/capabilities.

---

## 2. Minimal Working Prototype

- **Proof-of-Concept Bridge:**  
  - Demonstrated via interface_model_bridge.py (gpt2_model.py ↔ cli_chat_interface.py).
  - Current workflow: Hardcoded module paths in modman.py, which loads modules and passes to modcon.py for connection.
  - Focus on establishing true async streaming between modules.

---

## 3. Modular Loading & Passing

- **Present:** Python imports for instantiating module classes.
- **Near Future:** Loader passes one module at a time to controller, which manages connections.
- **Abstraction:** Loader/controller exchange instantiated objects, not file paths or subprocesses.
- **Goal:** Allow modules to be loaded, wait, and connect dynamically—by controller’s decision or external signal.

---

## 4. Configuration & Compatibility

- **Config Files:** JSON per module, specifying capabilities, requirements, and “personality” parameters.
- **Compatibility Checks:**  
  - Initial focus on matching required capabilities and minimal version/capability checks.
  - Only “compatible enough” modules connect; partial compatibility is accepted in some cases.
- **Config Location:**  
  - Each module/interface keeps its config under its own directory (e.g., `./interfaces/<name>/config/<name>/*.json`).
  - Supports “hot plug” and self-discovery.

---

## 5. Core System Priorities

- **Top features:** Multi-session support, dynamic reloading (developed in parallel), menu system (lower priority).
- **Goal:** Make module development and testing as frictionless as possible.
- **Manager Lifecycle:** module_manager.py detaches/daemonizes after connecting modules; wakes up for new connections.
- **Logging:**  
  - Each module handles its own logging.
  - module_manager logs failures (debug mode available); future centralized/customizable logging is possible.

---

## 6. Session & Connection Management

- **Definition:** Each module defines its own session concept; can be stateless or persistent.
- **Default:** Session data is not retained unless explicitly permitted by admin or secure policy.
- **Flexibility:** Supports ephemeral/persistent sessions, local/remote modules, and user personalization.
- **Security:**  
  - Data persistence and connection policies governed by admin/system policy.
  - Modules must not compromise privacy or security; robust checks required.

---

## 7. Dynamic Extension (“Hot-Plug”)

- **Workflows:**  
  - Self-detection (drop-zone/FS watcher), CLI, menu, plugin (drag-and-drop/network).
  - All methods interact with module_manager or helpers, ultimately connecting via module_controller.
- **Checks:**  
  - All modules must pass configuration, compatibility, and security checks before activation.
  - Networked modules must comply with protocol security (e.g., SSH, policy enforcement).

---

## 8. Documentation (Deferred for Parallel Work)

- **Keep at least:** README.md, BROADPLAN.md, MODULE_GUIDE.md.
- **Optional:** CONFIG_SCHEMA.md, TROUBLESHOOTING.md, CHANGELOG.md.
- **Meta-process:** DOCS_COMMUNICATION_BASE.md guides AI/collaborator documentation discussions.
- **You will revisit and expand documentation as development progresses.**

---

## Next Steps

- Begin iterative development based on this plan.
- Revisit and expand documentation and compatibility/security policies as the system matures.
- Use this summary as your “north star” for architecture and feature priorities.

---
