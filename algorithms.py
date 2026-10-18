import math


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def dist_sq(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def doubled_area(ring):
    n = len(ring)
    if n < 3:
        return 0
    s = 0
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s


def perimeter_m(ring, scale):
    n = len(ring)
    if n < 2:
        return 0.0
    if n == 2:
        return math.hypot(ring[0][0] - ring[1][0], ring[0][1] - ring[1][1]) / scale
    total = 0.0
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        total += math.hypot(x1 - x2, y1 - y2)
    return total / scale


def convex_hull(points, collinear_on_boundary=False):
    """
    points: список (x, y).
    Возвращает индексы вершин оболочки против часовой стрелки.
    """
    n = len(points)
    if n == 0:
        return []

    order = list(range(n))
    order.sort(key=lambda i: (points[i][0], points[i][1]))

    unique_order = []
    for i in order:
        if not unique_order or points[i] != points[unique_order[-1]]:
            unique_order.append(i)

    if len(unique_order) == 1:
        return [unique_order[0]]

    if len(unique_order) == 2:
        return unique_order

    def should_pop(a, b, c):
        o = cross(a, b, c)
        if collinear_on_boundary:
            return o < 0
        return o <= 0

    lower = []
    for i in unique_order:
        p = points[i]
        while len(lower) >= 2 and should_pop(points[lower[-2]], points[lower[-1]], p):
            lower.pop()
        lower.append(i)

    upper = []
    for i in reversed(unique_order):
        p = points[i]
        while len(upper) >= 2 and should_pop(points[upper[-2]], points[upper[-1]], p):
            upper.pop()
        upper.append(i)

    hull = lower[:-1] + upper[:-1]
    if doubled_area([points[i] for i in hull]) == 0:
        if collinear_on_boundary:
            return list(lower)
        return [unique_order[0], unique_order[-1]]
    return hull


def distinct_points_count(points):
    return len(set(points))


def point_in_rings(x, y, rings):
    p = (x, y)
    crossings = 0
    for ring in rings:
        n = len(ring)
        if n < 3:
            continue
        for i in range(n):
            a = ring[i]
            b = ring[(i + 1) % n]
            if a[1] <= y < b[1]:
                if cross(a, b, p) > 0:
                    crossings += 1
            elif b[1] <= y < a[1]:
                if cross(b, a, p) > 0:
                    crossings += 1
    return crossings % 2 == 1


def closest_pair_brute(points, scale):
    n = len(points)
    if n < 2:
        return 0, 0, 0.0, 0
    comps = 0
    best_i, best_j = 0, 1
    best_sq = dist_sq(points[0], points[1])
    for i in range(n):
        for j in range(i + 1, n):
            comps += 1
            d = dist_sq(points[i], points[j])
            if d < best_sq:
                best_sq = d
                best_i, best_j = i, j
    dist_m = math.hypot(points[best_i][0] - points[best_j][0], points[best_i][1] - points[best_j][1]) / scale
    return best_i, best_j, dist_m, comps


def _solve_closest_rec(points, px_part, py_part):
    m = len(px_part)
    if m <= 3:
        best_i = px_part[0]
        best_j = px_part[1] if m > 1 else px_part[0]
        best_sq = dist_sq(points[best_i], points[best_j])
        comps = 0
        for a in range(m):
            for b in range(a + 1, m):
                comps += 1
                i, j = px_part[a], px_part[b]
                d = dist_sq(points[i], points[j])
                if d < best_sq:
                    best_sq = d
                    best_i, best_j = i, j
        return best_i, best_j, best_sq, comps

    mid = m // 2
    mid_x = points[px_part[mid]][0]
    left_px = px_part[:mid]
    right_px = px_part[mid:]
    left_set = set(left_px)
    left_py = [i for i in py_part if i in left_set]
    right_py = [i for i in py_part if i not in left_set]

    li, lj, lsq, lcomps = _solve_closest_rec(points, left_px, left_py)
    ri, rj, rsq, rcomps = _solve_closest_rec(points, right_px, right_py)
    comps = lcomps + rcomps

    if lsq <= rsq:
        bi, bj, bsq = li, lj, lsq
    else:
        bi, bj, bsq = ri, rj, rsq

    strip = []
    for i in py_part:
        dx = points[i][0] - mid_x
        if dx * dx <= bsq:
            strip.append(i)

    for a in range(len(strip)):
        for b in range(a + 1, min(a + 8, len(strip))):
            comps += 1
            i, j = strip[a], strip[b]
            d = dist_sq(points[i], points[j])
            if d < bsq:
                bsq = d
                bi, bj = i, j
    return bi, bj, bsq, comps


def closest_pair_divide(points, scale):
    n = len(points)
    if n < 2:
        return 0, 0, 0.0, 0

    px = list(range(n))
    px.sort(key=lambda i: (points[i][0], points[i][1]))
    py = list(range(n))
    py.sort(key=lambda i: (points[i][1], points[i][0]))

    i, j, _, comps = _solve_closest_rec(points, px, py)
    dist_m = math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1]) / scale
    return i, j, dist_m, comps
