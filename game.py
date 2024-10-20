import pygame
import math
import random

# Game configuration
class GameConfig:
    CANVAS_WIDTH = 900
    CANVAS_HEIGHT = 600
    PLAYER_SPEED = 200
    PLAYER_SIZE = 10
    PLAYER_COLOR = (0, 0, 255)  # Blue
    PLAYER_FLASH_COLOR = (255, 0, 0)  # Red
    BULLET_SIZE = 8
    BULLET_SPEED = 150
    BULLET_COLOR = (255, 255, 0)
    BULLET_SPAWN_INTERVAL = 2000
    DIFFICULTY_INCREASE_INTERVAL = 60000
    BULLET_LIFETIME = 30000
    BULLET_SPLIT_SIZE_RATIO = 0.7
    MINIMUM_BULLET_SIZE = 4  # New constant for minimum bullet size
    SHIELD_DURATION = 3000  # 3 seconds in milliseconds
    SHIELD_COOLDOWN = 30000  # 30 seconds in milliseconds
    SHIELD_COLOR = (0, 255, 255)  # Cyan

def random_color(exclude_colors):
    while True:
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if color not in exclude_colors and sum(color) > 50:  # Ensure it's not too dark
            return color

# Game entities
class GameObject:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def render(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

class Player(GameObject):
    def __init__(self, x, y, width, height, color):
        super().__init__(x, y, width, height, color)
        self.reset_health()
        self.original_color = color
        self.hit_flash_duration = 200
        self.last_hit_time = 0
        self.is_dead = False
        self.shield_active = False
        self.shield_start_time = 0
        self.shield_end_time = 0
        self.last_shield_use = None  # Changed this line
        self.radius = width // 2

    def reset_health(self):
        self.health = 100

    def take_damage(self, amount):
        if not self.shield_active:
            self.health -= amount
            self.last_hit_time = pygame.time.get_ticks()
            print(f"Player health: {self.health}")
            if self.health <= 0:
                print("Game Over! Restarting...")
                self.is_dead = True

    def activate_shield(self, current_time):
        if not self.shield_active and (self.last_shield_use is None or 
                                       current_time - self.last_shield_use >= GameConfig.SHIELD_COOLDOWN):
            self.shield_active = True
            self.shield_start_time = current_time

    def update_shield(self, current_time):
        if self.shield_active and current_time - self.shield_start_time >= GameConfig.SHIELD_DURATION:
            self.shield_active = False
            self.last_shield_use = current_time

    def render(self, screen):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time < self.hit_flash_duration:
            color = (255, 0, 0)
        else:
            color = self.original_color
        pygame.draw.circle(screen, color, (int(self.x + self.radius), int(self.y + self.radius)), self.radius)
        if self.shield_active:
            pygame.draw.circle(screen, GameConfig.SHIELD_COLOR, 
                               (int(self.x + self.width / 2), int(self.y + self.height / 2)), 
                               int(max(self.width, self.height) / 2 + 5), 2)

    def get_shield_cooldown(self, current_time):
        time_since_last_use = current_time - self.last_shield_use
        return max(0, (GameConfig.SHIELD_COOLDOWN - time_since_last_use) / 1000)

    def increase_size(self):
        self.width += 2
        self.height += 2
        self.radius += 1

    def get_shield_status(self, current_time):
        if self.shield_active:
            remaining_time = (GameConfig.SHIELD_DURATION - (current_time - self.shield_start_time)) / 1000
            return f"Shield Active: {remaining_time:.1f}s"
        elif self.last_shield_use is not None:
            time_since_last_use = current_time - self.last_shield_use
            if time_since_last_use < GameConfig.SHIELD_COOLDOWN:
                cooldown = (GameConfig.SHIELD_COOLDOWN - time_since_last_use) / 1000
                return f"Shield Cooldown: {cooldown:.1f}s"
        return "Shield Available"

class Bullet(GameObject):
    def __init__(self, x, y, direction, size=None, color=None):
        size = size or GameConfig.BULLET_SIZE
        if color is None:
            exclude_colors = [(0, 0, 0), GameConfig.PLAYER_COLOR, GameConfig.PLAYER_FLASH_COLOR]
            color = random_color(exclude_colors)
        super().__init__(x, y, size, size, color)
        self.direction = direction  # direction should be a tuple (dx, dy)
        self.speed = GameConfig.BULLET_SPEED
        self.radius = size // 2
        self.spawn_time = pygame.time.get_ticks()

    def update(self, delta_time):
        dx, dy = self.direction
        self.x += dx * self.speed * delta_time
        self.y += dy * self.speed * delta_time

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x + self.radius), int(self.y + self.radius)), self.radius)

    def collides_with(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < self.radius + other.radius

    def should_despawn(self, current_time):
        return current_time - self.spawn_time > GameConfig.BULLET_LIFETIME

    def split(self):
        new_size = int(self.width * GameConfig.BULLET_SPLIT_SIZE_RATIO)
        if new_size < GameConfig.MINIMUM_BULLET_SIZE:
            return []  # Return an empty list, effectively "dying" instead of splitting
        
        angle1 = random.uniform(0, 2 * math.pi)
        angle2 = angle1 + math.pi
        
        dir1 = (math.cos(angle1), math.sin(angle1))
        dir2 = (math.cos(angle2), math.sin(angle2))
        
        bullet1 = Bullet(self.x, self.y, dir1, new_size)
        bullet2 = Bullet(self.x, self.y, dir2, new_size)
        
        return [bullet1, bullet2]

# Game functions
def spawn_bullet():
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top':
        x = random.randint(0, GameConfig.CANVAS_WIDTH)
        y = 0
        direction = (0, 1)
    elif side == 'bottom':
        x = random.randint(0, GameConfig.CANVAS_WIDTH)
        y = GameConfig.CANVAS_HEIGHT
        direction = (0, -1)
    elif side == 'left':
        x = 0
        y = random.randint(0, GameConfig.CANVAS_HEIGHT)
        direction = (1, 0)
    else:  # right
        x = GameConfig.CANVAS_WIDTH
        y = random.randint(0, GameConfig.CANVAS_HEIGHT)
        direction = (-1, 0)
    
    bullet = Bullet(x, y, direction)
    game_entities.add(bullet)

def spawn_bullets(count):
    for _ in range(count):
        spawn_bullet()

def handle_bullet_collisions(bullets):
    bullets_to_remove = set()
    new_bullets = []

    for i, bullet in enumerate(bullets):
        if bullet in bullets_to_remove:
            continue
        for j in range(i + 1, len(bullets)):
            other = bullets[j]
            if other in bullets_to_remove:
                continue
            if bullet.collides_with(other):
                bullets_to_remove.add(bullet)
                bullets_to_remove.add(other)
                split_bullets = bullet.split() + other.split()
                if split_bullets:  # Only add new bullets if splitting occurred
                    new_bullets.extend(split_bullets)
                break

    return bullets_to_remove, new_bullets

def update_bullets(delta_time):
    current_time = pygame.time.get_ticks()
    bullets_to_remove = set()
    new_bullets = []

    bullets = [entity for entity in game_entities if isinstance(entity, Bullet)]

    for bullet in bullets:
        bullet.update(delta_time)

        # Wrap around screen edges
        bullet.x %= GameConfig.CANVAS_WIDTH
        bullet.y %= GameConfig.CANVAS_HEIGHT

        if bullet.collides_with(player):
            player.take_damage(10)
            bullets_to_remove.add(bullet)
        elif bullet.should_despawn(current_time):
            bullets_to_remove.add(bullet)

    collision_removals, collision_new_bullets = handle_bullet_collisions(bullets)
    bullets_to_remove.update(collision_removals)
    new_bullets.extend(collision_new_bullets)

    for bullet in bullets_to_remove:
        if bullet in game_entities:
            game_entities.remove(bullet)

    game_entities.update(new_bullets)

def restart_game():
    global start_time, last_bullet_spawn_time, high_score, difficulty_level
    survived_time = (pygame.time.get_ticks() - start_time) // 1000
    if survived_time > high_score:
        high_score = survived_time
        print(f"New High Score: {high_score} seconds!")

    player.x = GameConfig.CANVAS_WIDTH // 2
    player.y = GameConfig.CANVAS_HEIGHT // 2
    player.reset_health()
    player.is_dead = False
    player.width = player.height = GameConfig.PLAYER_SIZE
    player.radius = GameConfig.PLAYER_SIZE // 2

    game_entities.clear()
    game_entities.add(player)

    start_time = pygame.time.get_ticks()
    last_bullet_spawn_time = start_time
    difficulty_level = 1

# Game initialization
pygame.init()
screen = pygame.display.set_mode((GameConfig.CANVAS_WIDTH, GameConfig.CANVAS_HEIGHT))
pygame.display.set_caption("Bullet Dodge Game")

player = Player(100, 100, GameConfig.PLAYER_SIZE, GameConfig.PLAYER_SIZE, GameConfig.PLAYER_COLOR)
game_entities = {player}

start_time = pygame.time.get_ticks()
last_bullet_spawn_time = start_time
high_score = 0
difficulty_level = 1

# Game loop
running = True
clock = pygame.time.Clock()
last_difficulty_level = 1

while running:
    delta_time = clock.tick(60) / 1000.0
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.activate_shield(current_time)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x = max(player.x - GameConfig.PLAYER_SPEED * delta_time, 0)
    if keys[pygame.K_RIGHT]:
        player.x = min(player.x + GameConfig.PLAYER_SPEED * delta_time, GameConfig.CANVAS_WIDTH - player.width)
    if keys[pygame.K_UP]:
        player.y = max(player.y - GameConfig.PLAYER_SPEED * delta_time, 0)
    if keys[pygame.K_DOWN]:
        player.y = min(player.y + GameConfig.PLAYER_SPEED * delta_time, GameConfig.CANVAS_HEIGHT - player.height)

    player.update_shield(current_time)

    if player.is_dead:
        restart_game()
        difficulty_level = 1  # Reset difficulty level
        continue

    elapsed_time = current_time - start_time

    # Increase difficulty every minute
    if elapsed_time // GameConfig.DIFFICULTY_INCREASE_INTERVAL >= difficulty_level:
        difficulty_level = (elapsed_time // GameConfig.DIFFICULTY_INCREASE_INTERVAL) + 1
        if difficulty_level > last_difficulty_level:
            player.increase_size()
            last_difficulty_level = difficulty_level

    if current_time - last_bullet_spawn_time > GameConfig.BULLET_SPAWN_INTERVAL:
        spawn_bullets(difficulty_level)
        last_bullet_spawn_time = current_time

    update_bullets(delta_time)

    # Render
    screen.fill((0, 0, 0))  # Black background

    for entity in game_entities:
        entity.render(screen)

    # Render health bar
    health_bar_width = 250  # 250 pixels wide
    health_bar_height = 40  # 40 pixels high
    pygame.draw.rect(screen, (128, 128, 128), (10, 10, health_bar_width, health_bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, int(player.health * 2.5), health_bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (10, 10, health_bar_width, health_bar_height), 2)

    # Render text
    font = pygame.font.Font(None, 36)
    health_text = font.render(f"Health: {player.health}", True, (255, 255, 255))
    text_rect = health_text.get_rect(center=(135, 30))
    screen.blit(health_text, text_rect)

    current_survival_time = (current_time - start_time) // 1000
    time_text = font.render(f"Time: {current_survival_time}s", True, (255, 255, 255))
    screen.blit(time_text, (10, 60))

    high_score_text = font.render(f"High Score: {high_score}s", True, (255, 215, 0))
    screen.blit(high_score_text, (GameConfig.CANVAS_WIDTH - 250, 10))

    difficulty_text = font.render(f"Difficulty: {difficulty_level}", True, (255, 255, 255))
    screen.blit(difficulty_text, (10, 100))

    # Render shield status
    shield_status = player.get_shield_status(current_time)
    if shield_status.startswith("Shield Active"):
        color = (0, 255, 255)  # Cyan for active shield
    elif shield_status == "Shield Available":
        color = (0, 255, 0)  # Green for available shield
    else:
        color = (255, 255, 0)  # Yellow for cooldown
    shield_text = font.render(shield_status, True, color)
    shield_text_rect = shield_text.get_rect()
    shield_text_rect.bottomleft = (10, GameConfig.CANVAS_HEIGHT - 10)
    screen.blit(shield_text, shield_text_rect)

    pygame.display.flip()

pygame.quit()
