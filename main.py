import math
import random

import pygame


WIDTH = 1280
HEIGHT = 720
FPS = 60

PLAYER_SIZE = 40
PLAYER_START_HEALTH = 5
PLAYER_START_SPEED = 300

BULLET_START_SPEED = 600
BULLET_START_RADIUS = 8
BULLET_START_DAMAGE = 1
BULLET_START_COOLDOWN = 0.35
BULLET_START_SPREAD = 10

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
INFINITE_WAVE_START = 60
BASE_WAVE_INTERVAL = 10
MIN_WAVE_INTERVAL = 4
BOSS_WAVE_INTERVAL = 45


class Player:
    def __init__(self, x, y):
        self.max_health = PLAYER_START_HEALTH
        self.health = self.max_health
        self.speed = PLAYER_START_SPEED
        self.damage = BULLET_START_DAMAGE
        self.shot_cooldown = BULLET_START_COOLDOWN
        self.shot_timer = 0
        self.bullet_speed = BULLET_START_SPEED
        self.bullet_radius = BULLET_START_RADIUS
        self.bullet_count = 1
        self.bullet_spread = BULLET_START_SPREAD
        self.hurt_cooldown = 1
        self.point_bonus = 0
        self.regen_rate = 0
        self.regen_progress = 0
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

        if self.regen_rate > 0 and self.health < self.max_health:
            self.regen_progress += self.regen_rate * dt
            if self.regen_progress >= 1:
                healing = int(self.regen_progress)
                self.health = min(self.max_health, self.health + healing)
                self.regen_progress -= healing

        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.shot_timer = max(0, self.shot_timer - dt)

    def can_shoot(self):
        return self.shot_timer <= 0

    def shoot(self, target_x, target_y):
        if not self.can_shoot():
            return []

        self.shot_timer = self.shot_cooldown
        dx = target_x - self.pos.x
        dy = target_y - self.pos.y
        base_angle = math.atan2(dy, dx) if dx or dy else 0
        spread_step = math.radians(self.bullet_spread)
        total_spread = spread_step * (self.bullet_count - 1)

        bullets = []
        for i in range(self.bullet_count):
            angle = base_angle - total_spread / 2 + spread_step * i
            bullets.append(
                Bullet(
                    self.pos.x,
                    self.pos.y,
                    angle,
                    self.damage,
                    self.bullet_speed,
                    self.bullet_radius,
                )
            )
        return bullets

    def draw(self, screen):
        pygame.draw.circle(screen, "blue", (int(self.pos.x), int(self.pos.y)), 20)


class Enemy:
    def __init__(self, x, y, game_time, is_boss=False, wave_number=0):
        self.is_boss = is_boss
        size = BOSS_SIZE if is_boss else ENEMY_SIZE
        self.rect = pygame.Rect(0, 0, size, size)
        self.pos = pygame.Vector2(x, y)
        self.rect.center = self.pos

        normal_health = self.normal_enemy_health(game_time, wave_number)
        if is_boss:
            self.speed = BOSS_SPEED
            self.health = normal_health * 3
            self.points = 12 + wave_number * 3
        else:
            self.speed = ENEMY_SPEED + min(60, wave_number * 2)
            self.health = normal_health
            self.points = max(1, normal_health // 2)

    @staticmethod
    def normal_enemy_health(game_time, wave_number=0):
        if game_time >= 40:
            return 4 + wave_number // 2
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
    def __init__(self, x, y, angle, damage, speed, radius):
        self.pos = pygame.Vector2(x, y)
        self.damage = damage
        self.radius = radius
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

    def update(self, dt):
        self.pos += self.vel * dt

    def draw(self, screen):
        pygame.draw.circle(screen, "orange", (int(self.pos.x), int(self.pos.y)), self.radius)

    def is_off_screen(self):
        return (
            self.pos.x < -self.radius
            or self.pos.x > WIDTH + self.radius
            or self.pos.y < -self.radius
            or self.pos.y > HEIGHT + self.radius
        )


class Shop:
    def __init__(self):
        self.open = False
        self.items = [
            self.item(pygame.K_1, "1) Max Health +1", 5, 2, self.buy_health),
            self.item(pygame.K_2, "2) Heal +2", 4, 2, self.buy_heal),
            self.item(pygame.K_3, "3) Bullet Damage +1", 10, 4, self.buy_damage),
            self.item(pygame.K_4, "4) Faster Fire Rate", 12, 5, self.buy_fire_rate),
            self.item(pygame.K_5, "5) Move Speed +30", 8, 3, self.buy_speed),
            self.item(pygame.K_6, "6) Bullet Speed +75", 7, 3, self.buy_bullet_speed),
            self.item(pygame.K_7, "7) Bullet Size +1", 9, 4, self.buy_bullet_size),
            self.item(pygame.K_8, "8) Extra Shot", 15, 8, self.buy_extra_shot),
            self.item(pygame.K_9, "9) Kill Point Bonus +1", 18, 9, self.buy_point_bonus),
            self.item(pygame.K_0, "0) Health Regen +0.2/s", 20, 10, self.buy_regen),
        ]

    @staticmethod
    def item(key, label, base_cost, cost_growth, apply):
        return {
            "key": key,
            "label": label,
            "base_cost": base_cost,
            "cost_growth": cost_growth,
            "purchases": 0,
            "apply": apply,
        }

    def cost(self, item):
        return item["base_cost"] + item["cost_growth"] * item["purchases"]

    def try_buy(self, key, player, points):
        for item in self.items:
            cost = self.cost(item)
            if key == item["key"] and points >= cost:
                item["apply"](player)
                item["purchases"] += 1
                return points - cost
        return points

    def buy_health(self, player):
        player.max_health += 1
        player.health = min(player.max_health, player.health + 1)

    def buy_heal(self, player):
        player.health = min(player.max_health, player.health + 2)

    def buy_damage(self, player):
        player.damage += 1

    def buy_fire_rate(self, player):
        player.shot_cooldown *= 0.9

    def buy_speed(self, player):
        player.speed += 30

    def buy_bullet_speed(self, player):
        player.bullet_speed += 75

    def buy_bullet_size(self, player):
        player.bullet_radius += 1

    def buy_extra_shot(self, player):
        player.bullet_count += 1
        player.bullet_spread = min(18, player.bullet_spread + 1)

    def buy_point_bonus(self, player):
        player.point_bonus += 1

    def buy_regen(self, player):
        player.regen_rate += 0.2

    def reset_purchases(self):
        for item in self.items:
            item["purchases"] = 0

    def draw(self, screen, font, player, points):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(230, 45, 820, 630)
        pygame.draw.rect(screen, "darkgray", panel)
        pygame.draw.rect(screen, "black", panel, 4)

        title = font.render("Shop - repeat buys allowed - press TAB to close", True, "white")
        screen.blit(title, (panel.x + 30, panel.y + 20))

        points_text = font.render(f"Points: {points}", True, "yellow")
        screen.blit(points_text, (panel.x + 30, panel.y + 60))

        for i, item in enumerate(self.items):
            cost = self.cost(item)
            affordable = points >= cost
            color = "white" if affordable else "gray"
            text = font.render(
                f"{item['label']} - {cost} pts (bought {item['purchases']})",
                True,
                color,
            )
            screen.blit(text, (panel.x + 30, panel.y + 110 + i * 42))

        stats = [
            f"Health: {player.health}/{player.max_health}",
            f"Damage: {player.damage}",
            f"Shot cooldown: {player.shot_cooldown:.2f}s",
            f"Move speed: {player.speed}",
            f"Bullet speed: {player.bullet_speed}",
            f"Bullet size: {player.bullet_radius}",
            f"Bullets/shot: {player.bullet_count}",
            f"Point bonus: +{player.point_bonus}",
            f"Regen: {player.regen_rate:.1f}/s",
        ]
        for i, stat in enumerate(stats):
            text = font.render(stat, True, "black")
            screen.blit(text, (panel.x + 460, panel.y + 110 + i * 42))


def draw_text(screen, font, text, color, x, y):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))


def spawn_enemy(game_time, wave_number=0):
    edge = random.choice(("top", "bottom", "left", "right"))
    if edge == "top":
        x, y = random.randint(0, WIDTH), 0
    elif edge == "bottom":
        x, y = random.randint(0, WIDTH), HEIGHT
    elif edge == "left":
        x, y = 0, random.randint(0, HEIGHT)
    else:
        x, y = WIDTH, random.randint(0, HEIGHT)

    return Enemy(x, y, game_time, wave_number=wave_number)


def spawn_boss(game_time, wave_number=0):
    return Enemy(WIDTH // 2, 60, game_time, is_boss=True, wave_number=wave_number)


def spawn_infinite_wave(game):
    game["wave_number"] += 1
    count = 6 + game["wave_number"] * 2
    for _ in range(count):
        game["enemies"].append(spawn_enemy(game["game_time"], game["wave_number"]))

    interval = max(MIN_WAVE_INTERVAL, BASE_WAVE_INTERVAL - game["wave_number"] * 0.25)
    game["next_wave_time"] += interval


def reset_game(shop=None):
    if shop is not None:
        shop.reset_purchases()

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
        "bosses_defeated": 0,
        "next_wave_time": INFINITE_WAVE_START,
        "wave_number": 0,
        "next_boss_time": BOSS_TRIGGER_TIME + BOSS_WAVE_INTERVAL,
    }


def draw_hud(screen, font, player, kills, points, game_time, wave_number, bosses_defeated):
    max_bar_width = 400
    bar_width = min(max_bar_width, player.max_health * 40)
    fill_width = int(bar_width * player.health / player.max_health) if player.max_health else 0
    pygame.draw.rect(screen, "red", (40, 10, fill_width, 20))
    pygame.draw.rect(screen, "black", (40, 10, bar_width, 20), 3)

    draw_text(screen, font, f"Player Health: {player.health}/{player.max_health}", "black", 40, 35)
    draw_text(screen, font, f"Kills: {kills}", "black", 40, 65)
    draw_text(screen, font, f"Points: {points}", "black", 40, 95)
    draw_text(screen, font, f"Time: {int(game_time)}s", "black", 40, 125)
    draw_text(screen, font, f"Infinite Wave: {wave_number}", "black", 40, 155)
    draw_text(screen, font, f"Bosses Defeated: {bosses_defeated}", "black", 40, 185)

    if player.can_shoot():
        draw_text(screen, font, "Shot Ready", "green", 40, 215)
    else:
        draw_text(screen, font, f"Cooldown: {player.shot_timer:.1f}s", "red", 40, 215)

    draw_text(screen, font, "TAB: Shop", "black", WIDTH - 180, 20)


def draw_menu(screen, font, title_font):
    screen.fill("black")
    draw_text(screen, title_font, "Survival Shooter", "white", 430, 150)
    draw_text(screen, font, "WASD to move. Left click to shoot.", "gray", 430, 260)
    draw_text(screen, font, "Earn points from kills, then press TAB for repeatable upgrades.", "gray", 430, 305)
    draw_text(screen, font, "Bosses start at 50 seconds and waves continue forever.", "gray", 430, 350)
    draw_text(screen, font, "Press ENTER to start or Q to quit.", "yellow", 430, 430)


def draw_end_screen(screen, font, title, kills, points, wave_number, bosses_defeated):
    screen.fill("black")
    draw_text(screen, font, title, "white", 540, 260)
    draw_text(screen, font, f"Final Kills: {kills}", "white", 540, 310)
    draw_text(screen, font, f"Final Points: {points}", "white", 540, 350)
    draw_text(screen, font, f"Highest Wave: {wave_number}", "white", 540, 390)
    draw_text(screen, font, f"Bosses Defeated: {bosses_defeated}", "white", 540, 430)
    draw_text(screen, font, "Press R to Restart, M for Menu, or Q to Quit", "gray", 420, 485)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Survival Shooter")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 72)

    shop = Shop()
    game = reset_game(shop)
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
                    game = reset_game(shop)
                    shop.open = False
                    state = "playing"
                elif state == "game_over":
                    if event.key == pygame.K_r:
                        game = reset_game(shop)
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
                    game["bullets"].extend(player.shoot(mx, my))

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
                                game["points"] += enemy.points + player.point_bonus
                                if enemy.is_boss:
                                    game["bosses_defeated"] += 1
                            break

                for enemy in game["enemies"][:]:
                    enemy.update(player.pos, dt, game["enemies"])
                    if enemy.rect.colliderect(player.rect) and game["damage_cooldown"] <= 0:
                        player.health -= 1
                        game["damage_cooldown"] = player.hurt_cooldown
                        if player.health <= 0:
                            state = "game_over"
                            break

                if state == "playing":
                    for trigger_time, count in SPAWN_TIMING.items():
                        if game["game_time"] >= trigger_time and trigger_time not in game["spawned"]:
                            if trigger_time == BOSS_TRIGGER_TIME:
                                game["enemies"].append(spawn_boss(game["game_time"], game["wave_number"]))
                            else:
                                for _ in range(count):
                                    game["enemies"].append(spawn_enemy(game["game_time"], game["wave_number"]))
                            game["spawned"].add(trigger_time)

                while state == "playing" and game["game_time"] >= game["next_wave_time"]:
                    spawn_infinite_wave(game)

                while state == "playing" and game["game_time"] >= game["next_boss_time"]:
                    game["enemies"].append(spawn_boss(game["game_time"], game["wave_number"]))
                    game["next_boss_time"] += BOSS_WAVE_INTERVAL

            player.draw(screen)
            for bullet in game["bullets"]:
                bullet.draw(screen)
            for enemy in game["enemies"]:
                enemy.draw(screen, font)
            draw_hud(
                screen,
                font,
                player,
                game["kills"],
                game["points"],
                game["game_time"],
                game["wave_number"],
                game["bosses_defeated"],
            )

            if shop.open:
                shop.draw(screen, font, player, game["points"])
        elif state == "game_over":
            draw_end_screen(
                screen,
                font,
                "GAME OVER",
                game["kills"],
                game["points"],
                game["wave_number"],
                game["bosses_defeated"],
            )

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
