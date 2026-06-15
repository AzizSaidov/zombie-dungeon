import pygame


class Menu:
    def __init__(self, title, options, subtitle=""):
        self.title = title
        self.subtitle = subtitle
        self.options = options
        self.sel = 0
        self._rects = []

    def move(self, delta):
        self.sel = (self.sel + delta) % len(self.options)

    def handle_key(self, key):
        if key in (pygame.K_w, pygame.K_UP):
            self.move(-1)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.move(1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            return self.options[self.sel][1]
        return None

    def handle_mouse_motion(self, pos):
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(pos):
                self.sel = i

    def handle_mouse_click(self, pos):
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(pos):
                self.sel = i
                return self.options[i][1]
        return None

    def draw(self, surface, fonts, t, accent=(190, 40, 36)):
        w, h = surface.get_size()
        font_title, font_opt, font_sub = fonts

        title_y = int(h * 0.26)
        ts = font_title.render(self.title, True, accent)
        sh = font_title.render(self.title, True, (0, 0, 0))
        surface.blit(sh, sh.get_rect(center=(w // 2 + 4, title_y + 4)))
        surface.blit(ts, ts.get_rect(center=(w // 2, title_y)))

        if self.subtitle:
            ss = font_sub.render(self.subtitle, True, (150, 150, 150))
            surface.blit(ss, ss.get_rect(center=(w // 2, title_y + 54)))

        self._rects = []
        start_y = int(h * 0.5)
        gap = 58
        for i, (label, _) in enumerate(self.options):
            selected = (i == self.sel)
            color = (255, 222, 130) if selected else (190, 190, 190)
            text = ("> " + label + " <") if selected else label
            surf = font_opt.render(text, True, color)
            rect = surf.get_rect(center=(w // 2, start_y + i * gap))
            self._rects.append(rect.inflate(60, 18))
            if selected:
                glow = pygame.Surface((rect.width + 80, rect.height + 20), pygame.SRCALPHA)
                glow.fill((accent[0], accent[1], accent[2], 40))
                surface.blit(glow, glow.get_rect(center=rect.center))
            surface.blit(surf, rect)

        hint = font_sub.render("W/S — выбор   Enter — ок   Esc — назад", True, (110, 110, 110))
        surface.blit(hint, hint.get_rect(center=(w // 2, int(h * 0.9))))
