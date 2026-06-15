import pygame
import math
import random


def create_vignette(width, height, color=(0, 0, 0), strength=190):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width // 2, height // 2
    max_r = int(math.hypot(cx, cy)) + 1
    steps = 90
    for i in range(steps, 0, -1):
        r = int(max_r * i / steps)
        alpha = int(strength * (i / steps) ** 2.4)
        pygame.draw.circle(surf, (*color, alpha), (cx, cy), r)
    return surf


def _soft_blob(radius, color, max_alpha):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        frac = r / radius
        a = int(max_alpha * (1.0 - frac) ** 1.8)
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    return surf


class FogLayer:
    def __init__(self, w, h, density=1.0, color=(120, 128, 122), speed=16):
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.density = density
        self.blob = _soft_blob(150, color, int(13 + 5 * density))
        count = int(14 + 16 * density)
        self.blobs = []
        for _ in range(count):
            self.blobs.append([
                random.uniform(-300, w),
                random.uniform(-150, h),
                random.uniform(0.5, 1.3),
                random.uniform(0.4, 1.0),
            ])

    def resize(self, w, h):
        self.w = w
        self.h = h

    def update(self, dt):
        for b in self.blobs:
            b[0] += self.speed * b[3] * dt
            if b[0] - 300 > self.w:
                b[0] = -300
                b[1] = random.uniform(-150, self.h)

    def draw(self, surface):
        for x, y, scale, _ in self.blobs:
            size = int(300 * scale)
            img = pygame.transform.scale(self.blob, (size, size))
            surface.blit(img, (int(x), int(y)))


class DripSystem:
    def __init__(self, w, h, color=(90, 130, 80), rate=0.12):
        self.w = w
        self.h = h
        self.color = color
        self.rate = rate
        self._t = 0
        self.drops = []
        self.splashes = []

    def resize(self, w, h):
        self.w = w
        self.h = h

    def update(self, dt):
        self._t += dt
        while self._t >= self.rate:
            self._t -= self.rate
            self.drops.append([random.uniform(0, self.w),
                               random.uniform(0, self.h * 0.4),
                               0.0])
        for d in self.drops:
            d[2] += 600 * dt
            d[1] += d[2] * dt
        landed = [d for d in self.drops if d[1] >= self.h * 0.6 + random.uniform(0, self.h * 0.4)]
        for d in landed:
            self.splashes.append([d[0], d[1], 0.0])
        self.drops = [d for d in self.drops if d[1] < self.h]
        for s in self.splashes:
            s[2] += dt
        self.splashes = [s for s in self.splashes if s[2] < 0.35]

    def draw(self, surface):
        for x, y, _ in self.drops:
            pygame.draw.line(surface, self.color, (int(x), int(y)), (int(x), int(y) + 7), 2)
        for x, y, t in self.splashes:
            r = int(2 + t * 22)
            a = max(0, 120 - int(t * 340))
            if a > 0:
                s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, a), (r + 1, r + 1), r, 1)
                surface.blit(s, (int(x) - r, int(y) - r))


class Popups:
    def __init__(self):
        self.items = []

    def add(self, x, y, text, color=(240, 240, 240)):
        self.items.append([x, y - 18, text, color, 1.1])

    def update(self, dt):
        for p in self.items:
            p[1] -= 36 * dt
            p[4] -= dt
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, surface, camera, font):
        for x, y, text, color, life in self.items:
            sx, sy = camera.world_to_screen(x, y)
            a = max(0, min(255, int(255 * (life / 1.1))))
            txt = font.render(text, True, color)
            txt.set_alpha(a)
            sh = font.render(text, True, (0, 0, 0))
            sh.set_alpha(a)
            rect = txt.get_rect(center=(int(sx), int(sy)))
            surface.blit(sh, (rect.x + 1, rect.y + 1))
            surface.blit(txt, rect)


class Flicker:
    def __init__(self, base=1.0, kind='fluorescent'):
        self.base = base
        self.kind = kind
        self.value = base
        self._t = 0
        self._next = 0
        self._dark_until = 0

    def update(self, dt):
        self._t += dt
        if self.kind == 'fluorescent':
            if self._t < self._dark_until:
                self.value = random.uniform(0.15, 0.4)
            elif self._t >= self._next:
                self._next = self._t + random.uniform(0.05, 1.6)
                if random.random() < 0.3:
                    self._dark_until = self._t + random.uniform(0.04, 0.18)
                    self.value = 0.2
                else:
                    self.value = random.uniform(0.85, 1.0)
        elif self.kind == 'alarm':
            self.value = 0.5 + 0.5 * abs(math.sin(self._t * 3.0))
