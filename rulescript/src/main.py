# rulescript/main.py

from lexer import Lexer
from parser import Parser


code = """
use player

rule low_health_jump:
    when player . hp < 20 and player . on_ground
    then:
        player . jump ( )

rule speed_boost:
    when player . score > 100
    then:
        player . speed = player . speed + 2
"""


# STEP 1: TOKENIZE
lexer = Lexer(code)
tokens = lexer.tokenize()

print("=== TOKENS ===")

for token in tokens:
    print(token)


# STEP 2: PARSE
parser = Parser(tokens)
rules = parser.parse()

print("\n=== PARSED RULES ===")

for rule in rules:
    print(rule)