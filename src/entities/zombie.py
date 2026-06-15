import os
import math
import random
import pygame

ZOMBIE_DIR = os.path.join("assets", "images", "zombies", "export")

ANIM_FPS = 11
BITE_INTERVAL = 0.6

ZOMBIE_TYPES = {
    'walker': {'hp': 45,  'speed': 70,  'damage': 16, 'scale': 0.26,
               'tint': (150, 190, 120), 'score': 10},
    'runner': {'hp': 24,  'speed': 150, 'damage': 11, 'scale': 0.20,
               'tint': (120, 210, 120), 'score': 15},
    'brute':  {'hp': 140, 'speed': 46,  'damage': 34, 'scale': 0.40,
               'tint': (200, 170, 130), 'score': 30},
    'boss':   {'hp': 2400, 'speed': 58, 'damage': 16, 'scale': 0.95,
               'tint': (118, 150, 92), 'score': 500},
}

_raw_frames = None
_type_frames = {}


def _load_raw():
    global _raw_frames
    if _raw_frames is not None:
        return _raw_frames
    files = [f for f in os.listdir(ZOMBIE_DIR)
             if f.startswith("skeleton-move") and f.endswith(".png")]
    files.sort(key=lambda f: int(f.split("_")[1].split(".")[0]))
    _raw_frames = [pygame.image.load(os.path.join(ZOMBIE_DIR, f)).convert_alpha()
                   for f in files]
    return _raw_frames


def _frames_for(type_name):
    cached = _type_frames.get(type_name)
    if cached is not None:
        return cached
    spec = ZOMBIE_TYPES[type_name]
    scale = spec['scale']
    tint = spec['tint']
    frames = []
    for img in _load_raw():
        w = int(img.get_width() * scale)
        h = int(img.get_height() * scale)
        scaled = pygame.transform.smoothscale(img, (w, h))
        scaled.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        frames.append(scaled)
    _type_frames[type_name] = frames
    return frames


class Zombie:
    def __init__(self, x, y, type_name='walker'):
        spec = ZOMBIE_TYPES[type_name]
        self.type_name = type_name
        self.frames = _frames_for(type_name)
        self.max_hp = spec['hp']
        self.hp = spec['hp']
        self.speed = spec['speed']
        self.damage = spec['damage']
        self.score = spec['score']

        self.pos = pygame.math.Vector2(x, y)
        self.angle = 0.0
        self.anim = random.uniform(0, len(self.frames))
        self.dead = False
        self.hit_flash = 0.0
        self.bite_cd = 0.0
        self.kb = pygame.math.Vector2(0, 0)
        self.kb_resist = 0.26 / spec['scale']

        r = int(28 * (spec['scale'] / 0.26))
        self.hit_rect = pygame.Rect(0, 0, r, r)
        self.hit_rect.center = (int(x), int(y))

    def take_damage(self, dmg, kb_dir=None, kb_force=0.0):
        self.hp -= dmg
        self.hit_flash = 0.08
        if kb_dir is not None and kb_force > 0:
            self.kb += kb_dir * (kb_force * self.kb_resist)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def try_bite(self):
        if self.bite_cd <= 0:
            self.bite_cd = BITE_INTERVAL
            return self.damage
        return 0

    def update(self, dt, player_pos, wall_rects):
        self.hit_flash = max(0, self.hit_flash - dt)
        self.bite_cd = max(0, self.bite_cd - dt)

        if self.kb.length_squared() > 1:
            self.pos.x += self.kb.x * dt
            self.hit_rect.centerx = int(self.pos.x)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if self.kb.x > 0:
                        self.hit_rect.right = wall.left
                    else:
                        self.hit_rect.left = wall.right
                    self.pos.x = self.hit_rect.centerx
                    self.kb.x = 0
            self.pos.y += self.kb.y * dt
            self.hit_rect.centery = int(self.pos.y)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if self.kb.y > 0:
                        self.hit_rect.bottom = wall.top
                    else:
                        self.hit_rect.top = wall.bottom
                    self.pos.y = self.hit_rect.centery
                    self.kb.y = 0
            self.kb *= math.exp(-dt * 9)

        to_player = pygame.math.Vector2(player_pos[0] - self.pos.x,
                                        player_pos[1] - self.pos.y)
        dist = to_player.length()
        if dist > 1:
            d = to_player / dist
            self.angle = math.degrees(math.atan2(-d.y, d.x))

            self.pos.x += d.x * self.speed * dt
            self.hit_rect.centerx = int(self.pos.x)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if d.x > 0:
                        self.hit_rect.right = wall.left
                    else:
                        self.hit_rect.left = wall.right
                    self.pos.x = self.hit_rect.centerx

            self.pos.y += d.y * self.speed * dt
            self.hit_rect.centery = int(self.pos.y)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if d.y > 0:
                        self.hit_rect.bottom = wall.top
                    else:
                        self.hit_rect.top = wall.bottom
                    self.pos.y = self.hit_rect.centery

            self.anim = (self.anim + ANIM_FPS * dt) % len(self.frames)

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        frame = self.frames[int(self.anim)]
        rotated = pygame.transform.rotate(frame, self.angle)
        rect = rotated.get_rect(center=(int(sx), int(sy)))
        surface.blit(rotated, rect)
        if self.hit_flash > 0:
            flash = rotated.copy()
            flash.fill((180, 40, 40), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(flash, rect, special_flags=pygame.BLEND_RGB_ADD)
        if self.hp < self.max_hp:
            self._draw_hp_bar(surface, sx, sy, rect)

    def _draw_hp_bar(self, surface, sx, sy, rect):
        w = rect.width
        x = int(sx - w / 2)
        y = rect.top - 8
        pygame.draw.rect(surface, (40, 0, 0), (x, y, w, 4))
        pygame.draw.rect(surface, (200, 40, 40), (x, y, int(w * self.hp / self.max_hp), 4))
