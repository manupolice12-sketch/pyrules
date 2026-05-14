import argparse
import json
import sys
import os
from lexer import Lexer
from parser import Parser

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

    compiled_data = {
        "format": "rsc",
        "version": "1.0",
        "source": input_path,
        "rules": rules_data
    }

    with open(output_path, 'w') as f:
        json.dump(compiled_data, f, indent=4)

if __name__ == "__main__":
    main()