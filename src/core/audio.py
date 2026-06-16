import math
import random
import array
import pygame


def _freq():
    return pygame.mixer.get_init()[0]


def _to_sound(mono):
    _f, _size, channels = pygame.mixer.get_init()
    buf = array.array('h')
    for s in mono:
        v = int(max(-1.0, min(1.0, s)) * 32767)
        buf.append(v)
        if channels == 2:
            buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _gun(dur, boom_f, decay, crack_amt, boom_amt, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    for i in range(n):
        t = i / f
        crack = random.uniform(-1, 1) * math.exp(-t * 140) * crack_amt
        pf = boom_f * (1 + 2.6 * math.exp(-t * 30))
        boom = math.sin(2 * math.pi * pf * t) * math.exp(-t * decay) * boom_amt
        tail = random.uniform(-1, 1) * math.exp(-t * decay * 0.55) * 0.3
        out.append((crack + boom + tail) * vol)
    return out


def _hit():
    f = _freq()
    n = int(f * 0.12)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        prev = prev * 0.55 + random.uniform(-1, 1) * 0.45
        thud = math.sin(2 * math.pi * 90 * t) * math.exp(-t * 30) * 0.5
        out.append((prev * math.exp(-t * 45) + thud) * 0.7)
    return out


def _growl(dur, base, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    rasp = random.uniform(24, 34)
    for i in range(n):
        t = i / f
        rough = 0.55 + 0.45 * math.sin(2 * math.pi * rasp * t)
        vib = base * (1 + 0.05 * math.sin(2 * math.pi * 4.5 * t))
        tone = math.sin(2 * math.pi * vib * t)
        sub = math.sin(2 * math.pi * vib * 0.5 * t) * 0.55
        nz = random.uniform(-1, 1) * 0.3
        env = min(1.0, t * 5) * math.exp(-t * 1.1)
        out.append((tone * 0.5 + sub + nz * 0.4) * rough * env * vol)
    return out


def _gurgle(dur, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    prev = 0.0
    am = random.uniform(10, 16)
    for i in range(n):
        t = i / f
        prev = prev * 0.7 + random.uniform(-1, 1) * 0.3
        wet = 0.4 + 0.6 * abs(math.sin(2 * math.pi * am * t))
        low = math.sin(2 * math.pi * 70 * t) * 0.4
        env = min(1.0, t * 6) * math.exp(-t * 1.4)
        out.append((prev * wet + low) * env * vol)
    return out


def _hiss(dur, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        nz = random.uniform(-1, 1)
        hp = nz - prev
        prev = nz
        env = math.sin(math.pi * min(1.0, t / dur)) ** 0.6
        out.append(hp * env * vol * 0.5)
    return out


def _snarl(dur, base, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    for i in range(n):
        t = i / f
        rise = base * (1 + 1.4 * (t / dur))
        rough = 0.5 + 0.5 * math.sin(2 * math.pi * 30 * t)
        tone = math.sin(2 * math.pi * rise * t)
        sub = math.sin(2 * math.pi * rise * 0.5 * t) * 0.5
        nz = random.uniform(-1, 1) * 0.4
        env = min(1.0, t * 12) * math.exp(-t * 3.0)
        out.append((tone * 0.5 + sub + nz) * rough * env * vol)
    return out


def _pickup():
    f = _freq()
    n = int(f * 0.2)
    out = []
    for i in range(n):
        t = i / f
        freq = 680 if t < 0.06 else 1020
        tone = math.sin(2 * math.pi * freq * t)
        env = math.exp(-t * 11)
        out.append(tone * env * 0.4)
    return out


def _heal():
    f = _freq()
    n = int(f * 0.5)
    out = []
    for i in range(n):
        t = i / f
        tone = math.sin(2 * math.pi * 523 * t) + math.sin(2 * math.pi * 784 * t) * 0.6
        env = min(1.0, t * 14) * math.exp(-t * 3.6)
        out.append(tone * env * 0.28)
    return out


def _reload():
    f = _freq()
    out = [0.0] * int(f * 0.34)
    for start in (0.0, 0.2):
        s0 = int(f * start)
        for i in range(int(f * 0.05)):
            if s0 + i < len(out):
                t = i / f
                out[s0 + i] += random.uniform(-1, 1) * math.exp(-t * 90) * 0.55
    return out


def _verb(samples, decay=0.4, delay=0.032, taps=4, tail=0.1):
    f = _freq()
    d = max(1, int(f * delay))
    out = list(samples)
    out += [0.0] * (d * taps + int(f * tail))
    for tp in range(1, taps + 1):
        g = decay ** tp
        off = d * tp
        for i, s in enumerate(samples):
            out[off + i] += s * g
    return out


def _footstep():
    f = _freq()
    n = int(f * 0.12)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        prev = prev * 0.6 + random.uniform(-1, 1) * 0.4
        body = math.sin(2 * math.pi * 68 * t) * math.exp(-t * 42)
        out.append((prev * math.exp(-t * 58) * 0.55 + body * 0.5) * 0.4)
    return out


def _casing():
    f = _freq()
    n = int(f * 0.2)
    out = []
    for i in range(n):
        t = i / f
        s = (math.sin(2 * math.pi * 2600 * t) * 0.5
             + math.sin(2 * math.pi * 4100 * t) * 0.3
             + math.sin(2 * math.pi * 5300 * t) * 0.2)
        bounce = 1.0 if t < 0.07 else (0.5 if t < 0.12 else 0.28)
        out.append(s * math.exp(-t * 24) * bounce * 0.22)
    return out


def _click():
    f = _freq()
    n = int(f * 0.05)
    out = []
    for i in range(n):
        t = i / f
        out.append(random.uniform(-1, 1) * math.exp(-t * 210) * 0.4)
    return out


def _zombie_die():
    f = _freq()
    n = int(f * 0.5)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        prev = prev * 0.75 + random.uniform(-1, 1) * 0.25
        wet = prev * (0.5 + 0.5 * abs(math.sin(2 * math.pi * 17 * t)))
        groan = math.sin(2 * math.pi * (125 - 75 * (t / 0.5)) * t) * 0.5
        env = min(1.0, t * 8) * math.exp(-t * 4.2)
        out.append((wet * 0.7 + groan) * env * 0.55)
    return out


def _wall_hit():
    f = _freq()
    n = int(f * 0.09)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        prev = prev * 0.5 + random.uniform(-1, 1) * 0.5
        thud = math.sin(2 * math.pi * 150 * t) * math.exp(-t * 62)
        out.append((prev * math.exp(-t * 82) * 0.5 + thud * 0.4) * 0.4)
    return out


def _heartbeat():
    f = _freq()
    n = int(f * 0.55)
    out = [0.0] * n
    for start, amp in ((0.0, 1.0), (0.2, 0.72)):
        s0 = int(f * start)
        for i in range(int(f * 0.15)):
            if s0 + i < n:
                t = i / f
                out[s0 + i] += math.sin(2 * math.pi * 52 * t) * math.exp(-t * 17) * amp * 0.6
    return out


def _dash():
    f = _freq()
    n = int(f * 0.28)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        prev = prev * 0.86 + random.uniform(-1, 1) * 0.14
        env = math.sin(math.pi * (t / 0.28)) ** 1.2
        out.append(prev * env * 0.4)
    return out


def _boom(dur, base, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    for i in range(n):
        t = i / f
        sweep = base * (1 + 1.6 * math.exp(-t * 22))
        sub = math.sin(2 * math.pi * sweep * t) * math.exp(-t * 6.5)
        nz = random.uniform(-1, 1) * math.exp(-t * 9) * 0.45
        out.append((sub + nz) * vol)
    return out


def _rain_loop():
    f = _freq()
    n = int(f * 1.5)
    out = []
    prev = 0.0
    for i in range(n):
        prev = prev * 0.6 + random.uniform(-1, 1) * 0.4
        out.append(prev * 0.18)
    return out


def _wind_loop():
    f = _freq()
    dur = 7.5
    n = int(f * dur)
    out = []
    low = 0.0
    hi = 0.0
    ph = random.uniform(0, math.tau)
    for i in range(n):
        t = i / f
        nz = random.uniform(-1, 1)
        low = low * 0.93 + nz * 0.07
        hi = hi * 0.55 + nz * 0.45
        gust = (0.5
                + 0.24 * math.sin(2 * math.pi * 0.11 * t + ph)
                + 0.15 * math.sin(2 * math.pi * 0.29 * t + 1.3)
                + 0.08 * math.sin(2 * math.pi * 0.061 * t + 2.7))
        gust = max(0.12, gust)
        out.append((low * 0.85 + hi * 0.14) * gust * 0.26)
    xf = int(f * 0.6)
    body = out[:n - xf]
    for i in range(xf):
        a = i / xf
        body[i] = out[i] * a + out[n - xf + i] * (1 - a)
    return body


def _thunder():
    f = _freq()
    n = int(f * 1.7)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / f
        crack = random.uniform(-1, 1) * math.exp(-t * 8) * 0.5
        rumble = math.exp(-t * 1.5)
        low = math.sin(2 * math.pi * (44 + 9 * math.sin(t * 3)) * t) * 0.5
        prev = prev * 0.85 + random.uniform(-1, 1) * 0.15
        out.append((crack + (low + prev * 0.6) * rumble) * 0.6)
    return out


def _boss_roar(dur, base, vol):
    f = _freq()
    n = int(f * dur)
    out = []
    for i in range(n):
        t = i / f
        rough = 0.5 + 0.5 * math.sin(2 * math.pi * 18 * t)
        vib = base * (1 + 0.06 * math.sin(2 * math.pi * 3 * t))
        tone = math.sin(2 * math.pi * vib * t)
        sub = math.sin(2 * math.pi * vib * 0.5 * t) * 0.7
        nz = random.uniform(-1, 1) * 0.35
        env = min(1.0, t * 4) * math.exp(-t * 1.3)
        out.append((tone * 0.5 + sub + nz * 0.4) * rough * env * vol)
    return out


class Audio:
    def __init__(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(24)
            self.ok = True
        except Exception:
            self.ok = False
            return

        self.sfx = {
            'shot_pistol':  _to_sound(_verb(_gun(0.16, 135, 26, 0.9, 0.55, 0.5), decay=0.3, taps=3)),
            'shot_shotgun': _to_sound(_verb(_gun(0.34, 88, 13, 1.0, 0.85, 0.65), decay=0.45, taps=4)),
            'shot_rifle':   _to_sound(_verb(_gun(0.10, 175, 46, 0.85, 0.4, 0.45), decay=0.28, taps=3)),
            'shot_sniper':  _to_sound(_verb(_gun(0.46, 66, 9, 1.0, 1.0, 0.8), decay=0.5, taps=5, delay=0.05)),
            'hit':          _to_sound(_hit()),
            'wall_hit':     _to_sound(_wall_hit()),
            'casing':       _to_sound(_casing()),
            'footstep':     _to_sound(_footstep()),
            'dryfire':      _to_sound(_click()),
            'dash':         _to_sound(_dash()),
            'heartbeat':    _to_sound(_heartbeat()),
            'zombie_die':   _to_sound(_zombie_die()),
            'boss_slam':    _to_sound(_verb(_boom(0.55, 48, 0.95), decay=0.45, taps=5, delay=0.05)),
            'boss_roar':    _to_sound(_boss_roar(1.2, 55, 0.85)),
            'thunder':      _to_sound(_verb(_thunder(), decay=0.4, taps=4, delay=0.08)),
            'pickup':       _to_sound(_pickup()),
            'heal':         _to_sound(_heal()),
            'reload':       _to_sound(_reload()),
            'hurt':         _to_sound(_gun(0.2, 120, 14, 0.5, 0.6, 0.45)),
            'growl1':       _to_sound(_growl(0.75, 80, 0.5)),
            'growl2':       _to_sound(_growl(0.6, 105, 0.45)),
            'gurgle':       _to_sound(_gurgle(0.7, 0.5)),
            'hiss':         _to_sound(_hiss(0.55, 0.45)),
            'snarl':        _to_sound(_snarl(0.4, 95, 0.55)),
        }
        for name, snd in self.sfx.items():
            if name in ('growl1', 'growl2', 'gurgle', 'hiss'):
                snd.set_volume(0.55)

        self.ambient_snds = {'rain': _to_sound(_rain_loop()), 'wind': _to_sound(_wind_loop())}
        self.ambient_kind = None
        self.ambient_ch = None

    def set_ambient(self, kind):
        if not self.ok or kind == self.ambient_kind:
            return
        if self.ambient_ch:
            self.ambient_ch.stop()
            self.ambient_ch = None
        self.ambient_kind = kind
        snd = self.ambient_snds.get(kind)
        if snd:
            self.ambient_ch = snd.play(loops=-1)
            if self.ambient_ch:
                self.ambient_ch.set_volume(0.4 if kind == 'rain' else 0.32)

    def play(self, name, volume=1.0):
        if not self.ok:
            return
        snd = self.sfx.get(name)
        if snd is None:
            return
        ch = snd.play()
        if ch:
            ch.set_volume(volume)

    def play_at(self, name, src, listener, max_dist=1300, base=1.0):
        if not self.ok:
            return
        snd = self.sfx.get(name)
        if snd is None:
            return
        dx = src[0] - listener[0]
        dy = src[1] - listener[1]
        dist = math.hypot(dx, dy)
        if dist > max_dist:
            return
        vol = base * (1 - dist / max_dist) ** 1.5
        if vol <= 0.02:
            return
        pan = max(-1.0, min(1.0, dx / (max_dist * 0.55)))
        ch = snd.play()
        if ch:
            ch.set_volume(vol * (1 - max(0.0, pan)), vol * (1 + min(0.0, pan)))

    def groan_at(self, src, listener):
        if not self.ok:
            return
        self.play_at(random.choice(('growl1', 'growl2', 'gurgle', 'hiss')),
                     src, listener, max_dist=1600, base=0.7)
