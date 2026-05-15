"""
validate.py — RuleScript semantic analysis pass

Walks the normalized IR and enforces semantic contracts defined in
.var files. Supports both v1.0 (flat attribute lists) and v2.0
(typed field/method schemas) .var formats.

Semantic checks performed:
  - Field existence and type compatibility
  - Readonly field assignment enforcement
  - Method existence, argument count, and argument types
"""

import os
import json
from typing import List, Optional, Dict, Any

from errors import ValidationError, InternalCompilerError


PRIMITIVE_TYPES = {"int", "float", "string", "bool", "void", "any"}

# Type compatibility table. A value of type `actual` is compatible with
# an expected type if `actual` appears in the expected type's set.
_TYPE_COMPAT: Dict[str, set] = {
    "int":    {"int", "float", "any"},
    "float":  {"int", "float", "any"},
    "string": {"string", "any"},
    "bool":   {"bool", "any"},
    "void":   set(),
    "any":    PRIMITIVE_TYPES,
}


def types_compatible(expected: str, actual: str) -> bool:
    """Return True if a value of type `actual` satisfies type `expected`."""
    if expected == "any" or actual == "any":
        return True
    return actual in _TYPE_COMPAT.get(expected, set())


class Validator:
    def __init__(self, rules_data: List[Dict[str, Any]], search_path: str = "."):
        self.rules_data = rules_data
        self.search_path = search_path
        self.errors: List[ValidationError] = []
        self._var_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # .var loading
    # ------------------------------------------------------------------

    def _load_var(self, obj_name: str) -> Optional[Dict[str, Any]]:
        """Load a .var file and normalise it to the v2.0 internal format."""
        var_file = os.path.join(self.search_path, f"{obj_name}.var")
        if not os.path.exists(var_file):
            self.errors.append(ValidationError(
                code="MISSING_VAR",
                message=f"No .var file found for object '{obj_name}' (expected: {var_file})",
            ))
            return None

        try:
            with open(var_file, "r") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(ValidationError(
                code="INVALID_VAR",
                message=f".var file for '{obj_name}' is not valid JSON: {e}",
            ))
            return None

        return self._normalise_var(raw, obj_name)

    def _normalise_var(self, raw: Dict, obj_name: str) -> Dict[str, Any]:
        """Normalise v1.0 and v2.0 .var files into a unified internal schema.

        v1.0 files used flat lists: {"attributes": [...], "methods": [...]}.
        These are promoted to v2.0 with type="any" so old .var files continue
        to work without modification.
        """
        if raw.get("version", "1.0") == "1.0" or "attributes" in raw:
            fields = {
                name: {"type": "any", "nullable": False, "readonly": False}
                for name in raw.get("attributes", [])
            }
            methods = {
                name: {"params": [], "returns": "any"}
                for name in raw.get("methods", [])
            }
            return {"fields": fields, "methods": methods}

        fields = {}
        for fname, fdef in raw.get("fields", {}).items():
            ftype = fdef.get("type", "any")
            if ftype not in PRIMITIVE_TYPES:
                self.errors.append(ValidationError(
                    code="UNKNOWN_TYPE",
                    message=f"Unknown type '{ftype}' for field '{obj_name}.{fname}'",
                ))
            fields[fname] = {
                "type":     ftype,
                "nullable": fdef.get("nullable", False),
                "readonly": fdef.get("readonly", False),
            }

        methods = {}
        for mname, mdef in raw.get("methods", {}).items():
            params = mdef.get("params", [])
            returns = mdef.get("returns", "void")
            for i, p in enumerate(params):
                if p not in PRIMITIVE_TYPES:
                    self.errors.append(ValidationError(
                        code="UNKNOWN_TYPE",
                        message=f"Unknown param type '{p}' at position {i} of '{obj_name}.{mname}()'",
                    ))
            if returns not in PRIMITIVE_TYPES | {"void"}:
                self.errors.append(ValidationError(
                    code="UNKNOWN_TYPE",
                    message=f"Unknown return type '{returns}' for '{obj_name}.{mname}()'",
                ))
            methods[mname] = {"params": params, "returns": returns}

        return {"fields": fields, "methods": methods}

    def get_var_metadata(self, obj_name: str) -> Optional[Dict[str, Any]]:
        if obj_name not in self._var_cache:
            self._var_cache[obj_name] = self._load_var(obj_name)
        return self._var_cache[obj_name]

    # ------------------------------------------------------------------
    # Type inference
    # ------------------------------------------------------------------

    def infer_type(self, node: Dict[str, Any]) -> Optional[str]:
        """Derive a RuleScript primitive type from an IR node.

        Returns "any" when the type cannot be statically determined,
        rather than failing — type inference is best-effort at this stage.
        """
        if not isinstance(node, dict):
            return None

        ntype = node.get("type")

        if ntype == "literal":
            value = node.get("value")
            if isinstance(value, bool):   return "bool"
            if isinstance(value, int):    return "int"
            if isinstance(value, float):  return "float"
            if isinstance(value, str):    return "string"
            return "any"

        if ntype == "variable":
            return "any"

        if ntype == "attribute_access":
            obj_node = node.get("object", {})
            if obj_node.get("type") == "variable":
                meta = self.get_var_metadata(obj_node.get("id", ""))
                if meta:
                    field = meta["fields"].get(node.get("property", ""))
                    if field:
                        return field["type"]
            return "any"

        if ntype == "method_call":
            func_node = node.get("func", {})
            if func_node.get("type") == "attribute_access":
                obj_node = func_node.get("object", {})
                if obj_node.get("type") == "variable":
                    meta = self.get_var_metadata(obj_node.get("id", ""))
                    if meta:
                        method = meta["methods"].get(func_node.get("property", ""))
                        if method:
                            return method["returns"]
            return "any"

        if ntype in ("comparison", "bool_op", "unary_op"):
            return "bool"

        if ntype == "binary_operation":
            left_type  = self.infer_type(node.get("left", {}))
            right_type = self.infer_type(node.get("right", {}))
            if left_type == "float" or right_type == "float":
                return "float"
            if left_type == "int" and right_type == "int":
                return "int"
            return "any"

        return "any"

    # ------------------------------------------------------------------
    # Semantic checks
    # ------------------------------------------------------------------

    def walk_ast(self, node: Any, rule_name: str) -> None:
        if not isinstance(node, dict):
            return

        ntype = node.get("type")

        if ntype == "attribute_access":
            self._check_attribute_access(node, rule_name)
        elif ntype == "method_call":
            self._check_method_call(node, rule_name)
        elif ntype == "assignment":
            self._check_assignment(node, rule_name)

        for value in node.values():
            if isinstance(value, dict):
                self.walk_ast(value, rule_name)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.walk_ast(item, rule_name)

    def _check_attribute_access(self, node: Dict, rule_name: str) -> None:
        obj_node = node.get("object", {})
        if obj_node.get("type") != "variable":
            return
        obj_name  = obj_node.get("id", "")
        prop_name = node.get("property", "")
        meta = self.get_var_metadata(obj_name)
        if meta and prop_name not in meta["fields"]:
            self.errors.append(ValidationError(
                code="UNDEFINED_FIELD",
                message=f"'{obj_name}.{prop_name}' is not a declared field of '{obj_name}'",
                rule_name=rule_name,
            ))

    def _check_method_call(self, node: Dict, rule_name: str) -> None:
        func_node = node.get("func", {})
        if func_node.get("type") != "attribute_access":
            return
        obj_node = func_node.get("object", {})
        if obj_node.get("type") != "variable":
            return

        obj_name    = obj_node.get("id", "")
        method_name = func_node.get("property", "")
        args        = node.get("args", [])
        meta        = self.get_var_metadata(obj_name)
        if meta is None:
            return

        method_def = meta["methods"].get(method_name)
        if method_def is None:
            self.errors.append(ValidationError(
                code="UNDEFINED_METHOD",
                message=f"'{obj_name}.{method_name}()' is not a declared method of '{obj_name}'",
                rule_name=rule_name,
            ))
            return

        expected_count = len(method_def["params"])
        if len(args) != expected_count:
            self.errors.append(ValidationError(
                code="WRONG_ARG_COUNT",
                message=(
                    f"'{obj_name}.{method_name}()' expects {expected_count} argument(s), "
                    f"got {len(args)}"
                ),
                rule_name=rule_name,
            ))
            return

        for i, (param_type, arg_node) in enumerate(zip(method_def["params"], args)):
            arg_type = self.infer_type(arg_node)
            if arg_type and arg_type != "any" and not types_compatible(param_type, arg_type):
                self.errors.append(ValidationError(
                    code="TYPE_MISMATCH",
                    message=(
                        f"Argument {i + 1} of '{obj_name}.{method_name}()' expects "
                        f"'{param_type}', got '{arg_type}'"
                    ),
                    rule_name=rule_name,
                ))

    def _check_assignment(self, node: Dict, rule_name: str) -> None:
        target = node.get("target", {})
        value  = node.get("value", {})

        if target.get("type") != "attribute_access":
            return
        obj_node = target.get("object", {})
        if obj_node.get("type") != "variable":
            return

        obj_name   = obj_node.get("id", "")
        field_name = target.get("property", "")
        meta       = self.get_var_metadata(obj_name)
        if meta is None:
            return

        field_def = meta["fields"].get(field_name)
        if field_def is None:
            return  # Already reported by _check_attribute_access

        if field_def.get("readonly", False):
            self.errors.append(ValidationError(
                code="READONLY_FIELD",
                message=f"'{obj_name}.{field_name}' is readonly and cannot be assigned",
                rule_name=rule_name,
            ))
            return

        expected_type = field_def["type"]
        actual_type   = self.infer_type(value)
        if (
            actual_type
            and actual_type != "any"
            and expected_type != "any"
            and not types_compatible(expected_type, actual_type)
        ):
            self.errors.append(ValidationError(
                code="TYPE_MISMATCH",
                message=(
                    f"Cannot assign '{actual_type}' to '{obj_name}.{field_name}' "
                    f"(declared as '{expected_type}')"
                ),
                rule_name=rule_name,
            ))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        for rule in self.rules_data:
            name = rule.get("name") or "Unnamed"
            self.walk_ast(rule.get("condition", {}), name)
            self.walk_ast(rule.get("action", {}), name)
        return len(self.errors) == 0

    def report(self) -> None:
        for err in self.errors:
            print(f"[!] {err}")
        if self.errors:
            raise ValidationError(
                code="VALIDATION_FAILED",
                message=f"{len(self.errors)} error(s) found",
            )
