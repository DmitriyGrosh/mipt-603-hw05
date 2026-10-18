"""
Независимая проверка через Shapely (не входит в geo_osm.py).
"""
import sys

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from algorithms import closest_pair_brute, convex_hull, doubled_area
from osm_data import COORD_SCALE, load_district_file, load_points_file


def rings_to_shapely(rings):
    if not rings:
        return Polygon()
    polys = []
    for ring in rings:
        if len(ring) < 3:
            continue
        polys.append(Polygon(ring))
    if len(polys) == 1:
        return polys[0]
    return unary_union(polys)


def main():
    if len(sys.argv) < 3:
        print("Использование: python3 verify.py <points.txt> <district.txt>")
        sys.exit(1)

    scale = COORD_SCALE
    ids, points = load_points_file(sys.argv[1])
    rings = load_district_file(sys.argv[2])

    hull_idx = convex_hull(points)
    ring = [points[i] for i in hull_idx]
    my_da = doubled_area(ring) if len(ring) >= 3 else 0

    if len(ring) >= 3:
        shapely_hull = Polygon(ring)
        if not shapely_hull.is_valid:
            shapely_hull = shapely_hull.buffer(0)
        ref_area = int(round(shapely_hull.area * 2))
        ref_verts = len(list(shapely_hull.exterior.coords)) - 1
    else:
        ref_area = 0
        ref_verts = len(ring)

    district = rings_to_shapely(rings)
    inside_ref = sum(1 for p in points if district.contains(Point(p)))

    bi, bj, _, _ = closest_pair_brute(points, scale)

    print("Вершин оболочки (мы / shapely):", len(hull_idx), ref_verts)
    print("Удвоенная площадь оболочки (мы / shapely):", my_da, ref_area)
    print("Точек внутри района (мы / shapely):", end=" ")

    from algorithms import point_in_rings

    inside_my = sum(1 for p in points if point_in_rings(p[0], p[1], rings))
    print(inside_my, inside_ref)
    print("Ближайшая пара (перебор):", bi, bj, ids[bi], ids[bj])


if __name__ == "__main__":
    main()
