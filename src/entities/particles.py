import math
import random
import pygame


class Particles:
    def __init__(self):
        self.items = []
        self.decals = []

    def blood(self, x, y, amount=10, direction=None, big=False):
        for _ in range(amount):
            if direction is not None:
                base = math.atan2(direction[1], direction[0])
                ang = base + random.uniform(-0.7, 0.7)
            else:
                ang = random.uniform(0, math.tau)
            spd = random.uniform(40, 220) * (1.4 if big else 1.0)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            self.items.append([x, y, vx, vy, random.uniform(0.3, 0.7),
                               random.randint(2, 5),
                               random.choice([(150, 10, 10), (110, 6, 6), (90, 4, 4)])])

    def spark(self, x, y, direction=None, amount=7):
        for _ in range(amount):
            if direction is not None:
                base = math.atan2(-direction[1], -direction[0])
                ang = base + random.uniform(-0.9, 0.9)
            else:
                ang = random.uniform(0, math.tau)
            spd = random.uniform(110, 380)
            self.items.append([x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                               random.uniform(0.1, 0.28), random.randint(1, 2),
                               random.choice([(255, 224, 140), (255, 186, 80), (255, 248, 210)])])

    def casing(self, x, y, vx, vy):
        self.items.append([x, y, vx, vy, random.uniform(0.45, 0.75), 2, (198, 162, 70)])

    def add_decal(self, x, y, big=False):
        r = random.randint(8, 16) * (1.6 if big else 1.0)
        self.decals.append((int(x), int(y), int(r)))
        if len(self.decals) > 120:
            self.decals.pop(0)

    def update(self, dt):
        alive = []
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.90
            p[3] *= 0.90
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    def draw_decals(self, surface, camera):
        for x, y, r in self.decals:
            sx, sy = camera.world_to_screen(x, y)
            if -r < sx < surface.get_width() + r and -r < sy < surface.get_height() + r:
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (80, 6, 6, 150), (r, r), r)
                surface.blit(s, (int(sx) - r, int(sy) - r))

    def draw(self, surface, camera):
        for x, y, vx, vy, life, size, color in self.items:
            sx, sy = camera.world_to_screen(x, y)
            pygame.draw.circle(surface, color, (int(sx), int(sy)), size)
