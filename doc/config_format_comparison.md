## Comparison Table: Configuration Formats for Complex C++ Structures

| Feature/Criterion          | YAML                     | JSON        | Lua (Embedded)   | XML         | Python (.py)     | Jsonnet                  |
| :------------------------- | :----------------------- | :---------- | :--------------- | :---------- | :--------------- | :----------------------- |
| **Base Format**            | Superset of JSON         | JSON        | Lua Script       | XML         | Python Script    | Superset of JSON         |
| **Readability**            | High (human-friendly)    | Medium      | Medium           | Medium-Low  | High             | High (human-friendly)    |
| **Expressiveness**         | Medium (Anchors/Aliases) | Low         | Very High (Code) | Medium (DTD/XSD) | Very High (Code) | High (Functions, Vars)   |
| **Schema/Validation**      | Limited (External tools) | Yes (JSON Schema) | Custom (Lua code) | Yes (DTD/XSD) | Custom (Python code) | Limited (External tools) |
| **Templating/Generation**  | Limited (External tools) | No          | Yes (Lua code)   | Yes (XSLT)  | Yes (Python code)| **Built-in**             |
| **Comments**               | Yes (`#`)                | No          | Yes (`--`)       | Yes (`<!-- -->`) | Yes (`#`)        | Yes (`#`, `//`, `/* */`) |
| **Complexity (Parsing)**   | Medium                   | Low         | High             | Medium-High | High             | Medium (Requires Eval)   |
| **Complexity (Learning)**  | Low-Medium               | Low         | Medium           | Medium      | Low-Medium       | Medium                   |
| **Ecosystem/Tooling**      | Strong                   | Very Strong | Medium           | Very Strong | Very Strong      | Growing                  |
| **Use Case (C++ Config)**  | Good (readable static)   | Good (simple static) | Powerful (dynamic) | Okay (verbose) | Powerful (dynamic) | **Excellent (complex static/generated)** |
| **Integration (C++)**      | Many libraries           | Many libraries | Requires Lua VM  | Many libraries | Requires Python Int. | Lib available (outputs JSON) |