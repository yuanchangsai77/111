# game.py
import pygame
import random
from config import *
from sprites import Player, Ghost
from database import Database

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man")
        self.clock = pygame.time.Clock()
        self.db = Database()
        
        self.state = STATE_MENU
        self.current_level = 1
        self.score = 0
        self.lives = INITIAL_LIVES
        
        self.player = None
        self.ghosts = []
        self.walls = []
        self.dots = []
        self.power_pellets = []
        
    def load_level(self):
        map_data, wall_color, power_pellets = self.db.get_map(self.current_level)
        if not map_data:
            return False
            
        self.walls.clear()
        self.dots.clear()
        self.power_pellets.clear()
        
        for y, row in enumerate(map_data):
            for x, cell in enumerate(row):
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                if cell == 1:
                    self.walls.append(pygame.Rect(pos, (CELL_SIZE, CELL_SIZE)))
                elif cell == 0:
                    if f"{x},{y}" in power_pellets:
                        self.power_pellets.append(pygame.Rect(pos, (CELL_SIZE, CELL_SIZE)))
                    else:
                        self.dots.append(pygame.Rect(pos, (CELL_SIZE, CELL_SIZE)))
                        
        # Create player and ghosts
        self.player = Player(13 * CELL_SIZE, 23 * CELL_SIZE)
        self.ghosts = [
            Ghost(12 * CELL_SIZE, 14 * CELL_SIZE, GHOST_COLORS[0]),
            Ghost(13 * CELL_SIZE, 14 * CELL_SIZE, GHOST_COLORS[1]),
            Ghost(14 * CELL_SIZE, 14 * CELL_SIZE, GHOST_COLORS[2]),
            Ghost(15 * CELL_SIZE, 14 * CELL_SIZE, GHOST_COLORS[3])
        ]
        
        return True
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    if self.state == STATE_MENU:
                        self.state = STATE_PLAYING
                        self.load_level()
                    elif self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                    elif self.state == STATE_GAME_OVER:
                        self.__init__()
                        self.state = STATE_MENU
        return True
        
    def update(self):
        if self.state != STATE_PLAYING:
            return

        ################################################
        # Handle player movement based on next_direction
        keys = pygame.key.get_pressed()
        new_direction = None
        if keys[pygame.K_LEFT]:
            new_direction = 2
        elif keys[pygame.K_RIGHT]:
            new_direction = 0
        elif keys[pygame.K_UP]:
            new_direction = 3
        elif keys[pygame.K_DOWN]:
            new_direction = 1

        # Try new direction if key pressed
        if new_direction is not None:
            next_rect = self.player.rect.copy()
            if new_direction == 0: next_rect.x += self.player.speed
            elif new_direction == 1: next_rect.y += self.player.speed
            elif new_direction == 2: next_rect.x -= self.player.speed
            elif new_direction == 3: next_rect.y -= self.player.speed
            
            # Check if new direction is possible
            can_move = True
            for wall in self.walls:
                if next_rect.colliderect(wall):
                    can_move = False
                    break
            
            if can_move:
                self.player.direction = new_direction
        ################################################

        ################################################

        # Update player position
        self.player.update(self.walls)
                
        # Update ghost positions
        for ghost in self.ghosts:
            ghost.update(self.player, self.walls)
            
        # Check dot collection
        player_rect = self.player.rect
        for dot in self.dots[:]:
            if player_rect.colliderect(dot):
                self.dots.remove(dot)
                self.score += 10
                
        # Check power pellet collection
        for pellet in self.power_pellets[:]:
            if player_rect.colliderect(pellet):
                self.power_pellets.remove(pellet)
                self.score += 50
                for ghost in self.ghosts:
                    ghost.state = 3
                    ghost.frightened_timer = POWER_PELLET_DURATION
                    
        # Check ghost collisions
        for ghost in self.ghosts:
            if player_rect.colliderect(ghost.rect):
                if ghost.state == 3:
                    ghost.state = 4
                    self.score += 100
                elif ghost.state == 1:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = STATE_GAME_OVER
                    else:
                        self.load_level()
                        
        # Check level completion
        if not self.dots and not self.power_pellets:
            self.current_level += 1
            if not self.load_level():
                self.state = STATE_GAME_OVER

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state in (STATE_PLAYING, STATE_PAUSED):
            self.draw_game()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
            
        pygame.display.flip()
        
    def draw_menu(self):
        font = pygame.font.Font(None, 64)
        title = font.render("PAC-MAN", True, YELLOW)
        start = font.render("Press SPACE to Start", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
        self.screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, SCREEN_HEIGHT//2))
        
    def draw_game(self):
        # Draw walls
        for wall in self.walls:
            pygame.draw.rect(self.screen, BLUE, wall)
            
        # Draw dots
        for dot in self.dots:
            pygame.draw.circle(self.screen, WHITE,
                             dot.center, 2)
                             
        # Draw power pellets
        for pellet in self.power_pellets:
            pygame.draw.circle(self.screen, WHITE,
                             pellet.center, 6)
                             
        # Draw player and ghosts
        self.player.draw(self.screen)
        for ghost in self.ghosts:
            ghost.draw(self.screen)

        # Draw score and lives
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = font.render(f"Level: {self.current_level}", True, WHITE)
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(lives_text, (20, 50))
        self.screen.blit(level_text, (20, 80))
        
        if self.state == STATE_PAUSED:
            pause_text = font.render("PAUSED", True, WHITE)
            self.screen.blit(pause_text,
                           (SCREEN_WIDTH//2 - pause_text.get_width()//2,
                            SCREEN_HEIGHT//2))
            
    def draw_game_over(self):
        font = pygame.font.Font(None, 64)
        if self.lives > 0:
            text1 = font.render("YOU WIN!", True, WHITE)
        else:
            text1 = font.render("GAME OVER", True, WHITE)
            
        text2 = font.render(f"Final Score: {self.score}", True, WHITE)
        text3 = font.render("Press SPACE to Play Again", True, WHITE)
        
        self.screen.blit(text1, (SCREEN_WIDTH//2 - text1.get_width()//2, SCREEN_HEIGHT//3))
        self.screen.blit(text2, (SCREEN_WIDTH//2 - text2.get_width()//2, SCREEN_HEIGHT//2))
        self.screen.blit(text3, (SCREEN_WIDTH//2 - text3.get_width()//2, 2*SCREEN_HEIGHT//3))
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()