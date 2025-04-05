# Methods that must be used for all code in this project
*  Modular Design
*  Minimal Code Duplication
*  Clean Separation of Concerns
*  Scalability
*  Latency Considerations: Best handled if each piece of code can do it's own task
*  Modular Persistence: Encapsulating specific behaviors in dedicated components makes is the most natural fit for future expansion plans.

## Static Connection Map (Find Output with Additional Fields)
./ModdularAI/module_manager.py
  [Role] Main loop: Reads configuration files, presents menus, connects interface and AI-model.
  [Reads]
    - ./ModdularAI/config/interface_modules.json
      [Contains] Interface definitions, connection details, non-blocking specs, multi-connection support.
    - ./ModdularAI/config/model_modules.json
      [Contains] AI-model (agent) definitions, connection details, non-blocking specs, multi-session support.
  [Connects]
    - Interface Module: (e.g., ./ModularAI/interfaces/cli_chat_interface.py)
    - Model Module: (e.g., ./ModularAI/models/gpt2/gpt2_model.py)
  [Uses]
    - ./ModdularAI/core/module_controller.py
      [Role] Mediator for connection between modules and interfaces; issues non-blocking calls.
  [Additional Fields]
    - Compatibility Checks:
        * Partial compatibility: Issue warning.
        * No compatibility: Print error and exit.
    - Non-Blocking Behavior: Main loop and all modules operate asynchronously.
    - Dynamic Extension: Supports (and later extends to allow) adding more agents/interfaces at runtime.
  [Dynamic Behavior]
    - After connection establishment, module_manager detaches control to the selected interface.

./ModdularAI/core/module_controller.py
  [Role] Mediator between module and interface.
  [Features]
    - Issues non-blocking calls.
    - Bridges connection based on compatibility checks.
    - No hardcoded dependency on either module or interface.
  [Additional Fields]
    - Connection Handling: Ensures modules communicate as per configuration details.

./ModularAI/interfaces/cli_chat_interface.py
  [Role] Command-line interface for user interaction.
  [Features]
    - Presents menu for this interface. The menu shall be exactky as much needed to serve as a glue between the user and the model.
    - Handles non-blocking user input.
    - Can support multiple simultaneous connections from other model. Interface does not manage the connections.
      The responsibility for the connectionss are in
      1:module_controller.py, which has the event loop and serves as a  channel for communication between the model and the interface.
      2:module_manager.py which has
        a:the initial contact with the user.
        b:module_manager Presents the modules for the user (interfaces and models),
        c:module_manager checks with it's knoweledge from the ./config files the compatibility for the choosed model_modules.
        d:if checks passed (brief compatibility test ok), the module_manager handles over the control to the
        let the user choose
  [Additional Fields]
    - Dynamic Session Management: Capable of handling multiple sessions (multiple agents/interfaces).

./ModularAI/models/gpt2/gpt2_model.py
  [Role] AI-model agent based on gpt2.
  [Features]
    - Provides AI functionalities.
    - Operates in a non-blocking manner.
    - No built-in knowledge of the interface; relies on external connection mediation.
  [Additional Fields]
    - Connection Handling: Compatibility with interfaces checked by module_manager.

./ModdularAI/config/model_modules.json
  [Role] Configuration file for AI-model modules.
  [Contains]
    - Module definitions.
    - Connection details.
    - Non-blocking operation specifications.
  [Additional Fields]
    - Compatibility Parameters: Fields to verify model-to-interface requirements.

./ModdularAI/config/interface_modules.json
  [Role] Configuration file for interface modules.
  [Contains]
    - Module definitions.
    - Connection details.
    - Non-blocking operation specifications.
  [Additional Fields]
    - Compatibility Parameters: Fields to verify interface-to-model requirements.

## Dynamic Flow Details

1. Startup Phase:
   - The main loop in ./ModdularAI/module_manager.py is initiated.
   - Reads configuration files: ./ModdularAI/config/model_modules.json and ./ModdularAI/config/interface_modules.json.

2. User Interaction:
   - Presents a menu for the user to select an interface (e.g., ./ModularAI/interfaces/cli_chat_interface.py).
   - Upon interface selection, presents a subsequent menu for AI-model selection (e.g., ./ModularAI/models/gpt2/gpt2_model.py).

3. Connection Establishment:
   - ./ModdularAI/module_manager.py calls ./ModdularAI/core/module_controller.py to establish the connection between the selected interface and AI-model.
   - Compatibility checks are performed:
       * Partial compatibility: Issue a warning to the user.
       * Total incompatibility: Print error and exit.
   - All operations (both in the module_controller and in the modules) are non-blocking.

4. Control Transfer:
   - After successfully connecting, module_manager detaches and transfers control to the selected interface.
   - The interface then manages the session, capable of through the module_controller handling multiple connections concurrently.

5. Dynamic Extensions (Future Enhancements):
   - It will be possible to add more agents to the same interface or add more interfaces to the same agent at runtime.
   - The current module_manager supports a single connection at startup; future tweaks will allow dynamic additions.
   - Non-blocking connections remain central even with these dynamic extensions.

6. Non-Blocking Execution:
   - Both the modules (./ModularAI/interfaces/cli_chat_interface.py and ./ModularAI/models/gpt2/gpt2_model.py) and the mediator (./ModdularAI/core/module_controller.py) rely on non-blocking calls.
# Networking
    Keep connection establishment isolated in module_controller.py
    Use standard stream interfaces consistently
    Don't hardcode assumptions about connection locality

# Future Improvements.
## ModuleManager
    Possibly we can restart Module_manager if needed,
    to attache (and in future both attach and deattach models and / or interfaces)  - but not for now.
.
## Summary of Additional Module Details (Future goal, no need to be inplanted yet)

- Compatibility Checks between modules:
    * Partial Compatibility: Issue a warning to the user.
    * Incompatibility: Print error and exit.

- Connection Behavior:
    * All modules and connections operate non-blocking.
    * Module_manager connects modules to the module_controller where Module_manager is using a non-blocking main loop.
    * Future enhancements may include dynamic module additions during runtime.

- Session Management:
    * Interfaces can connect simultaneously to multiple agents.
    * Agents can be accessed by multiple interfaces concurrently or in separate sessions.
    * The entire system is designed to support concurrent sessions and multi-connection capabilities.
    * The system is designed to become a multi-session system where two or more modules is in one session, and other session can         cooparate in session-groups, which can go under one or more simoultnanous multi-sessions.  


- Configuration Files:
    * Both configuration files include module definitions and non-blocking specifications.
    * They also contain fields to guide compatibility checks during the connection phase.
    * Coming session system will have it's set ofconfiguration files which maps the during session connected modules configuration       files.
    
