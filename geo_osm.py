import os
import sys

from algorithms import (
    closest_pair_brute,
    closest_pair_divide,
    convex_hull,
    distinct_points_count,
    doubled_area,
    perimeter_m,
    point_in_rings,
)
from osm_data import COORD_SCALE, load_district_file, load_points_file, project_osm


def area_km2_from_doubled(da, scale):
    area_m2 = abs(da) / 2.0 / (scale * scale)
    return area_m2 / 1_000_000.0


def cmd_project(argv):
    if len(argv) < 3:
        print("Использование: python3 geo_osm.py project <overpass.json> <район.geojson>")
        sys.exit(1)
    overpass = argv[1]
    district = argv[2]
    points_out = "data/points.txt"
    district_out = "data/district.txt"
    if len(argv) >= 5:
        points_out = argv[3]
        district_out = argv[4]

    stats = project_osm(overpass, district, points_out, district_out)
    print("Объектов в выгрузке:", stats["total"])
    print("Записано точек:", stats["written"])
    print("Пропущено (нет координат):", stats["skipped_no_coords"])
    print("Пропущено (повтор id):", stats["skipped_dup"])
    print("Центр проекции: lat=%.6f lon=%.6f" % (stats["lat0"], stats["lon0"]))
    print("Единица округления: %.1f м (scale=%d)" % (1.0 / stats["scale"], stats["scale"]))
    print("Макс. |координата|:", stats["max_abs"])
    print("Файлы:", points_out, district_out)


def cmd_hull(argv):
    if len(argv) < 2:
        print("Использование: python3 geo_osm.py hull <points.txt>")
        sys.exit(1)
    scale = COORD_SCALE
    collinear = "--collinear" in argv
    path = argv[1]
    for arg in argv[2:]:
        if arg.startswith("--scale="):
            scale = int(arg.split("=", 1)[1])

    ids, points = load_points_file(path)
    hull_idx = convex_hull(points, collinear_on_boundary=collinear)
    ring = [points[i] for i in hull_idx]
    da = doubled_area(ring) if len(ring) >= 3 else 0

    print("Точек:", len(points))
    print("Различных точек:", distinct_points_count(points))
    print("Вершин оболочки:", len(hull_idx))
    if len(hull_idx) < 3 or da == 0:
        print("Примечание: вырожденная оболочка, площадь 0")
    for num, idx in enumerate(hull_idx, 1):
        x, y = points[idx]
        print("  %d: объект #%d (%s) %d %d" % (num, idx, ids[idx], x, y))
    print("Удвоенная площадь:", da)
    print("Площадь км^2:", round(area_km2_from_doubled(da, scale), 6))
    if len(ring) >= 2:
        print("Периметр км:", round(perimeter_m(ring, scale) / 1000.0, 6))
    else:
        print("Периметр км: 0")


def cmd_closest(argv):
    if len(argv) < 2:
        print("Использование: python3 geo_osm.py closest <points.txt> [--bruteforce]")
        sys.exit(1)
    path = argv[1]
    brute = "--bruteforce" in argv
    scale = COORD_SCALE
    for arg in argv[2:]:
        if arg.startswith("--scale="):
            scale = int(arg.split("=", 1)[1])

    ids, points = load_points_file(path)
    if brute:
        i, j, dist_m, comps = closest_pair_brute(points, scale)
        mode = "перебор"
    else:
        i, j, dist_m, comps = closest_pair_divide(points, scale)
        mode = "разделяй и властвуй"

    print("Режим:", mode)
    print("Расстояние м:", round(dist_m, 3))
    print("Индексы объектов:", i, j)
    print("Id:", ids[i], ids[j])
    print("Вычислений расстояния:", comps)


def cmd_inside(argv):
    if len(argv) < 3:
        print("Использование: python3 geo_osm.py inside <points.txt> <district.txt>")
        sys.exit(1)
    scale = COORD_SCALE
    points_path = argv[1]
    district_path = argv[2]

    ids, points = load_points_file(points_path)
    rings = load_district_file(district_path)
    total_da = 0
    for num, ring in enumerate(rings, 1):
        da = doubled_area(ring)
        total_da += da
        print("Кольцо %d, удвоенная ориентированная площадь:" % num, da)
    print("Площадь района км^2:", round(area_km2_from_doubled(total_da, scale), 6))

    inside = 0
    outside = 0
    for x, y in points:
        if point_in_rings(x, y, rings):
            inside += 1
        else:
            outside += 1
    print("Внутри:", inside)
    print("Снаружи:", outside)


def cmd_plot(argv):
    if len(argv) < 3:
        print("Использование: python3 geo_osm.py plot <points.txt> <district.txt> [картинка.png]")
        sys.exit(1)
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Нужен matplotlib: pip install -r requirements.txt")
        sys.exit(1)

    points_path = argv[1]
    district_path = argv[2]
    out_path = "data/map.png"
    if len(argv) >= 4:
        out_path = argv[3]

    scale = COORD_SCALE
    collinear = "--collinear" in argv
    ids, points = load_points_file(points_path)
    rings = load_district_file(district_path)
    hull_idx = convex_hull(points, collinear_on_boundary=collinear)
    ci, cj, _, _ = closest_pair_divide(points, scale)

    fig, ax = plt.subplots(figsize=(11, 9))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.scatter(xs, ys, s=6, c="#2563eb", alpha=0.55, zorder=2)

    if len(hull_idx) >= 2:
        hx = [points[i][0] for i in hull_idx] + [points[hull_idx[0]][0]]
        hy = [points[i][1] for i in hull_idx] + [points[hull_idx[0]][1]]
        ax.plot(hx, hy, c="#dc2626", linewidth=1.4, zorder=3)

    for ring in rings:
        if not ring:
            continue
        rx = [p[0] for p in ring] + [ring[0][0]]
        ry = [p[1] for p in ring] + [ring[0][1]]
        ax.plot(rx, ry, c="#16a34a", linewidth=1.1, zorder=4)

    p1, p2 = points[ci], points[cj]
    ax.plot(
        [p1[0], p2[0]],
        [p1[1], p2[1]],
        c="#f59e0b",
        linewidth=2,
        marker="o",
        zorder=5,
    )
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title("Точки, оболочка, район, ближайшая пара")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print("Картинка:", out_path)


def main():
    if len(sys.argv) < 2:
        print(
            "Команды: project, hull, closest, inside, plot\n"
            "Пример: python3 geo_osm.py hull data/points.txt"
        )
        sys.exit(1)

    cmd = sys.argv[1]
    argv = sys.argv[1:]

    if cmd == "project":
        cmd_project(argv)
    elif cmd == "hull":
        cmd_hull(argv)
    elif cmd == "closest":
        cmd_closest(argv)
    elif cmd == "inside":
        cmd_inside(argv)
    elif cmd == "plot":
        cmd_plot(argv)
    else:
        print("Неизвестная команда:", cmd)
        sys.exit(1)


if __name__ == "__main__":
    main()
