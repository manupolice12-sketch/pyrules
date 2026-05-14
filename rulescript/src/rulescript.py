import argparse
import json
import sys
import os
from lexer import Lexer
from parser import Parser
from validate import Validator

def main():
    arg_parser = argparse.ArgumentParser(description="RuleScript Compiler")
    arg_parser.add_argument("input", help="Source .rules file")
    arg_parser.add_argument("-o", "--output", help="Output .rsc file")
    args = arg_parser.parse_args()

    input_path = args.input
    output_path = args.output if args.output else input_path.rsplit('.', 1)[0] + ".rsc"

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' not found.")

    with open(input_path, 'r') as f:
        source_code = f.read()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    rules_data = parser.parse()
    validator = Validator(rules_data, search_path=os.path.dirname(input_path))
    if not validator.validate():
        validator.report()  
    compiled_data = {
        "format": "rsc",
        "source": input_path,
        "rules": rules_data
    }

    with open(output_path, 'w') as f:
        json.dump(compiled_data, f, indent=4)
        print(f"Compiled '{input_path}' to '{output_path}' successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()