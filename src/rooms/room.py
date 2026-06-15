import os
import random
import pygame

from src.core.settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.effects import create_vignette, FogLayer, DripSystem, Flicker
from src.core.lighting import LightingSystem
from src.rooms.props import generate_props
from src.rooms.layouts import LAYOUTS, FLOOR, WALL

THEMES = {
    'forest': {
        'label':        'Тёмный лес',
        'floor_style':  'grass',
        'floor':        [(26, 44, 20), (24, 42, 18), (28, 46, 22)],
        'detail':       [(18, 34, 14), (38, 60, 30)],
        'wall':         (52, 50, 44),
        'wall_top':     (72, 68, 60),
        'darkness':     205,
        'tint':         (6, 12, 6),
        'player_light': 230,
        'light_color':  (55, 46, 30),
        'fog':          1.5,
        'drips':        False,
        'flicker':      None,
        'vignette':     (0, 10, 0),
        'music':        'crypt.ogg',
    },
    'town': {
        'label':        'Заброшенный город',
        'floor_style':  'asphalt',
        'floor':        [(56, 56, 58), (54, 54, 56), (58, 58, 60)],
        'detail':       [(40, 40, 42), (78, 76, 74)],
        'wall':         (54, 50, 46),
        'wall_top':     (84, 78, 70),
        'darkness':     172,
        'tint':         (8, 8, 14),
        'player_light': 210,
        'light_color':  (52, 46, 32),
        'fog':          0.5,
        'drips':        False,
        'flicker':      None,
        'vignette':     (6, 6, 10),
        'music':        'warehouse.mp3',
    },
    'hospital': {
        'label':        'Заброшенная больница',
        'floor_style':  'tiles',
        'floor':        [(150, 154, 146), (147, 151, 143), (153, 157, 149)],
        'detail':       [(120, 124, 116), (90, 86, 70)],
        'wall':         (104, 108, 100),
        'wall_top':     (140, 144, 134),
        'darkness':     145,
        'tint':         (10, 12, 11),
        'player_light': 270,
        'light_color':  (60, 62, 60),
        'fog':          0.0,
        'drips':        False,
        'flicker':      'fluorescent',
        'vignette':     (4, 10, 6),
        'music':        'hospital.ogg',
    },
}

THEME_ORDER = ['forest', 'town', 'hospital']


class Room:
    def __init__(self, cols, rows, theme_name='forest'):
        self.cols = cols
        self.rows = rows
        self.width = cols * TILE_SIZE
        self.height = rows * TILE_SIZE

        self.scr_w = SCREEN_WIDTH
        self.scr_h = SCREEN_HEIGHT
        self.lighting = LightingSystem(self.scr_w, self.scr_h)

        self.set_theme(theme_name)

    # ---------- theme ----------

    def set_theme(self, name):
        self.theme_name = name
        t = THEMES[name]
        self.label = t['label']
        self.darkness = t['darkness']
        self.tint = t['tint']
        self.player_light = t['player_light']
        self.light_color = t['light_color']
        self._vignette_col = t['vignette']

        self.grid = LAYOUTS[name](self.cols, self.rows, random.Random())
        self.wall_rects = self._build_wall_rects()

        self.floor_surface, self.static_lights = self._render_floor(t)
        self.vignette = create_vignette(self.scr_w, self.scr_h, t['vignette'])

        self.fog = FogLayer(self.scr_w, self.scr_h, density=t['fog']) if t['fog'] > 0 else None
        self.drips = DripSystem(self.scr_w, self.scr_h) if t['drips'] else None
        self.flicker = Flicker(kind=t['flicker']) if t['flicker'] else None

        self._load_music(t['music'])

    def resize(self, w, h):
        self.scr_w, self.scr_h = w, h
        self.lighting.resize(w, h)
        self.vignette = create_vignette(w, h, self._vignette_col)
        if self.fog:
            self.fog.resize(w, h)
        if self.drips:
            self.drips.resize(w, h)

    def _load_music(self, filename):
        path = os.path.join('assets', 'sounds', filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.stop()

    def find_spawn(self):
        cc, cr = self.cols // 2, self.rows // 2
        for radius in range(0, max(self.cols, self.rows)):
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    r, c = cr + dr, cc + dc
                    if 0 < r < self.rows - 1 and 0 < c < self.cols - 1 and self.grid[r][c] == FLOOR:
                        return (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2)
        return (self.width // 2, self.height // 2)

    def _build_wall_rects(self):
        rects = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == WALL:
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    # ---------- floor ----------

    def _render_floor(self, t):
        rng = random.Random(1234)
        surf = pygame.Surface((self.width, self.height))
        style = t['floor_style']
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                if self.grid[r][c] == WALL:
                    self._draw_wall_tile(surf, x, y, t, rng, r, c)
                else:
                    self._draw_floor_tile(surf, x, y, t, style, rng)
        lights = generate_props(self.theme_name, surf, self.grid, TILE_SIZE)
        return surf, lights

    def _is_floor(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == FLOOR

    def _draw_wall_tile(self, surf, x, y, t, rng, r, c):
        base = t['wall']
        var = rng.randint(-5, 5)
        col = tuple(max(0, min(255, ch + var)) for ch in base)
        pygame.draw.rect(surf, col, (x, y, TILE_SIZE, TILE_SIZE))

        if self._is_floor(r - 1, c):
            pygame.draw.rect(surf, t['wall_top'], (x, y, TILE_SIZE, 7))
        if self._is_floor(r + 1, c):
            shade = tuple(max(0, ch - 16) for ch in col)
            pygame.draw.rect(surf, shade, (x, y + TILE_SIZE - 6, TILE_SIZE, 6))
        if self._is_floor(r, c - 1):
            pygame.draw.line(surf, tuple(min(255, ch + 12) for ch in col), (x, y), (x, y + TILE_SIZE), 2)
        if self._is_floor(r, c + 1):
            pygame.draw.line(surf, tuple(max(0, ch - 12) for ch in col),
                             (x + TILE_SIZE - 1, y), (x + TILE_SIZE - 1, y + TILE_SIZE), 2)

    def _draw_floor_tile(self, surf, x, y, t, style, rng):
        base = rng.choice(t['floor'])
        var = rng.randint(-3, 3)
        col = tuple(max(0, min(255, ch + var)) for ch in base)
        pygame.draw.rect(surf, col, (x, y, TILE_SIZE, TILE_SIZE))
        d_dark, d_light = t['detail']

        if style == 'grass':
            for _ in range(rng.randint(4, 7)):
                bx = x + rng.randint(2, TILE_SIZE - 2)
                by = y + rng.randint(2, TILE_SIZE - 2)
                blade = d_light if rng.random() > 0.5 else d_dark
                pygame.draw.line(surf, blade, (bx, by), (bx, by - rng.randint(3, 6)), 1)
        elif style == 'asphalt':
            if rng.random() < 0.16:
                cx, cy = x + rng.randint(8, TILE_SIZE - 8), y + rng.randint(8, TILE_SIZE - 8)
                pts = [(cx, cy)]
                for _ in range(rng.randint(2, 4)):
                    cx += rng.randint(-14, 14)
                    cy += rng.randint(-14, 14)
                    pts.append((cx, cy))
                pygame.draw.lines(surf, d_dark, False, pts, 1)
            for _ in range(rng.randint(2, 5)):
                sx, sy = x + rng.randint(2, TILE_SIZE - 2), y + rng.randint(2, TILE_SIZE - 2)
                surf.set_at((sx, sy), d_light)
        elif style == 'tiles':
            seam = tuple(max(0, ch - 9) for ch in col)
            pygame.draw.rect(surf, seam, (x, y, TILE_SIZE, TILE_SIZE), 1)
            if rng.random() < 0.12:
                gx, gy = x + rng.randint(10, TILE_SIZE - 10), y + rng.randint(10, TILE_SIZE - 10)
                gs = pygame.Surface((20, 16), pygame.SRCALPHA)
                pygame.draw.ellipse(gs, (*d_dark, 70), gs.get_rect())
                surf.blit(gs, (gx - 10, gy - 8))

    # ---------- loop ----------

    def update(self, dt):
        if self.fog:
            self.fog.update(dt)
        if self.drips:
            self.drips.update(dt)
        if self.flicker:
            self.flicker.update(dt)

    def draw_floor(self, surface, camera):
        surface.blit(self.floor_surface, (-int(camera.offset.x), -int(camera.offset.y)))

    def draw_overlays(self, surface, camera, light_pos, extra_lights=()):
        if self.fog:
            self.fog.draw(surface)

        psx, psy = camera.world_to_screen(light_pos[0], light_pos[1])
        radius = self.player_light
        if self.flicker and self.flicker.kind == 'fluorescent':
            radius = int(radius * (0.55 + 0.45 * self.flicker.value))

        lights = [(int(psx), int(psy), radius, self.light_color)]
        for (wx, wy, r, color) in self.static_lights:
            sx, sy = camera.world_to_screen(wx, wy)
            if -r < sx < self.scr_w + r and -r < sy < self.scr_h + r:
                lights.append((int(sx), int(sy), r, color))
        for (wx, wy, r, color) in extra_lights:
            sx, sy = camera.world_to_screen(wx, wy)
            if -r < sx < self.scr_w + r and -r < sy < self.scr_h + r:
                lights.append((int(sx), int(sy), int(r), color))

        darkness = self.darkness
        if self.flicker and self.flicker.kind == 'fluorescent':
            darkness = int(darkness + (1.0 - self.flicker.value) * 70)

        self.lighting.render(surface, darkness, self.tint, lights)
        surface.blit(self.vignette, (0, 0))

        if self.flicker and self.flicker.kind == 'alarm':
            a = int(self.flicker.value * 40)
            pulse = pygame.Surface((self.scr_w, self.scr_h), pygame.SRCALPHA)
            pulse.fill((140, 0, 0, a))
            surface.blit(pulse, (0, 0))

        if self.drips:
            self.drips.draw(surface)
