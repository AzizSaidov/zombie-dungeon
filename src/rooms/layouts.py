import random

FLOOR = 0
WALL = 1


def _blank(cols, rows):
    g = [[FLOOR] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                g[r][c] = WALL
    return g


def forest_layout(cols, rows, rng):
    g = _blank(cols, rows)
    for _ in range(rng.randint(6, 11)):
        cx = rng.randint(4, cols - 5)
        cy = rng.randint(4, rows - 5)
        for _ in range(rng.randint(3, 7)):
            ox = rng.randint(-2, 2)
            oy = rng.randint(-2, 2)
            r, c = cy + oy, cx + ox
            if 1 < c < cols - 1 and 1 < r < rows - 1:
                g[r][c] = WALL
    return g


def town_layout(cols, rows, rng):
    g = _blank(cols, rows)
    cell = 13
    street = 5
    by = 2
    while by < rows - 7:
        bx = 2
        while bx < cols - 7:
            if rng.random() < 0.82:
                max_w = min(cell - street, cols - 2 - bx)
                max_h = min(cell - street, rows - 2 - by)
                if max_w >= 5 and max_h >= 5:
                    bw = rng.randint(5, max_w)
                    bh = rng.randint(5, max_h)
                    ox = rng.randint(0, max(0, (cell - street) - bw))
                    oy = rng.randint(0, max(0, (cell - street) - bh))
                    for r in range(by + oy, by + oy + bh):
                        for c in range(bx + ox, bx + ox + bw):
                            g[r][c] = WALL
            bx += cell
        by += cell
    return g


def _seal_unreachable(g):
    rows = len(g)
    cols = len(g[0])
    cc, cr = cols // 2, rows // 2
    start = None
    for radius in range(max(cols, rows)):
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                r, c = cr + dr, cc + dc
                if 0 < r < rows - 1 and 0 < c < cols - 1 and g[r][c] == FLOOR:
                    start = (r, c)
                    break
            if start:
                break
        if start:
            break
    if not start:
        return g
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] == FLOOR and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == FLOOR and (r, c) not in seen:
                g[r][c] = WALL
    return g


def storm_layout(cols, rows, rng):
    g = _blank(cols, rows)
    shells = []
    for _ in range(rng.randint(4, 7)):
        bw = rng.randint(6, 12)
        bh = rng.randint(6, 12)
        bx = rng.randint(2, max(2, cols - 3 - bw))
        by = rng.randint(2, max(2, rows - 3 - bh))
        shells.append((bx, by, bw, bh))
        for r in range(by, by + bh):
            for c in range(bx, bx + bw):
                if r in (by, by + bh - 1) or c in (bx, bx + bw - 1):
                    g[r][c] = WALL
    for _ in range(rng.randint(10, 16)):
        cr = rng.randint(2, rows - 3)
        cc = rng.randint(2, cols - 3)
        for _ in range(rng.randint(1, 2)):
            r = cr + rng.randint(-1, 1)
            c = cc + rng.randint(-1, 1)
            if 1 < r < rows - 1 and 1 < c < cols - 1:
                g[r][c] = WALL
    for (bx, by, bw, bh) in shells:
        for _ in range(rng.randint(2, 4)):
            side = rng.randint(0, 3)
            if side in (0, 1):
                rr = by if side == 0 else by + bh - 1
                c0 = rng.randint(bx, bx + bw - 2)
                g[rr][c0] = FLOOR
                g[rr][c0 + 1] = FLOOR
            else:
                cc = bx if side == 2 else bx + bw - 1
                r0 = rng.randint(by, by + bh - 2)
                g[r0][cc] = FLOOR
                g[r0 + 1][cc] = FLOOR
    return _seal_unreachable(g)


def hospital_layout(cols, rows, rng):
    g = _blank(cols, rows)

    v_step = 10
    h_step = 9
    v_lines = list(range(v_step, cols - 4, v_step))
    h_lines = list(range(h_step, rows - 4, h_step))

    for vc in v_lines:
        for r in range(1, rows - 1):
            g[r][vc] = WALL
    for hr in h_lines:
        for c in range(1, cols - 1):
            g[hr][c] = WALL

    corridor = h_lines[len(h_lines) // 2] if h_lines else rows // 2
    for off in (-1, 0, 1):
        cr = corridor + off
        if 0 < cr < rows - 1:
            for c in range(1, cols - 1):
                g[cr][c] = FLOOR

    xs = [0] + sorted(v_lines) + [cols - 1]
    ys = [0] + sorted(h_lines) + [rows - 1]

    for vc in v_lines:
        for i in range(len(ys) - 1):
            y0, y1 = ys[i] + 1, ys[i + 1] - 1
            if y1 - y0 < 3:
                continue
            dr = rng.randint(y0 + 1, y1 - 1)
            g[dr][vc] = FLOOR
            g[dr - 1][vc] = FLOOR

    for hr in h_lines:
        if abs(hr - corridor) <= 1:
            continue
        for i in range(len(xs) - 1):
            x0, x1 = xs[i] + 1, xs[i + 1] - 1
            if x1 - x0 < 3:
                continue
            dc = rng.randint(x0 + 1, x1 - 1)
            g[hr][dc] = FLOOR
            g[hr][dc - 1] = FLOOR

    return g


LAYOUTS = {
    'forest': forest_layout,
    'town': town_layout,
    'hospital': hospital_layout,
    'storm': storm_layout,
    'snow': forest_layout,
}
