# rulescript/lexer.py

KEYWORDS = {
    "rule": "RULE",
    "class": "CLASS",
    "func": "FUNC",
    "when": "WHEN",
    "then": "THEN",
    "use": "USE",
    "and": "AND",
    "or": "OR",
}

OPERATORS = {
    ">": "GREATER_THAN",
    "<": "LESS_THAN",
    "=": "ASSIGN",
    "==": "EQUALS",
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
}

SYMBOLS = {
    ":": "COLON",
    ".": "DOT",
    "(": "LPAREN",
    ")": "RPAREN",
}


class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"{self.type}({self.value})"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.tokens = []

    def tokenize(self):
        words = self.text.replace("(", " ( ") \
                              .replace(")", " ) ") \
                              .replace(":", " : ") \
                              .replace(".", " . ") \
                              .split()

        i = 0

        while i < len(words):
            word = words[i]

            # Handle ==
            if word == "=" and i + 1 < len(words) and words[i + 1] == "=":
                self.tokens.append(Token("EQUALS", "=="))
                i += 2
                continue

            # Keywords
            if word in KEYWORDS:
                self.tokens.append(Token(KEYWORDS[word], word))

            # Operators
            elif word in OPERATORS:
                self.tokens.append(Token(OPERATORS[word], word))

            # Symbols
            elif word in SYMBOLS:
                self.tokens.append(Token(SYMBOLS[word], word))

            # Numbers
            elif word.isdigit():
                self.tokens.append(Token("NUMBER", int(word)))

            # Identifiers
            else:
                self.tokens.append(Token("IDENTIFIER", word))

            i += 1

        return self.tokens
