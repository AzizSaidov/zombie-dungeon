import math
import random
import pygame
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, room_width, room_height):
        self.offset = pygame.math.Vector2(0, 0)
        self.center = pygame.math.Vector2(0, 0)
        self.room_w = room_width
        self.room_h = room_height
        self.screen_w = SCREEN_WIDTH
        self.screen_h = SCREEN_HEIGHT
        self.trauma = 0.0

    def resize(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._apply()

    def snap(self, pos):
        self.center.update(pos[0], pos[1])
        self._apply()

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, target, dt, aim=(0, 0)):
        desired_x = target[0] + aim[0]
        desired_y = target[1] + aim[1]
        s = 1.0 - math.exp(-12.0 * dt)
        self.center.x += (desired_x - self.center.x) * s
        self.center.y += (desired_y - self.center.y) * s
        self._apply()
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - dt * 1.7)
            shake = self.trauma * self.trauma * 26
            self.offset.x += random.uniform(-1, 1) * shake
            self.offset.y += random.uniform(-1, 1) * shake

    def _apply(self):
        x = self.center.x - self.screen_w / 2
        y = self.center.y - self.screen_h / 2
        self.offset.x = max(0, min(x, self.room_w - self.screen_w))
        self.offset.y = max(0, min(y, self.room_h - self.screen_h))

    def world_to_screen(self, wx, wy):
        return (wx - self.offset.x, wy - self.offset.y)
