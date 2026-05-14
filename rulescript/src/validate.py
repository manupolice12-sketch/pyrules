import os
import json
import sys

class Validator:
    def __init__(self, rules_data, search_path="."):
        self.rules_data = rules_data
        self.search_path = search_path
        self.errors = []

    def check_var_exists(self, obj_name):
        var_file = os.path.join(self.search_path, f"{obj_name}.var")
        if not os.path.exists(var_file):
            self.errors.append(f"MISSING_EXPORT: Object '{obj_name}' is used but no '{obj_name}.var' was found.")
            return None
        
        try:
            with open(var_file, 'r') as f:
                return json.load(f)
        except Exception:
            self.errors.append(f"READ_ERROR: Could not read metadata for '{obj_name}.var'.")
            return None

    def validate(self):
        for rule in self.rules_data:
            rule_name = rule.get("name", "Unknown Rule")
            full_logic = rule.get("condition", "") + " " + rule.get("action", "")
            tokens = full_logic.split()

            for i, token in enumerate(tokens):
                if token == "." and 0 < i < len(tokens) - 1:
                    obj_name = tokens[i-1]
                    attr_name = tokens[i+1]

                    metadata = self.check_var_exists(obj_name)
                    if not metadata:
                        continue

                    valid_attrs = metadata.get("attributes", [])
                    valid_methods = metadata.get("methods", [])
                    clean_attr = attr_name.split('(')[0]

                    if clean_attr not in valid_attrs and clean_attr not in valid_methods:
                        self.errors.append(f"UNDEFINED_PROPERTY: In rule '{rule_name}', '{obj_name}.{clean_attr}' does not exist.")
                        self.errors.append(f"    Available on '{obj_name}': {valid_attrs + valid_methods}")

        return len(self.errors) == 0

    def report(self):
        if self.errors:
            print("\n--- COMPILATION ERRORS ---")
            for err in self.errors:
                print(f"[!] {err}")
            print("--------------------------\n")
            sys.exit(1)
        else:
            sys.exit(0)    