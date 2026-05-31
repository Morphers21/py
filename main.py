import json
import math
import random
from pathlib import Path

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
MIN_SHOT_COOLDOWN = 0.18
MAX_BULLET_SPEED = 1200
MAX_BULLET_RADIUS = 28

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
START_XP_REQUIREMENT = 6
XP_REQUIREMENT_MULTIPLIER = 1.45
LEVEL_UP_CARD_COUNT = 3
META_FILE = Path("survival_shooter_scores.json")


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
        self.xp_multiplier = 1.0
        self.bullet_pierce = 0
        self.rocket_level = 0
        self.laser_level = 0
        self.kill_heal = 0.0
        self.armor = 0
        self.luck = 0
        self.boomerang_level = 0
        self.chain_level = 0
        self.mine_level = 0
        self.charge_level = 1
        self.curse_berserker = False
        self.railgun_level = 0
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
                    pierce=self.bullet_pierce,
                    color="orange",
                    weapon_type="bullet",
                )
            )

        if self.rocket_level > 0:
            rocket_count = min(3, 1 + max(0, self.bullet_count - 1) // 5)
            rocket_step = math.radians(8)
            rocket_spread = rocket_step * (rocket_count - 1)
            for i in range(rocket_count):
                angle = base_angle - rocket_spread / 2 + rocket_step * i
                bullets.append(
                    Bullet(
                        self.pos.x,
                        self.pos.y,
                        angle,
                        math.ceil(self.damage * (2.0 + self.rocket_level * 0.35)),
                        self.bullet_speed * (0.5 + min(0.25, self.rocket_level * 0.03)),
                        max(self.bullet_radius + 5, math.ceil(self.bullet_radius * 1.5)),
                        color="orangered",
                        weapon_type="rocket",
                        splash_radius=50 + self.bullet_radius * 3 + self.rocket_level * 18,
                    )
                )

        if self.laser_level > 0:
            laser_count = min(4, 1 + max(0, self.bullet_count - 1) // 4)
            laser_step = math.radians(5)
            laser_spread = laser_step * (laser_count - 1)
            for i in range(laser_count):
                angle = base_angle - laser_spread / 2 + laser_step * i
                bullets.append(
                    Bullet(
                        self.pos.x,
                        self.pos.y,
                        angle,
                        max(1, math.ceil(self.damage * (0.75 + self.laser_level * 0.12))),
                        self.bullet_speed * (1.8 + min(0.6, self.laser_level * 0.08)),
                        max(5, math.ceil(self.bullet_radius * 0.45)),
                        pierce=2 + self.laser_level + self.bullet_pierce,
                        color="cyan",
                        weapon_type="laser",
                    )
                )

        if self.rocket_level >= 3 and self.laser_level >= 3:
            self.railgun_level = max(self.railgun_level, 1)
        if self.railgun_level > 0:
            bullets.append(
                Bullet(
                    self.pos.x,
                    self.pos.y,
                    base_angle,
                    self.damage * (4 + self.railgun_level),
                    self.bullet_speed * 2.4,
                    max(7, self.bullet_radius * 0.6),
                    pierce=8 + self.bullet_pierce,
                    color="white",
                    weapon_type="railgun",
                )
            )

        return bullets


    def charged_shot(self, target_x, target_y, charge_time):
        charge = min(3.0, max(1.0, 1.0 + charge_time * 1.4 + self.charge_level * 0.25))
        dx = target_x - self.pos.x
        dy = target_y - self.pos.y
        angle = math.atan2(dy, dx) if dx or dy else 0
        return Bullet(
            self.pos.x,
            self.pos.y,
            angle,
            math.ceil(self.damage * charge * 2),
            self.bullet_speed * 0.85,
            min(MAX_BULLET_RADIUS * 1.4, self.bullet_radius * charge),
            pierce=self.bullet_pierce + self.charge_level,
            color="magenta",
            weapon_type="charge",
        )

    def draw(self, screen):
        pygame.draw.circle(screen, "blue", (int(self.pos.x), int(self.pos.y)), 20)


class Enemy:
    def __init__(self, x, y, game_time, is_boss=False, wave_number=0, enemy_type="normal"):
        self.is_boss = is_boss
        self.enemy_type = "boss" if is_boss else enemy_type
        size = BOSS_SIZE if is_boss else ENEMY_SIZE
        if self.enemy_type == "swarm":
            size = 24
        elif self.enemy_type == "splitter":
            size = 64
        self.rect = pygame.Rect(0, 0, size, size)
        self.pos = pygame.Vector2(x, y)
        self.rect.center = self.pos
        self.flash_timer = 0
        self.shoot_timer = random.uniform(0.4, 1.4)
        self.facing = pygame.Vector2(1, 0)

        normal_health = self.normal_enemy_health(game_time, wave_number)
        if is_boss:
            self.speed = BOSS_SPEED
            self.health = normal_health * 3
            self.points = 12 + wave_number * 3
            self.xp_reward = 8 + wave_number * 2
        elif self.enemy_type == "swarm":
            self.speed = (ENEMY_SPEED + min(60, wave_number * 2)) * 2
            self.health = 1
            self.points = 1
            self.xp_reward = 1
        elif self.enemy_type == "ranged":
            self.speed = ENEMY_SPEED * 0.85
            self.health = normal_health + 1
            self.points = max(2, normal_health)
            self.xp_reward = normal_health + 1
        elif self.enemy_type == "shield":
            self.speed = ENEMY_SPEED * 0.8
            self.health = normal_health + 2
            self.points = max(2, normal_health)
            self.xp_reward = normal_health + 1
        elif self.enemy_type == "splitter":
            self.speed = ENEMY_SPEED * 0.7
            self.health = normal_health * 2 + 2
            self.points = max(3, normal_health + 1)
            self.xp_reward = normal_health + 2
        else:
            self.speed = ENEMY_SPEED + min(60, wave_number * 2)
            self.health = normal_health
            self.points = max(1, normal_health // 2)
            self.xp_reward = max(1, normal_health)

    @staticmethod
    def normal_enemy_health(game_time, wave_number=0):
        if game_time >= 40:
            return 4 + wave_number // 2
        if game_time >= 27:
            return 3
        if game_time >= 15:
            return 2
        return 1

    def update(self, player_pos, dt, enemies, game=None):
        to_player = player_pos - self.pos
        distance = to_player.length()
        if distance != 0:
            self.facing = to_player.normalize()
            should_move = not (self.enemy_type == "ranged" and distance < 360)
            if should_move:
                self.pos += self.facing * self.speed * dt

        if self.enemy_type == "ranged" and game is not None:
            self.shoot_timer -= dt
            if distance < 520 and self.shoot_timer <= 0:
                angle = math.atan2(self.facing.y, self.facing.x)
                game["enemy_bullets"].append(
                    Bullet(self.pos.x, self.pos.y, angle, 1, 280, 6, color="purple", weapon_type="enemy")
                )
                self.shoot_timer = 1.6

        self.flash_timer = max(0, self.flash_timer - dt)
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

    def blocks_from_front(self, bullet):
        if self.enemy_type != "shield":
            return False
        incoming_side = bullet.pos - self.pos
        if incoming_side.length_squared() == 0:
            return False
        return self.facing.dot(incoming_side.normalize()) > 0.25

    def draw(self, screen, font):
        colors = {
            "boss": "purple",
            "swarm": "pink",
            "ranged": "darkorange",
            "shield": "slateblue",
            "splitter": "darkred",
        }
        color = colors.get(self.enemy_type, "red")
        pygame.draw.rect(screen, color, self.rect)
        if self.enemy_type == "shield":
            front = self.pos + self.facing * (self.rect.width / 2)
            pygame.draw.circle(screen, "lightblue", (int(front.x), int(front.y)), 6)
        if self.flash_timer > 0:
            flash = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 150))
            screen.blit(flash, self.rect.topleft)
        health_text = font.render(str(math.ceil(self.health)), True, "white" if self.is_boss else "black")
        screen.blit(health_text, (self.rect.x + 6, self.rect.y + 6))


class Bullet:
    def __init__(
        self,
        x,
        y,
        angle,
        damage,
        speed,
        radius,
        pierce=0,
        color="orange",
        weapon_type="bullet",
        splash_radius=0,
    ):
        self.pos = pygame.Vector2(x, y)
        self.prev_pos = self.pos.copy()
        self.damage = damage
        self.radius = radius
        self.pierce = pierce
        self.color = color
        self.weapon_type = weapon_type
        self.splash_radius = splash_radius
        self.hit_enemies = set()
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

    def update(self, dt):
        self.prev_pos = self.pos.copy()
        self.pos += self.vel * dt

    def collides_with(self, rect):
        if self.weapon_type == "laser":
            direction = self.vel.normalize() if self.vel.length_squared() else pygame.Vector2(1, 0)
            start = self.pos - direction * 14
            end = self.pos + direction * 14
            return self.segment_hits_rect(start, end, rect, self.radius)

        if self.circle_hits_rect(self.pos, rect, self.radius):
            return True

        # Swept collision catches fast projectiles that pass through an enemy between frames.
        return self.segment_hits_rect(self.prev_pos, self.pos, rect, self.radius)

    @staticmethod
    def circle_hits_rect(center, rect, radius):
        closest_x = max(rect.left, min(center.x, rect.right))
        closest_y = max(rect.top, min(center.y, rect.bottom))
        dx = center.x - closest_x
        dy = center.y - closest_y
        return dx * dx + dy * dy <= radius * radius

    @staticmethod
    def segment_hits_rect(start, end, rect, radius):
        inflated = rect.inflate(radius * 2, radius * 2)
        return bool(
            inflated.clipline(
                (int(start.x), int(start.y)),
                (int(end.x), int(end.y)),
            )
        )

    def draw(self, screen):
        center = (int(self.pos.x), int(self.pos.y))
        draw_radius = max(1, int(round(self.radius)))
        if self.weapon_type == "laser":
            direction = self.vel.normalize() if self.vel.length_squared() else pygame.Vector2(1, 0)
            start = self.pos - direction * 14
            end = self.pos + direction * 14
            pygame.draw.line(screen, self.color, start, end, draw_radius)
        elif self.weapon_type == "rocket":
            pygame.draw.circle(screen, self.color, center, draw_radius)
            pygame.draw.circle(screen, "yellow", center, max(3, draw_radius // 2))
        else:
            pygame.draw.circle(screen, self.color, center, draw_radius)

    def is_off_screen(self):
        return (
            self.pos.x < -self.radius
            or self.pos.x > WIDTH + self.radius
            or self.pos.y < -self.radius
            or self.pos.y > HEIGHT + self.radius
        )


class Explosion:
    def __init__(self, pos, radius):
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.life = 0.35
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def is_done(self):
        return self.life <= 0

    def draw(self, screen):
        progress = max(0, self.life / self.max_life)
        radius = int(self.radius * (1.05 - progress * 0.15))
        size = radius * 2 + 6
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        fill_alpha = int(35 * progress)
        ring_alpha = int(110 * progress)
        pygame.draw.circle(surface, (255, 150, 0, fill_alpha), center, radius)
        pygame.draw.circle(surface, (255, 220, 80, ring_alpha), center, radius, 3)
        screen.blit(surface, (self.pos.x - size // 2, self.pos.y - size // 2))


class Mine:
    def __init__(self, pos, damage, radius):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.arm_time = 0.35
        self.life = 12

    def update(self, dt):
        self.arm_time -= dt
        self.life -= dt

    def ready(self):
        return self.arm_time <= 0

    def is_done(self):
        return self.life <= 0

    def draw(self, screen):
        color = "darkgreen" if self.ready() else "gray"
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), 9)
        pygame.draw.circle(screen, "lime", (int(self.pos.x), int(self.pos.y)), int(self.radius), 1)


class XpOrb:
    def __init__(self, pos, amount):
        self.pos = pygame.Vector2(pos)
        self.amount = amount
        self.radius = 8

    def update(self, player_pos, dt):
        to_player = player_pos - self.pos
        distance = to_player.length()
        if distance < 170 and distance > 0:
            self.pos += to_player.normalize() * 260 * dt

    def draw(self, screen):
        pygame.draw.circle(screen, "deepskyblue", (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(screen, "white", (int(self.pos.x), int(self.pos.y)), self.radius, 1)


class FloatingText:
    def __init__(self, pos, text, color="yellow"):
        self.pos = pygame.Vector2(pos)
        self.text = text
        self.color = color
        self.life = 0.8

    def update(self, dt):
        self.life -= dt
        self.pos.y -= 35 * dt

    def is_done(self):
        return self.life <= 0

    def draw(self, screen, font):
        rendered = font.render(self.text, True, self.color)
        screen.blit(rendered, (self.pos.x, self.pos.y))


class LightningEffect:
    def __init__(self, points):
        self.points = [pygame.Vector2(point) for point in points]
        self.life = 0.18

    def update(self, dt):
        self.life -= dt

    def is_done(self):
        return self.life <= 0

    def draw(self, screen):
        if len(self.points) >= 2:
            pygame.draw.lines(screen, "cyan", False, self.points, 3)


class Shop:
    def __init__(self):
        self.open = False
        self.items = [
            self.item(pygame.K_1, "1) Max Health +1", 5, 2, self.buy_health),
            self.item(pygame.K_2, "2) Heal +2", 4, 2, self.buy_heal),
            self.item(pygame.K_3, "3) Bullet Damage +1", 10, 4, self.buy_damage),
            self.item(pygame.K_4, "4) Faster Fire Rate", 12, 5, self.buy_fire_rate),
            self.item(pygame.K_5, "5) Move Speed +30", 8, 3, self.buy_speed),
            self.item(pygame.K_6, "6) Bullet Speed +40", 7, 3, self.buy_bullet_speed),
            self.item(pygame.K_7, "7) Bullet Size +0.5", 9, 4, self.buy_bullet_size),
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

    def layout(self):
        panel = pygame.Rect(WIDTH - 365, 45, 340, 445)
        list_rect = pygame.Rect(panel.x + 10, panel.y + 72, panel.width - 20, 330)
        return panel, list_rect

    def item_rect(self, index, list_rect):
        row_height = 31
        y = list_rect.y + 10 + index * row_height
        return pygame.Rect(list_rect.x + 8, y - 3, list_rect.width - 16, row_height - 4)

    def buy_item(self, item, player, points):
        cost = self.cost(item)
        if points < cost:
            return points

        item["apply"](player)
        item["purchases"] += 1
        return points - cost

    def try_buy(self, key, player, points):
        for item in self.items:
            if key == item["key"]:
                return self.buy_item(item, player, points)
        return points

    def try_buy_at_pos(self, pos, player, points):
        _, list_rect = self.layout()
        for index, item in enumerate(self.items):
            if self.item_rect(index, list_rect).collidepoint(pos):
                return self.buy_item(item, player, points)
        return points

    def buy_health(self, player):
        player.max_health += 1
        player.health = min(player.max_health, player.health + 1)

    def buy_heal(self, player):
        player.health = min(player.max_health, player.health + 2)

    def buy_damage(self, player):
        player.damage += 1

    def buy_fire_rate(self, player):
        player.shot_cooldown = max(MIN_SHOT_COOLDOWN, player.shot_cooldown * 0.95)

    def buy_speed(self, player):
        player.speed += 30

    def buy_bullet_speed(self, player):
        player.bullet_speed = min(MAX_BULLET_SPEED, player.bullet_speed + 40)

    def buy_bullet_size(self, player):
        player.bullet_radius = min(MAX_BULLET_RADIUS, player.bullet_radius + 0.5)

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

    def draw(self, screen, font, small_font, tiny_font, player, points):
        panel, list_rect = self.layout()
        pygame.draw.rect(screen, (45, 45, 45), panel, border_radius=12)
        pygame.draw.rect(screen, "black", panel, 4, border_radius=12)

        title = small_font.render("SHOP", True, "white")
        screen.blit(title, (panel.x + 14, panel.y + 12))
        points_text = small_font.render(f"{points} pts", True, "yellow")
        screen.blit(points_text, (panel.right - points_text.get_width() - 14, panel.y + 12))
        hint = tiny_font.render("Click rows or press 1-0. I = stats.", True, "lightgray")
        screen.blit(hint, (panel.x + 14, panel.y + 42))

        pygame.draw.rect(screen, (68, 68, 68), list_rect, border_radius=8)
        pygame.draw.rect(screen, "black", list_rect, 2, border_radius=8)

        for i, item in enumerate(self.items):
            cost = self.cost(item)
            affordable = points >= cost
            row_rect = self.item_rect(i, list_rect)
            y = row_rect.y + 3
            pygame.draw.rect(screen, (45, 85, 50) if affordable else (55, 55, 55), row_rect, border_radius=5)

            label = tiny_font.render(item["label"], True, "white" if affordable else "lightgray")
            meta = tiny_font.render(f"{cost} | x{item['purchases']}", True, "yellow" if affordable else "gray")
            screen.blit(label, (row_rect.x + 7, y))
            screen.blit(meta, (row_rect.right - meta.get_width() - 7, y))

        footer = tiny_font.render("Detailed stats moved to the I menu.", True, "lightgray")
        screen.blit(footer, (panel.x + 14, list_rect.bottom + 12))



def load_meta():
    if not META_FILE.exists():
        return {"high_scores": [], "prestige": 0}
    try:
        data = json.loads(META_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"high_scores": [], "prestige": 0}
    data.setdefault("high_scores", [])
    data.setdefault("prestige", 0)
    return data


def save_meta(meta):
    META_FILE.write_text(json.dumps(meta, indent=2))


def record_run(meta, game):
    score = game["points"] + game["kills"] * 2 + game["bosses_defeated"] * 25
    meta["high_scores"].append(
        {
            "score": score,
            "kills": game["kills"],
            "level": game["level"],
            "wave": game["wave_number"],
        }
    )
    meta["high_scores"] = sorted(meta["high_scores"], key=lambda row: row["score"], reverse=True)[:5]
    meta["prestige"] = meta.get("prestige", 0) + max(1, game["level"] // 3)
    save_meta(meta)
    return score


def draw_text(screen, font, text, color, x, y):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))


def spawn_enemy(game_time, wave_number=0, enemy_type=None):
    edge = random.choice(("top", "bottom", "left", "right"))
    if edge == "top":
        x, y = random.randint(0, WIDTH), 0
    elif edge == "bottom":
        x, y = random.randint(0, WIDTH), HEIGHT
    elif edge == "left":
        x, y = 0, random.randint(0, HEIGHT)
    else:
        x, y = WIDTH, random.randint(0, HEIGHT)

    if enemy_type is None:
        roll = random.random()
        if wave_number >= 5 and roll < 0.12:
            enemy_type = "ranged"
        elif wave_number >= 3 and roll < 0.24:
            enemy_type = "shield"
        elif wave_number >= 4 and roll < 0.34:
            enemy_type = "splitter"
        else:
            enemy_type = "normal"
    return Enemy(x, y, game_time, wave_number=wave_number, enemy_type=enemy_type)


def spawn_boss(game_time, wave_number=0):
    return Enemy(WIDTH // 2, 60, game_time, is_boss=True, wave_number=wave_number)


def spawn_infinite_wave(game):
    game["wave_number"] += 1
    count = 6 + game["wave_number"] * 2
    for _ in range(count):
        game["enemies"].append(spawn_enemy(game["game_time"], game["wave_number"]))
    if game["wave_number"] % 3 == 0:
        for _ in range(20):
            game["enemies"].append(spawn_enemy(game["game_time"], game["wave_number"], "swarm"))
    game["kills_per_wave"].setdefault(game["wave_number"], 0)

    interval = max(MIN_WAVE_INTERVAL, BASE_WAVE_INTERVAL - game["wave_number"] * 0.25)
    game["next_wave_time"] += interval


def xp_requirement(level):
    return math.ceil(START_XP_REQUIREMENT * XP_REQUIREMENT_MULTIPLIER ** (level - 1))


def start_level_up_if_ready(game):
    if game["level_up_cards"] or game["xp"] < game["xp_to_next_level"]:
        return False

    game["xp"] -= game["xp_to_next_level"]
    game["level"] += 1
    game["xp_to_next_level"] = xp_requirement(game["level"])
    game["level_up_cards"] = make_level_cards(game["player"])
    return True


def add_xp(game, amount):
    gained = max(1, round(amount * game["player"].xp_multiplier))
    game["xp"] += gained
    return start_level_up_if_ready(game)


def make_level_cards(player=None):
    cards = [
        {
            "name": "Power Card",
            "description": "Bullet damage x1.25",
            "apply": apply_damage_card,
        },
        {
            "name": "Rapid Card",
            "description": "Shot cooldown x0.90",
            "apply": apply_fire_rate_card,
        },
        {
            "name": "Swift Card",
            "description": "Move speed x1.18",
            "apply": apply_speed_card,
        },
        {
            "name": "Tank Card",
            "description": "Max health x1.25 and heal",
            "apply": apply_health_card,
        },
        {
            "name": "Velocity Card",
            "description": "Bullet speed x1.12",
            "apply": apply_bullet_speed_card,
        },
        {
            "name": "Giant Card",
            "description": "Bullet size x1.10",
            "apply": apply_bullet_size_card,
        },
        {
            "name": "Wisdom Card",
            "description": "XP gain x1.25",
            "apply": apply_xp_card,
        },
        {
            "name": "Regrowth Card",
            "description": "Health regen x1.5",
            "apply": apply_regen_card,
        },
        {
            "name": "Rocket Launcher" if player is None or player.rocket_level == 0 else "Rocket Upgrade",
            "description": "Unlock explosive rockets" if player is None or player.rocket_level == 0 else "Rocket damage, AoE, and volley +",
            "apply": apply_rocket_card,
        },
        {
            "name": "Laser Rifle" if player is None or player.laser_level == 0 else "Laser Upgrade",
            "description": "Unlock piercing lasers" if player is None or player.laser_level == 0 else "Laser damage, speed, and pierce +",
            "apply": apply_laser_card,
        },
        {
            "name": "Piercing Ammo",
            "description": "Bullets pierce +1 enemy",
            "apply": apply_pierce_card,
        },
        {
            "name": "Scatter Weapon",
            "description": "+2 bullets per shot",
            "apply": apply_scatter_card,
        },
        {
            "name": "Vampire Card",
            "description": f"Heal/kill +{0.1 + (player.kill_heal if player else 0) * 0.25:.2f}",
            "apply": apply_vampire_card,
        },
        {
            "name": "Payday Card",
            "description": "Kill point bonus x1.5",
            "apply": apply_payday_card,
        },
        {
            "name": "Fortress Card",
            "description": "Armor +1, max health +1, longer iframes",
            "apply": apply_armor_card,
        },
        {
            "name": "Second Wind",
            "description": "Heal 50% and regen +0.1/s",
            "apply": apply_second_wind_card,
        },
        {
            "name": "Overclock Card",
            "description": "Damage +1 and cooldown x0.96",
            "apply": apply_overclock_card,
        },
        {
            "name": "Heavy Ammo",
            "description": "Damage +2, bullet speed -5%",
            "apply": apply_heavy_ammo_card,
        },
        {
            "name": "Split Chamber",
            "description": "+1 bullet and pierce +1",
            "apply": apply_split_chamber_card,
        },
        {
            "name": "Magnet Card",
            "description": "XP gain x1.10 and points +1",
            "apply": apply_magnet_card,
        },
        {
            "name": "Lucky Card",
            "description": "Luck +1 and point bonus +1",
            "apply": apply_lucky_card,
        },
        {
            "name": "Boomerang",
            "description": "Orbiting weapon +1",
            "apply": apply_boomerang_card,
        },
        {
            "name": "Chain Lightning",
            "description": "Kills zap nearby enemies",
            "apply": apply_chain_card,
        },
        {
            "name": "Mine Layer",
            "description": "Press E to drop stronger mines",
            "apply": apply_mine_card,
        },
        {
            "name": "Charge Core",
            "description": "Hold/release for bigger charge shots",
            "apply": apply_charge_card,
        },
        {
            "name": "Curse: Berserker",
            "description": "+50% damage, drift toward enemies",
            "apply": apply_berserker_curse,
        },
    ]
    return random.sample(cards, LEVEL_UP_CARD_COUNT)


def apply_level_card(game, card_index):
    cards = game["level_up_cards"]
    if not 0 <= card_index < len(cards):
        return False

    cards[card_index]["apply"](game["player"])
    game["level_up_cards"] = []
    return start_level_up_if_ready(game)


def apply_damage_card(player):
    player.damage = max(player.damage + 1, math.ceil(player.damage * 1.25))


def apply_fire_rate_card(player):
    player.shot_cooldown = max(MIN_SHOT_COOLDOWN, player.shot_cooldown * 0.9)


def apply_speed_card(player):
    player.speed = math.ceil(player.speed * 1.18)


def apply_health_card(player):
    player.max_health = max(player.max_health + 1, math.ceil(player.max_health * 1.25))
    player.health = player.max_health


def apply_bullet_speed_card(player):
    player.bullet_speed = min(MAX_BULLET_SPEED, math.ceil(player.bullet_speed * 1.12))


def apply_bullet_size_card(player):
    player.bullet_radius = min(MAX_BULLET_RADIUS, max(player.bullet_radius + 0.5, player.bullet_radius * 1.1))


def apply_xp_card(player):
    player.xp_multiplier *= 1.25


def apply_regen_card(player):
    player.regen_rate = max(0.2, player.regen_rate * 1.5)


def apply_rocket_card(player):
    player.rocket_level += 1


def apply_laser_card(player):
    player.laser_level += 1


def apply_pierce_card(player):
    player.bullet_pierce += 1


def apply_scatter_card(player):
    player.bullet_count += 2
    player.bullet_spread = min(22, player.bullet_spread + 2)


def apply_vampire_card(player):
    player.kill_heal += 0.1 + player.kill_heal * 0.25


def apply_payday_card(player):
    player.point_bonus = max(player.point_bonus + 1, math.ceil((player.point_bonus + 1) * 1.5))


def apply_armor_card(player):
    player.armor += 1
    player.max_health += 1
    player.health = min(player.max_health, player.health + 1)
    player.hurt_cooldown += 0.05


def apply_second_wind_card(player):
    heal_amount = max(1, math.ceil(player.max_health * 0.5))
    player.health = min(player.max_health, player.health + heal_amount)
    player.regen_rate += 0.1


def apply_overclock_card(player):
    player.damage += 1
    player.shot_cooldown = max(MIN_SHOT_COOLDOWN, player.shot_cooldown * 0.96)


def apply_heavy_ammo_card(player):
    player.damage += 2
    player.bullet_speed = max(BULLET_START_SPEED * 0.5, player.bullet_speed * 0.95)


def apply_split_chamber_card(player):
    player.bullet_count += 1
    player.bullet_pierce += 1
    player.bullet_spread = min(22, player.bullet_spread + 1)


def apply_magnet_card(player):
    player.xp_multiplier *= 1.1
    player.point_bonus += 1


def apply_lucky_card(player):
    player.luck += 1
    player.point_bonus += 1


def apply_boomerang_card(player):
    player.boomerang_level += 1


def apply_chain_card(player):
    player.chain_level += 1


def apply_mine_card(player):
    player.mine_level += 1


def apply_charge_card(player):
    player.charge_level += 1


def apply_berserker_curse(player):
    if not player.curse_berserker:
        player.damage = math.ceil(player.damage * 1.5)
        player.curse_berserker = True
    else:
        player.damage += 2


def make_obstacles():
    return [
        pygame.Rect(250, 170, 80, 260),
        pygame.Rect(570, 90, 140, 70),
        pygame.Rect(850, 330, 90, 250),
        pygame.Rect(470, 520, 260, 70),
    ]


def reset_game(shop=None, meta=None):
    if shop is not None:
        shop.reset_purchases()

    player = Player(WIDTH // 2, HEIGHT // 2)
    prestige = (meta or {}).get("prestige", 0)
    if prestige:
        player.damage += prestige // 3
        player.max_health += prestige // 5
        player.health = player.max_health
        player.speed += min(80, prestige * 2)
    enemies = [spawn_enemy(0) for _ in range(SPAWN_TIMING[3])]
    return {
        "player": player,
        "bullets": [],
        "enemy_bullets": [],
        "effects": [],
        "floating_texts": [],
        "mines": [],
        "xp_orbs": [],
        "obstacles": make_obstacles(),
        "enemies": enemies,
        "spawned": {3},
        "damage_cooldown": 0,
        "game_time": 0,
        "kills": 0,
        "points": 0,
        "level": 1,
        "xp": 0,
        "xp_to_next_level": xp_requirement(1),
        "level_up_cards": [],
        "bosses_defeated": 0,
        "next_wave_time": INFINITE_WAVE_START,
        "wave_number": 0,
        "next_boss_time": BOSS_TRIGGER_TIME + BOSS_WAVE_INTERVAL,
        "safe_radius": 520,
        "safe_damage_timer": 0,
        "boomerang_angle": 0,
        "boomerang_timer": 0,
        "boomerang_positions": [],
        "last_kill_time": -99,
        "streak": 0,
        "kills_per_wave": {0: 0},
        "damage_dealt": 0,
        "dps_samples": [],
        "dps_timer": 0,
        "sample_damage": 0,
        "run_recorded": False,
        "final_score": 0,
        "shake_timer": 0,
        "shake_intensity": 0,
        "charge_start": None,
    }


def defeat_enemy(game, enemy):
    if enemy not in game["enemies"]:
        return False

    player = game["player"]
    game["enemies"].remove(enemy)
    game["kills"] += 1
    game["kills_per_wave"][game["wave_number"]] = game["kills_per_wave"].get(game["wave_number"], 0) + 1
    if game["game_time"] - game["last_kill_time"] <= 3:
        game["streak"] += 1
    else:
        game["streak"] = 1
    game["last_kill_time"] = game["game_time"]
    streak_bonus = 1 + min(4, game["streak"] // 5)
    game["points"] += (enemy.points + player.point_bonus) * streak_bonus
    if streak_bonus > 1:
        game["floating_texts"].append(FloatingText(enemy.pos, f"x{streak_bonus}", "gold"))
    if player.kill_heal > 0:
        player.health = min(player.max_health, player.health + player.kill_heal)
    if player.chain_level > 0:
        chain_lightning(game, enemy.pos, player.chain_level)
    if enemy.enemy_type == "splitter":
        for offset in (-18, 18):
            child = Enemy(enemy.pos.x + offset, enemy.pos.y, game["game_time"], wave_number=game["wave_number"], enemy_type="swarm")
            game["enemies"].append(child)
    if enemy.is_boss:
        game["bosses_defeated"] += 1
        game["shake_timer"] = 0.35
        game["shake_intensity"] = 10
    game["xp_orbs"].append(XpOrb(enemy.pos, enemy.xp_reward))
    return False


def damage_enemy(game, enemy, damage):
    enemy.health -= damage
    enemy.flash_timer = 0.12
    game["damage_dealt"] += damage
    game["sample_damage"] += damage
    game["floating_texts"].append(FloatingText(enemy.pos, str(math.ceil(damage)), "white"))
    if enemy.health <= 0:
        return defeat_enemy(game, enemy)
    return False


def chain_lightning(game, origin, level):
    current = pygame.Vector2(origin)
    points = [current]
    hit = set()
    for _ in range(min(5, 1 + level)):
        candidates = [enemy for enemy in game["enemies"] if id(enemy) not in hit and enemy.pos.distance_to(current) < 220]
        if not candidates:
            break
        target = min(candidates, key=lambda enemy: enemy.pos.distance_to(current))
        hit.add(id(target))
        points.append(target.pos.copy())
        damage_enemy(game, target, max(1, game["player"].damage // 2 + level))
        current = target.pos.copy()
    if len(points) > 1:
        game["effects"].append(LightningEffect(points))


def explode_rocket(game, rocket):
    game["effects"].append(Explosion(rocket.pos, rocket.splash_radius))
    leveled_up = False
    for enemy in game["enemies"][:]:
        distance = rocket.pos.distance_to(enemy.pos)
        if distance <= rocket.splash_radius + enemy.rect.width / 2:
            leveled_up = damage_enemy(game, enemy, rocket.damage) or leveled_up
    return leveled_up



def format_number(value):
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}" if value >= 10 else f"{value:.2f}".rstrip("0").rstrip(".")
    return str(int(value)) if isinstance(value, float) else str(value)


def player_stat_rows(player):
    return [
        ("Health", f"{format_number(player.health)}/{player.max_health}"),
        ("Damage", str(player.damage)),
        ("Shot cooldown", f"{player.shot_cooldown:.2f}s"),
        ("Move speed", str(player.speed)),
        ("Bullet speed", str(player.bullet_speed)),
        ("Bullet size", f"{player.bullet_radius:.1f}"),
        ("Bullets/shot", str(player.bullet_count)),
        ("Pierce", str(player.bullet_pierce)),
        ("Rocket", f"Lv {player.rocket_level}"),
        ("Laser", f"Lv {player.laser_level}"),
        ("Heal/kill", f"+{player.kill_heal:.2f}"),
        ("Point bonus", f"+{player.point_bonus}"),
        ("XP gain", f"x{player.xp_multiplier:.2f}"),
        ("Regen", f"{player.regen_rate:.1f}/s"),
        ("Armor", str(player.armor)),
        ("Luck", str(player.luck)),
        ("Boomerang", f"Lv {player.boomerang_level}"),
        ("Chain", f"Lv {player.chain_level}"),
        ("Mines", f"Lv {player.mine_level}"),
        ("Charge", f"Lv {player.charge_level}"),
        ("Railgun", f"Lv {player.railgun_level}"),
        ("Berserker", "on" if player.curse_berserker else "off"),
    ]



def damage_player(game, amount):
    player = game["player"]
    player.health -= amount
    game["damage_cooldown"] = player.hurt_cooldown
    game["shake_timer"] = 0.25
    game["shake_intensity"] = 6
    return player.health <= 0


def drop_mine(game):
    player = game["player"]
    if player.mine_level <= 0:
        return
    game["mines"].append(Mine(player.pos, player.damage * (2 + player.mine_level), 45 + player.mine_level * 10))


def update_player_pressure(game, dt):
    player = game["player"]
    if player.curse_berserker and game["enemies"]:
        nearest = min(game["enemies"], key=lambda enemy: enemy.pos.distance_to(player.pos))
        direction = nearest.pos - player.pos
        if direction.length_squared() > 0:
            player.pos += direction.normalize() * 45 * dt
            player.rect.center = (int(player.pos.x), int(player.pos.y))

    game["safe_radius"] = max(120, 520 - game["game_time"] * 2.2)
    if player.pos.distance_to(pygame.Vector2(WIDTH / 2, HEIGHT / 2)) > game["safe_radius"]:
        game["safe_damage_timer"] -= dt
        if game["safe_damage_timer"] <= 0:
            damage_player(game, 1)
            game["safe_damage_timer"] = 1.2
    else:
        game["safe_damage_timer"] = 0.5


def update_xp_orbs(game, dt):
    player = game["player"]
    for orb in game["xp_orbs"][:]:
        orb.update(player.pos, dt)
        if orb.pos.distance_to(player.pos) < 24:
            game["xp_orbs"].remove(orb)
            if add_xp(game, orb.amount):
                return True
    return False


def update_mines(game, dt):
    for mine in game["mines"][:]:
        mine.update(dt)
        if mine.is_done():
            game["mines"].remove(mine)
            continue
        if not mine.ready():
            continue
        for enemy in game["enemies"][:]:
            if enemy.pos.distance_to(mine.pos) <= mine.radius + enemy.rect.width / 2:
                game["effects"].append(Explosion(mine.pos, mine.radius))
                damage_enemy(game, enemy, mine.damage)
                if mine in game["mines"]:
                    game["mines"].remove(mine)
                break


def update_boomerang(game, dt):
    player = game["player"]
    if player.boomerang_level <= 0:
        game["boomerang_positions"] = []
        return []
    game["boomerang_angle"] += dt * (2.5 + player.boomerang_level * 0.25)
    game["boomerang_timer"] -= dt
    positions = []
    count = min(4, player.boomerang_level)
    for index in range(count):
        angle = game["boomerang_angle"] + index * math.tau / count
        pos = player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * (70 + player.boomerang_level * 8)
        positions.append(pos)
    game["boomerang_positions"] = positions
    if game["boomerang_timer"] <= 0:
        game["boomerang_timer"] = 0.22
        for pos in positions:
            for enemy in game["enemies"][:]:
                if enemy.pos.distance_to(pos) < enemy.rect.width / 2 + 12:
                    damage_enemy(game, enemy, max(1, player.damage // 2 + player.boomerang_level))
    return positions


def update_enemy_bullets(game, dt):
    player = game["player"]
    for bullet in game["enemy_bullets"][:]:
        bullet.update(dt)
        if bullet.is_off_screen():
            game["enemy_bullets"].remove(bullet)
            continue
        if bullet.collides_with(player.rect) and game["damage_cooldown"] <= 0:
            if damage_player(game, bullet.damage):
                return True
            if bullet in game["enemy_bullets"]:
                game["enemy_bullets"].remove(bullet)
    return False


def update_effects_and_text(game, dt):
    for effect in game["effects"][:]:
        effect.update(dt)
        if effect.is_done():
            game["effects"].remove(effect)
    for text in game["floating_texts"][:]:
        text.update(dt)
        if text.is_done():
            game["floating_texts"].remove(text)
    game["dps_timer"] += dt
    if game["dps_timer"] >= 1:
        game["dps_samples"].append(game["sample_damage"])
        game["dps_samples"] = game["dps_samples"][-60:]
        game["sample_damage"] = 0
        game["dps_timer"] = 0


def player_hits_obstacle(player, obstacles):
    return any(player.rect.colliderect(obstacle) for obstacle in obstacles)


def draw_hud(
    screen,
    small_font,
    tiny_font,
    player,
    kills,
    points,
    level,
    xp,
    xp_to_next_level,
    game_time,
    wave_number,
    bosses_defeated,
):
    panel = pygame.Rect(18, 14, 300, 150)
    pygame.draw.rect(screen, (245, 245, 245), panel, border_radius=8)
    pygame.draw.rect(screen, "black", panel, 2, border_radius=8)

    health_bar_width = 190
    xp_bar_width = 145
    health_fill = int(health_bar_width * player.health / player.max_health) if player.max_health else 0
    xp_fill = int(xp_bar_width * xp / xp_to_next_level) if xp_to_next_level else 0

    hp_text = tiny_font.render(f"HP {format_number(player.health)}/{player.max_health}", True, "black")
    screen.blit(hp_text, (panel.x + 12, panel.y + 10))
    pygame.draw.rect(screen, "darkred", (panel.x + 85, panel.y + 12, health_bar_width, 12))
    pygame.draw.rect(screen, "red", (panel.x + 85, panel.y + 12, health_fill, 12))
    pygame.draw.rect(screen, "black", (panel.x + 85, panel.y + 12, health_bar_width, 12), 1)

    level_text = tiny_font.render(f"Lv {level}", True, "black")
    screen.blit(level_text, (panel.x + 12, panel.y + 36))
    pygame.draw.rect(screen, (120, 90, 0), (panel.x + 65, panel.y + 39, xp_bar_width, 12))
    pygame.draw.rect(screen, "gold", (panel.x + 65, panel.y + 39, xp_fill, 12))
    pygame.draw.rect(screen, "black", (panel.x + 65, panel.y + 39, xp_bar_width, 12), 1)
    xp_value_text = tiny_font.render(f"XP {xp}/{xp_to_next_level}", True, "black")
    screen.blit(xp_value_text, (panel.x + 220, panel.y + 36))

    lines = [
        f"Pts {points}   Kills {kills}",
        f"Time {int(game_time)}s   Wave {wave_number}",
        f"Bosses {bosses_defeated}",
    ]
    for i, line in enumerate(lines):
        text = tiny_font.render(line, True, "black")
        screen.blit(text, (panel.x + 12, panel.y + 64 + i * 20))

    shot_text = "Ready" if player.can_shoot() else f"CD {player.shot_timer:.1f}s"
    shot_color = "green" if player.can_shoot() else "red"
    shot_surface = tiny_font.render(f"Shot: {shot_text}", True, shot_color)
    screen.blit(shot_surface, (panel.x + 12, panel.y + 126))
    hint_surface = tiny_font.render(" | TAB shop | I stats", True, "black")
    screen.blit(hint_surface, (panel.x + 12 + shot_surface.get_width(), panel.y + 126))


def draw_stats_menu(screen, font, small_font, tiny_font, player, game):
    panel = pygame.Rect(WIDTH // 2 - 240, 80, 480, 520)
    pygame.draw.rect(screen, (40, 40, 40), panel, border_radius=12)
    pygame.draw.rect(screen, "black", panel, 4, border_radius=12)

    title = font.render("Stats / Weapons", True, "white")
    screen.blit(title, (panel.x + 24, panel.y + 20))
    hint = tiny_font.render("Press I to close. Game is paused while this is open.", True, "lightgray")
    screen.blit(hint, (panel.x + 24, panel.y + 60))

    summary = [
        ("Level", str(game["level"])),
        ("XP", f"{game['xp']}/{game['xp_to_next_level']}"),
        ("Points", str(game["points"])),
        ("Kills", str(game["kills"])),
        ("Wave", str(game["wave_number"])),
        ("Bosses defeated", str(game["bosses_defeated"])),
    ]
    rows = summary + player_stat_rows(player)
    for i, (name, value) in enumerate(rows):
        col = i // 11
        row = i % 11
        x = panel.x + 28 + col * 225
        y = panel.y + 105 + row * 34
        pygame.draw.rect(screen, (72, 72, 72), (x - 8, y - 4, 205, 28), border_radius=5)
        name_text = tiny_font.render(name, True, "white")
        value_text = tiny_font.render(value, True, "yellow")
        screen.blit(name_text, (x, y))
        screen.blit(value_text, (x + 195 - value_text.get_width(), y))



def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for word in text.split():
        test = word if not current else f"{current} {word}"
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered_text(screen, font, text, color, center_x, y):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (center_x - rendered.get_width() // 2, y))



def draw_world_ui(screen, tiny_font, game):
    center = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
    pygame.draw.circle(screen, (60, 180, 60), (int(center.x), int(center.y)), int(game["safe_radius"]), 2)
    for obstacle in game["obstacles"]:
        pygame.draw.rect(screen, (80, 80, 80), obstacle)
        pygame.draw.rect(screen, "black", obstacle, 2)
    boss_warning_time = min(game["next_boss_time"], BOSS_TRIGGER_TIME if BOSS_TRIGGER_TIME not in game["spawned"] else game["next_boss_time"])
    remaining = boss_warning_time - game["game_time"]
    if 0 < remaining <= 5 and int(game["game_time"] * 4) % 2 == 0:
        warning = tiny_font.render("BOSS INCOMING", True, "red")
        screen.blit(warning, (WIDTH // 2 - warning.get_width() // 2, 30))


def draw_minimap(screen, game):
    rect = pygame.Rect(WIDTH - 165, HEIGHT - 125, 145, 105)
    pygame.draw.rect(screen, (20, 20, 20), rect)
    pygame.draw.rect(screen, "white", rect, 1)
    px = rect.x + int(game["player"].pos.x / WIDTH * rect.width)
    py = rect.y + int(game["player"].pos.y / HEIGHT * rect.height)
    pygame.draw.circle(screen, "blue", (px, py), 3)
    for enemy in game["enemies"][:80]:
        ex = rect.x + int(enemy.pos.x / WIDTH * rect.width)
        ey = rect.y + int(enemy.pos.y / HEIGHT * rect.height)
        pygame.draw.circle(screen, "red" if not enemy.is_boss else "purple", (ex, ey), 2)


def draw_run_summary(screen, font, tiny_font, game, meta):
    draw_text(screen, font, f"Final Score: {game['final_score']}", "white", 540, 485)
    draw_text(screen, tiny_font, f"Prestige: {meta.get('prestige', 0)}", "gold", 540, 522)
    top = meta.get("high_scores", [])[:3]
    for i, row in enumerate(top):
        draw_text(screen, tiny_font, f"#{i + 1}: {row['score']} score / {row['kills']} kills", "gray", 540, 550 + i * 22)
    base_x, base_y = 40, 520
    draw_text(screen, tiny_font, "DPS", "white", base_x, base_y - 28)
    samples = game.get("dps_samples", [])[-20:]
    max_sample = max(samples or [1])
    for i, value in enumerate(samples):
        bar_h = int(70 * value / max_sample) if max_sample else 0
        pygame.draw.rect(screen, "orange", (base_x + i * 8, base_y + 80 - bar_h, 6, bar_h))
    draw_text(screen, tiny_font, "Kills/Wave", "white", 240, base_y - 28)
    waves = list(game.get("kills_per_wave", {}).items())[-12:]
    max_kills = max([value for _, value in waves] or [1])
    for i, (_, value) in enumerate(waves):
        bar_h = int(70 * value / max_kills) if max_kills else 0
        pygame.draw.rect(screen, "cyan", (240 + i * 12, base_y + 80 - bar_h, 9, bar_h))


def draw_level_up(screen, font, title_font, game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    draw_text(screen, title_font, f"LEVEL {game['level']}!", "gold", 515, 95)
    draw_text(screen, font, "Choose a stat multiplier card", "white", 460, 170)

    card_width = 300
    card_height = 250
    start_x = (WIDTH - (card_width * LEVEL_UP_CARD_COUNT + 35 * (LEVEL_UP_CARD_COUNT - 1))) // 2
    for i, card in enumerate(game["level_up_cards"]):
        x = start_x + i * (card_width + 35)
        y = 245
        rect = pygame.Rect(x, y, card_width, card_height)
        pygame.draw.rect(screen, "navy", rect)
        pygame.draw.rect(screen, "gold", rect, 4)
        draw_centered_text(screen, font, f"Press {i + 1}", "yellow", rect.centerx, y + 25)
        draw_centered_text(screen, font, card["name"], "white", rect.centerx, y + 85)

        for line_index, line in enumerate(wrap_text(card["description"], font, card_width - 40)):
            draw_centered_text(screen, font, line, "white", rect.centerx, y + 140 + line_index * 32)

    draw_text(screen, font, f"Next level needs {game['xp_to_next_level']} XP", "gray", 465, 555)


def draw_menu(screen, font, title_font):
    screen.fill("black")
    draw_text(screen, title_font, "Survival Shooter", "white", 430, 150)
    draw_text(screen, font, "WASD to move. Left click to shoot.", "gray", 430, 260)
    draw_text(screen, font, "Earn points from kills, then press TAB for repeatable upgrades.", "gray", 430, 305)
    draw_text(screen, font, "Kills also give XP. Level up to pick multiplier cards.", "gray", 430, 350)
    draw_text(screen, font, "Bosses start at 50 seconds and waves continue forever.", "gray", 430, 395)
    draw_text(screen, font, "Press ENTER to start or Q to quit.", "yellow", 430, 475)


def draw_end_screen(screen, font, title, kills, points, level, wave_number, bosses_defeated):
    screen.fill("black")
    draw_text(screen, font, title, "white", 540, 240)
    draw_text(screen, font, f"Final Level: {level}", "white", 540, 290)
    draw_text(screen, font, f"Final Kills: {kills}", "white", 540, 330)
    draw_text(screen, font, f"Final Points: {points}", "white", 540, 370)
    draw_text(screen, font, f"Highest Wave: {wave_number}", "white", 540, 410)
    draw_text(screen, font, f"Bosses Defeated: {bosses_defeated}", "white", 540, 450)
    draw_text(screen, font, "Press R to Restart, M for Menu, or Q to Quit", "gray", 420, 505)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Survival Shooter")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)
    tiny_font = pygame.font.Font(None, 22)
    title_font = pygame.font.Font(None, 72)

    shop = Shop()
    meta = load_meta()
    game = reset_game(shop, meta)
    state = "menu"
    stats_open = False
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
                    game = reset_game(shop, meta)
                    shop.open = False
                    stats_open = False
                    state = "playing"
                elif state == "level_up":
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        card_index = event.key - pygame.K_1
                        has_another_level = apply_level_card(game, card_index)
                        state = "level_up" if has_another_level else "playing"
                elif state == "game_over":
                    if event.key == pygame.K_r:
                        game = reset_game(shop, meta)
                        shop.open = False
                        stats_open = False
                        state = "playing"
                    elif event.key == pygame.K_m:
                        state = "menu"
                elif state == "playing":
                    if event.key == pygame.K_TAB:
                        shop.open = not shop.open
                        stats_open = False if shop.open else stats_open
                    elif event.key == pygame.K_i:
                        stats_open = not stats_open
                        shop.open = False if stats_open else shop.open
                    elif event.key == pygame.K_e and not shop.open and not stats_open:
                        drop_mine(game)
                    elif shop.open:
                        game["points"] = shop.try_buy(event.key, player, game["points"])

            if event.type == pygame.MOUSEBUTTONDOWN and state == "playing":
                if event.button == 1 and shop.open:
                    game["points"] = shop.try_buy_at_pos(event.pos, player, game["points"])
                elif event.button == 1 and not stats_open:
                    game["charge_start"] = game["game_time"]
                    mx, my = pygame.mouse.get_pos()
                    game["bullets"].extend(player.shoot(mx, my))
            if event.type == pygame.MOUSEBUTTONUP and state == "playing" and event.button == 1 and game.get("charge_start") is not None:
                held = game["game_time"] - game["charge_start"]
                game["charge_start"] = None
                if held >= 0.45 and not shop.open and not stats_open:
                    mx, my = pygame.mouse.get_pos()
                    game["bullets"].append(player.charged_shot(mx, my, held))

        if state == "menu":
            draw_menu(screen, font, title_font)
        elif state in ("playing", "level_up"):
            screen.fill("white")

            if state == "playing" and not shop.open and not stats_open:
                keys = pygame.key.get_pressed()
                previous_pos = player.pos.copy()
                player.update(keys, dt)
                if player_hits_obstacle(player, game["obstacles"]):
                    player.pos = previous_pos
                    player.rect.center = (int(player.pos.x), int(player.pos.y))
                update_player_pressure(game, dt)
                if player.health <= 0:
                    state = "game_over"
                if pygame.mouse.get_pressed(num_buttons=3)[0] and state == "playing":
                    mx, my = pygame.mouse.get_pos()
                    game["bullets"].extend(player.shoot(mx, my))
                game["game_time"] += dt
                game["damage_cooldown"] = max(0, game["damage_cooldown"] - dt)

                if update_xp_orbs(game, dt):
                    shop.open = False
                    state = "level_up"
                update_mines(game, dt)
                boomerang_positions = update_boomerang(game, dt)
                if update_enemy_bullets(game, dt):
                    state = "game_over"
                update_effects_and_text(game, dt)

                for bullet in game["bullets"][:]:
                    bullet.update(dt)
                    if bullet.is_off_screen() or any(obstacle.collidepoint(bullet.pos) for obstacle in game["obstacles"]):
                        game["bullets"].remove(bullet)

                for bullet in game["bullets"][:]:
                    for enemy in game["enemies"][:]:
                        enemy_id = id(enemy)
                        if enemy_id in bullet.hit_enemies:
                            continue
                        if bullet.collides_with(enemy.rect):
                            if enemy.blocks_from_front(bullet):
                                game["floating_texts"].append(FloatingText(enemy.pos, "BLOCK", "lightblue"))
                                if bullet in game["bullets"]:
                                    game["bullets"].remove(bullet)
                                break
                            if bullet.weapon_type == "rocket":
                                if explode_rocket(game, bullet):
                                    shop.open = False
                                    state = "level_up"
                                if bullet in game["bullets"]:
                                    game["bullets"].remove(bullet)
                                break

                            bullet.hit_enemies.add(enemy_id)
                            if damage_enemy(game, enemy, bullet.damage):
                                shop.open = False
                                state = "level_up"
                            bullet.pierce -= 1
                            if bullet.pierce < 0 and bullet in game["bullets"]:
                                game["bullets"].remove(bullet)
                            break

                if state == "playing":
                    for enemy in game["enemies"][:]:
                        enemy.update(player.pos, dt, game["enemies"], game)
                        if enemy.rect.colliderect(player.rect) and game["damage_cooldown"] <= 0:
                            if damage_player(game, 1):
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

            draw_world_ui(screen, tiny_font, game)
            for orb in game["xp_orbs"]:
                orb.draw(screen)
            for mine in game["mines"]:
                mine.draw(screen)
            for effect in game["effects"]:
                effect.draw(screen)
            for pos in game.get("boomerang_positions", []):
                pygame.draw.circle(screen, "silver", (int(pos.x), int(pos.y)), 12)
                pygame.draw.circle(screen, "black", (int(pos.x), int(pos.y)), 12, 2)
            player.draw(screen)
            for bullet in game["bullets"]:
                bullet.draw(screen)
            for bullet in game["enemy_bullets"]:
                bullet.draw(screen)
            for enemy in game["enemies"]:
                enemy.draw(screen, font)
            for floating in game["floating_texts"]:
                floating.draw(screen, tiny_font)
            draw_minimap(screen, game)
            draw_hud(
                screen,
                small_font,
                tiny_font,
                player,
                game["kills"],
                game["points"],
                game["level"],
                game["xp"],
                game["xp_to_next_level"],
                game["game_time"],
                game["wave_number"],
                game["bosses_defeated"],
            )

            if shop.open:
                shop.draw(screen, font, small_font, tiny_font, player, game["points"])
            if stats_open and state == "playing":
                draw_stats_menu(screen, font, small_font, tiny_font, player, game)
            if state == "level_up":
                draw_level_up(screen, font, title_font, game)
        elif state == "game_over":
            if not game.get("run_recorded"):
                game["final_score"] = record_run(meta, game)
                game["run_recorded"] = True
            draw_end_screen(
                screen,
                font,
                "GAME OVER",
                game["kills"],
                game["points"],
                game["level"],
                game["wave_number"],
                game["bosses_defeated"],
            )
            draw_run_summary(screen, font, tiny_font, game, meta)

        if game.get("shake_timer", 0) > 0:
            game["shake_timer"] = max(0, game["shake_timer"] - dt)
            offset_x = random.randint(-game["shake_intensity"], game["shake_intensity"])
            offset_y = random.randint(-game["shake_intensity"], game["shake_intensity"])
            snapshot = screen.copy()
            screen.fill("black")
            screen.blit(snapshot, (offset_x, offset_y))

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
