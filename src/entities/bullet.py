import math
import pygame


class Bullet:
    def __init__(self, x, y, angle_deg, speed, damage, crit=False):
        self.pos = pygame.math.Vector2(x, y)
        rad = math.radians(angle_deg)
        self.vel = pygame.math.Vector2(math.cos(rad), -math.sin(rad)) * speed
        self.damage = damage
        self.crit = crit
        self.life = 1.2
        self.dead = False
        self.hit_wall = False
        self.rect = pygame.Rect(int(x) - 3, int(y) - 3, 6, 6)

    def update(self, dt, wall_rects):
        self.pos += self.vel * dt
        self.life -= dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.life <= 0:
            self.dead = True
            return
        for wall in wall_rects:
            if self.rect.colliderect(wall):
                self.dead = True
                self.hit_wall = True
                return

    def draw(self, surface, camera):
        sx, sy = camera.world_to_screen(self.pos.x, self.pos.y)
        tail = self.vel.normalize() * 12 if self.vel.length() else pygame.math.Vector2()
        if self.crit:
            glow_c, line_c, core_c = (255, 120, 40, 150), (255, 150, 70), (255, 230, 180)
            gr = 9
        else:
            glow_c, line_c, core_c = (255, 200, 90, 120), (255, 230, 150), (255, 245, 200)
            gr = 7
        glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, glow_c, (gr, gr), gr)
        surface.blit(glow, (int(sx) - gr, int(sy) - gr), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.line(surface, line_c,
                         (int(sx - tail.x), int(sy - tail.y)), (int(sx), int(sy)), 3)
        pygame.draw.circle(surface, core_c, (int(sx), int(sy)), 2)
