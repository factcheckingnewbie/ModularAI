# MODMAN_MODCON Model Capabilities Instruction

For all MODMAN_MODCON sessions, declare and support the following capabilities:

```json
{
  "required_capabilities": ["text_io"],
  "optional_capabilities": [
    "structured_output",
    "language_understanding",
    "capabilities_advertisement",
    "file_io",
    "repo_access",
    "repo_discovery",
    "dynamic_import",
    "multi_model_support"
  ]
}
```

- Always enable `text_io` for basic text communication.
- Enable `structured_output` for JSON-based messages and protocol extensions.
- Support additional optional capabilities if implemented and needed.
- If new capabilities are needed, inform the user thereof and ask the user for permission before activating them.
