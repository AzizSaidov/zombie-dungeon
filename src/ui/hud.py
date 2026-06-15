import pygame


def draw_hud(surface, player, score, font, font_sub, location_label, combo=0, wave=0):
    w, h = surface.get_size()

    shadow = font.render(location_label, True, (0, 0, 0))
    label = font.render(location_label, True, (210, 210, 210))
    surface.blit(shadow, (22, 22))
    surface.blit(label, (20, 20))

    if wave > 0:
        wsh = font.render(f"Волна {wave}", True, (0, 0, 0))
        wtxt = font.render(f"Волна {wave}", True, (235, 210, 140))
        surface.blit(wsh, (22, 56))
        surface.blit(wtxt, (20, 54))

    bar_x, bar_y = 20, h - 46
    bar_w, bar_h = 280, 26
    pygame.draw.rect(surface, (0, 0, 0), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=4)
    pygame.draw.rect(surface, (45, 12, 12), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    frac = max(0, player.hp) / player.max_hp
    col = (200, 50, 50) if frac > 0.3 else (220, 90, 40)
    pygame.draw.rect(surface, col, (bar_x, bar_y, int(bar_w * frac), bar_h), border_radius=3)
    pygame.draw.rect(surface, (90, 90, 90), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
    hp_txt = font_sub.render(f"HP {max(0, int(player.hp))}/{player.max_hp}", True, (240, 240, 240))
    surface.blit(hp_txt, hp_txt.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2)))

    box_w, gap = 132, 6
    slot_y = bar_y - 60
    for i, wpn in enumerate(player.weapons):
        active = (i == player.active)
        box = pygame.Rect(bar_x + i * (box_w + gap), slot_y, box_w, 48)
        bg = (52, 46, 28) if active else (26, 26, 28)
        pygame.draw.rect(surface, bg, box, border_radius=4)
        pygame.draw.rect(surface, (235, 200, 90) if active else (75, 75, 75), box, 2, border_radius=4)
        key = font_sub.render(str(i + 1), True, (120, 120, 120))
        surface.blit(key, (box.x + 6, box.y + 3))
        name = font_sub.render(wpn.name, True, (240, 240, 220) if active else (155, 155, 155))
        surface.blit(name, (box.x + 26, box.y + 4))
        if wpn.reload_t > 0:
            ammo_s, ammo_c = "...", (240, 200, 90)
        else:
            ammo_s, ammo_c = wpn.ammo_text(), (220, 220, 180) if active else (140, 140, 140)
        ammo = font_sub.render(ammo_s, True, ammo_c)
        surface.blit(ammo, (box.x + 26, box.y + 25))

    score_txt = font.render(f"Убито: {score}", True, (235, 235, 235))
    sh = font.render(f"Убито: {score}", True, (0, 0, 0))
    surface.blit(sh, (w - score_txt.get_width() - 18, 22))
    surface.blit(score_txt, (w - score_txt.get_width() - 20, 20))

    dash_ready = player.dash_cd <= 0
    dx, dy = bar_x + bar_w + 16, bar_y
    pygame.draw.rect(surface, (0, 0, 0), (dx - 2, dy - 2, 70, bar_h + 4), border_radius=4)
    fill = 1.0 if dash_ready else (1 - player.dash_cd / 0.85)
    base = (60, 130, 200) if dash_ready else (40, 50, 64)
    pygame.draw.rect(surface, (24, 28, 36), (dx, dy, 70, bar_h), border_radius=3)
    pygame.draw.rect(surface, base, (dx, dy, int(70 * fill), bar_h), border_radius=3)
    pygame.draw.rect(surface, (90, 110, 130), (dx, dy, 70, bar_h), 2, border_radius=3)
    dlbl = font_sub.render("DASH" if dash_ready else "...", True,
                           (220, 235, 250) if dash_ready else (130, 140, 150))
    surface.blit(dlbl, dlbl.get_rect(center=(dx + 35, dy + bar_h // 2)))

    if combo >= 2:
        c = (255, 210, 90) if combo >= 5 else (235, 235, 220)
        big = font.render(f"COMBO x{combo}", True, c)
        bsh = font.render(f"COMBO x{combo}", True, (0, 0, 0))
        cx = w // 2
        surface.blit(bsh, bsh.get_rect(center=(cx + 2, 56)))
        surface.blit(big, big.get_rect(center=(cx, 54)))
