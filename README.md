# RuleScript & PyRules (v1.0.0)

RuleScript is a domain-specific language (DSL) and compiler designed for high-performance, readable gameplay logic. It allows developers to write rules in a natural-language syntax, compile them into a validated Intermediate Representation (IR), and execute them against Python objects using the PyRules engine.

---

## PROJECT STATUS: VERSION 1.0.0 (STABLE)

The project has transitioned from an early prototype to a structured compiler pipeline. It now features full semantic validation, type checking, and a decoupled runtime engine.

---

## CORE ARCHITECTURE



[Image of compiler architecture diagram]


The system operates in four distinct stages:

1. SOURCE (.rules): Human-readable logic written in the RuleScript DSL.
2. COMPILER (rulescript.py): Tokenizes (Lexer), structures (Parser), and checks (Validator) the logic.
3. ARTIFACT (.rsc): A portable, optimized JSON representation of the rules.
4. RUNTIME (pyrules.py): A lightweight engine that executes the .rsc files against live Python objects.

---

## KEY FEATURES

- LEXICAL INTEGRITY: Tokenizer with column/line tracking for precise error reporting.
- SEMANTIC VALIDATION: Enforces contracts via .var metadata files to catch errors before execution.
- TYPE SAFETY: Supports v2.0 schema with type compatibility checking (e.g., int vs string).
- READONLY PROTECTION: Prevents rules from modifying protected game variables.
- LGPL v3 LICENSED: Open for use in commercial games while protecting engine improvements.

---

## EXAMPLE SYNTAX

rule HighScoreAlert:
    when Player.score > 1000 and Player.is_alive == true
    then Player.trigger_effect("fireworks")

---

## COMPILER USAGE

To compile a rules file:
$ python rulescript.py gameplay.rules

This will perform:
- Lexical analysis (Lexer)
- AST generation and normalization (Parser)
- Semantic contract enforcement (Validator)
- JSON IR emission (Emitter)

---

## RUNTIME INTEGRATION

from pyrules import RuleEngine

# 1. Initialize engine with compiled rules
engine = RuleEngine("gameplay.rsc", {"Player": player_instance})

# 2. Run the engine in your game loop
while game_running:
    engine.tick()

---

## LICENSE

This project is licensed under the GNU Lesser General Public License v3 (LGPL-3.0). See LICENCE.txt for details.