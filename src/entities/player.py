import pygame
import os
import math

from src.entities.weapon import Weapon

ASSETS = os.path.join("assets", "images", "player", "Top_Down_Survivor")

SCALE = 0.45
SPEED = 220
ANIM_FPS = 12

MUZZLE_FWD = 42
MUZZLE_SIDE = 16

DASH_SPEED = 760
DASH_TIME = 0.16
DASH_CD = 0.85
STEP_INTERVAL = 0.33


def load_frames(folder):
    frames = []
    for f in sorted(os.listdir(folder)):
        if f.endswith(".png"):
            img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
            w = int(img.get_width() * SCALE)
            h = int(img.get_height() * SCALE)
            frames.append(pygame.transform.scale(img, (w, h)))
    return frames


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.feet_idle = load_frames(os.path.join(ASSETS, "feet", "idle"))
        self.feet_run = load_frames(os.path.join(ASSETS, "feet", "run"))
        self.bodies = {
            'handgun': load_frames(os.path.join(ASSETS, "handgun", "idle")),
            'shotgun': load_frames(os.path.join(ASSETS, "shotgun", "idle")),
            'rifle': load_frames(os.path.join(ASSETS, "rifle", "idle")),
        }

        self.feet_index = 0.0
        self.pos = pygame.math.Vector2(x, y)
        self.angle = 0.0
        self.moving = False

        self.max_hp = 100
        self.hp = 100
        self.hurt_timer = 0.0

        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.dash_dir = pygame.math.Vector2(1, 0)
        self.invuln = 0.0
        self.trail = []
        self.step_timer = 0.0

        self.weapons = [Weapon('pistol'), Weapon('shotgun'),
                        Weapon('rifle'), Weapon('sniper')]
        self.active = 0
        self.sound_events = []
        self.prev_fire = False
        self.just_fired = False

        self.hit_rect = pygame.Rect(0, 0, 40, 40)
        self.hit_rect.center = (x, y)

        self.image = self.bodies['handgun'][0]
        self.rect = self.image.get_rect(center=(x, y))

    def current(self):
        return self.weapons[self.active]

    def reset(self, x, y):
        self.hp = self.max_hp
        self.hurt_timer = 0.0
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.invuln = 0.0
        self.trail.clear()
        self.step_timer = 0.0
        self.weapons = [Weapon('pistol'), Weapon('shotgun'),
                        Weapon('rifle'), Weapon('sniper')]
        self.active = 0
        self.prev_fire = False
        self.just_fired = False
        self.sound_events.clear()
        self.pos.update(x, y)
        self.hit_rect.center = (int(x), int(y))
        self.rect.center = (int(x), int(y))

    def start_dash(self):
        if self.dash_cd > 0 or self.dash_t > 0:
            return
        keys = pygame.key.get_pressed()
        d = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    d.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  d.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  d.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: d.x += 1
        if d.length() == 0:
            rad = math.radians(self.angle)
            d = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
        d.normalize_ip()
        self.dash_dir = d
        self.dash_t = DASH_TIME
        self.dash_cd = DASH_CD
        self.invuln = DASH_TIME + 0.06
        self.sound_events.append('dash')

    def set_active(self, i):
        if 0 <= i < len(self.weapons):
            self.active = i

    def swap(self, step=1):
        self.active = (self.active + step) % len(self.weapons)

    def reload(self):
        if self.current().begin_reload():
            self.sound_events.append('reload')

    def muzzle(self):
        rad = math.radians(self.angle)
        d = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
        perp = pygame.math.Vector2(-d.y, d.x)
        m = self.pos + d * MUZZLE_FWD + perp * MUZZLE_SIDE
        return (m.x, m.y)

    def take_damage(self, dmg):
        if self.invuln > 0:
            return False
        self.hp -= dmg
        self.hurt_timer = 0.25
        return True

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return int(self.hp - before)

    def add_ammo(self):
        w = self.current()
        if w.reserve is None:
            total = 0
            for ow in self.weapons:
                if ow.reserve is not None:
                    total += ow.add_reserve(ow.s['mag'])
            return total
        return w.add_reserve(w.s['mag'] * 2)

    def refill_all(self):
        for w in self.weapons:
            w.refill()

    def update(self, dt, wall_rects, cam_offset=(0, 0)):
        self.hurt_timer = max(0, self.hurt_timer - dt)
        self.dash_cd = max(0, self.dash_cd - dt)
        self.invuln = max(0, self.invuln - dt)
        self.current().update(dt)

        if self.dash_t > 0:
            self.dash_t = max(0, self.dash_t - dt)
            move = pygame.math.Vector2(self.dash_dir)
            speed = DASH_SPEED
            self.trail.append([self.pos.x, self.pos.y, 0.22])
        else:
            keys = pygame.key.get_pressed()
            move = pygame.math.Vector2(0, 0)
            if keys[pygame.K_w] or keys[pygame.K_UP]:    move.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  move.y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  move.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += 1
            speed = SPEED

        self.moving = move.length() > 0
        if self.moving:
            move.normalize_ip()
            self.pos.x += move.x * speed * dt
            self.hit_rect.centerx = int(self.pos.x)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if move.x > 0: self.hit_rect.right = wall.left
                    else:          self.hit_rect.left = wall.right
                    self.pos.x = self.hit_rect.centerx
            self.pos.y += move.y * speed * dt
            self.hit_rect.centery = int(self.pos.y)
            for wall in wall_rects:
                if self.hit_rect.colliderect(wall):
                    if move.y > 0: self.hit_rect.bottom = wall.top
                    else:          self.hit_rect.top = wall.bottom
                    self.pos.y = self.hit_rect.centery
            self.feet_index = (self.feet_index + ANIM_FPS * dt) % len(self.feet_run)
            if self.dash_t <= 0:
                self.step_timer -= dt
                if self.step_timer <= 0:
                    self.step_timer = STEP_INTERVAL
                    self.sound_events.append('footstep')
        else:
            self.step_timer = 0.0

        for t in self.trail:
            t[2] -= dt
        self.trail = [t for t in self.trail if t[2] > 0]

        mx, my = pygame.mouse.get_pos()
        sx = self.pos.x - cam_offset[0]
        sy = self.pos.y - cam_offset[1]
        self.angle = math.degrees(math.atan2(-(my - sy), mx - sx))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        mouse_down = pygame.mouse.get_pressed()[0]
        wpn = self.current()
        clicked = mouse_down and not self.prev_fire
        want_fire = mouse_down if wpn.auto else clicked
        self.prev_fire = mouse_down

        new_bullets = []
        self.just_fired = False
        if want_fire:
            res, empty = wpn.fire(*self.muzzle(), self.angle)
            if res:
                new_bullets = res
                self.just_fired = True
                self.sound_events.append(wpn.s['sound'])
            elif empty:
                if wpn.begin_reload():
                    self.sound_events.append('reload')
                elif clicked:
                    self.sound_events.append('dryfire')
        return new_bullets

    def draw(self, surface, camera):
        for tx, ty, age in self.trail:
            gx, gy = camera.world_to_screen(tx, ty)
            a = int(110 * (age / 0.22))
            r = 16
            ghost = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ghost, (120, 170, 230, a), (r, r), r)
            surface.blit(ghost, (int(gx) - r, int(gy) - r))

        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        screen_center = (int(sx), int(sy))

        feet_img = self.feet_run[int(self.feet_index)] if self.moving else self.feet_idle[0]
        surface.blit(feet_img, feet_img.get_rect(center=screen_center))

        body = self.bodies[self.current().s['body']][0]
        rotated = pygame.transform.rotate(body, self.angle)
        rect = rotated.get_rect(center=screen_center)
        surface.blit(rotated, rect)
        if self.invuln > 0:
            tint = rotated.copy()
            tint.fill((40, 90, 160), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(tint, rect, special_flags=pygame.BLEND_RGB_ADD)
