import math
import random
import pygame

DROP_CHANCE = {'walker': 0.20, 'runner': 0.16, 'brute': 0.55}

LOOT = {
    'medkit':  {'glow_r': 74,  'glow': (60, 16, 16),  'ring': (240, 90, 90),   'pulse': 0.0},
    'ammo':    {'glow_r': 66,  'glow': (52, 42, 14),  'ring': (228, 188, 80),  'pulse': 0.0},
    'arsenal': {'glow_r': 104, 'glow': (66, 52, 16),  'ring': (255, 214, 96),  'pulse': 1.0},
}

PICKUP_RADIUS = 34
LIFETIME = 22.0
BLINK_AT = 4.0


def roll_drop(zombie_type, player):
    if random.random() > DROP_CHANCE.get(zombie_type, 0.18):
        return None
    r = random.random()
    if r < 0.06:
        kind = 'arsenal'
    elif r < 0.42:
        kind = 'medkit'
    else:
        kind = 'ammo'
    if kind == 'medkit' and player.hp >= player.max_hp:
        kind = 'ammo'
    return kind


class LootDrop:
    def __init__(self, x, y, kind):
        self.pos = pygame.math.Vector2(x, y)
        self.kind = kind
        self.spec = LOOT[kind]
        self.bob = random.uniform(0, math.tau)
        self.spawn = 0.0
        self.life = LIFETIME
        self.dead = False

    def update(self, dt):
        self.spawn = min(1.0, self.spawn + dt * 4.0)
        self.bob += dt * 3.0
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def picked_by(self, player_pos):
        return (player_pos - self.pos).length() < PICKUP_RADIUS

    def light(self):
        r = self.spec['glow_r']
        if self.spec['pulse']:
            r = int(r * (0.82 + 0.18 * math.sin(self.bob * 1.6)))
        return (self.pos.x, self.pos.y, r, self.spec['glow'])

    def draw(self, surface, camera):
        if self.life < BLINK_AT and int(self.life * 7) % 2 == 0:
            return
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        if not (-40 < sx < surface.get_width() + 40 and -40 < sy < surface.get_height() + 40):
            return
        ix, iy = int(sx), int(sy)

        shadow = pygame.Surface((28, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
        surface.blit(shadow, (ix - 14, iy + 6))

        bob = math.sin(self.bob) * 3.0
        scale = 0.5 + 0.5 * self.spawn
        cy = iy + int(bob)
        self._draw_icon(surface, ix, cy, scale)

        if self.spec['pulse']:
            pr = int(18 + 4 * math.sin(self.bob * 1.6))
            ring = pygame.Surface((pr * 2 + 4, pr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*self.spec['ring'], 90), (pr + 2, pr + 2), pr, 2)
            surface.blit(ring, (ix - pr - 2, cy - pr - 2))

    def _draw_icon(self, surface, cx, cy, scale):
        if self.kind == 'medkit':
            w, h = int(24 * scale), int(20 * scale)
            box = pygame.Rect(0, 0, w, h)
            box.center = (cx, cy)
            pygame.draw.rect(surface, (236, 236, 232), box, border_radius=3)
            pygame.draw.rect(surface, (150, 150, 146), box, 2, border_radius=3)
            cw = max(2, int(4 * scale))
            pygame.draw.rect(surface, (210, 40, 40), (cx - cw // 2, cy - h // 3, cw, int(h * 0.66)))
            pygame.draw.rect(surface, (210, 40, 40), (cx - w // 3, cy - cw // 2, int(w * 0.66), cw))
        elif self.kind == 'ammo':
            w, h = int(24 * scale), int(18 * scale)
            box = pygame.Rect(0, 0, w, h)
            box.center = (cx, cy)
            pygame.draw.rect(surface, (74, 70, 40), box, border_radius=2)
            pygame.draw.rect(surface, (38, 36, 22), box, 2, border_radius=2)
            bw = max(2, int(3 * scale))
            for i in range(3):
                bx = box.left + int(5 * scale) + i * int(7 * scale)
                pygame.draw.rect(surface, (224, 188, 92), (bx, box.top - int(3 * scale), bw, int(7 * scale)))
                pygame.draw.rect(surface, (248, 228, 150), (bx, box.top - int(3 * scale), bw, max(1, int(2 * scale))))
        else:
            w, h = int(26 * scale), int(20 * scale)
            box = pygame.Rect(0, 0, w, h)
            box.center = (cx, cy)
            pygame.draw.rect(surface, (120, 92, 36), box, border_radius=3)
            pygame.draw.rect(surface, (74, 56, 20), box, 2, border_radius=3)
            pygame.draw.line(surface, (210, 170, 70), box.topleft, box.bottomright, 2)
            pygame.draw.line(surface, (210, 170, 70), box.topright, box.bottomleft, 2)
            r = max(3, int(5 * scale))
            self._star(surface, cx, cy, r, (255, 224, 120))

    def _star(self, surface, cx, cy, r, color):
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(surface, color, pts)
