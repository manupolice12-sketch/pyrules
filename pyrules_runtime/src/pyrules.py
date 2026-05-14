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

    def export(self, obj_name, obj, output_dir="."):
        members = dir(obj)
        public_members = [m for m in members if not m.startswith("_")]

        attributes = []
        methods = []

        for name in public_members:
            attr = getattr(obj, name)
            if inspect.ismethod(attr) or inspect.isfunction(attr):
                methods.append(name)
            else:
                attributes.append(name)

        metadata = {
            "name": obj_name,
            "attributes": attributes,
            "methods": methods
        }

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_path = os.path.join(output_dir, f"{obj_name}.var")
        with open(file_path, "w") as f:
            json.dump(metadata, f, indent=4)

        return file_path

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
            op = node.get("operator")

            ops = {
                "Lt": lambda a, b: a < b,
                "Gt": lambda a, b: a > b,
                "Eq": lambda a, b: a == b,
                "NotEq": lambda a, b: a != b
            }
            return ops[op](left, right) if op in ops else False

        elif node_type == "bool_op":
            values = [self.resolve(v) for v in node.get("values", [])]
            return all(values) if node.get("operator") == "And" else any(values)

        return None

    def apply(self, node):
        if not node:
            return
        node_type = node.get("type")

        if node_type == "assignment":
            target_node = node.get("target")
            obj = self.resolve(target_node.get("object"))
            new_val = self.resolve(node.get("value"))
            setattr(obj, target_node.get("property"), new_val)

        elif node_type == "method_call":
            target = self.resolve(node.get("func").get("object"))
            method = getattr(target, node.get("func").get("property"))
            args = [self.resolve(arg) for arg in node.get("args", [])]
            method(*args)

    def tick(self):
        for rule in self.rules:
            if self.resolve(rule.get("condition")):
                self.apply(rule.get("action"))
