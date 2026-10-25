import pygame
import random
import math
import sys

# ----------------- INITIALIZATION & CONFIG -----------------
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turbo Drift 2D - Arcade Highway")
CLOCK = pygame.time.Clock()
FPS = 60

# Palette
DARK_GRAY  = (34, 34, 38)
ROAD_GRAY  = (48, 50, 56)
GRASS_COL  = (38, 115, 60)
CURB_RED   = (210, 45, 45)
CURB_WHITE = (235, 235, 240)
MARK_WHITE = (240, 240, 245)
GOLD       = (255, 215, 0)
CYAN       = (0, 220, 255)
RED        = (230, 40, 40)
WHITE      = (255, 255, 255)
BLACK      = (15, 15, 18)

ROAD_LEFT = 180
ROAD_RIGHT = 620
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
LANES = [235, 345, 455, 565]

FONT_MAIN = pygame.font.SysFont("consolas", 20, bold=True)
FONT_BIG  = pygame.font.SysFont("consolas", 48, bold=True)
FONT_SUB  = pygame.font.SysFont("consolas", 24)

# ----------------- PROCEDURAL AUDIO GENERATION -----------------
def generate_tone(frequency=440, duration_ms=100, volume=0.2):
    sample_rate = 44100
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    buf = bytearray(n_samples * 2)
    for i in range(n_samples):
        t = float(i) / sample_rate
        val = int(math.sin(2.0 * math.pi * frequency * t) * 127 * volume + 128)
        buf[2 * i] = val
        buf[2 * i + 1] = val
    try:
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

COIN_SND = generate_tone(880, 80, 0.25)
CRASH_SND = generate_tone(140, 300, 0.4)
BOOST_SND = generate_tone(600, 150, 0.25)

def play_sfx(sound):
    if sound:
        sound.play()

# ----------------- GRAPHIC HELPERS -----------------
def draw_vehicle(surface, x, y, width, height, color, angle=0):
    car_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(car_surf, color, (0, 0, width, height), border_radius=8)
    pygame.draw.rect(car_surf, (20, 25, 35), (4, height * 0.25, width - 8, height * 0.28), border_radius=3)
    pygame.draw.rect(car_surf, (int(color[0]*0.8), int(color[1]*0.8), int(color[2]*0.8)), (6, height * 0.35, width - 12, height * 0.35), border_radius=2)
    pygame.draw.rect(car_surf, (20, 25, 35), (5, height * 0.72, width - 10, height * 0.15), border_radius=2)
    pygame.draw.circle(car_surf, (255, 255, 200), (7, 5), 4)
    pygame.draw.circle(car_surf, (255, 255, 200), (width - 7, 5), 4)
    pygame.draw.rect(car_surf, (255, 40, 40), (4, height - 4, 8, 3), border_radius=1)
    pygame.draw.rect(car_surf, (255, 40, 40), (width - 12, height - 4, 8, 3), border_radius=1)
    
    # Tires (black color: (10, 10, 10))
    pygame.draw.rect(car_surf, (10, 10, 10), (-2, height * 0.15, 4, 12), border_radius=2)
    pygame.draw.rect(car_surf, (10, 10, 10), (width - 2, height * 0.15, 4, 12), border_radius=2)
    pygame.draw.rect(car_surf, (10, 10, 10), (-2, height * 0.75, 4, 12), border_radius=2)
    pygame.draw.rect(car_surf, (10, 10, 10), (width - 2, height * 0.75, 4, 12), border_radius=2)

    rotated_surf = pygame.transform.rotate(car_surf, -angle)
    rect = rotated_surf.get_rect(center=(x, y))
    surface.blit(rotated_surf, rect.topleft)
    return rect

# ----------------- GAME CLASSES -----------------
class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 140
        self.width = 38
        self.height = 70
        self.color = (30, 144, 255)
        self.speed = 0.0
        self.max_speed = 13.0
        self.accel = 0.22
        self.brake = 0.35
        self.friction = 0.08
        self.angle = 0.0
        self.nitro = 100.0
        self.health = 100
        self.nitro_active = False

    def update(self, keys):
        self.nitro_active = (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]) and self.nitro > 5
        top_spd = self.max_speed * 1.45 if self.nitro_active else self.max_speed
        
        if self.nitro_active:
            self.nitro = max(0.0, self.nitro - 0.7)
            self.speed = min(top_spd, self.speed + self.accel * 1.8)
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(top_spd, self.speed + self.accel)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(-3.0, self.speed - self.brake)
        else:
            if self.speed > 0:
                self.speed = max(0.0, self.speed - self.friction)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + self.friction)

        target_angle = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= 5.5 * (self.speed / max(1.0, self.max_speed * 0.6))
            target_angle = -14
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += 5.5 * (self.speed / max(1.0, self.max_speed * 0.6))
            target_angle = 14

        self.angle += (target_angle - self.angle) * 0.25

        if self.x < ROAD_LEFT + 25 or self.x > ROAD_RIGHT - 25:
            self.speed *= 0.92
            if self.x < ROAD_LEFT - 40:
                self.x = ROAD_LEFT - 40
                self.health -= 0.5
            if self.x > ROAD_RIGHT + 40:
                self.x = ROAD_RIGHT + 40
                self.health -= 0.5

        if not self.nitro_active and self.nitro < 100.0:
            self.nitro = min(100.0, self.nitro + 0.08)

    def draw(self, surface):
        return draw_vehicle(surface, self.x, self.y, self.width, self.height, self.color, self.angle)

class TrafficCar:
    TRAFFIC_COLORS = [
        (220, 50, 47),
        (230, 160, 30),
        (130, 80, 220),
        (40, 180, 120),
        (240, 240, 245)
    ]

    def __init__(self, y=-100):
        self.lane = random.choice(LANES)
        self.x = self.lane
        self.y = y
        self.width = 36
        self.height = random.choice([66, 74, 90])
        self.color = random.choice(self.TRAFFIC_COLORS)
        self.is_oncoming = self.lane < (ROAD_LEFT + ROAD_RIGHT) // 2
        self.base_speed = random.uniform(3.0, 6.0) if not self.is_oncoming else random.uniform(5.0, 8.5)

    def update(self, player_speed):
        if self.is_oncoming:
            self.y += self.base_speed + player_speed
        else:
            self.y += player_speed - self.base_speed

    def draw(self, surface):
        angle = 180 if self.is_oncoming else 0
        return draw_vehicle(surface, self.x, self.y, self.width, self.height, self.color, angle)

class Pickup:
    def __init__(self, kind):
        self.kind = kind
        self.x = random.randint(ROAD_LEFT + 30, ROAD_RIGHT - 30)
        self.y = -50
        self.radius = 12

    def update(self, player_speed):
        self.y += player_speed

    def draw(self, surface):
        color = GOLD if self.kind == 'coin' else CYAN
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius - 4, width=2)
        label = "$" if self.kind == 'coin' else "N"
        txt = FONT_MAIN.render(label, True, BLACK)
        surface.blit(txt, (self.x - 5, self.y - 8))
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

# ----------------- MAIN GAME LOOP -----------------
def main():
    player = Player()
    traffic = []
    pickups = []
    
    road_scroll = 0
    score = 0
    distance_traveled = 0
    game_over = False

    while True:
        dt = CLOCK.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    player.reset()
                    traffic.clear()
                    pickups.clear()
                    score = 0
                    distance_traveled = 0
                    game_over = False

        if not game_over:
            player.update(keys)
            distance_traveled += player.speed * 0.05
            score += int(player.speed * 0.1)

            road_scroll = (road_scroll + player.speed) % 80

            if random.random() < 0.025 and len(traffic) < 7:
                traffic.append(TrafficCar(-120))

            if random.random() < 0.012 and len(pickups) < 3:
                pickups.append(Pickup(random.choice(['coin', 'nitro'])))

            for car in traffic[:]:
                car.update(player.speed)
                if car.y > HEIGHT + 150 or car.y < -300:
                    traffic.remove(car)

            for p in pickups[:]:
                p.update(player.speed)
                if p.y > HEIGHT + 50:
                    pickups.remove(p)

        # Background & Road
        SCREEN.fill(GRASS_COL)
        pygame.draw.rect(SCREEN, ROAD_GRAY, (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))

        curb_size = 20
        for y_pos in range(-80, HEIGHT + 80, curb_size):
            shifted_y = y_pos + int(road_scroll % (curb_size * 2))
            c = CURB_RED if (shifted_y // (curb_size * 2)) % 2 == 0 else CURB_WHITE
            pygame.draw.rect(SCREEN, c, (ROAD_LEFT - 12, shifted_y, 12, curb_size))
            pygame.draw.rect(SCREEN, c, (ROAD_RIGHT, shifted_y, 12, curb_size))

        center_x = (ROAD_LEFT + ROAD_RIGHT) // 2
        pygame.draw.line(SCREEN, (240, 180, 20), (center_x - 3, 0), (center_x - 3, HEIGHT), 3)
        pygame.draw.line(SCREEN, (240, 180, 20), (center_x + 3, 0), (center_x + 3, HEIGHT), 3)

        for lx in [ROAD_LEFT + ROAD_WIDTH // 4, ROAD_RIGHT - ROAD_WIDTH // 4]:
            dash_h = 30
            gap = 30
            for y_pos in range(-60, HEIGHT + 60, dash_h + gap):
                sy = y_pos + int(road_scroll % (dash_h + gap))
                pygame.draw.line(SCREEN, MARK_WHITE, (lx, sy), (lx, sy + dash_h), 3)

        # Pickups & Collisions
        player_rect = pygame.Rect(player.x - 18, player.y - 32, 36, 64)

        for p in pickups[:]:
            p_rect = p.draw(SCREEN)
            if player_rect.colliderect(p_rect):
                if p.kind == 'coin':
                    score += 250
                    play_sfx(COIN_SND)
                elif p.kind == 'nitro':
                    player.nitro = min(100.0, player.nitro + 40.0)
                    play_sfx(BOOST_SND)
                pickups.remove(p)

        for car in traffic:
            t_rect = car.draw(SCREEN)
            if player_rect.colliderect(t_rect):
                play_sfx(CRASH_SND)
                damage = 25 if not player.nitro_active else 45
                player.health -= damage
                player.speed *= 0.25
                car.y -= 70
                if player.health <= 0:
                    player.health = 0
                    game_over = True

        player.draw(SCREEN)

        # HUD
        hud_bg = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
        hud_bg.fill((15, 18, 24, 210))
        SCREEN.blit(hud_bg, (0, 0))

        speed_kmh = int(player.speed * 18)
        spd_text = FONT_MAIN.render(f"SPEED: {speed_kmh:03d} km/h", True, WHITE)
        score_text = FONT_MAIN.render(f"SCORE: {score:05d}", True, GOLD)
        dist_text = FONT_MAIN.render(f"DIST: {distance_traveled:.1f} m", True, WHITE)
        SCREEN.blit(spd_text, (20, 14))
        SCREEN.blit(score_text, (240, 14))
        SCREEN.blit(dist_text, (430, 14))

        pygame.draw.rect(SCREEN, (50, 50, 50), (620, 12, 160, 12), border_radius=4)
        hp_col = (46, 204, 113) if player.health > 40 else (231, 76, 60)
        pygame.draw.rect(SCREEN, hp_col, (620, 12, int(160 * (player.health / 100)), 12), border_radius=4)
        hp_label = FONT_MAIN.render("HP", True, WHITE)
        SCREEN.blit(hp_label, (590, 8))

        pygame.draw.rect(SCREEN, (50, 50, 50), (620, 28, 160, 10), border_radius=3)
        pygame.draw.rect(SCREEN, CYAN, (620, 28, int(160 * (player.nitro / 100)), 10), border_radius=3)
        nos_label = FONT_MAIN.render("NOS", True, CYAN)
        SCREEN.blit(nos_label, (585, 24))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            SCREEN.blit(overlay, (0, 0))

            go_txt = FONT_BIG.render("TOTALED!", True, RED)
            score_final = FONT_SUB.render(f"Final Score: {score}", True, WHITE)
            restart_txt = FONT_SUB.render("Press 'R' to Restart", True, GOLD)

            SCREEN.blit(go_txt, (WIDTH // 2 - go_txt.get_width() // 2, HEIGHT // 2 - 80))
            SCREEN.blit(score_final, (WIDTH // 2 - score_final.get_width() // 2, HEIGHT // 2 - 10))
            SCREEN.blit(restart_txt, (WIDTH // 2 - restart_txt.get_width() // 2, HEIGHT // 2 + 40))

        pygame.display.flip()

if __name__ == "__main__":
    main()