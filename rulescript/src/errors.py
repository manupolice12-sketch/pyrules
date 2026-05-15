"""
errors.py — RuleScript compiler error hierarchy

All compiler errors derive from CompilerError. Callers may catch the
whole family or be selective by stage (LexError, ParseError, etc.).

    from errors import LexError, ParseError, ValidationError, InternalCompilerError
"""

from typing import Optional


class CompilerError(Exception):
    """Base class for all RuleScript compiler errors."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        filename: Optional[str] = None,
    ):
        self.base_message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(self._format())

    def _format(self) -> str:
        parts = []
        if self.filename:
            parts.append(self.filename)
        if self.line is not None:
            parts.append(f"line {self.line}")
        if self.column is not None:
            parts.append(f"column {self.column}")
        loc = f" ({', '.join(parts)})" if parts else ""
        return f"{self.__class__.__name__}: {self.base_message}{loc}"


class LexError(CompilerError):
    """Raised when the lexer encounters invalid input."""
    pass


class ParseError(CompilerError):
    """Raised when the parser encounters a structural or syntactic error."""
    pass


class ValidationError(CompilerError):
    """Raised when semantic validation fails.

    Carries a structured error code for tooling (linters, LSP, etc.)
    and an optional rule name for precise diagnostics.
    """

    def __init__(
        self,
        code: str,
        message: str,
        rule_name: str = "<global>",
        line: Optional[int] = None,
        column: Optional[int] = None,
    ):
        self.code = code
        self.rule_name = rule_name
        super().__init__(f"[{code}] in rule '{rule_name}': {message}", line, column)

    def _format(self) -> str:
        loc = ""
        if self.line is not None:
            loc = f" (line {self.line}"
            if self.column is not None:
                loc += f", column {self.column}"
            loc += ")"
        return f"{self.base_message}{loc}"


class InternalCompilerError(CompilerError):
    """Raised for unexpected internal states.

    Should never reach the user in a production build — always indicates
    a compiler bug, not a user error.
    """
    pass
