"""
parser.py — RuleScript parser and AST normalizer

Consumes the token stream from the lexer and produces a list of rule
dicts (the IR). Python's ast module is used to parse expressions —
this is an intentional bootstrap strategy. The ast_to_dict() method
normalizes all CPython operator names into RuleScript-native symbols
so the IR is decoupled from Python internals.

IR invariants enforced here:
  - All operator fields use the key "operator" (never "op").
  - Unsupported Python constructs raise ParseError explicitly.
  - Every rule must have exactly one "when" and one "then" clause.
"""

import ast
import re
from typing import Optional, Dict, Any, List

from lexer import Token
from errors import ParseError, InternalCompilerError


# Maps CPython AST operator class names to RuleScript-native symbols.
# This table is the authoritative source for IR operator values.
_OPERATOR_MAP: Dict[str, str] = {
    "Lt": "<",    "Gt": ">",    "Eq": "==",   "NotEq": "!=",
    "LtE": "<=",  "GtE": ">=",
    "Is": "is",   "IsNot": "is not",
    "In": "in",   "NotIn": "not in",
    "And": "and", "Or": "or",   "Not": "not",
    "Add": "+",   "Sub": "-",   "Mult": "*",  "Div": "/",
    "Mod": "%",   "Pow": "**",  "FloorDiv": "//",
    "USub": "-",  "UAdd": "+",  "Invert": "~",
}

# Python constructs that have no equivalent in RuleScript.
# Encountering any of these in an expression is a hard parse error.
_UNSUPPORTED_NODES = {
    ast.Lambda, ast.IfExp, ast.Dict, ast.Set, ast.ListComp,
    ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Await,
    ast.Yield, ast.YieldFrom, ast.Global, ast.Nonlocal,
    ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef,
    ast.Import, ast.ImportFrom, ast.Delete, ast.With,
    ast.For, ast.While, ast.If, ast.Try,
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def error(self, message: str, token: Optional[Token] = None) -> None:
        tok = token or self.current_token()
        raise ParseError(message, tok.line if tok else None, tok.column if tok else None)

    def normalize_operator(self, op_name: str) -> str:
        """Translate a CPython operator class name to a RuleScript symbol."""
        return _OPERATOR_MAP.get(op_name, op_name)

    def ast_to_dict(self, node, source_token: Optional[Token] = None) -> Dict[str, Any]:
        """Recursively convert a Python AST node to a RuleScript IR dict.

        Raises ParseError for unsupported constructs.
        Raises InternalCompilerError for unhandled node types (compiler bug).
        """
        if isinstance(node, ast.Module):
            return self.ast_to_dict(node.body[0], source_token) if node.body else {}
        if isinstance(node, ast.Expression):
            return self.ast_to_dict(node.body, source_token)
        if isinstance(node, ast.Expr):
            return self.ast_to_dict(node.value, source_token)

        for unsupported in _UNSUPPORTED_NODES:
            if isinstance(node, unsupported):
                raise ParseError(
                    f"Unsupported construct '{type(node).__name__}' — "
                    f"RuleScript does not allow arbitrary Python syntax.",
                    source_token.line if source_token else None,
                    source_token.column if source_token else None,
                )

        if isinstance(node, ast.BoolOp):
            return {
                "type": "bool_op",
                "operator": self.normalize_operator(type(node.op).__name__),
                "values": [self.ast_to_dict(v, source_token) for v in node.values],
            }
        if isinstance(node, ast.UnaryOp):
            return {
                "type": "unary_op",
                "operator": self.normalize_operator(type(node.op).__name__),
                "operand": self.ast_to_dict(node.operand, source_token),
            }
        if isinstance(node, ast.BinOp):
            return {
                "type": "binary_operation",
                "left": self.ast_to_dict(node.left, source_token),
                "operator": self.normalize_operator(type(node.op).__name__),
                "right": self.ast_to_dict(node.right, source_token),
            }
        if isinstance(node, ast.Compare):
            return {
                "type": "comparison",
                "left": self.ast_to_dict(node.left, source_token),
                "operator": self.normalize_operator(type(node.ops[0]).__name__),
                "right": self.ast_to_dict(node.comparators[0], source_token),
            }
        if isinstance(node, ast.Attribute):
            return {
                "type": "attribute_access",
                "object": self.ast_to_dict(node.value, source_token),
                "property": node.attr,
            }
        if isinstance(node, ast.Name):
            return {"type": "variable", "id": node.id}
        if isinstance(node, ast.Constant):
            return {"type": "literal", "value": node.value}
        if isinstance(node, ast.Call):
            return {
                "type": "method_call",
                "func": self.ast_to_dict(node.func, source_token),
                "args": [self.ast_to_dict(arg, source_token) for arg in node.args],
            }
        if isinstance(node, ast.Assign):
            return {
                "type": "assignment",
                "target": self.ast_to_dict(node.targets[0], source_token),
                "value": self.ast_to_dict(node.value, source_token),
            }

        raise InternalCompilerError(
            f"Unhandled AST node '{type(node).__name__}' in ast_to_dict — please report this bug."
        )

    def parse_expr(self, raw: str, token: Token) -> Dict[str, Any]:
        """Parse a raw expression string into an IR node.

        Uses Python's ast module as the expression frontend. Assignment
        expressions are parsed in 'exec' mode; all others in 'eval' mode.
        All failures raise ParseError — there is no silent fallback.
        """
        if not raw or not raw.strip():
            return {"type": "empty"}

        try:
            mode = "exec" if re.search(r"(?<!=)=(?!=)", raw) else "eval"
            tree = ast.parse(raw.strip(), mode=mode)
            return self.ast_to_dict(tree, token)
        except (ParseError, InternalCompilerError):
            raise
        except SyntaxError as e:
            raise ParseError(
                f"Invalid expression: '{raw.strip()}'\n"
                f"  -> {e.msg}" + (f" (offset {e.offset})" if e.offset else ""),
                token.line, token.column,
            )
        except Exception as e:
            raise ParseError(
                f"Unexpected error parsing '{raw.strip()}': {e}",
                token.line, token.column,
            )

    def parse_rule(self) -> Dict[str, Any]:
        rule_token = self.current_token()
        if not rule_token or rule_token.type != "RULE":
            self.error("Expected 'rule' keyword", rule_token)

        self.advance()
        rule_data: Dict[str, Any] = {"name": "", "condition": {}, "action": {}}

        if self.current_token() and self.current_token().type == "EXPR":
            rule_data["name"] = self.current_token().value.rstrip(":").strip()
            self.advance()

        seen_when = False
        seen_then = False

        while self.current_token() and self.current_token().type != "RULE":
            tok = self.current_token()

            if tok.type == "WHEN":
                if seen_when:
                    self.error(f"Duplicate 'when' clause in rule '{rule_data['name']}'", tok)
                seen_when = True
                self.advance()
                expr_tok = self.current_token()
                if not expr_tok or expr_tok.type != "EXPR":
                    self.error(f"Expected condition expression after 'when'", tok)
                rule_data["condition"] = self.parse_expr(expr_tok.value, expr_tok)
                self.advance()

            elif tok.type == "THEN":
                if seen_then:
                    self.error(f"Duplicate 'then' clause in rule '{rule_data['name']}'", tok)
                seen_then = True
                self.advance()
                expr_tok = self.current_token()
                if not expr_tok or expr_tok.type != "EXPR":
                    self.error(f"Expected action expression after 'then'", tok)
                rule_data["action"] = self.parse_expr(expr_tok.value, expr_tok)
                self.advance()

            else:
                self.advance()

        if not seen_when:
            self.error(f"Rule '{rule_data['name']}' is missing a 'when' clause", rule_token)
        if not seen_then:
            self.error(f"Rule '{rule_data['name']}' is missing a 'then' clause", rule_token)

        return rule_data

    def parse(self) -> List[Dict[str, Any]]:
        rules = []
        while self.current_token():
            if self.current_token().type == "RULE":
                rules.append(self.parse_rule())
            else:
                self.advance()
        return rules
