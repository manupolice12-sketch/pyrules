import os
import json

class Validator:
    def __init__(self, rules_data, search_path="."):
        self.rules_data = rules_data
        self.search_path = search_path
        self.errors = []
        self.cached_vars = {}

    def get_var_metadata(self, obj_name):
        if obj_name in self.cached_vars:
            return self.cached_vars[obj_name]
        
        var_file = os.path.join(self.search_path, f"{obj_name}.var")
        if not os.path.exists(var_file):
            self.errors.append(f"MISSING_EXPORT: Object '{obj_name}' has no .var file.")
            return None
        
        try:
            with open(var_file, 'r') as f:
                data = json.load(f)
                self.cached_vars[obj_name] = data
                return data
        except:
            return None

    def walk_ast(self, node, rule_name):
        if not isinstance(node, dict):
            return

        if node.get("type") == "attribute_access":
            obj_node = node.get("object", {})
            if obj_node.get("type") == "variable":
                obj_name = obj_node.get("id")
                prop_name = node.get("property")
                
                metadata = self.get_var_metadata(obj_name)
                if metadata:
                    valid_items = metadata.get("attributes", []) + metadata.get("methods", [])
                    if prop_name not in valid_items:
                        self.errors.append(f"UNDEFINED_PROPERTY: '{obj_name}.{prop_name}' in rule '{rule_name}'")

        for key, value in node.items():
            if isinstance(value, dict):
                self.walk_ast(value, rule_name)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.walk_ast(item, rule_name)

    def validate(self):
        for rule in self.rules_data:
            name = rule.get("name", "Unknown")
            self.walk_ast(rule.get("condition", {}), name)
            self.walk_ast(rule.get("action", {}), name)
        return len(self.errors) == 0

    def report(self):
        if self.errors:
            for err in self.errors:
                raise Exception(f"[!] {err}")
            