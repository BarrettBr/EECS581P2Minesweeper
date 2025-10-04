'''
Game Manager
Manages the state of the game and calls the other .py files that were written by team mates
Author: Carlos Mbnedera, Mahdi Essawi
Last modified: 2025-09-18

Classes, Inputs and Outputs

BoardAdapter: wraps Board for renderer (width/height, get_cell, reveal/flag, won/lost)
GameManager: pygame loop (init -> input -> update -> render -> quit)
Inputs: width:int, height:int, num_mines:int, cell_size:int (pixels)
Outputs: visuals

Sources: (Carlos) Pygame Example Implementations of Minesweeper 
Multiple tutorials found at https://www.pygame.org/
'''

import pygame
import sys
import os
import shutil
import random

from board import Board, GameState as BoardGameState
from input_handler import InputHandler
from renderer import Renderer

class BoardAdapter:
    def __init__(self, core_board: Board):
        self._core = core_board
        # Provide width/height attributes the renderer expects
        self.width = core_board.cols
        self.height = core_board.rows

    def get_cell(self, x: int, y: int):
        # Renderer passes (col=x, row=y). Board indexes as [row][col].
        if 0 <= y < self._core.rows and 0 <= x < self._core.cols:
            cell = self._core[y][x]
            if not hasattr(cell, "clicked"):
                # Alias clicked -> exploded (clicked mine on loss)
                setattr(cell, "clicked", getattr(cell, "exploded", False))
            return cell
        return None

    # Delegated actions used by manager
    def reveal_cell(self, x: int, y: int):
        if 0 <= y < self._core.rows and 0 <= x < self._core.cols:
            self._core.reveal_cell(y, x)  # Board expects (row, col)

    def toggle_flag(self, x: int, y: int):
        if 0 <= y < self._core.rows and 0 <= x < self._core.cols:
            self._core.toggle_flag(y, x)

    def is_game_over(self) -> bool:
        return self._core.state == BoardGameState.LOST

    def is_game_won(self) -> bool:
        return self._core.state == BoardGameState.WON

    # Simple state probes used by manager
    def lost(self) -> bool:
        return self._core.state == BoardGameState.LOST
    def won(self) -> bool:
        return self._core.state == BoardGameState.WON


class GameManager:
    """Manager: input -> board mutate -> render."""
    def __init__(self, width: int, height: int , num_mines: int, 
                 cell_size: int, alg_involvement: str="None", difficulty: str="Easy"):
        """
          Three newly added variables used to track alg_involvement/difficulty, currently stored as strs as shown
          however this can change just used for easy placeholders for now
          alg_involvement: str "None", "Assisted", "Full Auto" 
          difficulty: str "Easy", "Medium", "Hard"
        """
        self.alg_involvement = alg_involvement
        self.difficulty = difficulty
        self.board_width = width
        self.board_height = height
        self.num_mines = num_mines
        self.cell_size = cell_size
        self.padding_right = 40
        self.padding_bottom = 80
        self.screen_width = width * cell_size + self.padding_right
        self.screen_height = height * cell_size + self.padding_bottom

        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Minesweeper")
        self.clock = pygame.time.Clock()
        self.running = True
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize the core board, adapter, input handler, and renderer."""
        # Ensure expected image filename used by renderer exists (renderer expects bomb-at-clicked-spot.png)
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        expected = os.path.join(images_dir, "bomb-at-clicked-spot.png")
        alt = os.path.join(images_dir, "bomb-at-clicked-block.png")
        if not os.path.exists(expected) and os.path.exists(alt):
          try:
            shutil.copyfile(alt, expected)
          except Exception:
            #renderer may still fail but we tried
            pass

        core_board = Board(self.board_height, self.board_width, self.num_mines)
        self.board = BoardAdapter(core_board)
        self.input_handler = InputHandler(cell_size=self.cell_size, board_offset_y=0)
        self.renderer = Renderer(self.screen, self.cell_size)
    
    def start_new_game(self):
        core_board = Board(self.board_height, self.board_width, self.num_mines)
        self.board = BoardAdapter(core_board)
    
    def handle_input(self):
        """Handle all input events through the InputHandler."""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Handle restart key (R)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

        # Might not need lost/win check cause it is also done after so just added for robustness for now        
        if self.turn != "human" or self.board.lost() or self.board.won():
            return

        # Delegate input handling to InputHandler
        action = self.input_handler.handle_events(events)
        
        if action and not (self.board.lost() or self.board.won()):
            self._process_game_action(action)
    
    def _process_game_action(self, action):
        """
        Process game actions from input handler
        Can call directly to simulate a flag/reveal
        Action: dict: { 'type': 'reveal'|'flag', 'x': int, 'y': int } or None
          x and y are the grid col/row stored as an int, a player gets called to
          handle_input and that turns their click into the x/y bit a bot would pass this value directly into this
        """
        if not action:
            return
        
        action_type = action.get('type')
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        if action_type == 'reveal':
            self.board.reveal_cell(x, y)
        elif action_type == 'flag':
            self.board.toggle_flag(x, y)

    def _process_game_action_bot(self, action):
        """
        Process game actions from input handler
        Can call directly to simulate a flag/reveal
        Action: dict: { 'type': 'reveal'|'flag', 'x': int, 'y': int } or None
          x and y are the grid col/row stored as an int, a player gets called to
          handle_input and that turns their click into the x/y bit a bot would pass this value directly into this
        """
        if not action:
            return
        
        action_type = action.get('type')
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        if action_type == 'reveal':
            self.board.reveal_cell(x, y)
        elif action_type == 'flag':
            self.board.toggle_flag(x, y)

        if self.alg_involvement == "Assisted":
            self._bot_turn()

    def _bot_turn(self):
        print("Bot")
        if self.board.is_game_over() or self.board.is_game_won():
            self.running = False
            return
        match self.difficulty:
            case "Easy":
                self.ez_turn()
            case "Medium":
                self.med_turn()
            case "Hard":
                self.hard_turn()
            case _:
                self.running = False


    def ez_turn(self):
        pass
    
    def med_turn(self):
        # Look for safe moves or mines
        for y in range(self.board.height):
            for x in range(self.board.width):
                cell = self.board.get_cell(x, y)
                if not cell or not cell.revealed or cell.count == 0:
                    continue

                # Collect neighbors
                neighbors = [(nx, ny) for nx in range(x-1, x+2)
                                       for ny in range(y-1, y+2)
                                       if (nx, ny) != (x, y)
                                       and 0 <= nx < self.board.width
                                       and 0 <= ny < self.board.height]

                unrevealed = []
                flagged = 0
                for nx, ny in neighbors:
                    ncell = self.board.get_cell(nx, ny)
                    if ncell.flagged:
                        flagged += 1
                    elif not ncell.revealed:
                        unrevealed.append((nx, ny))

                # all unrevealed must be mines → flag them
                if cell.count - flagged == len(unrevealed) and unrevealed:
                    ux, uy = random.choice(unrevealed)
                    action = {"type": "flag", "x": ux, "y": uy}
                    self._process_game_action_bot(action) 
                    return  

                # all unrevealed must be safe → reveal one
                if flagged == cell.count and unrevealed:
                    ux, uy = random.choice(unrevealed)
                    action = {"type": "flag", "x": ux, "y": uy}
                    self._process_game_action_bot(action) 
                    return  

        # Random guess (last ditch effort)
        choices = [(x, y) for y in range(self.board.height)
                           for x in range(self.board.width)
                           if not self.board.get_cell(x, y).revealed
                           and not self.board.get_cell(x, y).flagged]
        if choices:
            x, y = random.choice(choices)
            action = {"type": "flag", "x": x, "y": y}
            self._process_game_action_bot(action) 

    
    def hard_turn(self):
        pass

    # this looks for 1-2-1 patterns on the board
    # if a mine is found, flag it and return true, 
    # otherwise, return false
    def _pattern_121(self): 
        grid_height = self.board.height
        grid_width = self.board.width

        # looks for the horizontal 1-2-1 pattern
        for row in range(grid_height):
            for col in range(1, grid_width - 1): 
                cell_left = self.board.get_cell(col - 1, row) 
                cell_middle = self.board.get_cell(col, row)
                cell_right = self.board.get_cell(col + 1, row) 
                if not (cell_left and cell_middle and cell_right): 
                    continue
                if (cell_left.revealed and cell_left.count == 1 and
                    cell_middle.revealed and cell_middle.count == 2 and 
                    cell_right.revealed and cell_right.count == 1): 
                    
                    # check the covered row above this one
                    if row > 0: 
                        row_above = [(col - 1, row - 1), (col, row - 1), (col + 1, row - 1)]
                        hidden_cells = all(not self.board.get_cell(c, r).revealed for c, r in row_above) 

                        if hidden_cells: 
                            mine_col, mine_row = row_above[1]
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action = {"type": "flag", "x": mine_col, "y": mine_row}
                                self._process_game_action_bot(action)  
                                return True
                    
                    # check the covered row below this one
                    if row < grid_height - 1: 
                        row_below = [(col - 1, row + 1), (col, row + 1), (col + 1, row + 1)] 
                        hidden_cells = all(not self.board.get_cell(c, r).revealed for c, r in row_below)
                        
                        if hidden_cells: 
                            mine_col, mine_row = row_below[1] 
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action = {"type": "flag", "x": mine_col, "y": mine_row}
                                self._process_game_action_bot(action)   
                                return True
                            
        # looks for the vertical 1-2-1 pattern
        for row in range(1, grid_height - 1): 
            for col in range(grid_width): 
                cell_top = self.board.get_cell(col, row - 1)
                cell_middle = self.board.get_cell(col, row)
                cell_bottom = self.board.get_cell(col, row + 1)
                if not (cell_bottom and cell_middle and cell_top): 
                    continue
                if (cell_top.revealed and cell_top.count == 1 and 
                    cell_middle.revealed and cell_middle.count == 2 and 
                    cell_bottom.revealed and cell_bottom.count == 1): 

                    # check the covered column to the left
                    if col > 0: 
                        to_left = [(col - 1, row - 1), (col - 1, row), (col - 1, row + 1)]
                        hidden_cells = all(not self.board.get_cell(c, r).revealed for c, r in to_left)
                        
                        if hidden_cells: 
                            mine_col, mine_row = to_left[1]
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action = {"type": "flag", "x": mine_col, "y": mine_row} 
                                self._process_game_action_bot(action)  
                                return True

                    # check the covered column to the right
                    if col < grid_width - 1:
                        to_right = [(col + 1, row - 1), (col + 1, row), (col + 1, row + 1)] 
                        hidden_cells = all(self.board.get_cell(c, r).revealed for c, r in to_right)

                        if hidden_cells: 
                            mine_col, mine_row = to_right[1]
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action = {"type": "flag", "x": mine_col, "y": mine_row}
                                self._process_game_action_bot(action)  
                                return True       
        # no 1-2-1 pattern found
        return False                              
    
    def update(self):
        pass  
    
    def render(self):
        """Render the game using the Renderer."""
        # Clear screen
        self.screen.fill((192, 192, 192))  # Light gray background
        
        # Render board
        self.renderer.render_board(self.board)
        
        if self.board.won():
            self.renderer.render_game_over(won=True)
        elif self.board.lost():
            self.renderer.render_game_over(won=False)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """
        Main game loop.
        
        This method contains the core game loop that handles input,
        updates game state, and renders the game.
        """
        print("The Greatest Game of Minesweeper: LMB=reveal RMB=flag R=restart ESC=quit")
        if self.alg_involvement == "Full Auto":
            while self.running:
              self._bot_turn()
              self.update()
              self.render()
              self.clock.tick(60)
            self.quit()

        while self.running:
            self.handle_input()
            self.update()
            self.render()
            self.clock.tick(60)
        self.quit()
    
    def quit(self):
        """Clean up and quit the game."""
        print("Shutting down Minesweeper...")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Create and run a game instance for testing
    game = GameManager(width=10, height=10, num_mines=15)
    game.run()
