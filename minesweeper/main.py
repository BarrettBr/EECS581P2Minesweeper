'''
main.py
Main Entry Point for Game that invokes Game_Manager.py
Author: Carlos Mbnedera, Mahdi Essawi
Last modified: 2025-09-17
'''

import argparse
import os
from config import ConfigScreen
from game_manager import GameManager

def parse_args():
    p = argparse.ArgumentParser(description="Minesweeper MVP")
    p.add_argument("--width", type=int, default=10)
    p.add_argument("--height", type=int, default=10)
    p.add_argument("--mines", type=int, default=15)
    p.add_argument("--cell-size", type=int, default=32, dest="cell_size")
    return p.parse_args()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    args = parse_args()
    configurer = ConfigScreen()
    mine_count, alg_complexity, alg_involvement = configurer.run() 
    game = GameManager(width=args.width, height=args.height, num_mines=mine_count, cell_size=args.cell_size, alg_involvement=alg_involvement, difficulty=alg_complexity)
    game.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
