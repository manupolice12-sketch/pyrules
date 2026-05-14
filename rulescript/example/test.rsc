{
    "format": "rsc",
    "source": "C:\\Users\\ASHIK\\Python\\pyrules\\rulescript\\example\\test.rule",
    "rules": [
        {
            "name": "low_health_jump",
            "condition": "BoolOp(op=And(), values=[Compare(left=Attribute(value=Name(...), attr='hp', ctx=Load(...)), ops=[Lt()], comparators=[Constant(value=20, kind=None)]), Attribute(value=Name(id='player', ctx=Load(...)), attr='on_ground', ctx=Load())])",
            "action": {
                "type": "raw",
                "value": ": player . jump ( )"
            }
        },
        {
            "name": "enemy_attack",
            "condition": {
                "type": "comparison",
                "left": {
                    "type": "method_call",
                    "func": {
                        "type": "attribute_access",
                        "object": {
                            "type": "variable",
                            "id": "enemy"
                        },
                        "property": "distance"
                    },
                    "args": [
                        {
                            "type": "variable",
                            "id": "player"
                        }
                    ]
                },
                "operator": "Lt",
                "right": {
                    "type": "literal",
                    "value": 100
                }
            },
            "action": {
                "type": "raw",
                "value": ": enemy . attack ( player )"
            }
        },
        {
            "name": "game_over",
            "condition": "[Expr(value=Compare(left=Attribute(value=Name(...), attr='hp', ctx=Load(...)), ops=[Eq()], comparators=[Constant(value=0, kind=None)]))]",
            "action": {
                "type": "raw",
                "value": ": game . end ( )"
            }
        },
        {
            "name": "score_bonus",
            "condition": {
                "type": "comparison",
                "left": {
                    "type": "attribute_access",
                    "object": {
                        "type": "variable",
                        "id": "player"
                    },
                    "property": "score"
                },
                "operator": "Gt",
                "right": {
                    "type": "literal",
                    "value": 100
                }
            },
            "action": {
                "type": "raw",
                "value": ": player . speed = player . speed + 2"
            }
        }
    ]
}