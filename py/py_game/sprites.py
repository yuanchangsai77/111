# sprites.py
import pygame
import math
from config import *
import heapq
from typing import List, Tuple

class Player(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 2  # 0:right, 1:down, 2:left, 3:up
        self.speed = PLAYER_SPEED
        self.next_direction = None
        self.animation_frame = 0
        
    def update(self, walls: List[pygame.Rect]):
        # Movement and collision logic
        dx = [1, 0, -1, 0][self.direction] * self.speed
        dy = [0, 1, 0, -1][self.direction] * self.speed
        
        next_rect = self.rect.copy()
        next_rect.x += dx
        next_rect.y += dy
        
        collision = False
        for wall in walls:
            if next_rect.colliderect(wall):
                collision = True
                break
                
        if not collision:
            self.rect = next_rect
            
        # Animation
        self.animation_frame = (self.animation_frame + 1) % 10
        
    def draw(self, screen: pygame.Surface):
        angle = 90 * self.direction
        mouth_angle = 20 if self.animation_frame < 5 else 5
        
        pygame.draw.arc(screen, YELLOW,
                       self.rect,
                       math.radians(angle + mouth_angle),
                       math.radians(angle + 360 - mouth_angle))
        
        pygame.draw.line(screen, YELLOW,
                        self.rect.center,
                        (self.rect.centerx + math.cos(math.radians(angle)) * CELL_SIZE//2,
                         self.rect.centery - math.sin(math.radians(angle)) * CELL_SIZE//2))
        

def manhattan_distance(start: Tuple[int, int], goal: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two points"""
    return abs(start[0] - goal[0]) + abs(start[1] - goal[1])

def get_cell_position(pixel_pos: Tuple[int, int], cell_size: int) -> Tuple[int, int]:
    """Convert pixel coordinates to grid cell coordinates"""
    return (pixel_pos[0] // cell_size, pixel_pos[1] // cell_size)

def get_pixel_position(cell_pos: Tuple[int, int], cell_size: int) -> Tuple[int, int]:
    """Convert grid cell coordinates to pixel coordinates"""
    return (cell_pos[0] * cell_size, cell_pos[1] * cell_size)

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.start_x = x
        self.start_y = y
        self.color = color
        self.direction = 3
        self.speed = GHOST_SPEED
        self.state = 1  # 1:normal, 3:frightened, 4:eaten(dead)
        self.frightened_timer = 0
        self.path = []
        self.path_update_timer = 0
        self.respawn_timer = 0
        self.respawn_duration = 5000  # 5 seconds in milliseconds
        self.visible = True
        
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                  walls: List[pygame.Rect], cell_size: int) -> List[Tuple[int, int]]:
        """A* pathfinding algorithm implementation"""
        def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                pixel_pos = get_pixel_position(new_pos, cell_size)
                rect = pygame.Rect(pixel_pos[0], pixel_pos[1], cell_size, cell_size)
                
                can_move = True
                for wall in walls:
                    if rect.colliderect(wall):
                        can_move = False
                        break
                
                if can_move:
                    neighbors.append(new_pos)
            return neighbors

        # Initialize data structures for A*
        frontier = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                break
                
            for next_pos in get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + manhattan_distance(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        # Reconstruct path
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        
        return path if len(path) > 1 else []

    def get_escape_direction(self, player_pos: Tuple[int, int], walls: List[pygame.Rect]) -> int:
        """Calculate direction to move away from player"""
        current_pos = (self.rect.x, self.rect.y)
        dx = current_pos[0] - player_pos[0]
        dy = current_pos[1] - player_pos[1]
        
        # Try to move in direction opposite to player
        possible_directions = []
        if abs(dx) > abs(dy):
            if dx > 0:
                possible_directions.extend([0, 1, 3])  # Prefer right
            else:
                possible_directions.extend([2, 1, 3])  # Prefer left
        else:
            if dy > 0:
                possible_directions.extend([1, 0, 2])  # Prefer down
            else:
                possible_directions.extend([3, 0, 2])  # Prefer up
        
        # Check which directions are valid
        for direction in possible_directions:
            next_rect = self.rect.copy()
            if direction == 0: next_rect.x += self.speed
            elif direction == 1: next_rect.y += self.speed
            elif direction == 2: next_rect.x -= self.speed
            elif direction == 3: next_rect.y -= self.speed
            
            can_move = True
            for wall in walls:
                if next_rect.colliderect(wall):
                    can_move = False
                    break
            
            if can_move:
                return direction
        
        return self.direction  # Keep current direction if no better option

    def handle_eaten_state(self, current_time: int):
        """Handle ghost state when eaten"""
        if self.state == 4:  # Eaten state
            if self.respawn_timer == 0:  # Just entered eaten state
                self.respawn_timer = current_time
                self.visible = False
            elif current_time - self.respawn_timer >= self.respawn_duration:
                # Time to respawn
                self.state = 1  # Back to normal state
                self.rect.x = self.start_x
                self.rect.y = self.start_y
                self.visible = True
                self.respawn_timer = 0
                self.direction = 3  # Reset direction
            return True  # Ghost is in eaten state
        return False  # Ghost is not in eaten state

    def update(self, player: Player, walls: List[pygame.Rect]):
        current_time = pygame.time.get_ticks()
        
        # Handle eaten state
        if self.handle_eaten_state(current_time):
            return  # Skip normal update if ghost is eaten
        
        # Update frightened state
        if self.state == 3 and self.frightened_timer > 0:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = 1
        
        # Update path every 500ms
        if current_time - self.path_update_timer > 500:
            self.path_update_timer = current_time
            
            # Get current positions in grid coordinates
            ghost_pos = get_cell_position((self.rect.x, self.rect.y), CELL_SIZE)
            player_pos = get_cell_position((player.rect.x, player.rect.y), CELL_SIZE)
            
            if self.state == 3:  # Frightened state - run away
                self.direction = self.get_escape_direction((player.rect.x, player.rect.y), walls)
            else:  # Normal state - chase player
                self.path = self.find_path(ghost_pos, player_pos, walls, CELL_SIZE)
                if len(self.path) > 1:
                    # Determine direction to next path point
                    next_pos = self.path[1]
                    current_pos = ghost_pos
                    
                    dx = next_pos[0] - current_pos[0]
                    dy = next_pos[1] - current_pos[1]
                    
                    if dx > 0: self.direction = 0
                    elif dx < 0: self.direction = 2
                    elif dy > 0: self.direction = 1
                    elif dy < 0: self.direction = 3
        
        # Movement
        dx = [1, 0, -1, 0][self.direction] * self.speed
        dy = [0, 1, 0, -1][self.direction] * self.speed
        
        next_rect = self.rect.copy()
        next_rect.x += dx
        next_rect.y += dy
        
        # Check collision
        collision = False
        for wall in walls:
            if next_rect.colliderect(wall):
                collision = True
                break
        
        if not collision:
            self.rect = next_rect
            
    def draw(self, screen: pygame.Surface):
        if not self.visible:  # Don't draw if ghost is invisible
            return
            
        color = (185, 185, 185) if self.state == 3 else self.color
        
        # Draw ghost body
        pygame.draw.ellipse(screen, color,
                          (self.rect.x, self.rect.y,
                           CELL_SIZE, CELL_SIZE * 0.8))
        
        # Draw ghost skirt
        points = [
            (self.rect.x, self.rect.bottom - 5),
            (self.rect.x + CELL_SIZE//3, self.rect.bottom),
            (self.rect.x + 2*CELL_SIZE//3, self.rect.bottom - 5),
            (self.rect.right, self.rect.bottom)
        ]
        pygame.draw.polygon(screen, color, points)
        
        # Draw eyes
        eye_color = WHITE if self.state != 3 else BLUE
        pygame.draw.circle(screen, eye_color,
                         (self.rect.x + CELL_SIZE//3, self.rect.y + CELL_SIZE//3), 4)
        pygame.draw.circle(screen, eye_color,
                         (self.rect.x + 2*CELL_SIZE//3, self.rect.y + CELL_SIZE//3), 4)