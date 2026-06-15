import math
import random
import pygame
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, TILE_SIZE
from src.entities.player import Player
from src.entities.zombie import Zombie
from src.entities.particles import Particles
from src.entities.loot import LootDrop, roll_drop
from src.rooms.room import Room, THEME_ORDER, THEMES
from src.rooms.layouts import FLOOR
from src.core.camera import Camera
from src.core.audio import Audio
from src.core.effects import Popups
from src.ui.menu import Menu
from src.ui.hud import draw_hud

ROOM_COLS = 55
ROOM_ROWS = 40

LOOK_FACTOR = 0.35
LOOK_MAX = 220

MAX_ZOMBIES = 16
SPAWN_EVERY = 1.6
INITIAL_ZOMBIES = 8

WEAPON_TRAUMA = {'pistol': 0.12, 'shotgun': 0.34, 'rifle': 0.09, 'sniper': 0.5}
FLASH_SCALE = {'pistol': 0.9, 'shotgun': 1.5, 'rifle': 1.0, 'sniper': 1.7}
SFX_VOL = {'footstep': 0.3, 'dash': 0.6, 'casing': 0.4, 'dryfire': 0.7}
LOW_HP = 0.3

MENU = 'menu'
LOCATION_SELECT = 'location_select'
PLAYING = 'playing'
PAUSED = 'paused'
GAME_OVER = 'game_over'


class Game:
    def __init__(self):
        self.fullscreen = True
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        pygame.mixer.init()
        self.audio = Audio()

        self.font_title = pygame.font.SysFont("consolas", 84, bold=True)
        self.font_opt = pygame.font.SysFont("consolas", 38, bold=True)
        self.font = pygame.font.SysFont("consolas", 30, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 22)
        self.fonts = (self.font_title, self.font_opt, self.font_sub)

        self._theme_idx = 0
        self.room = Room(ROOM_COLS, ROOM_ROWS, THEME_ORDER[self._theme_idx])
        self.camera = Camera(self.room.width, self.room.height)
        self.player = Player(*self.room.find_spawn())

        w, h = self.screen.get_size()
        self.camera.resize(w, h)
        self.room.resize(w, h)

        self.zombies = []
        self.bullets = []
        self.loot = []
        self.muzzle_flashes = []
        self.particles = Particles()
        self.popups = Popups()
        self.spawn_timer = 0.0
        self.groan_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.hitstop = 0.0
        self.heartbeat_timer = 0.0
        self.cross_kick = 0.0

        self.score = 0
        self.elapsed = 0.0
        self.state = MENU

        self.main_menu = Menu("ZOMBIE DUNGEON",
                              [("Играть", "select"), ("Выход", "quit")],
                              subtitle="выживи в темноте")
        loc_opts = [(THEMES[name]['label'], "loc:" + name) for name in THEME_ORDER]
        loc_opts.append(("Назад", "menu"))
        self.loc_menu = Menu("ВЫБОР ЛОКАЦИИ", loc_opts)
        self.pause_menu = Menu("ПАУЗА",
                               [("Продолжить", "resume"),
                                ("В главное меню", "menu"),
                                ("Выход", "quit")])
        self.over_menu = Menu("ВЫ ПОГИБЛИ",
                              [("Заново", "restart"),
                               ("В главное меню", "menu"),
                               ("Выход", "quit")])

    # ---------- setup ----------

    def start_game(self, theme_idx=0):
        self._theme_idx = theme_idx
        self.room.set_theme(THEME_ORDER[theme_idx])
        self._reset_level()
        self.score = 0
        self.elapsed = 0.0
        self.state = PLAYING

    def _reset_level(self):
        sx, sy = self.room.find_spawn()
        self.player.reset(sx, sy)
        self.camera.snap((sx, sy))
        self.zombies.clear()
        self.bullets.clear()
        self.loot.clear()
        self.muzzle_flashes.clear()
        self.particles = Particles()
        self.popups = Popups()
        self.spawn_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.hitstop = 0.0
        self.heartbeat_timer = 0.0
        self.cross_kick = 0.0
        for _ in range(INITIAL_ZOMBIES):
            self._spawn_zombie()

    def _spawn_zombie(self):
        if len(self.zombies) >= MAX_ZOMBIES:
            return
        for _ in range(40):
            c = random.randint(2, self.room.cols - 3)
            r = random.randint(2, self.room.rows - 3)
            if self.room.grid[r][c] != FLOOR:
                continue
            wx = c * TILE_SIZE + TILE_SIZE // 2
            wy = r * TILE_SIZE + TILE_SIZE // 2
            if (pygame.math.Vector2(wx, wy) - self.player.pos).length() < 460:
                continue
            roll = random.random()
            t = 'runner' if roll < 0.3 else ('brute' if roll > 0.9 else 'walker')
            self.zombies.append(Zombie(wx, wy, t))
            return

    def _next_theme(self):
        self._theme_idx = (self._theme_idx + 1) % len(THEME_ORDER)
        self.room.set_theme(THEME_ORDER[self._theme_idx])
        self._reset_level()

    # ---------- helpers ----------

    def _aim_offset(self):
        mx, my = pygame.mouse.get_pos()
        v = pygame.math.Vector2((mx - self.scr_w() / 2) * LOOK_FACTOR,
                                (my - self.scr_h() / 2) * LOOK_FACTOR)
        if v.length() > LOOK_MAX:
            v.scale_to_length(LOOK_MAX)
        return (v.x, v.y)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        w, h = self.screen.get_size()
        self.camera.resize(w, h)
        self.room.resize(w, h)

    def _do_action(self, action):
        if action == "select":
            self.loc_menu.sel = 0
            self.state = LOCATION_SELECT
        elif action.startswith("loc:"):
            self.start_game(THEME_ORDER.index(action[4:]))
        elif action == "restart":
            self.start_game(self._theme_idx)
        elif action == "resume":
            self.state = PLAYING
        elif action == "menu":
            self.state = MENU
        elif action == "quit":
            self.running = False

    def scr_w(self):
        return self.screen.get_width()

    def scr_h(self):
        return self.screen.get_height()

    # ---------- events ----------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
                continue

            if self.state == MENU:
                self._menu_events(event, self.main_menu, back=None)
            elif self.state == LOCATION_SELECT:
                self._menu_events(event, self.loc_menu, back="menu")
            elif self.state == PAUSED:
                self._menu_events(event, self.pause_menu, back="resume")
            elif self.state == GAME_OVER:
                self._menu_events(event, self.over_menu, back=None)
            elif self.state == PLAYING:
                self._play_events(event)

    def _menu_events(self, event, menu, back):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and back:
                self._do_action(back)
                return
            action = menu.handle_key(event.key)
            if action:
                self._do_action(action)
        elif event.type == pygame.MOUSEMOTION:
            menu.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = menu.handle_mouse_click(event.pos)
            if action:
                self._do_action(action)

    def _play_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = PAUSED
            elif event.key == pygame.K_SPACE:
                self.player.start_dash()
            elif event.key == pygame.K_TAB:
                self._next_theme()
            elif event.key == pygame.K_r:
                self.player.reload()
            elif event.key == pygame.K_q:
                self.player.swap(-1)
            elif event.key == pygame.K_e:
                self.player.swap(1)
            elif event.key == pygame.K_1:
                self.player.set_active(0)
            elif event.key == pygame.K_2:
                self.player.set_active(1)
            elif event.key == pygame.K_3:
                self.player.set_active(2)
            elif event.key == pygame.K_4:
                self.player.set_active(3)
        elif event.type == pygame.MOUSEWHEEL:
            self.player.swap(-1 if event.y > 0 else 1)

    # ---------- update ----------

    def update(self):
        dt = self.clock.get_time() / 1000
        if dt > 0.05:
            dt = 0.05

        if self.state == PLAYING:
            self._update_play(dt)
        elif self.state in (MENU, LOCATION_SELECT):
            self.room.update(dt)
            span = max(1, self.room.width - self.scr_w())
            self.camera.offset.x = (self.camera.offset.x + 18 * dt) % span
            self.camera.offset.y = (self.room.height - self.scr_h()) * 0.5

    def _update_play(self, dt):
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            return

        self.elapsed += dt
        self.room.update(dt)
        listener = self.player.pos

        new_bullets = self.player.update(dt, self.room.wall_rects, self.camera.offset)
        self.bullets.extend(new_bullets)
        for s in self.player.sound_events:
            self.audio.play(s, SFX_VOL.get(s, 1.0))
        self.player.sound_events.clear()
        if self.player.just_fired:
            self._on_fire()
        self.camera.update(self.player.pos, dt, self._aim_offset())

        for z in self.zombies:
            z.update(dt, self.player.pos, self.room.wall_rects)
            if z.hit_rect.colliderect(self.player.hit_rect):
                dmg = z.try_bite()
                if dmg and self.player.take_damage(dmg):
                    self.camera.add_trauma(0.35)
                    self.audio.play_at('snarl', z.pos, listener, base=0.9)

        for b in self.bullets:
            b.update(dt, self.room.wall_rects)
            if b.dead:
                if b.hit_wall:
                    self.particles.spark(b.pos.x, b.pos.y, (b.vel.x, b.vel.y), 5)
                    self.audio.play_at('wall_hit', b.pos, listener, base=0.5)
                continue
            for z in self.zombies:
                if not z.dead and b.rect.colliderect(z.hit_rect):
                    kb_dir = b.vel.normalize() if b.vel.length() else None
                    killed = z.take_damage(b.damage, kb_dir, min(900, b.damage * 22))
                    self.particles.blood(b.pos.x, b.pos.y, 14 if b.crit else 8, (b.vel.x, b.vel.y))
                    self.particles.spark(b.pos.x, b.pos.y, (b.vel.x, b.vel.y), 3)
                    self.audio.play_at('hit', b.pos, listener, base=0.55)
                    b.dead = True
                    if killed:
                        self._on_kill(z, b.crit)
                    break

        for d in self.loot:
            d.update(dt)
            if not d.dead and d.picked_by(self.player.pos) and self._apply_loot(d):
                d.dead = True
        self.loot = [d for d in self.loot if not d.dead]

        for fl in self.muzzle_flashes:
            fl['life'] -= dt
        self.muzzle_flashes = [f for f in self.muzzle_flashes if f['life'] > 0]
        self.cross_kick = max(0.0, self.cross_kick - dt * 90)

        self.bullets = [b for b in self.bullets if not b.dead]
        self.zombies = [z for z in self.zombies if not z.dead]
        self.particles.update(dt)
        self.popups.update(dt)

        if self.combo_timer > 0:
            self.combo_timer = max(0.0, self.combo_timer - dt)
            if self.combo_timer == 0:
                self.combo = 0

        self.spawn_timer += dt
        if self.spawn_timer >= SPAWN_EVERY:
            self.spawn_timer = 0.0
            self._spawn_zombie()

        self.groan_timer -= dt
        if self.groan_timer <= 0 and self.zombies:
            self.groan_timer = random.uniform(1.3, 3.4)
            self.audio.groan_at(random.choice(self.zombies).pos, listener)

        self._update_heartbeat(dt)

        if self.player.hp <= 0:
            self.state = GAME_OVER

    def _on_fire(self):
        wpn = self.player.current()
        scale = FLASH_SCALE.get(wpn.id, 1.0)
        mx, my = self.player.muzzle()
        self.muzzle_flashes.append({'x': mx, 'y': my, 'angle': self.player.angle,
                                    'life': 0.05, 'max': 0.05, 'scale': scale})
        self.camera.add_trauma(WEAPON_TRAUMA.get(wpn.id, 0.12))
        self.cross_kick = min(24, self.cross_kick + scale * 6)
        rad = math.radians(self.player.angle)
        d = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
        perp = pygame.math.Vector2(-d.y, d.x)
        vel = (perp - d * 0.3) * random.uniform(130, 230)
        self.particles.casing(mx, my, vel.x, vel.y)
        self.audio.play('casing', SFX_VOL['casing'])

    def _on_kill(self, z, crit):
        self.combo += 1
        self.combo_timer = 2.2
        gained = int(z.score * (1 + 0.1 * (self.combo - 1)))
        self.score += gained
        self.particles.blood(z.pos.x, z.pos.y, 26, big=True)
        self.particles.add_decal(z.pos.x, z.pos.y, big=(z.type_name == 'brute'))
        self.audio.play_at('zombie_die', z.pos, self.player.pos, base=0.7)
        txt = f'+{gained}' + (f'  x{self.combo}' if self.combo >= 3 else '')
        col = (255, 210, 90) if self.combo >= 3 else (220, 220, 200)
        self.popups.add(z.pos.x, z.pos.y, txt, col)
        big = z.type_name == 'brute'
        if big or crit:
            self.camera.add_trauma(0.5 if big else 0.3)
            self.hitstop = 0.05 if big else 0.03
        kind = roll_drop(z.type_name, self.player)
        if kind:
            self.loot.append(LootDrop(z.pos.x, z.pos.y, kind))

    def _update_heartbeat(self, dt):
        frac = self.player.hp / self.player.max_hp
        if 0 < frac < LOW_HP:
            self.heartbeat_timer -= dt
            if self.heartbeat_timer <= 0:
                self.heartbeat_timer = 0.45 + 0.9 * (frac / LOW_HP)
                self.audio.play('heartbeat', 0.7)
        else:
            self.heartbeat_timer = 0.0

    def _apply_loot(self, drop):
        x, y = drop.pos.x, drop.pos.y
        if drop.kind == 'medkit':
            got = self.player.heal(35)
            if got <= 0:
                return False
            self.popups.add(x, y, f'+{got} HP', (120, 230, 120))
            self.audio.play('heal')
            return True
        if drop.kind == 'ammo':
            got = self.player.add_ammo()
            if got <= 0:
                return False
            self.popups.add(x, y, f'+{got} патронов', (240, 210, 120))
            self.audio.play('pickup')
            return True
        self.player.refill_all()
        self.player.heal(25)
        self.popups.add(x, y, 'АРСЕНАЛ', (255, 222, 120))
        self.audio.play('pickup')
        return True

    # ---------- draw ----------

    def draw(self):
        pygame.mouse.set_visible(self.state != PLAYING)
        if self.state in (MENU, LOCATION_SELECT):
            self._draw_backdrop()
            self._dim(120)
            menu = self.main_menu if self.state == MENU else self.loc_menu
            menu.draw(self.screen, self.fonts, self.elapsed)
        else:
            self._draw_play()
            self._draw_low_hp()
            if self.player.hurt_timer > 0:
                a = int(120 * (self.player.hurt_timer / 0.25))
                flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                flash.fill((160, 0, 0, a))
                self.screen.blit(flash, (0, 0))
            draw_hud(self.screen, self.player, self.score, self.font, self.font_sub,
                     self.room.label, self.combo)
            if self.state == PLAYING:
                self._draw_crosshair()
            elif self.state == PAUSED:
                self._dim(150)
                self.pause_menu.draw(self.screen, self.fonts, self.elapsed)
            elif self.state == GAME_OVER:
                self._dim(180)
                self.over_menu.draw(self.screen, self.fonts, self.elapsed, accent=(150, 20, 20))

        fps = int(self.clock.get_fps())
        pygame.display.set_caption(f"{TITLE}  |  FPS: {fps}")
        pygame.display.flip()

    def _draw_low_hp(self):
        frac = self.player.hp / self.player.max_hp
        if not (0 < frac < LOW_HP):
            return
        p = 0.5 + 0.5 * math.sin(self.elapsed * 6.0)
        a = int(70 * p * (1 - frac / LOW_HP))
        if a <= 0:
            return
        pulse = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pulse.fill((150, 0, 0, a))
        self.screen.blit(pulse, (0, 0))

    def _draw_backdrop(self):
        self.room.draw_floor(self.screen, self.camera)
        lp = (self.camera.offset.x + self.scr_w() / 2,
              self.camera.offset.y + self.scr_h() / 2)
        self.room.draw_overlays(self.screen, self.camera, lp)

    def _draw_play(self):
        self.room.draw_floor(self.screen, self.camera)
        self.particles.draw_decals(self.screen, self.camera)
        for d in self.loot:
            d.draw(self.screen, self.camera)
        for z in self.zombies:
            z.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        extra = [d.light() for d in self.loot]
        for fl in self.muzzle_flashes:
            k = fl['life'] / fl['max']
            extra.append((fl['x'], fl['y'], int(150 * fl['scale'] * k) + 40, (90, 70, 42)))
        self.room.draw_overlays(self.screen, self.camera, (self.player.pos.x, self.player.pos.y),
                                extra_lights=extra)

        for fl in self.muzzle_flashes:
            self._draw_flash(fl)
        for b in self.bullets:
            b.draw(self.screen, self.camera)
        self.particles.draw(self.screen, self.camera)
        self.popups.draw(self.screen, self.camera, self.font_sub)

    def _draw_flash(self, fl):
        sx, sy = self.camera.world_to_screen(fl['x'], fl['y'])
        k = fl['life'] / fl['max']
        r = int((10 + 16 * fl['scale']) * k) + 4
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 216, 150), (r * 2, r * 2), r)
        pygame.draw.circle(glow, (255, 250, 224), (r * 2, r * 2), max(1, r // 2))
        self.screen.blit(glow, (int(sx) - r * 2, int(sy) - r * 2), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_crosshair(self):
        mx, my = pygame.mouse.get_pos()
        gap = int(6 + self.cross_kick)
        ln = 10
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x1, y1 = mx + dx * gap, my + dy * gap
            x2, y2 = mx + dx * (gap + ln), my + dy * (gap + ln)
            pygame.draw.line(self.screen, (0, 0, 0), (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 4)
            pygame.draw.line(self.screen, (235, 235, 235), (x1, y1), (x2, y2), 2)
        pygame.draw.circle(self.screen, (235, 60, 60), (mx, my), 2)

    def _dim(self, alpha):
        dim = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, alpha))
        self.screen.blit(dim, (0, 0))

    # ---------- loop ----------

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
