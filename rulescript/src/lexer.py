"""
lexer.py — RuleScript tokenizer

Converts raw .rules source text into a flat token stream.
Keywords are only recognised at the start of a logical line — this
prevents identifiers like `player.or.hp` from producing spurious tokens.
"""

from dataclasses import dataclass
from typing import List

KEYWORDS = {"rule", "when", "then", "use", "and", "or"}


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"{self.type}({self.value})@{self.line}:{self.column}"


class Lexer:
    def __init__(self, text: str):
        self.text = text

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        for line_num, line in enumerate(self.text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            lower_stripped = stripped.lower()
            keyword_found = None
            keyword_col = None

            # Sort longest-first so "when" is never shadowed by a shorter keyword.
            for kw in sorted(KEYWORDS, key=len, reverse=True):
                if lower_stripped.startswith(kw):
                    remainder = lower_stripped[len(kw):]
                    # Whole-word boundary: reject "rules", "whenever", etc.
                    if not remainder or (not remainder[0].isalnum() and remainder[0] != '_'):
                        keyword_found = kw
                        keyword_col = line.find(stripped) + 1
                        break

            if keyword_found:
                tokens.append(Token(keyword_found.upper(), keyword_found, line_num, keyword_col))
                rest_start = line.find(stripped) + len(keyword_found)
                rest = line[rest_start:].strip()
                if rest and not rest.startswith('#'):
                    rest = rest.split('#')[0].strip()
                if rest:
                    expr_col = line.find(rest) + 1
                    tokens.append(Token("EXPR", rest, line_num, expr_col))
            else:
                col = line.find(stripped) + 1
                tokens.append(Token("EXPR", stripped, line_num, col))

        return tokens
