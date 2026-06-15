import random
from src.entities.bullet import Bullet

WEAPONS = {
    'pistol': {
        'name': 'Пистолет', 'dmg': 26, 'rate': 0.16, 'pellets': 1, 'spread': 2.0,
        'speed': 1150, 'mag': 14, 'reserve': None, 'reload': 1.2, 'auto': False,
        'crit': 0.10, 'crit_mult': 2.0, 'sound': 'shot_pistol', 'body': 'handgun',
    },
    'shotgun': {
        'name': 'Дробовик', 'dmg': 13, 'rate': 0.75, 'pellets': 8, 'spread': 13,
        'speed': 1000, 'mag': 8, 'reserve': 64, 'reload': 1.5, 'auto': False,
        'crit': 0.08, 'crit_mult': 2.0, 'sound': 'shot_shotgun', 'body': 'shotgun',
    },
    'rifle': {
        'name': 'Винтовка', 'dmg': 18, 'rate': 0.085, 'pellets': 1, 'spread': 4,
        'speed': 1400, 'mag': 30, 'reserve': 240, 'reload': 1.9, 'auto': True,
        'crit': 0.12, 'crit_mult': 2.0, 'sound': 'shot_rifle', 'body': 'rifle',
    },
    'sniper': {
        'name': 'Снайперка', 'dmg': 130, 'rate': 1.1, 'pellets': 1, 'spread': 0.5,
        'speed': 2200, 'mag': 5, 'reserve': 40, 'reload': 2.1, 'auto': False,
        'crit': 0.30, 'crit_mult': 2.5, 'sound': 'shot_sniper', 'body': 'rifle',
    },
}

WEAPON_ORDER = ['pistol', 'shotgun', 'rifle', 'sniper']


class Weapon:
    def __init__(self, wid):
        self.id = wid
        self.s = WEAPONS[wid]
        self.name = self.s['name']
        self.in_mag = self.s['mag']
        self.reserve = self.s['reserve']
        self.fire_cd = 0.0
        self.reload_t = 0.0

    @property
    def auto(self):
        return self.s['auto']

    def update(self, dt):
        self.fire_cd = max(0.0, self.fire_cd - dt)
        if self.reload_t > 0:
            self.reload_t = max(0.0, self.reload_t - dt)
            if self.reload_t == 0:
                self._finish_reload()

    def _finish_reload(self):
        need = self.s['mag'] - self.in_mag
        if self.reserve is None:
            self.in_mag = self.s['mag']
        else:
            take = min(need, self.reserve)
            self.in_mag += take
            self.reserve -= take

    def begin_reload(self):
        if self.reload_t > 0 or self.in_mag >= self.s['mag']:
            return False
        if self.reserve is not None and self.reserve <= 0:
            return False
        self.reload_t = self.s['reload']
        return True

    def fire(self, x, y, angle):
        if self.fire_cd > 0 or self.reload_t > 0:
            return None, False
        if self.in_mag <= 0:
            return None, True
        self.fire_cd = self.s['rate']
        self.in_mag -= 1
        bullets = []
        for _ in range(self.s['pellets']):
            sp = random.uniform(-self.s['spread'], self.s['spread'])
            crit = random.random() < self.s['crit']
            dmg = self.s['dmg'] * (self.s['crit_mult'] if crit else 1)
            bullets.append(Bullet(x, y, angle + sp, self.s['speed'], dmg, crit))
        return bullets, False

    def add_reserve(self, amount):
        if self.reserve is None:
            return 0
        cap = self.s['reserve']
        if self.reserve >= cap:
            return 0
        add = min(amount, cap - self.reserve)
        self.reserve += add
        return add

    def refill(self):
        self.in_mag = self.s['mag']
        if self.reserve is not None:
            self.reserve = self.s['reserve']

    def ammo_text(self):
        res = '∞' if self.reserve is None else self.reserve
        return f'{self.in_mag} / {res}'
