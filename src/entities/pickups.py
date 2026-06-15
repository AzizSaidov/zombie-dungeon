import math
import random
import pygame

from src.entities.weapon import WEAPONS

OBJ_COLORS = {
    'key':     (240, 205, 90),
    'fuel':    (235, 140, 60),
    'vaccine': (120, 220, 200),
}
OBJ_LABELS = {'key': 'КЛЮЧ', 'fuel': 'ТОПЛИВО', 'vaccine': 'ВАКЦИНА'}


def _glow(surface, sx, sy, radius, color):
    g = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(g, (*color, 70), (radius, radius), radius)
    pygame.draw.circle(g, (*color, 90), (radius, radius), radius // 2)
    surface.blit(g, (int(sx) - radius, int(sy) - radius), special_flags=pygame.BLEND_RGB_ADD)


def _shadow(surface, sx, sy, w=26):
    s = pygame.Surface((w, w // 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 110), s.get_rect())
    surface.blit(s, (int(sx) - w // 2, int(sy) + 6))


def _label(surface, font, sx, sy, text, color):
    if not font:
        return
    t = font.render(text, True, color)
    sh = font.render(text, True, (0, 0, 0))
    surface.blit(sh, sh.get_rect(center=(int(sx) + 1, int(sy) + 1)))
    surface.blit(t, t.get_rect(center=(int(sx), int(sy))))


class WeaponPickup:
    def __init__(self, x, y, weapon_id):
        self.pos = pygame.math.Vector2(x, y)
        self.weapon_id = weapon_id
        self.name = WEAPONS[weapon_id]['name']
        self.bob = random.uniform(0, math.tau)
        self.taken = False

    def update(self, dt):
        self.bob += dt * 3.0

    def near(self, p, r=44):
        return (p - self.pos).length() < r

    def light(self):
        return (self.pos.x, self.pos.y, 80, (24, 40, 48))

    def draw(self, surface, camera, font=None):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        if not (-60 < sx < surface.get_width() + 60 and -60 < sy < surface.get_height() + 60):
            return
        bob = math.sin(self.bob) * 3
        cy = sy + bob
        _shadow(surface, sx, sy)
        _glow(surface, sx, cy, 30, (90, 150, 175))
        box = pygame.Rect(0, 0, 30, 16)
        box.center = (int(sx), int(cy))
        pygame.draw.rect(surface, (40, 46, 52), box, border_radius=3)
        pygame.draw.rect(surface, (150, 210, 235), box, 2, border_radius=3)
        pygame.draw.rect(surface, (120, 170, 190), (box.left + 4, box.centery - 2, 20, 4))
        pygame.draw.rect(surface, (120, 170, 190), (box.left + 6, box.centery + 2, 6, 5))
        _label(surface, font, sx, sy + 22, self.name, (190, 225, 240))


class Objective:
    def __init__(self, x, y, kind):
        self.pos = pygame.math.Vector2(x, y)
        self.kind = kind
        self.color = OBJ_COLORS[kind]
        self.label = OBJ_LABELS[kind]
        self.bob = random.uniform(0, math.tau)
        self.taken = False

    def update(self, dt):
        self.bob += dt * 2.4

    def near(self, p, r=44):
        return (p - self.pos).length() < r

    def light(self):
        return (self.pos.x, self.pos.y, 100, tuple(c // 4 for c in self.color))

    def draw(self, surface, camera, font=None):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        if not (-60 < sx < surface.get_width() + 60 and -60 < sy < surface.get_height() + 60):
            return
        cy = sy + math.sin(self.bob) * 3
        _shadow(surface, sx, sy)
        pulse = int(34 + 8 * math.sin(self.bob * 1.7))
        _glow(surface, sx, cy, pulse, self.color)
        ix, iy = int(sx), int(cy)
        if self.kind == 'key':
            pygame.draw.circle(surface, self.color, (ix - 6, iy), 6, 2)
            pygame.draw.line(surface, self.color, (ix - 1, iy), (ix + 10, iy), 3)
            pygame.draw.line(surface, self.color, (ix + 10, iy), (ix + 10, iy + 5), 3)
            pygame.draw.line(surface, self.color, (ix + 6, iy), (ix + 6, iy + 5), 3)
        elif self.kind == 'fuel':
            body = pygame.Rect(ix - 8, iy - 9, 16, 18)
            pygame.draw.rect(surface, self.color, body, border_radius=2)
            pygame.draw.rect(surface, (60, 30, 12), body, 2, border_radius=2)
            pygame.draw.rect(surface, self.color, (ix + 6, iy - 11, 5, 4))
        else:
            pygame.draw.rect(surface, self.color, (ix - 9, iy - 4, 14, 8), border_radius=2)
            pygame.draw.line(surface, self.color, (ix + 5, iy), (ix + 13, iy), 4)
            pygame.draw.line(surface, (235, 245, 250), (ix + 13, iy), (ix + 17, iy), 2)
            pygame.draw.line(surface, self.color, (ix - 11, iy - 4), (ix - 11, iy + 4), 3)
        _label(surface, font, sx, sy + 24, self.label, self.color)


class ExitGate:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.open = False
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def near(self, p, r=58):
        return self.open and (p - self.pos).length() < r

    def light(self):
        if self.open:
            return (self.pos.x, self.pos.y, 150, (20, 60, 28))
        return (self.pos.x, self.pos.y, 90, (50, 18, 16))

    def draw(self, surface, camera, font=None):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        if not (-80 < sx < surface.get_width() + 80 and -80 < sy < surface.get_height() + 80):
            return
        ix, iy = int(sx), int(sy)
        if self.open:
            r = int(34 + 5 * math.sin(self.t * 4))
            _glow(surface, sx, sy, r + 18, (40, 200, 90))
            frame = pygame.Rect(ix - 26, iy - 40, 52, 80)
            pygame.draw.rect(surface, (20, 80, 36), frame, border_radius=6)
            pygame.draw.rect(surface, (90, 240, 130), frame, 3, border_radius=6)
            for i in range(3):
                a = 120 - i * 35
                rr = r - i * 8
                if rr > 0:
                    s = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (120, 255, 160, a), (rr, rr), rr, 3)
                    surface.blit(s, (ix - rr, iy - rr))
            _label(surface, font, sx, sy - 52, 'ВЫХОД', (150, 245, 180))
        else:
            _glow(surface, sx, sy, 40, (120, 30, 26))
            frame = pygame.Rect(ix - 26, iy - 40, 52, 80)
            pygame.draw.rect(surface, (44, 22, 20), frame, border_radius=6)
            pygame.draw.rect(surface, (150, 50, 44), frame, 3, border_radius=6)
            pygame.draw.line(surface, (210, 70, 60), (ix - 16, iy - 18), (ix + 16, iy + 18), 4)
            pygame.draw.line(surface, (210, 70, 60), (ix + 16, iy - 18), (ix - 16, iy + 18), 4)
            _label(surface, font, sx, sy - 52, 'ЗАКРЫТО', (200, 110, 100))
