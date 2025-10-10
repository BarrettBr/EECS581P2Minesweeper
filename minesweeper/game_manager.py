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

import time
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
        self.turn = "human"
        self.start_time = time.time()
        self.board_width = width
        self.board_height = height
        self.num_mines = num_mines
        self.cell_size = cell_size
        self.padding_right = 40
        self.padding_bottom = 80
        self.screen_width = width * cell_size + self.padding_right
        self.screen_height = height * cell_size + self.padding_bottom
        self.arr = []

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
        self.sfx_win = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "sfx", "win.mp3"))
        self.sfx_lost = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "sfx", "lost.mp3"))
        self.sfx_played = False
    
    def start_new_game(self):
        core_board = Board(self.board_height, self.board_width, self.num_mines)
        self.board = BoardAdapter(core_board)
        self.start_time = time.time() # Used to reset the start time upon starting a new game
        self.sfx_played = False # Used to reset the ability to play a new SFX
    
    def handle_input(self):
        """Handle all input events through the InputHandler."""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return False

            # Handle restart key (R)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.start_new_game()
                    return False
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False

        # Might not need lost/win check cause it is also done after so just added for robustness for now        
        if self.turn != "human" or self.board.lost() or self.board.won():
            return False

        # Delegate input handling to InputHandler
        action = self.input_handler.handle_events(events)

        if action and not (self.board.lost() or self.board.won()):
            return self._process_game_action(action)
    
    def _process_game_action(self, action):
        """
        Process game actions from input handler
        Can call directly to simulate a flag/reveal
        Action: dict: { 'type': 'reveal'|'flag', 'x': int, 'y': int } or None
          x and y are the grid col/row stored as an int, a player gets called to
          handle_input and that turns their click into the x/y bit a bot would pass this value directly into this
        """
        if not action:
            return False
        
        action_type = action.get('type')
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        if action_type == 'reveal':
            self.board.reveal_cell(x, y)
            return True
        elif action_type == 'flag':
            self.board.toggle_flag(x, y)
            return True

    """
    Helper function that passes to the ez/med/hard func that controls it's turn,
    will return True/False from those functions to run to see if a turn was played or not so as to not flip turn needlisly

    Inputs: Nothing
    Output: Bool on whether a turn was played
    """
    def _bot_turn(self):
        # Base case to make sure we actually need to do a turn vs the game is done already
        if self.board.is_game_over() or self.board.is_game_won():
          return False
        # Switch statement that passes to the functions needed
        match self.difficulty:
          case "Easy":
            return self.ez_turn()
          case "Medium":
            return self.med_turn()
          case "Hard":
            # Does a pattern _121 move and if it isn't done then returns to a medium turn algo instead
            moved = self._pattern_121()
            if moved:
              return True
            return self.med_turn()
          case _:
            return False

    """
    Function that does the easy algorithm i.e: Choose a random cell and uncover it at random
    """
    def ez_turn(self):
        # Creates a list of all possible x/y values this board could have
        choices = [(x, y) for y in range(self.board.height)
                           for x in range(self.board.width)
                           if not self.board.get_cell(x, y).revealed
                           and not self.board.get_cell(x, y).flagged]
        # Makes sure there is a choice to make
        if choices:
            x, y = random.choice(choices) # Choose a random tuple from the choice and assign it to var x/y
            action = {"type": "reveal", "x": x, "y": y} # Create the dict object for the action needed
            return self._process_game_action(action) # Send this action to be processed/reflected on main board
        else:
            return False # If no choice can be made we return False for no turn played
    
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
                    return self._process_game_action(action) 

                # all unrevealed must be safe → reveal one
                if flagged == cell.count and unrevealed:
                    ux, uy = random.choice(unrevealed)
                    action = {"type": "reveal", "x": ux, "y": uy}
                    return self._process_game_action(action)   

        # Random guess (last ditch effort)
        return self.ez_turn()

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
                                action1 = {"type": "flag", "x": mine_col - 1, "y": mine_row}
                                action2 = {"type": "flag", "x": mine_col + 1, "y": mine_row}
                                if ((mine_col - 1, mine_row) in self.arr) and ((mine_col + 1, mine_row) in self.arr):
                                    return False
                                self.arr.append((mine_col - 1, mine_row)) 
                                self.arr.append((mine_col + 1, mine_row))
                                return self._process_game_action(action1) or self._process_game_action(action2)

                    # check the covered row below this one
                    if row < grid_height - 1: 
                        row_below = [(col - 1, row + 1), (col, row + 1), (col + 1, row + 1)] 
                        hidden_cells = all(not self.board.get_cell(c, r).revealed for c, r in row_below)
                        
                        if hidden_cells: 
                            mine_col, mine_row = row_below[1] 
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action1 = {"type": "flag", "x": mine_col - 1, "y": mine_row}
                                action2 = {"type": "flag", "x": mine_col + 1, "y": mine_row}
                                if ((mine_col - 1, mine_row) in self.arr) and ((mine_col + 1, mine_row) in self.arr):
                                    return False
                                self.arr.append((mine_col - 1, mine_row)) 
                                self.arr.append((mine_col + 1, mine_row))
                                return self._process_game_action(action1) or self._process_game_action(action2)
                            
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
                                action1 = {"type": "flag", "x": mine_col, "y": mine_row - 1} 
                                action2 = {"type": "flag", "x": mine_col, "y": mine_row + 1}
                                if ((mine_col, mine_row - 1) in self.arr) and ((mine_col + 1, mine_row + 1) in self.arr):
                                    return False
                                self.arr.append((mine_col, mine_row - 1)) 
                                self.arr.append((mine_col, mine_row + 1))
                                return self._process_game_action(action1) or self._process_game_action(action2)

                    # check the covered column to the right
                    if col < grid_width - 1:
                        to_right = [(col + 1, row - 1), (col + 1, row), (col + 1, row + 1)] 
                        hidden_cells = all(self.board.get_cell(c, r).revealed for c, r in to_right)

                        if hidden_cells: 
                            mine_col, mine_row = to_right[1]
                            candidate_cell = self.board.get_cell(mine_col, mine_row) 
                            if candidate_cell and not candidate_cell.flagged: 
                                action1 = {"type": "flag", "x": mine_col, "y": mine_row - 1}
                                action2 = {"type": "flag", "x": mine_col, "y": mine_row + 1}
                                if ((mine_col, mine_row - 1) in self.arr) and ((mine_col, mine_row + 1) in self.arr):
                                    return False
                                self.arr.append((mine_col, mine_row - 1)) 
                                self.arr.append((mine_col, mine_row + 1))
                                return self._process_game_action(action1) or self._process_game_action(action2)
        # no 1-2-1 pattern found
        return False


    def render(self):
        """Render the game using the Renderer."""
        # Clear screen
        self.screen.fill((192, 192, 192))  # Light gray background
        
        # Render board
        self.renderer.render_board(self.board)
        
        if self.board.won():
            self.renderer.render_game_over(won=True)
            # Just check to ensure not spamming the user
            if not self.sfx_played:
                self.sfx_win.play() # Play the win SFX
                self.sfx_played = True
        elif self.board.lost():
            self.renderer.render_game_over(won=False)
            # Just check to ensure not spamming the user
            if not self.sfx_played:
                self.sfx_lost.play() # Play the lost SFX
                self.sfx_played = True

        # Setup/display timer like they did on renderer but we just put it here for easy access to self.start_time
        y_value = self.board.height * self.cell_size + 55
        timer_font = pygame.font.SysFont("arial", 15, bold=True) # Copied from font_flag_counter
        elapsed_time = int(time.time() - self.start_time) # Cheap way to see time from start regardless of single core time.sleep() pauses
        timer_surface = timer_font.render(f"Time: {elapsed_time}s", True, (0, 0, 0)) # Text/Antialiasing/color they just had every text set as True so I matched it

        # Places/renders timer, (Text/Color object, (x,y) value)
        self.screen.blit(timer_surface, (10, y_value))

        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """
        Main game loop.
        
        This method contains the core game loop that handles input,
        updates game state, and renders the game.
        """
        print("The Greatest Game of Minesweeper: LMB=reveal RMB=flag R=restart ESC=quit")

        while self.running:
            # Assisted Game
            while self.running and not (self.board.lost() or self.board.won()):
              if self.alg_involvement.lower() == "full auto":
                  self._bot_turn()
                  time.sleep(.33)
              elif self.alg_involvement.lower() == "assisted":
                if self.turn.lower() == "human":
                    moved = self.handle_input()
                    if moved and not (self.board.lost() or self.board.won()):
                        self.turn = "bot"
                else:
                    time.sleep(.25) # Just made as an artificial buffer between player -> bot turn, as python is single threaded this *might mess up given we have a timer/sfx or anything like that implemented
                    moved = self._bot_turn()
                    self.turn = "human"
              else:
                  self.handle_input()
              self.render()
              self.clock.tick(30)
            while self.running and (self.board.lost() or self.board.won()):
                self.handle_input()
                self.render()
                self.clock.tick(30)
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
