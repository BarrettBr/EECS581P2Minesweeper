import pygame
# Authors: Adam berry
# Creation Date: October 3
# 
# Description:
#   This file holds the configuration screen that shows before the game starts.
#   it is entirely self contained, including spinning up its own pygame completely seperate to the rest
#   If done well it should have no side effect anywhere else in the code except for the return values
#  Functions:
#       Init:
#           initializes the self contained pygame scene
#       
#       Draw UI:
#           Draws all of the screen element every frame
#       handle_input:
#           Catches the user's input and updates the screen accordingly
#       modify_selected_option
#           A helper function for handle_input that changes the state for handle_input
#       run
#           Contains the other functions and the main game loop.
#           this is the function that returns the usable values
#   
#       Inputs:
#           User input: up, down, left, right, enter
#
#       Outputs:
#           Mine count, AI Difficulty level, ai involvement level

# Class to contain all of the config screen 
class ConfigScreen:
    # Initialize the pygame instance and any constants/variables
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((500, 300))
        pygame.display.set_caption("Config Screen")
        self.font = pygame.font.SysFont(None, 36)
        self.clock = pygame.time.Clock()

        # Config options
        self.mineCount = 15
        self.algo_involvement = ['None', 'Assisted', 'Full Auto']
        self.involve_level = 'None'; 
        self.alg_complexity = ['Easy', 'Medium', 'Hard']
        self.complexity = 'Easy' 

        self.selected_option = 0

    # Function that draws all on screen elements per frame, updates with state
    def draw_ui(self):
        self.screen.fill((30, 30, 30))
        color = [(200, 200, 200)] * 3
        color[self.selected_option] = (255, 255, 0)

        mine_text = self.font.render(f"Mines: {self.mineCount}", True, color[0])
        ai_text = self.font.render(f"Alg Involvement: {self.involve_level}", True, color[1])
        complexity_text = self.font.render(f"Difficulty: {self.complexity}", True, color[2])

        self.screen.blit(mine_text, (50, 50))
        self.screen.blit(ai_text, (50, 100))
        self.screen.blit(complexity_text, (50, 150))

        instruction1 = self.font.render("Up/Down to select, L/R to change", True, (100, 100, 100))
        instruction2 = self.font.render("Enter to accept", True, (100, 100, 100))
        self.screen.blit(instruction1, (18, 230))
        self.screen.blit(instruction2, (18, 250))

        pygame.display.flip()

    # Catches the users input and routes it appropriately
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                return False  # Exit config screen
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 3
            elif event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                self.modify_selected_option(event.key)
        return True

    # Changes the actual value on a left/right arrow
    def modify_selected_option(self, key):
        if self.selected_option == 0:  # mine count 
            if key == pygame.K_LEFT:
                self.mineCount = max(10, self.mineCount - 1)
            else:
                self.mineCount = min(20, self.mineCount + 1)
        elif self.selected_option == 1:  # algorithm involvement 
            idx = self.algo_involvement.index(self.involve_level)
            if key == pygame.K_LEFT:
                idx = (idx - 1) % len(self.algo_involvement)
            else:
                idx = (idx + 1) % len(self.algo_involvement)
            self.involve_level = self.algo_involvement[idx]
        elif self.selected_option == 2:  # complexity 
            idx = self.alg_complexity.index(self.complexity)
            if key == pygame.K_LEFT:
                idx = (idx - 1) % len(self.alg_complexity)
            else:
                idx = (idx + 1) % len(self.alg_complexity)
            self.complexity = self.alg_complexity[idx]

    # The top level function that contains the game loop
    def run(self):
        running = True
        while running:
            self.draw_ui()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self.handle_input(event)
            self.clock.tick(30)

        pygame.quit()
        return self.mineCount, self.complexity, self.involve_level

