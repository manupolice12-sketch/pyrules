import ast
import re

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def ast_to_dict(self, node):
        if isinstance(node, ast.Module):
            if node.body:
                return self.ast_to_dict(node.body[0])
            return {}
        elif isinstance(node, ast.Expression):
            return self.ast_to_dict(node.body)
        elif isinstance(node, ast.Expr):
            return self.ast_to_dict(node.value)
        elif isinstance(node, ast.BoolOp):
            return {
                "type": "bool_op",
                "operator": type(node.op).__name__,
                "values": [self.ast_to_dict(v) for v in node.values]
            }
        elif isinstance(node, ast.BinOp):
            return {
                "type": "binary_operation",
                "left": self.ast_to_dict(node.left),
                "op": type(node.op).__name__,
                "right": self.ast_to_dict(node.right)
            }
        elif isinstance(node, ast.Compare):
            return {
                "type": "comparison",
                "left": self.ast_to_dict(node.left),
                "operator": type(node.ops[0]).__name__,
                "right": self.ast_to_dict(node.comparators[0])
            }
        elif isinstance(node, ast.Attribute):
            return {
                "type": "attribute_access",
                "object": self.ast_to_dict(node.value),
                "property": node.attr
            }
        elif isinstance(node, ast.Name):
            return {"type": "variable", "id": node.id}
        elif isinstance(node, ast.Constant):
            return {"type": "literal", "value": node.value}
        elif isinstance(node, ast.Call):
            return {
                "type": "method_call",
                "func": self.ast_to_dict(node.func),
                "args": [self.ast_to_dict(arg) for arg in node.args]
            }
        elif isinstance(node, ast.Assign):
            return {
                "type": "assignment",
                "target": self.ast_to_dict(node.targets[0]),
                "value": self.ast_to_dict(node.value)
            }
        return str(node)

    def parse_logic_block(self, stop_tokens):
        content = []
        while self.current_token() and self.current_token().type not in stop_tokens:
            content.append(str(self.current_token().value))
            self.advance()

        raw_string = " ".join(content).strip()
        try:
            mode = 'exec' if re.search(r'(?<!=)=(?!=)', raw_string) else 'eval'
            tree = ast.parse(raw_string, mode=mode)
            return self.ast_to_dict(tree)
        except Exception:
            return {"type": "raw", "value": raw_string}

    def parse_rule(self):
        rule_data = {"name": "", "condition": {}, "action": {}}

        if self.current_token() and self.current_token().type == "RULE":
            self.advance()
            if self.current_token() and self.current_token().type == "IDENTIFIER":
                rule_data["name"] = self.current_token().value
                self.advance()

            while self.current_token() and self.current_token().type != "RULE":
                if self.current_token().type == "WHEN":
                    self.advance()
                    rule_data["condition"] = self.parse_logic_block(["THEN", "RULE"])
                elif self.current_token().type == "THEN":
                    self.advance()
                    rule_data["action"] = self.parse_logic_block(["WHEN", "RULE"])
                else:
                    self.advance()

        return rule_data

    def parse(self):
        rules = []
        while self.current_token():
            if self.current_token().type == "RULE":
                rules.append(self.parse_rule())
            else:
                self.advance()
        return rules
