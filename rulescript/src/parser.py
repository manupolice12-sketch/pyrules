class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def parse(self):
        rules = []

        while self.current_token() is not None:
            token = self.current_token()

            if token.type == "RULE":
                rules.append(self.parse_rule())
            else:
                self.advance()

        return rules

    def parse_rule(self):
        self.advance()  
        name_token = self.current_token()
        rule_name = name_token.value
        self.advance()
        if self.current_token() and self.current_token().type == "COLON":
            self.advance()

        condition = None
        action = None

        while self.current_token() is not None:
            token = self.current_token()

            if token.type == "WHEN":
                self.advance()

                condition_parts = []

                while (
                    self.current_token() is not None
                    and self.current_token().type != "THEN"
                ):
                    condition_parts.append(str(self.current_token().value))
                    self.advance()

                condition = " ".join(condition_parts)

            elif token.type == "THEN":
                self.advance()

                if self.current_token() and self.current_token().type == "COLON":
                    self.advance()

                action_parts = []

                while (
                    self.current_token() is not None
                    and self.current_token().type != "RULE"
                ):
                    action_parts.append(str(self.current_token().value))
                    self.advance()

                action = " ".join(action_parts)
                break

            else:
                self.advance()

        return {
            "type": "rule",
            "name": rule_name,
            "condition": condition,
            "action": action
        }
