import argparse
import json
import sys
import os

from lexer import Lexer
from parser import Parser
from validate import Validator
from errors import CompilerError, LexError, ParseError, ValidationError, InternalCompilerError


def main():
    arg_parser = argparse.ArgumentParser(description="RuleScript Compiler — .rules -> .rsc")
    arg_parser.add_argument("input", help="Source .rules file")
    arg_parser.add_argument("-o", "--output", help="Output .rsc file")
    args = arg_parser.parse_args()

    input_path = args.input
    output_path = (
        args.output if args.output
        else input_path.rsplit(".", 1)[0] + ".rsc"
    )

    if not os.path.exists(input_path):
        print(f"[error] Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r") as f:
        source_code = f.read()

    try:
        # --- Lex ---
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        # --- Parse ---
        parser = Parser(tokens)
        rules_data = parser.parse()

        # --- Validate ---
        validator = Validator(
            rules_data,
            search_path=os.path.dirname(os.path.abspath(input_path)),
        )
        if not validator.validate():
            validator.report()
            sys.exit(1)

    except LexError as e:
        print(f"[lex error] {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"[parse error] {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"[validation error] {e}", file=sys.stderr)
        sys.exit(1)
    except InternalCompilerError as e:
        print(f"[internal compiler error] {e}", file=sys.stderr)
        print("This is a compiler bug. Please report it.", file=sys.stderr)
        sys.exit(2)
    except CompilerError as e:
        print(f"[compiler error] {e}", file=sys.stderr)
        sys.exit(1)

    # --- Emit IR ---
    compiled_data = {
        "format": "rsc",
        "version": "1.0",
        "source": input_path,
        "rules": rules_data,
    }

    try:
        with open(output_path, "w") as f:
            json.dump(compiled_data, f, indent=4)
    except IOError as e:
        print(f"[error] Could not write '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Compiled '{input_path}' -> '{output_path}' successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
