import pygame

_mask_cache = {}
_glow_cache = {}


def _radial_mask(radius, intensity):
    key = (radius, intensity)
    cached = _mask_cache.get(key)
    if cached is not None:
        return cached
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        frac = r / radius
        a = int(intensity * (1.0 - frac) ** 1.4)
        pygame.draw.circle(surf, (255, 255, 255, a), (radius, radius), r)
    _mask_cache[key] = surf
    return surf


def _radial_glow(radius, color):
    key = (radius, color)
    cached = _glow_cache.get(key)
    if cached is not None:
        return cached
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r0, g0, b0 = color
    for r in range(radius, 0, -1):
        frac = r / radius
        k = (1.0 - frac) ** 2.2
        col = (int(r0 * k), int(g0 * k), int(b0 * k))
        pygame.draw.circle(surf, col, (radius, radius), r)
    _glow_cache[key] = surf
    return surf


class LightingSystem:
    def __init__(self, w, h):
        self.resize(w, h)

    def resize(self, w, h):
        self.w = w
        self.h = h
        self.shadow = pygame.Surface((w, h), pygame.SRCALPHA)

    def render(self, surface, darkness, tint, lights):
        for (sx, sy, radius, color) in lights:
            glow = _radial_glow(radius, color)
            surface.blit(glow, glow.get_rect(center=(sx, sy)),
                         special_flags=pygame.BLEND_RGB_ADD)

        if darkness <= 0:
            return

        self.shadow.fill((tint[0], tint[1], tint[2], darkness))
        for (sx, sy, radius, color) in lights:
            mask = _radial_mask(int(radius * 1.15), 255)
            self.shadow.blit(mask, mask.get_rect(center=(sx, sy)),
                             special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(self.shadow, (0, 0))
