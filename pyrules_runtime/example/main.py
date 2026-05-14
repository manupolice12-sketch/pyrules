import os
import json
from ..src.pyrules import RuleEngine

class Player:
    def __init__(self):
        self.hp = 15
        self.on_ground = True
        self.speed = 5
        self.score = 0
    
    def jump(self):
        print("ACTION: Player Jump")

class Enemy:
    def distance(self, target):
        return 50
    
    def attack(self, target):
        print("ACTION: Enemy Attack")

class Game:
    def end(self):
        print("ACTION: Game Over")

def main():
    player = Player()
    enemy = Enemy()
    game = Game()

    context = {
        "player": player,
        "enemy": enemy,
        "game": game
    }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    example_dir = os.path.join(project_root, "rulescript", "example")
    rsc_path = os.path.join(example_dir, "test.rsc")

    engine = RuleEngine(game_context=context)

    engine.export("player", player, output_dir=example_dir)
    engine.export("enemy", enemy, output_dir=example_dir)
    engine.export("game", game, output_dir=example_dir)

    if os.path.exists(rsc_path):
        with open(rsc_path, 'r') as f:
            data = json.load(f)
            engine.rules = data.get("rules", [])
        
        engine.tick()
    else:
        print(f"File not found: {rsc_path}")

if __name__ == "__main__":
    main()