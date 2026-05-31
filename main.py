import math
import random

import pygame


WIDTH = 1280
HEIGHT = 720
FPS = 60

PLAYER_SIZE = 40
PLAYER_START_HEALTH = 5
PLAYER_START_SPEED = 300

BULLET_SPEED = 600
BULLET_RADIUS = 8
BULLET_START_DAMAGE = 1
BULLET_START_COOLDOWN = 0.35
MIN_SHOT_COOLDOWN = 0.12

ENEMY_SIZE = 40
ENEMY_SPEED = 120
BOSS_SIZE = 120
BOSS_SPEED = 70

SPAWN_TIMING = {
    3: 3,
    15: 5,
    27: 7,
    40: 10,
    50: 1,
}
BOSS_TRIGGER_TIME = 50


class Player:
    def __init__(self, x, y):
        self.max_health = PLAYER_START_HEALTH
        self.health = self.max_health
        self.speed = PLAYER_START_SPEED
        self.damage = BULLET_START_DAMAGE
        self.shot_cooldown = BULLET_START_COOLDOWN
        self.shot_timer = 0
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = self.pos

    def update(self, keys, dt):
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * dt

        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.shot_timer = max(0, self.shot_timer - dt)

    def can_shoot(self):
        return self.shot_timer <= 0

    def shoot(self, target_x, target_y):
        if not self.can_shoot():
            return None

        self.shot_timer = self.shot_cooldown
        return Bullet(self.pos.x, self.pos.y, target_x, target_y, self.damage)

    def draw(self, screen):
        pygame.draw.circle(screen, "blue", (int(self.pos.x), int(self.pos.y)), 20)


class Enemy:
    def __init__(self, x, y, game_time, is_boss=False):
        self.is_boss = is_boss
        size = BOSS_SIZE if is_boss else ENEMY_SIZE
        self.rect = pygame.Rect(0, 0, size, size)
        self.pos = pygame.Vector2(x, y)
        self.rect.center = self.pos

        if is_boss:
            self.speed = BOSS_SPEED
            self.health = self.normal_enemy_health(game_time) * 3
            self.points = 15
        else:
            self.speed = ENEMY_SPEED
            self.health = self.normal_enemy_health(game_time)
            self.points = 1

    @staticmethod
    def normal_enemy_health(game_time):
        if game_time >= 40:
            return 4
        if game_time >= 27:
            return 3
        if game_time >= 15:
            return 2
        return 1

    def update(self, player_pos, dt, enemies):
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        distance = math.hypot(dx, dy)
        if distance != 0:
            self.pos.x += dx / distance * self.speed * dt
            self.pos.y += dy / distance * self.speed * dt

        # Keep enemies from stacking perfectly on top of each other.
        for other in enemies:
            if other is self:
                continue

            dx = self.pos.x - other.pos.x
            dy = self.pos.y - other.pos.y
            distance = math.hypot(dx, dy)
            min_distance = self.rect.width / 2 + other.rect.width / 2
            if 0 < distance < min_distance:
                self.pos.x += dx / distance * 2
                self.pos.y += dy / distance * 2

        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, screen, font):
        color = "purple" if self.is_boss else "red"
        pygame.draw.rect(screen, color, self.rect)
        health_text = font.render(str(self.health), True, "white" if self.is_boss else "black")
        screen.blit(health_text, (self.rect.x + 6, self.rect.y + 6))


class Bullet:
    def __init__(self, x, y, target_x, target_y, damage):
        self.pos = pygame.Vector2(x, y)
        self.damage = damage
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        if distance != 0:
            self.vel = pygame.Vector2(dx / distance * BULLET_SPEED, dy / distance * BULLET_SPEED)
        else:
            self.vel = pygame.Vector2(BULLET_SPEED, 0)

    def update(self, dt):
        self.pos += self.vel * dt

    def draw(self, screen):
        pygame.draw.circle(screen, "orange", (int(self.pos.x), int(self.pos.y)), BULLET_RADIUS)

    def is_off_screen(self):
        return (
            self.pos.x < 0
            or self.pos.x > WIDTH
            or self.pos.y < 0
            or self.pos.y > HEIGHT
        )


class Shop:
    def __init__(self):
        self.open = False
        self.items = [
            {
                "key": pygame.K_1,
                "label": "1) Max Health +1",
                "cost": 5,
                "apply": self.buy_health,
            },
            {
                "key": pygame.K_2,
                "label": "2) Bullet Damage +1",
                "cost": 10,
                "apply": self.buy_damage,
            },
            {
                "key": pygame.K_3,
                "label": "3) Faster Fire Rate",
                "cost": 12,
                "apply": self.buy_fire_rate,
            },
            {
                "key": pygame.K_4,
                "label": "4) Move Speed +40",
                "cost": 8,
                "apply": self.buy_speed,
            },
        ]

    def try_buy(self, key, player, points):
        for item in self.items:
            if key == item["key"] and points >= item["cost"]:
                item["apply"](player)
                return points - item["cost"]
        return points

    def buy_health(self, player):
        player.max_health += 1
        player.health = player.max_health

    def buy_damage(self, player):
        player.damage += 1

    def buy_fire_rate(self, player):
        player.shot_cooldown = max(MIN_SHOT_COOLDOWN, player.shot_cooldown - 0.06)

    def buy_speed(self, player):
        player.speed += 40

    def draw(self, screen, font, player, points):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(330, 100, 620, 470)
        pygame.draw.rect(screen, "darkgray", panel)
        pygame.draw.rect(screen, "black", panel, 4)

        title = font.render("Shop - press TAB to close", True, "white")
        screen.blit(title, (panel.x + 30, panel.y + 25))

        points_text = font.render(f"Points: {points}", True, "yellow")
        screen.blit(points_text, (panel.x + 30, panel.y + 70))

        for i, item in enumerate(self.items):
            affordable = points >= item["cost"]
            color = "white" if affordable else "gray"
            text = font.render(f"{item['label']} - {item['cost']} pts", True, color)
            screen.blit(text, (panel.x + 30, panel.y + 130 + i * 55))

        stats = [
            f"Health: {player.health}/{player.max_health}",
            f"Damage: {player.damage}",
            f"Shot cooldown: {player.shot_cooldown:.2f}s",
            f"Speed: {player.speed}",
        ]
        for i, stat in enumerate(stats):
            text = font.render(stat, True, "black")
            screen.blit(text, (panel.x + 350, panel.y + 130 + i * 45))


def draw_text(screen, font, text, color, x, y):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))


def spawn_enemy(game_time):
    edge = random.choice(("top", "bottom", "left", "right"))
    if edge == "top":
        x, y = random.randint(0, WIDTH), 0
    elif edge == "bottom":
        x, y = random.randint(0, WIDTH), HEIGHT
    elif edge == "left":
        x, y = 0, random.randint(0, HEIGHT)
    else:
        x, y = WIDTH, random.randint(0, HEIGHT)

    return Enemy(x, y, game_time)


def spawn_boss(game_time):
    return Enemy(WIDTH // 2, 60, game_time, is_boss=True)


def reset_game():
    player = Player(WIDTH // 2, HEIGHT // 2)
    enemies = [spawn_enemy(0) for _ in range(SPAWN_TIMING[3])]
    return {
        "player": player,
        "bullets": [],
        "enemies": enemies,
        "spawned": {3},
        "damage_cooldown": 0,
        "game_time": 0,
        "kills": 0,
        "points": 0,
        "boss_defeated": False,
    }


def draw_hud(screen, font, player, kills, points, game_time):
    pygame.draw.rect(screen, "red", (40, 10, player.health * 40, 20))
    pygame.draw.rect(screen, "black", (40, 10, player.max_health * 40, 20), 3)

    draw_text(screen, font, f"Player Health: {player.health}/{player.max_health}", "black", 40, 35)
    draw_text(screen, font, f"Kills: {kills}", "black", 40, 65)
    draw_text(screen, font, f"Points: {points}", "black", 40, 95)
    draw_text(screen, font, f"Time: {int(game_time)}s", "black", 40, 125)

    if player.can_shoot():
        draw_text(screen, font, "Shot Ready", "green", 40, 155)
    else:
        draw_text(screen, font, f"Cooldown: {player.shot_timer:.1f}s", "red", 40, 155)

    draw_text(screen, font, "TAB: Shop", "black", WIDTH - 180, 20)


def draw_menu(screen, font, title_font):
    screen.fill("black")
    draw_text(screen, title_font, "Survival Shooter", "white", 430, 150)
    draw_text(screen, font, "WASD to move. Left click to shoot.", "gray", 430, 260)
    draw_text(screen, font, "Earn points from kills, then press TAB for the shop.", "gray", 430, 305)
    draw_text(screen, font, "A final boss arrives at 50 seconds.", "gray", 430, 350)
    draw_text(screen, font, "Press ENTER to start or Q to quit.", "yellow", 430, 430)


def draw_end_screen(screen, font, title, kills, points):
    screen.fill("black")
    draw_text(screen, font, title, "white", 540, 285)
    draw_text(screen, font, f"Final Kills: {kills}", "white", 540, 335)
    draw_text(screen, font, f"Final Points: {points}", "white", 540, 375)
    draw_text(screen, font, "Press R to Restart, M for Menu, or Q to Quit", "gray", 420, 430)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Survival Shooter")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 72)

    shop = Shop()
    game = reset_game()
    state = "menu"
    running = True
    dt = 0

    while running:
        player = game["player"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif state == "menu" and event.key == pygame.K_RETURN:
                    game = reset_game()
                    shop.open = False
                    state = "playing"
                elif state in ("game_over", "victory"):
                    if event.key == pygame.K_r:
                        game = reset_game()
                        shop.open = False
                        state = "playing"
                    elif event.key == pygame.K_m:
                        state = "menu"
                elif state == "playing":
                    if event.key == pygame.K_TAB:
                        shop.open = not shop.open
                    elif shop.open:
                        game["points"] = shop.try_buy(event.key, player, game["points"])

            if event.type == pygame.MOUSEBUTTONDOWN and state == "playing" and not shop.open:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    bullet = player.shoot(mx, my)
                    if bullet is not None:
                        game["bullets"].append(bullet)

        if state == "menu":
            draw_menu(screen, font, title_font)
        elif state == "playing":
            screen.fill("white")

            if not shop.open:
                keys = pygame.key.get_pressed()
                player.update(keys, dt)
                game["game_time"] += dt
                game["damage_cooldown"] = max(0, game["damage_cooldown"] - dt)

                for bullet in game["bullets"][:]:
                    bullet.update(dt)
                    if bullet.is_off_screen():
                        game["bullets"].remove(bullet)

                for bullet in game["bullets"][:]:
                    for enemy in game["enemies"][:]:
                        if enemy.rect.collidepoint(bullet.pos):
                            if bullet in game["bullets"]:
                                game["bullets"].remove(bullet)
                            enemy.health -= bullet.damage
                            if enemy.health <= 0:
                                game["enemies"].remove(enemy)
                                game["kills"] += 1
                                game["points"] += enemy.points
                                if enemy.is_boss:
                                    game["boss_defeated"] = True
                                    state = "victory"
                            break

                if state == "playing":
                    for enemy in game["enemies"][:]:
                        enemy.update(player.pos, dt, game["enemies"])
                        if enemy.rect.colliderect(player.rect) and game["damage_cooldown"] <= 0:
                            player.health -= 1
                            game["damage_cooldown"] = 1
                            if player.health <= 0:
                                state = "game_over"
                                break

                if state == "playing":
                    for trigger_time, count in SPAWN_TIMING.items():
                        if game["game_time"] >= trigger_time and trigger_time not in game["spawned"]:
                            if trigger_time == BOSS_TRIGGER_TIME:
                                game["enemies"].append(spawn_boss(game["game_time"]))
                            else:
                                for _ in range(count):
                                    game["enemies"].append(spawn_enemy(game["game_time"]))
                            game["spawned"].add(trigger_time)

            player.draw(screen)
            for bullet in game["bullets"]:
                bullet.draw(screen)
            for enemy in game["enemies"]:
                enemy.draw(screen, font)
            draw_hud(screen, font, player, game["kills"], game["points"], game["game_time"])

            if shop.open:
                shop.draw(screen, font, player, game["points"])
        elif state == "game_over":
            draw_end_screen(screen, font, "GAME OVER", game["kills"], game["points"])
        elif state == "victory":
            draw_end_screen(screen, font, "BOSS DEFEATED!", game["kills"], game["points"])

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
