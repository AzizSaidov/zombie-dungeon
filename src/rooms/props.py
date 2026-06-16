import pygame
import random
import math


def _shadow(surf, x, y, w, h, alpha=80):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
    surf.blit(s, (x - w // 2, y - h // 2))


# ---------- FOREST ----------

def draw_tree(surf, x, y):
    _shadow(surf, x + 6, y + 26, 70, 30, 70)
    pygame.draw.rect(surf, (48, 30, 14), (x - 6, y + 6, 12, 26), border_radius=3)
    pygame.draw.rect(surf, (38, 23, 10), (x - 6, y + 6, 5, 26), border_radius=3)
    layers = [
        ((10, 36, 10), 34, (0, 2)),
        ((16, 50, 16), 28, (-12, -8)),
        ((22, 62, 22), 24, (13, -12)),
        ((30, 74, 30), 18, (-2, -22)),
        ((40, 88, 40), 12, (6, -10)),
    ]
    for color, r, (ox, oy) in layers:
        pygame.draw.circle(surf, color, (x + ox, y + oy), r)
    return None


def draw_pine(surf, x, y):
    _shadow(surf, x + 4, y + 24, 50, 22, 70)
    pygame.draw.rect(surf, (44, 28, 12), (x - 4, y + 8, 8, 20))
    for i, (w, dy) in enumerate([(40, 12), (32, -2), (24, -16), (16, -30)]):
        c = (14 + i * 6, 46 + i * 8, 18 + i * 4)
        pygame.draw.polygon(surf, c, [(x - w, y + dy), (x + w, y + dy), (x, y + dy - 26)])
    return None


def draw_bush(surf, x, y):
    _shadow(surf, x, y + 8, 34, 14, 60)
    pygame.draw.circle(surf, (18, 44, 16), (x, y), 15)
    pygame.draw.circle(surf, (14, 36, 12), (x - 11, y + 4), 11)
    pygame.draw.circle(surf, (24, 54, 22), (x + 10, y + 3), 10)
    pygame.draw.circle(surf, (34, 68, 30), (x + 2, y - 5), 7)
    return None


def draw_rock(surf, x, y):
    r = random.randint(10, 18)
    _shadow(surf, x, y + r // 2, r * 2, r, 70)
    pts = [(x + int(r * math.cos(a)) + random.randint(-3, 3),
            y + int(r * 0.7 * math.sin(a)) + random.randint(-3, 3))
           for a in [i * math.pi / 4 for i in range(8)]]
    pygame.draw.polygon(surf, (74, 72, 70), pts)
    pygame.draw.polygon(surf, (54, 52, 50), pts, 2)
    pygame.draw.circle(surf, (94, 92, 90), (x - r // 3, y - r // 3), r // 3)
    return None


def draw_log(surf, x, y):
    ang = random.uniform(0, math.pi)
    length = random.randint(50, 90)
    dx = int(math.cos(ang) * length // 2)
    dy = int(math.sin(ang) * length // 2)
    _shadow(surf, x, y + 6, length, 18, 60)
    pygame.draw.line(surf, (70, 42, 20), (x - dx, y - dy), (x + dx, y + dy), 14)
    pygame.draw.line(surf, (52, 30, 14), (x - dx, y - dy), (x + dx, y + dy), 9)
    pygame.draw.line(surf, (88, 58, 30), (x - dx, y - dy), (x + dx, y + dy), 3)
    for cx, cy in [(x - dx, y - dy), (x + dx, y + dy)]:
        pygame.draw.circle(surf, (96, 64, 34), (cx, cy), 7)
        pygame.draw.circle(surf, (70, 44, 22), (cx, cy), 7, 2)
    return None


# ---------- TOWN ----------

def draw_building(surf, x, y):
    w = random.randint(120, 200)
    h = random.randint(120, 200)
    _shadow(surf, x + 10, y + 12, w + 20, h + 20, 90)
    roof = random.choice([(58, 54, 48), (66, 50, 42), (52, 56, 60)])
    pygame.draw.rect(surf, roof, (x - w // 2, y - h // 2, w, h))
    pygame.draw.rect(surf, (30, 28, 24), (x - w // 2, y - h // 2, w, h), 4)
    edge = tuple(min(255, c + 18) for c in roof)
    pygame.draw.rect(surf, edge, (x - w // 2 + 4, y - h // 2 + 4, w - 8, h - 8), 2)
    for _ in range(random.randint(2, 4)):
        vx = random.randint(x - w // 2 + 10, x + w // 2 - 20)
        pygame.draw.rect(surf, (24, 22, 20), (vx, y - h // 2 + 6, 3, h - 12))
    ac_x = x + random.randint(-w // 4, w // 4)
    ac_y = y + random.randint(-h // 4, h // 4)
    pygame.draw.rect(surf, (90, 92, 94), (ac_x - 12, ac_y - 9, 24, 18))
    pygame.draw.rect(surf, (60, 62, 64), (ac_x - 12, ac_y - 9, 24, 18), 2)
    return None


def draw_car(surf, x, y):
    rot = random.choice([0, 90])
    color = random.choice([(150, 40, 38), (40, 50, 130), (50, 110, 60),
                           (70, 72, 76), (150, 140, 50), (40, 42, 46)])
    bw, bh = (52, 28) if rot == 0 else (28, 52)
    _shadow(surf, x + 3, y + 4, bw + 8, bh + 8, 80)
    pygame.draw.rect(surf, color, (x - bw // 2, y - bh // 2, bw, bh), border_radius=6)
    pygame.draw.rect(surf, (12, 12, 12), (x - bw // 2, y - bh // 2, bw, bh), 2, border_radius=6)
    hi = tuple(min(255, c + 35) for c in color)
    if rot == 0:
        pygame.draw.rect(surf, (28, 32, 40), (x - 10, y - bh // 2 + 4, 20, bh - 8), border_radius=3)
        pygame.draw.rect(surf, hi, (x - bw // 2 + 3, y - bh // 2 + 3, bw - 6, 4), border_radius=2)
    else:
        pygame.draw.rect(surf, (28, 32, 40), (x - bw // 2 + 4, y - 10, bw - 8, 20), border_radius=3)
        pygame.draw.rect(surf, hi, (x - bw // 2 + 3, y - bh // 2 + 3, 4, bh - 6), border_radius=2)
    return None


def draw_streetlight(surf, x, y):
    _shadow(surf, x, y + 6, 16, 10, 110)
    pygame.draw.circle(surf, (40, 40, 42), (x, y), 7)
    pygame.draw.circle(surf, (60, 60, 62), (x, y), 7, 2)
    pygame.draw.circle(surf, (255, 240, 180), (x, y), 4)
    pygame.draw.circle(surf, (255, 255, 230), (x, y), 2)
    return (x, y, 150, (120, 95, 35))


def draw_debris(surf, x, y):
    for _ in range(random.randint(4, 9)):
        ox = random.randint(-20, 20)
        oy = random.randint(-20, 20)
        w = random.randint(6, 22)
        h = random.randint(4, 13)
        c = random.randint(55, 90)
        pygame.draw.rect(surf, (c, c - 6, c - 12), (x + ox, y + oy, w, h))
        pygame.draw.rect(surf, (c - 25, c - 28, c - 32), (x + ox, y + oy, w, h), 1)
    return None


def draw_dumpster(surf, x, y):
    _shadow(surf, x + 4, y + 6, 56, 26, 90)
    pygame.draw.rect(surf, (32, 70, 50), (x - 24, y - 14, 48, 28), border_radius=2)
    pygame.draw.rect(surf, (18, 44, 30), (x - 24, y - 14, 48, 28), 2, border_radius=2)
    pygame.draw.rect(surf, (44, 92, 66), (x - 24, y - 16, 48, 6), border_radius=2)
    pygame.draw.line(surf, (18, 44, 30), (x, y - 14), (x, y + 14), 2)
    return None


# ---------- SEWER ----------

def draw_pipe(surf, x, y):
    horiz = random.random() > 0.5
    length = random.randint(70, 130)
    if horiz:
        pygame.draw.rect(surf, (52, 54, 56), (x - length // 2, y - 9, length, 18), border_radius=9)
        pygame.draw.rect(surf, (74, 78, 80), (x - length // 2, y - 9, length, 5), border_radius=4)
        pygame.draw.rect(surf, (34, 36, 38), (x - length // 2, y + 2, length, 5))
        for fx in range(x - length // 2 + 8, x + length // 2, 28):
            pygame.draw.rect(surf, (40, 42, 44), (fx, y - 11, 5, 22))
    else:
        pygame.draw.rect(surf, (52, 54, 56), (x - 9, y - length // 2, 18, length), border_radius=9)
        pygame.draw.rect(surf, (74, 78, 80), (x - 9, y - length // 2, 5, length), border_radius=4)
        for fy in range(y - length // 2 + 8, y + length // 2, 28):
            pygame.draw.rect(surf, (40, 42, 44), (x - 11, fy, 22, 5))
    return None


def draw_puddle(surf, x, y):
    w = random.randint(26, 46)
    h = random.randint(14, 26)
    s = pygame.Surface((w * 2, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (20, 50, 30, 150), s.get_rect())
    pygame.draw.ellipse(s, (40, 80, 50, 120), (3, 2, w * 2 - 6, h - 4), 1)
    pygame.draw.ellipse(s, (70, 120, 80, 80), (w - 8, 3, 14, 5))
    surf.blit(s, (x - w, y - h // 2))
    return None


def draw_grate(surf, x, y):
    pygame.draw.rect(surf, (40, 42, 40), (x - 16, y - 16, 32, 32))
    pygame.draw.rect(surf, (26, 28, 26), (x - 16, y - 16, 32, 32), 2)
    for i in range(-12, 14, 7):
        pygame.draw.line(surf, (20, 22, 20), (x + i, y - 14), (x + i, y + 14), 3)
    return None


def draw_barrel(surf, x, y):
    _shadow(surf, x + 2, y + 4, 30, 14, 90)
    color = random.choice([(120, 90, 30), (40, 70, 50), (90, 40, 36)])
    pygame.draw.circle(surf, color, (x, y), 14)
    pygame.draw.circle(surf, tuple(c - 20 for c in color), (x, y), 14, 2)
    pygame.draw.circle(surf, tuple(min(255, c + 25) for c in color), (x - 4, y - 4), 5)
    return None


# ---------- HOSPITAL ----------

def draw_bed(surf, x, y):
    _shadow(surf, x + 3, y + 4, 52, 26, 70)
    pygame.draw.rect(surf, (90, 92, 96), (x - 24, y - 12, 48, 24), border_radius=3)
    pygame.draw.rect(surf, (210, 212, 208), (x - 22, y - 10, 30, 20), border_radius=2)
    pygame.draw.rect(surf, (180, 185, 190), (x + 8, y - 10, 14, 20), border_radius=2)
    pygame.draw.rect(surf, (60, 62, 66), (x - 24, y - 12, 48, 24), 2, border_radius=3)
    return None


def draw_med_table(surf, x, y):
    _shadow(surf, x + 2, y + 3, 36, 18, 60)
    pygame.draw.rect(surf, (150, 154, 150), (x - 16, y - 10, 32, 20), border_radius=2)
    pygame.draw.rect(surf, (95, 98, 95), (x - 16, y - 10, 32, 20), 2, border_radius=2)
    pygame.draw.rect(surf, (200, 70, 70), (x - 9, y - 6, 6, 4))
    pygame.draw.rect(surf, (70, 200, 90), (x + 1, y - 6, 6, 4))
    pygame.draw.rect(surf, (210, 210, 215), (x - 9, y + 1, 14, 4))
    return None


def draw_locker(surf, x, y):
    _shadow(surf, x + 3, y + 4, 26, 44, 70)
    pygame.draw.rect(surf, (140, 144, 140), (x - 11, y - 22, 22, 44))
    pygame.draw.rect(surf, (95, 98, 95), (x - 11, y - 22, 22, 44), 2)
    pygame.draw.line(surf, (95, 98, 95), (x, y - 22), (x, y + 22), 1)
    pygame.draw.rect(surf, (60, 62, 60), (x - 6, y - 6, 2, 6))
    pygame.draw.rect(surf, (60, 62, 60), (x + 4, y - 6, 2, 6))
    return None


def draw_blood(surf, x, y):
    r = random.randint(12, 26)
    s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
    cx = cy = r * 2
    pygame.draw.circle(s, (96, 6, 6, 170), (cx, cy), r)
    pygame.draw.circle(s, (70, 4, 4, 150), (cx, cy), r, 2)
    for _ in range(random.randint(4, 8)):
        ang = random.uniform(0, math.tau)
        dist = random.randint(r, r + 18)
        sr = random.randint(3, 9)
        sx = cx + int(math.cos(ang) * dist)
        sy = cy + int(math.sin(ang) * dist)
        pygame.draw.circle(s, (86, 5, 5, 140), (sx, sy), sr)
    surf.blit(s, (x - cx, y - cy))
    return None


def draw_wheelchair(surf, x, y):
    _shadow(surf, x, y + 4, 30, 16, 70)
    pygame.draw.circle(surf, (40, 42, 44), (x - 8, y + 4), 10, 3)
    pygame.draw.circle(surf, (40, 42, 44), (x + 8, y + 4), 10, 3)
    pygame.draw.rect(surf, (70, 74, 80), (x - 9, y - 12, 18, 14), border_radius=2)
    pygame.draw.rect(surf, (40, 44, 50), (x - 9, y - 12, 18, 4))
    return None


# ---------- LAB ----------

def draw_lab_table(surf, x, y):
    _shadow(surf, x + 3, y + 4, 64, 28, 70)
    pygame.draw.rect(surf, (120, 128, 142), (x - 30, y - 12, 60, 24), border_radius=3)
    pygame.draw.rect(surf, (80, 88, 102), (x - 30, y - 12, 60, 24), 2, border_radius=3)
    pygame.draw.rect(surf, (150, 158, 172), (x - 30, y - 12, 60, 5), border_radius=2)
    for i in range(3):
        ox = -18 + i * 18
        pygame.draw.rect(surf, (70, 78, 92), (x + ox - 5, y - 7, 10, 15), border_radius=2)
    return None


def draw_monitor(surf, x, y):
    _shadow(surf, x + 2, y + 6, 38, 12, 70)
    pygame.draw.rect(surf, (20, 22, 30), (x - 18, y - 13, 36, 26), border_radius=3)
    glow = random.choice([(0, 150, 200), (0, 200, 140), (200, 160, 0)])
    pygame.draw.rect(surf, tuple(c // 3 for c in glow), (x - 14, y - 9, 28, 18))
    pygame.draw.rect(surf, glow, (x - 14, y - 9, 28, 18), 1)
    for ly in range(y - 6, y + 7, 4):
        lw = random.randint(6, 22)
        pygame.draw.line(surf, glow, (x - 12, ly), (x - 12 + lw, ly), 1)
    pygame.draw.rect(surf, (45, 48, 60), (x - 8, y + 13, 16, 4))
    return (x, y, 95, (glow[0] // 4, glow[1] // 4, glow[2] // 4))


def draw_tank(surf, x, y):
    r = random.randint(20, 30)
    _shadow(surf, x + 2, y + r - 4, r * 2, r, 80)
    pygame.draw.rect(surf, (40, 44, 52), (x - r - 3, y - r - 6, (r + 3) * 2, 8), border_radius=3)
    pygame.draw.circle(surf, (22, 40, 60), (x, y), r)
    fluid = random.choice([(0, 120, 160), (40, 160, 90), (140, 60, 160)])
    pygame.draw.circle(surf, tuple(c // 2 for c in fluid), (x, y), r - 4)
    pygame.draw.circle(surf, fluid, (x, y), r - 4, 2)
    for _ in range(4):
        bx = x + random.randint(-r + 6, r - 6)
        by = y + random.randint(-r + 6, r - 6)
        pygame.draw.circle(surf, (200, 230, 240), (bx, by), random.randint(1, 3))
    pygame.draw.circle(surf, (90, 110, 130), (x, y), r, 2)
    pygame.draw.circle(surf, (140, 200, 220), (x - r // 3, y - r // 3), r // 4)
    return (x, y, 120, (fluid[0] // 3, fluid[1] // 3, fluid[2] // 3))


def draw_warning(surf, x, y):
    w = random.randint(44, 84)
    h = 14
    pygame.draw.rect(surf, (160, 140, 0), (x - w // 2, y - h // 2, w, h))
    for i in range(0, w, 16):
        pygame.draw.polygon(surf, (18, 18, 18),
                            [(x - w // 2 + i, y - h // 2),
                             (x - w // 2 + i + 8, y - h // 2),
                             (x - w // 2 + i, y + h // 2)])
    pygame.draw.rect(surf, (40, 36, 0), (x - w // 2, y - h // 2, w, h), 1)
    return None


def draw_crate(surf, x, y):
    s = random.randint(22, 32)
    _shadow(surf, x + 2, y + 3, s + 8, s + 8, 70)
    pygame.draw.rect(surf, (96, 70, 38), (x - s // 2, y - s // 2, s, s))
    pygame.draw.rect(surf, (62, 44, 22), (x - s // 2, y - s // 2, s, s), 2)
    pygame.draw.line(surf, (62, 44, 22), (x - s // 2, y - s // 2), (x + s // 2, y + s // 2), 2)
    pygame.draw.line(surf, (62, 44, 22), (x + s // 2, y - s // 2), (x - s // 2, y + s // 2), 2)
    return None


def draw_stump(surf, x, y):
    _shadow(surf, x + 2, y + 4, 30, 16, 70)
    pygame.draw.circle(surf, (78, 50, 26), (x, y), 13)
    pygame.draw.circle(surf, (58, 36, 18), (x, y), 13, 2)
    pygame.draw.circle(surf, (96, 64, 34), (x, y), 8, 1)
    pygame.draw.circle(surf, (110, 74, 40), (x, y), 3)
    return None


def draw_fern(surf, x, y):
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        ex = x + int(math.cos(rad) * 14)
        ey = y + int(math.sin(rad) * 10)
        pygame.draw.line(surf, (26, 58, 24), (x, y), (ex, ey), 2)
        pygame.draw.line(surf, (36, 74, 32), (x, y), ((x + ex) // 2, (y + ey) // 2), 1)
    return None


def draw_mushroom(surf, x, y):
    for _ in range(random.randint(2, 4)):
        ox = random.randint(-8, 8)
        oy = random.randint(-6, 6)
        pygame.draw.rect(surf, (210, 200, 180), (x + ox - 1, y + oy, 3, 6))
        cap = random.choice([(150, 40, 40), (140, 110, 70), (90, 70, 110)])
        pygame.draw.ellipse(surf, cap, (x + ox - 5, y + oy - 4, 11, 7))
        pygame.draw.ellipse(surf, tuple(c - 20 for c in cap), (x + ox - 5, y + oy - 4, 11, 7), 1)
    return None


def draw_bench(surf, x, y):
    _shadow(surf, x + 2, y + 4, 50, 18, 70)
    pygame.draw.rect(surf, (90, 64, 36), (x - 24, y - 8, 48, 16), border_radius=2)
    for sx in (x - 20, x - 7, x + 6, x + 19):
        pygame.draw.line(surf, (60, 42, 22), (sx, y - 8), (sx, y + 8), 2)
    pygame.draw.rect(surf, (50, 36, 20), (x - 24, y - 8, 48, 16), 2, border_radius=2)
    return None


def draw_trashcan(surf, x, y):
    _shadow(surf, x + 1, y + 4, 22, 12, 80)
    tipped = random.random() < 0.3
    if tipped:
        pygame.draw.ellipse(surf, (70, 72, 74), (x - 14, y - 8, 28, 16))
        pygame.draw.ellipse(surf, (40, 42, 44), (x - 14, y - 8, 28, 16), 2)
        pygame.draw.ellipse(surf, (30, 32, 34), (x + 6, y - 6, 10, 12))
    else:
        pygame.draw.circle(surf, (70, 72, 74), (x, y), 11)
        pygame.draw.circle(surf, (40, 42, 44), (x, y), 11, 2)
        pygame.draw.circle(surf, (90, 92, 94), (x, y), 11, 1)
    return None


def draw_hydrant(surf, x, y):
    _shadow(surf, x + 1, y + 4, 16, 10, 90)
    pygame.draw.rect(surf, (150, 40, 36), (x - 5, y - 8, 10, 16), border_radius=3)
    pygame.draw.circle(surf, (170, 55, 50), (x, y - 9), 5)
    pygame.draw.rect(surf, (110, 28, 26), (x - 8, y - 2, 16, 4), border_radius=2)
    return None


def draw_manhole(surf, x, y):
    pygame.draw.circle(surf, (44, 44, 46), (x, y), 14)
    pygame.draw.circle(surf, (30, 30, 32), (x, y), 14, 2)
    pygame.draw.circle(surf, (56, 56, 58), (x, y), 10, 1)
    for ang in range(0, 360, 30):
        rad = math.radians(ang)
        pygame.draw.line(surf, (34, 34, 36),
                         (x + int(math.cos(rad) * 4), y + int(math.sin(rad) * 4)),
                         (x + int(math.cos(rad) * 9), y + int(math.sin(rad) * 9)), 1)
    return None


def draw_iv_stand(surf, x, y):
    _shadow(surf, x, y + 6, 16, 8, 70)
    pygame.draw.line(surf, (170, 172, 175), (x, y - 22), (x, y + 8), 2)
    pygame.draw.circle(surf, (120, 122, 125), (x, y + 8), 4, 1)
    pygame.draw.rect(surf, (180, 200, 190), (x - 4, y - 26, 8, 10), border_radius=2)
    pygame.draw.rect(surf, (120, 150, 140), (x - 4, y - 26, 8, 10), 1, border_radius=2)
    return None


def draw_plant(surf, x, y):
    _shadow(surf, x, y + 6, 22, 10, 70)
    pygame.draw.rect(surf, (90, 70, 50), (x - 8, y + 2, 16, 10), border_radius=2)
    for ang in (-40, -15, 15, 40, 0):
        rad = math.radians(ang - 90)
        ex = x + int(math.cos(rad) * 16)
        ey = y + 2 + int(math.sin(rad) * 18)
        pygame.draw.line(surf, (40, 80, 36), (x, y + 2), (ex, ey), 2)
    return None


def draw_sign(surf, x, y):
    pygame.draw.rect(surf, (40, 80, 60), (x - 16, y - 8, 32, 16), border_radius=2)
    pygame.draw.rect(surf, (200, 210, 205), (x - 16, y - 8, 32, 16), 1, border_radius=2)
    pygame.draw.rect(surf, (200, 210, 205), (x - 12, y - 2, 8, 2))
    pygame.draw.rect(surf, (200, 210, 205), (x - 2, y - 2, 14, 2))
    pygame.draw.polygon(surf, (200, 210, 205), [(x + 10, y - 4), (x + 14, y), (x + 10, y + 4)])
    return None


# ---------- STORM / SNOW ----------

def draw_wet_puddle(surf, x, y):
    w = random.randint(28, 52)
    h = random.randint(14, 28)
    s = pygame.Surface((w * 2, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (30, 40, 60, 150), s.get_rect())
    pygame.draw.ellipse(s, (60, 82, 112, 120), (3, 2, w * 2 - 6, h - 4), 1)
    pygame.draw.ellipse(s, (120, 150, 195, 90), (w - 10, 3, 16, 5))
    surf.blit(s, (x - w, y - h // 2))
    return None


def draw_snowdrift(surf, x, y):
    w = random.randint(30, 62)
    h = random.randint(12, 22)
    _shadow(surf, x, y + 4, w, h // 2, 40)
    pygame.draw.ellipse(surf, (206, 214, 230), (x - w // 2, y - h // 2, w, h))
    pygame.draw.ellipse(surf, (236, 242, 252), (x - w // 2 + 4, y - h // 2 + 2, w - 8, h - 7))
    return None


def draw_snowman(surf, x, y):
    _shadow(surf, x, y + 10, 28, 12, 70)
    pygame.draw.circle(surf, (234, 240, 248), (x, y + 8), 12)
    pygame.draw.circle(surf, (234, 240, 248), (x, y - 6), 9)
    pygame.draw.circle(surf, (248, 251, 255), (x, y - 6), 9, 1)
    pygame.draw.circle(surf, (20, 20, 24), (x - 3, y - 8), 1)
    pygame.draw.circle(surf, (20, 20, 24), (x + 3, y - 8), 1)
    pygame.draw.polygon(surf, (212, 120, 40), [(x, y - 6), (x + 8, y - 5), (x, y - 4)])
    for by in (y + 4, y + 9):
        pygame.draw.circle(surf, (40, 40, 46), (x, by), 1)
    return None


def draw_snow_pine(surf, x, y):
    draw_pine(surf, x, y)
    for w, dy in [(40, 12), (32, -2), (24, -16), (16, -30)]:
        pygame.draw.line(surf, (220, 228, 242), (x - w + 6, y + dy - 2), (x + w - 6, y + dy - 2), 3)
    pygame.draw.polygon(surf, (236, 242, 252), [(x - 7, y - 30), (x + 7, y - 30), (x, y - 46)])
    return None


PROP_SETS = {
    'forest': [
        (draw_tree, 110, 60),
        (draw_pine, 60, 56),
        (draw_bush, 70, 32),
        (draw_stump, 16, 44),
        (draw_rock, 22, 36),
        (draw_log, 14, 50),
        (draw_fern, 40, 30),
        (draw_mushroom, 26, 26),
    ],
    'town': [
        (draw_car, 18, 56),
        (draw_streetlight, 16, 64),
        (draw_dumpster, 10, 56),
        (draw_bench, 12, 48),
        (draw_hydrant, 10, 40),
        (draw_trashcan, 16, 36),
        (draw_manhole, 8, 60),
        (draw_debris, 24, 40),
    ],
    'hospital': [
        (draw_bed, 16, 50),
        (draw_med_table, 14, 42),
        (draw_locker, 12, 40),
        (draw_iv_stand, 12, 36),
        (draw_wheelchair, 10, 42),
        (draw_plant, 10, 40),
        (draw_sign, 8, 50),
        (draw_blood, 26, 30),
    ],
    'storm': [
        (draw_wet_puddle, 44, 30),
        (draw_streetlight, 14, 78),
        (draw_barrel, 18, 44),
        (draw_crate, 14, 46),
        (draw_car, 8, 80),
        (draw_debris, 24, 38),
        (draw_trashcan, 12, 40),
    ],
    'snow': [
        (draw_snow_pine, 70, 56),
        (draw_pine, 38, 56),
        (draw_rock, 22, 40),
        (draw_snowdrift, 44, 42),
        (draw_log, 12, 50),
        (draw_stump, 14, 44),
        (draw_snowman, 4, 90),
    ],
}


def generate_props(theme_name, surface, grid, tile_size):
    rows = len(grid)
    cols = len(grid[0])
    cx = (cols // 2) * tile_size
    cy = (rows // 2) * tile_size

    candidates = []
    for row in range(2, rows - 2):
        for col in range(2, cols - 2):
            if grid[row][col] != 0:
                continue
            wx = col * tile_size + tile_size // 2
            wy = row * tile_size + tile_size // 2
            if abs(wx - cx) < tile_size * 2 and abs(wy - cy) < tile_size * 2:
                continue
            candidates.append((wx, wy))

    random.shuffle(candidates)
    placed = []
    lights = []

    for draw_fn, count, min_dist in PROP_SETS.get(theme_name, []):
        done = 0
        for (wx, wy) in candidates:
            if done >= count:
                break
            if any(math.hypot(wx - px, wy - py) < min_dist for px, py, _ in placed):
                continue
            light = draw_fn(surface, wx, wy)
            placed.append((wx, wy, min_dist))
            done += 1
            if light is not None:
                lights.append(light)

    return lights
