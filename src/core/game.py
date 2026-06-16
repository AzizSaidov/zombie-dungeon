import math
import random
import pygame
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, TILE_SIZE
from src.entities.player import Player
from src.entities.zombie import Zombie
from src.entities.boss import Boss
from src.entities.particles import Particles
from src.entities.loot import LootDrop, roll_drop
from src.entities.pickups import WeaponPickup, Objective, ExitGate
from src.rooms.room import Room, THEME_ORDER, THEMES
from src.rooms.layouts import FLOOR
from src.core.camera import Camera
from src.core.audio import Audio
from src.core.effects import Popups
from src.core import scores
from src.ui.menu import Menu
from src.ui.hud import draw_hud

ROOM_COLS = 55
ROOM_ROWS = 40

LOOK_FACTOR = 0.35
LOOK_MAX = 220

MAX_ZOMBIES = 16
SPAWN_EVERY = 1.6
INITIAL_ZOMBIES = 8

WAVE_INTRO_TIME = 2.4
WAVE_CLEAR_TIME = 3.0
BOSS_WAVE_EVERY = 5

CAMPAIGN_LEVELS = [
    {'theme': 'forest',   'cols': 48, 'rows': 36, 'objective': 'key',
     'weapon': 'shotgun', 'spawn_cap': 11, 'spawn_int': 1.45},
    {'theme': 'town',     'cols': 52, 'rows': 38, 'objective': 'fuel',
     'weapon': 'rifle',   'spawn_cap': 14, 'spawn_int': 1.2},
    {'theme': 'hospital', 'cols': 54, 'rows': 40, 'objective': 'vaccine',
     'weapon': 'sniper',  'spawn_cap': 16, 'spawn_int': 1.0, 'boss': True},
]

DIFFICULTIES = {
    'easy':   {'label': 'Лёгкий', 'hp': 0.75, 'dmg': 0.6, 'spawn': 0.8},
    'normal': {'label': 'Норма',  'hp': 1.0,  'dmg': 1.0, 'spawn': 1.0},
    'hard':   {'label': 'Хард',   'hp': 1.4,  'dmg': 1.5, 'spawn': 1.3},
}
DIFF_ORDER = ['easy', 'normal', 'hard']

WEAPON_TRAUMA = {'pistol': 0.12, 'shotgun': 0.34, 'rifle': 0.09, 'sniper': 0.5}
FLASH_SCALE = {'pistol': 0.9, 'shotgun': 1.5, 'rifle': 1.0, 'sniper': 1.7}
SFX_VOL = {'footstep': 0.3, 'dash': 0.6, 'casing': 0.4, 'dryfire': 0.7}
LOW_HP = 0.3

MENU = 'menu'
LOCATION_SELECT = 'location_select'
DIFFICULTY_SELECT = 'difficulty_select'
PLAYING = 'playing'
PAUSED = 'paused'
GAME_OVER = 'game_over'
VICTORY = 'victory'


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
        self.boss = None
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

        self.mode = 'waves'
        self.wave = 0
        self.wave_state = 'intro'
        self.wave_timer = 0.0
        self.wave_spawn_timer = 0.0
        self.wave_interval = 1.2
        self.wave_max_alive = 10
        self.wave_is_boss = False
        self.to_spawn = 0
        self.new_record = False
        self.best = scores.load_best()

        self.difficulty = 'normal'

        self.campaign_level = 0
        self.level_cfg = None
        self.objective = None
        self.exit = None
        self.weapon_pickups = []
        self.objective_done = False
        self.campaign_boss_pending = False

        self.score = 0
        self.elapsed = 0.0
        self.state = MENU

        self.main_menu = Menu("ZOMBIE DUNGEON",
                              [("Кампания", "mode:campaign"),
                               ("Волны", "mode:waves"),
                               ("Бесконечно", "mode:endless"),
                               ("Выход", "quit")],
                              subtitle="выживи в темноте")
        loc_opts = [(THEMES[name]['label'], "loc:" + name) for name in THEME_ORDER]
        loc_opts.append(("Назад", "menu"))
        self.loc_menu = Menu("ВЫБОР ЛОКАЦИИ", loc_opts)
        diff_opts = [(DIFFICULTIES[d]['label'], "diff:" + d) for d in DIFF_ORDER]
        diff_opts.append(("Назад", "menu"))
        self.diff_menu = Menu("СЛОЖНОСТЬ", diff_opts, subtitle="насколько больно")
        self.pause_menu = Menu("ПАУЗА",
                               [("Продолжить", "resume"),
                                ("В главное меню", "menu"),
                                ("Выход", "quit")])
        self.over_menu = Menu("ВЫ ПОГИБЛИ",
                              [("Заново", "restart"),
                               ("В главное меню", "menu"),
                               ("Выход", "quit")])
        self.victory_menu = Menu("ВЫ СПАСЛИСЬ",
                                 [("Ещё раз", "restart"),
                                  ("В главное меню", "menu"),
                                  ("Выход", "quit")])

    # ---------- setup ----------

    def start_game(self, theme_idx=0):
        self._theme_idx = theme_idx
        self.room.set_theme(THEME_ORDER[theme_idx])
        self.score = 0
        self.elapsed = 0.0
        self.new_record = False
        self._reset_level()
        self.state = PLAYING

    def _reset_level(self):
        sx, sy = self.room.find_spawn()
        self.player.reset(sx, sy)
        self.camera.snap((sx, sy))
        self.zombies.clear()
        self.bullets.clear()
        self.loot.clear()
        self.boss = None
        self.muzzle_flashes.clear()
        self.particles = Particles()
        self.popups = Popups()
        self.spawn_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.hitstop = 0.0
        self.heartbeat_timer = 0.0
        self.cross_kick = 0.0
        if self.mode == 'waves':
            self._start_wave(1)
        else:
            for _ in range(INITIAL_ZOMBIES):
                self._spawn_zombie()

    def _spawn_zombie(self, type_name=None, ignore_cap=False):
        if not ignore_cap and len(self.zombies) >= MAX_ZOMBIES:
            return False
        for _ in range(40):
            c = random.randint(2, self.room.cols - 3)
            r = random.randint(2, self.room.rows - 3)
            if self.room.grid[r][c] != FLOOR:
                continue
            wx = c * TILE_SIZE + TILE_SIZE // 2
            wy = r * TILE_SIZE + TILE_SIZE // 2
            if (pygame.math.Vector2(wx, wy) - self.player.pos).length() < 460:
                continue
            if type_name is None:
                roll = random.random()
                t = 'runner' if roll < 0.3 else ('brute' if roll > 0.9 else 'walker')
            else:
                t = type_name
            self.zombies.append(Zombie(wx, wy, t, self._hpm(), self._dmgm()))
            return True
        return False

    # ---------- waves ----------

    def _wave_plan(self, n):
        is_boss = (n % BOSS_WAVE_EVERY == 0)
        quota = 6 + n * 2
        max_alive = min(8 + n, 22)
        interval = max(0.35, 1.4 - n * 0.06)
        return quota, max_alive, interval, is_boss

    def _wave_zombie_type(self, n):
        brute_ch = min(0.26, 0.04 + n * 0.02)
        runner_ch = min(0.45, 0.18 + n * 0.02)
        r = random.random()
        if r < brute_ch:
            return 'brute'
        if r < brute_ch + runner_ch:
            return 'runner'
        return 'walker'

    def _start_wave(self, n):
        self.wave = n
        quota, max_alive, interval, is_boss = self._wave_plan(n)
        sm = self._spm()
        self.wave_max_alive = max(4, int(max_alive * sm))
        self.wave_interval = max(0.25, interval / sm)
        self.wave_spawn_timer = 0.6
        self.wave_is_boss = is_boss
        self.to_spawn = 4 if is_boss else quota
        self.wave_state = 'intro'
        self.wave_timer = WAVE_INTRO_TIME

    def _update_waves(self, dt):
        if self.wave_state == 'intro':
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.wave_state = 'active'
                if self.wave_is_boss:
                    self._spawn_boss()
        elif self.wave_state == 'active':
            if self.to_spawn > 0 and len(self.zombies) < self.wave_max_alive:
                self.wave_spawn_timer -= dt
                if self.wave_spawn_timer <= 0:
                    if self._spawn_zombie(self._wave_zombie_type(self.wave), ignore_cap=True):
                        self.to_spawn -= 1
                        self.wave_spawn_timer = self.wave_interval
            if self.to_spawn <= 0 and not self.zombies and self.boss is None:
                self._clear_wave()
        elif self.wave_state == 'cleared':
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self._start_wave(self.wave + 1)

    def _clear_wave(self):
        self.wave_state = 'cleared'
        self.wave_timer = WAVE_CLEAR_TIME
        got = self.player.heal(20)
        if got > 0:
            self.popups.add(self.player.pos.x, self.player.pos.y, f'+{got} HP', (120, 230, 120))
        self.audio.play('pickup')

    # ---------- campaign ----------

    def _make_room(self, theme_name, cols, rows):
        self.room = Room(cols, rows, theme_name)
        w, h = self.screen.get_size()
        self.room.resize(w, h)
        self.camera.room_w = self.room.width
        self.camera.room_h = self.room.height

    def _find_floor_far(self, avoid, min_dist):
        best, best_d = None, -1.0
        for _ in range(200):
            c = random.randint(2, self.room.cols - 3)
            r = random.randint(2, self.room.rows - 3)
            if self.room.grid[r][c] != FLOOR:
                continue
            p = pygame.math.Vector2(c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2)
            d = min((p - a).length() for a in avoid)
            if d >= min_dist:
                return (p.x, p.y)
            if d > best_d:
                best_d, best = d, (p.x, p.y)
        return best if best else (self.room.width // 2, self.room.height // 2)

    def _campaign_zombie_type(self, level):
        return self._wave_zombie_type(level * 4 + 3)

    def _start_campaign(self):
        self.mode = 'campaign'
        self.score = 0
        self.elapsed = 0.0
        self.new_record = False
        self.campaign_level = 0
        self._setup_campaign_level(0, first=True)
        self.state = PLAYING

    def _setup_campaign_level(self, level, first=False):
        cfg = CAMPAIGN_LEVELS[level]
        self.level_cfg = cfg
        self._theme_idx = THEME_ORDER.index(cfg['theme'])
        self._make_room(cfg['theme'], cfg['cols'], cfg['rows'])

        sx, sy = self.room.find_spawn()
        if first:
            self.player.reset(sx, sy, loadout=['pistol'])
        else:
            self.player.place(sx, sy)
            self.player.heal(40)
        self.camera.snap((sx, sy))

        self.zombies.clear()
        self.bullets.clear()
        self.loot.clear()
        self.boss = None
        self.muzzle_flashes.clear()
        self.particles = Particles()
        self.popups = Popups()
        self.spawn_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.hitstop = 0.0
        self.heartbeat_timer = 0.0
        self.cross_kick = 0.0

        spawn_pt = pygame.math.Vector2(sx, sy)
        ox, oy = self._find_floor_far([spawn_pt], 1000)
        self.objective = Objective(ox, oy, cfg['objective'])
        ex, ey = self._find_floor_far([spawn_pt, pygame.math.Vector2(ox, oy)], 640)
        self.exit = ExitGate(ex, ey)
        wx, wy = self._find_floor_far([spawn_pt], 300)
        self.weapon_pickups = [WeaponPickup(wx, wy, cfg['weapon'])]
        self.objective_done = False
        self.campaign_boss_pending = cfg.get('boss', False)

        for _ in range(6 + level * 2):
            self._spawn_zombie(self._campaign_zombie_type(level), ignore_cap=True)

    def _update_campaign(self, dt):
        cfg = self.level_cfg
        sm = self._spm()
        if len(self.zombies) < max(4, int(cfg['spawn_cap'] * sm)):
            self.spawn_timer += dt
            if self.spawn_timer >= cfg['spawn_int'] / sm:
                self.spawn_timer = 0.0
                self._spawn_zombie(self._campaign_zombie_type(self.campaign_level), ignore_cap=True)

        for wp in self.weapon_pickups:
            wp.update(dt)
            if not wp.taken and wp.near(self.player.pos):
                wp.taken = True
                self.player.give_weapon(wp.weapon_id)
                self.popups.add(wp.pos.x, wp.pos.y, 'НОВОЕ ОРУЖИЕ: ' + wp.name, (170, 225, 245))
                self.audio.play('pickup')
        self.weapon_pickups = [w for w in self.weapon_pickups if not w.taken]

        self.objective.update(dt)
        if not self.objective_done and self.objective.near(self.player.pos):
            self.objective_done = True
            self.objective.taken = True
            self.audio.play('pickup')
            if self.campaign_boss_pending:
                self._spawn_boss()
                self.popups.add(self.objective.pos.x, self.objective.pos.y,
                                'ВАКЦИНА ВЗЯТА — УБЕЙ БОССА!', (255, 120, 90))
            else:
                self.exit.open = True
                self.popups.add(self.objective.pos.x, self.objective.pos.y,
                                self.objective.label + ' ВЗЯТ — К ВЫХОДУ!', (235, 220, 120))

        self.exit.update(dt)
        if self.campaign_boss_pending and self.objective_done and self.boss is None and not self.exit.open:
            self.exit.open = True
            self.popups.add(self.exit.pos.x, self.exit.pos.y, 'ВЫХОД ОТКРЫТ!', (150, 240, 150))
        if self.exit.near(self.player.pos):
            self._advance_campaign()

    def _advance_campaign(self):
        self.campaign_level += 1
        if self.campaign_level >= len(CAMPAIGN_LEVELS):
            self.state = VICTORY
            self.audio.play('heal')
        else:
            self.audio.play('pickup')
            self._setup_campaign_level(self.campaign_level)

    def _spawn_boss(self):
        if self.boss is not None:
            return
        best = None
        for _ in range(80):
            c = random.randint(2, self.room.cols - 3)
            r = random.randint(2, self.room.rows - 3)
            if self.room.grid[r][c] != FLOOR:
                continue
            wx = c * TILE_SIZE + TILE_SIZE // 2
            wy = r * TILE_SIZE + TILE_SIZE // 2
            dist = (pygame.math.Vector2(wx, wy) - self.player.pos).length()
            if best is None or dist > best[0]:
                best = (dist, wx, wy)
            if dist > 700:
                break
        if best:
            self.boss = Boss(best[1], best[2], self._hpm(), self._dmgm())
            self.audio.play('boss_roar', 1.0)

    def _spawn_minion(self):
        if self.boss is None:
            return
        for _ in range(30):
            ang = random.uniform(0, math.tau)
            r = random.uniform(120, 240)
            wx = self.boss.pos.x + math.cos(ang) * r
            wy = self.boss.pos.y + math.sin(ang) * r
            c, rr = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
            if 0 <= rr < self.room.rows and 0 <= c < self.room.cols and self.room.grid[rr][c] == FLOOR:
                self.zombies.append(Zombie(wx, wy, 'runner' if random.random() < 0.5 else 'walker',
                                           self._hpm(), self._dmgm()))
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
        if action.startswith("mode:"):
            self.mode = action[5:]
            self.diff_menu.sel = 1
            self.state = DIFFICULTY_SELECT
        elif action.startswith("diff:"):
            self.difficulty = action[5:]
            if self.mode == 'campaign':
                self._start_campaign()
            else:
                self.loc_menu.sel = 0
                self.state = LOCATION_SELECT
        elif action.startswith("loc:"):
            self.start_game(THEME_ORDER.index(action[4:]))
        elif action == "restart":
            if self.mode == 'campaign':
                self._start_campaign()
            else:
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

    def _hpm(self):
        return DIFFICULTIES[self.difficulty]['hp']

    def _dmgm(self):
        return DIFFICULTIES[self.difficulty]['dmg']

    def _spm(self):
        return DIFFICULTIES[self.difficulty]['spawn']

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
            elif self.state == DIFFICULTY_SELECT:
                self._menu_events(event, self.diff_menu, back="menu")
            elif self.state == PAUSED:
                self._menu_events(event, self.pause_menu, back="resume")
            elif self.state == GAME_OVER:
                self._menu_events(event, self.over_menu, back=None)
            elif self.state == VICTORY:
                self._menu_events(event, self.victory_menu, back=None)
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
            elif event.key == pygame.K_b:
                self._spawn_boss()
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

        room_updated = False
        if self.state == PLAYING:
            self._update_play(dt)
            room_updated = True
        elif self.state in (MENU, LOCATION_SELECT, DIFFICULTY_SELECT):
            self.room.update(dt)
            room_updated = True
            span = max(1, self.room.width - self.scr_w())
            self.camera.offset.x = (self.camera.offset.x + 18 * dt) % span
            self.camera.offset.y = (self.room.height - self.scr_h()) * 0.5

        self.audio.set_ambient(self.room.ambient)
        if room_updated and self.room.lightning is not None and self.room.lightning.struck:
            self.audio.play('thunder', 0.85)

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

        if self.boss is not None:
            self._apply_boss_events(self.boss.update(
                dt, self.player.pos, self.player.hit_rect, self.room.wall_rects))

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
            if not b.dead and self.boss is not None and not self.boss.dead \
                    and b.rect.colliderect(self.boss.hit_rect):
                kb_dir = b.vel.normalize() if b.vel.length() else None
                killed = self.boss.take_damage(b.damage, kb_dir, min(900, b.damage * 22))
                self.particles.blood(b.pos.x, b.pos.y, 16 if b.crit else 10, (b.vel.x, b.vel.y))
                self.particles.spark(b.pos.x, b.pos.y, (b.vel.x, b.vel.y), 4)
                self.audio.play_at('hit', b.pos, listener, base=0.6)
                b.dead = True
                if killed:
                    self._on_boss_death()

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

        if self.mode == 'waves':
            self._update_waves(dt)
        elif self.mode == 'campaign':
            self._update_campaign(dt)
        else:
            self.spawn_timer += dt
            if self.spawn_timer >= SPAWN_EVERY / self._spm():
                self.spawn_timer = 0.0
                self._spawn_zombie()

        self.groan_timer -= dt
        if self.groan_timer <= 0 and self.zombies:
            self.groan_timer = random.uniform(1.3, 3.4)
            self.audio.groan_at(random.choice(self.zombies).pos, listener)

        self._update_heartbeat(dt)

        if self.player.hp <= 0:
            self._on_game_over()

    def _on_game_over(self):
        self.state = GAME_OVER
        self.new_record = False
        if self.mode == 'waves':
            self.new_record = scores.save_best(self.wave, self.score)
            self.best = scores.load_best()

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

    def _apply_boss_events(self, events):
        listener = self.player.pos
        for ev in events:
            kind = ev[0]
            if kind == 'player_dmg':
                _, dmg, d, force = ev
                if self.player.take_damage(dmg):
                    self.player.apply_knockback(pygame.math.Vector2(d), force)
                    self.camera.add_trauma(0.4)
            elif kind == 'spawn':
                for _ in range(ev[1]):
                    self._spawn_minion()
            elif kind == 'shake':
                self.camera.add_trauma(ev[1])
            elif kind == 'sound':
                self.audio.play_at(ev[1], self.boss.pos, listener, base=1.0)
            elif kind == 'shockwave':
                self.particles.spark(ev[1], ev[2], None, 18)

    def _on_boss_death(self):
        b = self.boss
        self.score += b.score
        for _ in range(6):
            self.particles.blood(b.pos.x + random.randint(-44, 44),
                                 b.pos.y + random.randint(-44, 44), 30, big=True)
        self.particles.add_decal(b.pos.x, b.pos.y, big=True)
        self.camera.add_trauma(1.0)
        self.hitstop = 0.12
        self.audio.play('boss_roar', 1.0)
        self.loot.append(LootDrop(b.pos.x, b.pos.y, 'arsenal'))
        self.popups.add(b.pos.x, b.pos.y - 30, 'БОСС ПОВЕРЖЕН!', (255, 210, 90))
        self.boss = None

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
        self.player.resupply()
        self.player.heal(15)
        self.popups.add(x, y, 'АРСЕНАЛ', (255, 222, 120))
        self.audio.play('pickup')
        return True

    # ---------- draw ----------

    def draw(self):
        pygame.mouse.set_visible(self.state != PLAYING)
        if self.state in (MENU, LOCATION_SELECT, DIFFICULTY_SELECT):
            self._draw_backdrop()
            self._dim(120)
            menu = {MENU: self.main_menu, LOCATION_SELECT: self.loc_menu,
                    DIFFICULTY_SELECT: self.diff_menu}[self.state]
            menu.draw(self.screen, self.fonts, self.elapsed)
            if self.state == MENU and self.best['wave'] > 0:
                rec = self.font_sub.render(
                    f"Рекорд волн: {self.best['wave']}   ·   очки: {self.best['score']}",
                    True, (175, 175, 175))
                self.screen.blit(rec, rec.get_rect(center=(self.scr_w() // 2, int(self.scr_h() * 0.82))))
        else:
            self._draw_play()
            self._draw_low_hp()
            if self.player.hurt_timer > 0:
                a = int(120 * (self.player.hurt_timer / 0.25))
                flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                flash.fill((160, 0, 0, a))
                self.screen.blit(flash, (0, 0))
            draw_hud(self.screen, self.player, self.score, self.font, self.font_sub,
                     self.room.label, self.combo, self.wave if self.mode == 'waves' else 0)
            dl = self.font_sub.render(DIFFICULTIES[self.difficulty]['label'], True, (185, 185, 185))
            self.screen.blit(dl, (self.scr_w() - dl.get_width() - 20, 52))
            if self.boss is not None:
                self.boss.draw_health_bar(self.screen, self.font_sub)
            if self.state == PLAYING:
                if self.mode == 'waves':
                    self._draw_wave_banner()
                elif self.mode == 'campaign':
                    self._draw_campaign_hud()
                self._draw_crosshair()
            elif self.state == PAUSED:
                self._dim(150)
                self.pause_menu.draw(self.screen, self.fonts, self.elapsed)
            elif self.state == GAME_OVER:
                self._dim(180)
                self.over_menu.draw(self.screen, self.fonts, self.elapsed, accent=(150, 20, 20))
                if self.mode == 'waves':
                    self._draw_gameover_stats()
            elif self.state == VICTORY:
                self._dim(180)
                self.victory_menu.draw(self.screen, self.fonts, self.elapsed, accent=(60, 180, 90))
                self._draw_victory_stats()

        fps = int(self.clock.get_fps())
        pygame.display.set_caption(f"{TITLE}  |  FPS: {fps}")
        pygame.display.flip()

    def _draw_wave_banner(self):
        if self.wave_state == 'intro':
            text = f"ВОЛНА {self.wave}" + ("   —   БОСС!" if self.wave_is_boss else "")
            sub = "приготовься"
            color = (235, 80, 60) if self.wave_is_boss else (235, 220, 150)
        elif self.wave_state == 'cleared':
            text = f"ВОЛНА {self.wave} ЗАЧИЩЕНА"
            sub = "следующая волна..."
            color = (150, 230, 150)
        else:
            return
        w, h = self.screen.get_size()
        cx, cy = w // 2, int(h * 0.3)
        big = self.font_title.render(text, True, color)
        sh = self.font_title.render(text, True, (0, 0, 0))
        self.screen.blit(sh, sh.get_rect(center=(cx + 3, cy + 3)))
        self.screen.blit(big, big.get_rect(center=(cx, cy)))
        ss = self.font_opt.render(sub, True, (205, 205, 205))
        self.screen.blit(ss, ss.get_rect(center=(cx, cy + 58)))

    def _draw_campaign_hud(self):
        if self.objective is None:
            return
        w, h = self.screen.get_size()
        stage = self.font_sub.render(f"Этап {self.campaign_level + 1}/{len(CAMPAIGN_LEVELS)}",
                                     True, (200, 200, 200))
        ssh = self.font_sub.render(f"Этап {self.campaign_level + 1}/{len(CAMPAIGN_LEVELS)}",
                                   True, (0, 0, 0))
        self.screen.blit(ssh, (22, 56))
        self.screen.blit(stage, (20, 54))

        if not self.objective_done:
            text, target, col = f"ЦЕЛЬ: найти {self.objective.label}", None, self.objective.color
        elif self.campaign_boss_pending and self.boss is not None:
            text, target, col = "УБЕЙ БОССА", self.boss.pos, (235, 90, 70)
        elif self.exit.open:
            text, target, col = "К ВЫХОДУ", self.exit.pos, (150, 240, 150)
        else:
            text, target, col = "", None, (220, 220, 220)
        if text:
            t = self.font.render(text, True, col)
            sh = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(sh, sh.get_rect(center=(w // 2 + 2, 30)))
            self.screen.blit(t, t.get_rect(center=(w // 2, 28)))
        if target is not None:
            self._draw_target_arrow(target, col)

    def _draw_target_arrow(self, target, col):
        w, h = self.screen.get_size()
        tx, ty = self.camera.world_to_screen(target.x, target.y)
        margin = 80
        if margin < tx < w - margin and margin < ty < h - margin:
            return
        cx, cy = w / 2, h / 2
        ang = math.atan2(ty - cy, tx - cx)
        px = cx + math.cos(ang) * (w / 2 - margin)
        py = cy + math.sin(ang) * (h / 2 - margin)
        size = 16
        pts = [(px + math.cos(ang) * size, py + math.sin(ang) * size),
               (px + math.cos(ang + 2.5) * size, py + math.sin(ang + 2.5) * size),
               (px + math.cos(ang - 2.5) * size, py + math.sin(ang - 2.5) * size)]
        pygame.draw.polygon(self.screen, (0, 0, 0), [(x + 2, y + 2) for x, y in pts])
        pygame.draw.polygon(self.screen, col, pts)

    def _draw_victory_stats(self):
        w, h = self.screen.get_size()
        s = self.font.render(f"Очки {self.score}", True, (230, 235, 230))
        sh = self.font.render(f"Очки {self.score}", True, (0, 0, 0))
        self.screen.blit(sh, sh.get_rect(center=(w // 2 + 2, int(h * 0.4) + 2)))
        self.screen.blit(s, s.get_rect(center=(w // 2, int(h * 0.4))))

    def _draw_gameover_stats(self):
        w, h = self.screen.get_size()
        cx, y = w // 2, int(h * 0.4)
        line1 = f"Волна {self.wave}   ·   Очки {self.score}"
        if self.new_record:
            line2, c2 = "НОВЫЙ РЕКОРД!", (255, 215, 90)
        else:
            line2, c2 = f"Рекорд: волна {self.best['wave']} · очки {self.best['score']}", (165, 165, 165)
        for i, (ln, c) in enumerate(((line1, (235, 235, 235)), (line2, c2))):
            s = self.font.render(ln, True, c)
            sh = self.font.render(ln, True, (0, 0, 0))
            self.screen.blit(sh, sh.get_rect(center=(cx + 2, y + i * 36 + 2)))
            self.screen.blit(s, s.get_rect(center=(cx, y + i * 36)))

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
        if self.mode == 'campaign':
            self.exit.draw(self.screen, self.camera, self.font_sub)
            if not self.objective_done:
                self.objective.draw(self.screen, self.camera, self.font_sub)
            for wp in self.weapon_pickups:
                wp.draw(self.screen, self.camera, self.font_sub)
        for z in self.zombies:
            z.draw(self.screen, self.camera)
        if self.boss is not None:
            self.boss.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        extra = [d.light() for d in self.loot]
        if self.mode == 'campaign':
            extra.append(self.exit.light())
            if not self.objective_done:
                extra.append(self.objective.light())
            extra.extend(wp.light() for wp in self.weapon_pickups)
        if self.boss is not None:
            extra.append(self.boss.light())
        for fl in self.muzzle_flashes:
            k = fl['life'] / fl['max']
            extra.append((fl['x'], fl['y'], int(150 * fl['scale'] * k) + 40, (90, 70, 42)))
        self.room.draw_overlays(self.screen, self.camera, (self.player.pos.x, self.player.pos.y),
                                extra_lights=extra)

        if self.boss is not None:
            self.boss.draw_telegraph(self.screen, self.camera)
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
