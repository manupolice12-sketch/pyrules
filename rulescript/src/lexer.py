KEYWORDS = {"rule", "when", "then", "use", "and", "or"}

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"{self.type}({self.value})"


class Lexer:
    def __init__(self, text):
        self.text = text

    def tokenize(self):
        tokens = []
        for line in self.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            word, _, rest = stripped.partition(" ")

            if word in KEYWORDS:
                tokens.append(Token(word.upper(), word))
                if rest:
                    tokens.append(Token("EXPR", rest.strip()))
            else:
                tokens.append(Token("EXPR", stripped))

        return tokens