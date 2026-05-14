# pyrules

A lightweight gameplay scripting language and runtime for Python games.

`pyrules` aims to provide a simple, readable, engine-agnostic scripting system that can be embedded into:
- Pygame
- pygame-ce
- custom Python game engines
- experimental game frameworks

The project introduces:
- `.rules` source files
- a RuleScript-inspired syntax
- a future `.rsc` compiled format
- runtime object bindings
- gameplay-focused scripting

---

# Example

```rules
use player

rule low_health:
    when player.hp < 20 and player.on_ground
    then:
        player.jump()
```

---

# Goals

- Beginner-friendly syntax
- Readable gameplay logic
- Engine-independent design
- Safe runtime execution
- Modding support
- Lightweight integration
- Future bytecode/runtime support

---

# Planned Architecture

```text
.rules
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
.rsc
    ↓
Runtime
```

---

# Project Status

Early prototype.

Current focus:
- lexer
- parser
- AST design
- syntax experimentation

---

# Syntax

Current keywords:

```text
rule
class
func
when
then
use
and
or
```

Current operators:

```text
>
<
=
==
+
-
*
/
```

---

# Example Runtime Integration

```python
from pyrules import RuleEngine

engine = RuleEngine()

engine.export("player", player)
engine.load("player.rules")
```

---

# Vision

`pyrules` is intended to become:
- a reusable gameplay scripting system
- a standalone rules engine
- a moddable scripting layer
- an ecosystem tool usable beyond a single engine

---

# License

LGPL-3.0

---

# Future Plans

- `.rsc` compiled format
- syntax highlighting
- VS Code extension
- hot reload support
- debugger tooling
- optional native runtime experimentation