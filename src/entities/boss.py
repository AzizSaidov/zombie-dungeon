import math
import random
import pygame

from src.entities.zombie import ZOMBIE_TYPES, _frames_for

ANIM_FPS = 8
SLAM_RADIUS = 180
SLAM_DAMAGE = 30
CHARGE_SPEED = 660
CHARGE_DAMAGE = 26
MELEE_DAMAGE = 16
MELEE_CD = 0.9

WINDUP_SLAM = 0.55
WINDUP_CHARGE = 0.7
SLAM_ACTIVE = 0.3
CHARGE_TIME = 0.55
STAGGER_TIME = 0.9

NAME = "ГНИЛОЙ КОЛОСС"


class Boss:
    def __init__(self, x, y):
        spec = ZOMBIE_TYPES['boss']
        self.frames = _frames_for('boss')
        self.max_hp = spec['hp']
        self.hp = spec['hp']
        self.base_speed = spec['speed']
        self.score = spec['score']

        self.pos = pygame.math.Vector2(x, y)
        self.angle = 0.0
        self.anim = 0.0
        self.dead = False
        self.hit_flash = 0.0
        self.kb = pygame.math.Vector2(0, 0)

        self.state = 'chase'
        self.state_t = 0.0
        self.attack_cd = 2.5
        self.melee_cd = 0.0
        self.charge_dir = pygame.math.Vector2(1, 0)
        self.shock_r = 0.0
        self.flash_phase = False

        r = 96
        self.hit_rect = pygame.Rect(0, 0, r, r)
        self.hit_rect.center = (int(x), int(y))

    def phase(self):
        f = self.hp / self.max_hp
        return 1 if f > 0.66 else (2 if f > 0.33 else 3)

    def take_damage(self, dmg, kb_dir=None, kb_force=0.0):
        self.hp -= dmg
        self.hit_flash = 0.06
        if kb_dir is not None and self.state != 'charge':
            self.kb += kb_dir * (kb_force * 0.05)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def _move(self, vel, dt, wall_rects):
        hit = False
        self.pos.x += vel.x * dt
        self.hit_rect.centerx = int(self.pos.x)
        for wall in wall_rects:
            if self.hit_rect.colliderect(wall):
                if vel.x > 0: self.hit_rect.right = wall.left
                else:         self.hit_rect.left = wall.right
                self.pos.x = self.hit_rect.centerx
                hit = True
        self.pos.y += vel.y * dt
        self.hit_rect.centery = int(self.pos.y)
        for wall in wall_rects:
            if self.hit_rect.colliderect(wall):
                if vel.y > 0: self.hit_rect.bottom = wall.top
                else:         self.hit_rect.top = wall.bottom
                self.pos.y = self.hit_rect.centery
                hit = True
        return hit

    def update(self, dt, player_pos, player_hit_rect, wall_rects):
        events = []
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.melee_cd = max(0.0, self.melee_cd - dt)
        self.state_t -= dt
        ph = self.phase()

        if self.kb.length_squared() > 1:
            self._move(self.kb, dt, wall_rects)
            self.kb *= math.exp(-dt * 7)

        target = pygame.math.Vector2(player_pos)
        to_player = target - self.pos
        dist = to_player.length()
        if dist > 1:
            self.angle = math.degrees(math.atan2(-to_player.y, to_player.x))
        d = to_player / dist if dist > 1 else pygame.math.Vector2(1, 0)

        if self.state == 'chase':
            speed = self.base_speed * (1.0, 1.35, 1.7)[ph - 1]
            self._move(d * speed, dt, wall_rects)
            self.anim = (self.anim + ANIM_FPS * dt) % len(self.frames)
            if self.hit_rect.colliderect(player_hit_rect) and self.melee_cd <= 0:
                self.melee_cd = MELEE_CD
                events.append(('player_dmg', MELEE_DAMAGE, d, 320))
                events.append(('sound', 'snarl'))
            self.attack_cd -= dt
            if self.attack_cd <= 0:
                self._choose_attack(ph, dist, d, events)

        elif self.state == 'windup_slam':
            self.flash_phase = int(self.state_t * 12) % 2 == 0
            if self.state_t <= 0:
                self.state = 'slam'
                self.state_t = SLAM_ACTIVE
                self.shock_r = 0.0
                events.append(('shake', 0.8))
                events.append(('shockwave', self.pos.x, self.pos.y))
                events.append(('sound', 'boss_slam'))
                if (target - self.pos).length() < SLAM_RADIUS:
                    events.append(('player_dmg', SLAM_DAMAGE, d, 520))

        elif self.state == 'slam':
            self.shock_r += SLAM_RADIUS / SLAM_ACTIVE * dt
            if self.state_t <= 0:
                self._recover(ph)

        elif self.state == 'windup_charge':
            self.flash_phase = int(self.state_t * 12) % 2 == 0
            if self.state_t <= 0:
                self.state = 'charge'
                self.state_t = CHARGE_TIME
                events.append(('sound', 'boss_roar'))

        elif self.state == 'charge':
            self.anim = (self.anim + ANIM_FPS * 2 * dt) % len(self.frames)
            crashed = self._move(self.charge_dir * CHARGE_SPEED, dt, wall_rects)
            if self.hit_rect.colliderect(player_hit_rect):
                events.append(('player_dmg', CHARGE_DAMAGE, self.charge_dir, 700))
                events.append(('shake', 0.6))
                self._recover(ph)
            elif crashed:
                self.state = 'stagger'
                self.state_t = STAGGER_TIME
                events.append(('shake', 0.5))
            elif self.state_t <= 0:
                self._recover(ph)

        elif self.state == 'stagger':
            if self.state_t <= 0:
                self._recover(ph)

        return events

    def _choose_attack(self, ph, dist, d, events):
        roll = random.random()
        if ph >= 2 and roll < 0.3:
            events.append(('spawn', 3 if ph == 3 else 2))
            events.append(('sound', 'boss_roar'))
            self.attack_cd = (3.5, 2.6, 1.9)[ph - 1]
            return
        if dist < SLAM_RADIUS * 1.05:
            self.state = 'windup_slam'
            self.state_t = WINDUP_SLAM
        else:
            self.charge_dir = pygame.math.Vector2(d)
            self.state = 'windup_charge'
            self.state_t = WINDUP_CHARGE

    def _recover(self, ph):
        self.state = 'chase'
        self.state_t = 0.0
        self.attack_cd = (3.5, 2.6, 1.9)[ph - 1]

    def light(self):
        ph = self.phase()
        if ph == 3:
            return (self.pos.x, self.pos.y, 150, (70, 18, 14))
        return (self.pos.x, self.pos.y, 120, (28, 36, 22))

    def draw_telegraph(self, surface, camera):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        if self.state == 'windup_slam':
            self._draw_telegraph_circle(surface, sx, sy)
        elif self.state == 'slam' and self.shock_r > 0:
            self._draw_shock_ring(surface, sx, sy)
        elif self.state == 'windup_charge':
            self._draw_telegraph_charge(surface, sx, sy)

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        ph = self.phase()

        frame = self.frames[int(self.anim)]
        rotated = pygame.transform.rotate(frame, self.angle)
        rect = rotated.get_rect(center=(int(sx), int(sy)))
        surface.blit(rotated, rect)

        if ph == 3:
            aura = rotated.copy()
            aura.fill((85, 18, 14), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(aura, rect)
        if self.hit_flash > 0 or (self.flash_phase and self.state in ('windup_slam', 'windup_charge')):
            flash = rotated.copy()
            flash.fill((175, 60, 50), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(flash, rect)

    def _draw_telegraph_circle(self, surface, sx, sy):
        pulse = 0.5 + 0.5 * math.sin(self.state_t * 16)
        s = pygame.Surface((SLAM_RADIUS * 2, SLAM_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (190, 40, 30, int(40 + 50 * pulse)),
                           (SLAM_RADIUS, SLAM_RADIUS), SLAM_RADIUS)
        pygame.draw.circle(s, (255, 80, 60, 160), (SLAM_RADIUS, SLAM_RADIUS), SLAM_RADIUS, 4)
        surface.blit(s, (int(sx) - SLAM_RADIUS, int(sy) - SLAM_RADIUS))

    def _draw_shock_ring(self, surface, sx, sy):
        r = int(self.shock_r)
        if r < 2:
            return
        s = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        a = max(0, int(200 * (1 - self.shock_r / SLAM_RADIUS)))
        pygame.draw.circle(s, (255, 150, 90, a), (r + 4, r + 4), r, 8)
        surface.blit(s, (int(sx) - r - 4, int(sy) - r - 4), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_telegraph_charge(self, surface, sx, sy):
        end = (int(sx + self.charge_dir.x * 480), int(sy + self.charge_dir.y * 480))
        pulse = 0.5 + 0.5 * math.sin(self.state_t * 16)
        pygame.draw.line(surface, (255, 70, 50), (int(sx), int(sy)), end, int(4 + 6 * pulse))

    def draw_health_bar(self, surface, font):
        w = surface.get_width()
        bw, bh = int(w * 0.5), 22
        bx, by = (w - bw) // 2, 64
        pygame.draw.rect(surface, (0, 0, 0), (bx - 3, by - 3, bw + 6, bh + 6), border_radius=4)
        pygame.draw.rect(surface, (30, 12, 12), (bx, by, bw, bh), border_radius=3)
        frac = max(0, self.hp) / self.max_hp
        ph = self.phase()
        col = ((150, 30, 30), (180, 70, 30), (210, 40, 40))[ph - 1]
        pygame.draw.rect(surface, col, (bx, by, int(bw * frac), bh), border_radius=3)
        for t in (0.33, 0.66):
            mx = bx + int(bw * t)
            pygame.draw.line(surface, (10, 10, 10), (mx, by), (mx, by + bh), 2)
        pygame.draw.rect(surface, (120, 90, 90), (bx, by, bw, bh), 2, border_radius=3)
        label = font.render(f"{NAME}   фаза {ph}", True, (235, 220, 220))
        sh = font.render(f"{NAME}   фаза {ph}", True, (0, 0, 0))
        surface.blit(sh, sh.get_rect(center=(w // 2 + 1, by - 11)))
        surface.blit(label, label.get_rect(center=(w // 2, by - 12)))
