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
    "==": "EQUALS",
    ">": "GREATER_THAN",
    "<": "LESS_THAN",
    "=": "ASSIGN",
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
                         .replace("==", " == ") \
                         .replace(">=", " >= ") \
                         .replace("<=", " <= ") \
                         .split()

        for word in words:
            if word in KEYWORDS:
                self.tokens.append(Token(KEYWORDS[word], word))
            elif word in OPERATORS:
                self.tokens.append(Token(OPERATORS[word], word))
            elif word in SYMBOLS:
                self.tokens.append(Token(SYMBOLS[word], word))
            elif word.lstrip("-").isdigit():
                self.tokens.append(Token("NUMBER", int(word)))
            else:
                self.tokens.append(Token("IDENTIFIER", word))

        return self.tokens
