import json
import inspect
import os

class RuleEngine:
    def __init__(self, rsc_path=None, game_context=None):
        self.rules = []
        if rsc_path and os.path.exists(rsc_path):
            with open(rsc_path, 'r') as f:
                data = json.load(f)
                self.rules = data.get("rules", [])
        self.context = game_context if game_context else {}

    def resolve(self, node):
        if not isinstance(node, dict):
            return node

        node_type = node.get("type")

        if node_type == "literal":
            return node.get("value")

        elif node_type == "variable":
            return self.context.get(node.get("id"))

        elif node_type == "attribute_access":
            target = self.resolve(node.get("object"))
            return getattr(target, node.get("property"))

        elif node_type == "comparison":
            left = self.resolve(node.get("left"))
            right = self.resolve(node.get("right"))
            op = node.get("operator") # Parser now uses 'operator'
            ops = {
                "<":  lambda a, b: a < b,
                ">":  lambda a, b: a > b,
                "==": lambda a, b: a == b,
                "!=": lambda a, b: a != b,
                "<=": lambda a, b: a <= b,
                ">=": lambda a, b: a >= b,
            }
            return ops[op](left, right) if op in ops else False

        elif node_type == "bool_op":
            values = [self.resolve(v) for v in node.get("values", [])]
            op = node.get("operator")
            return all(values) if op == "and" else any(values)

        return None

    def apply(self, node):
        """Executes actions based on the normalized IR."""
        if not node:
            return
        node_type = node.get("type")

        if node_type == "assignment":
            target_node = node.get("target")
            obj = self.resolve(target_node.get("object"))
            new_val = self.resolve(node.get("value"))
            setattr(obj, target_node.get("property"), new_val)

        elif node_type == "method_call":
            func_node = node.get("func")
            target = self.resolve(func_node.get("object"))
            method = getattr(target, func_node.get("property"))
            args = [self.resolve(arg) for arg in node.get("args", [])]
            method(*args)

    def tick(self):
        """Runs one cycle of the engine."""
        for rule in self.rules:
            if self.resolve(rule.get("condition")):
                self.apply(rule.get("action"))