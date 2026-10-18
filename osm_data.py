import json
import math

EARTH_RADIUS_M = 6371000
# Целые координаты: дециметры (0.1 м).
COORD_SCALE = 10


def equirectangular(lat, lon, lat0, lon0):
    phi = math.radians(lat)
    lam = math.radians(lon)
    phi0 = math.radians(lat0)
    lam0 = math.radians(lon0)
    x = EARTH_RADIUS_M * (lam - lam0) * math.cos(phi0)
    y = EARTH_RADIUS_M * (phi - phi0)
    return x, y


def to_int_coords(x_m, y_m, scale):
    return round(x_m * scale), round(y_m * scale)


def osm_element_id(elem):
    return elem.get("type", "node") + "/" + str(elem["id"])


def element_lat_lon(elem):
    if "lat" in elem and "lon" in elem:
        return float(elem["lat"]), float(elem["lon"])
    center = elem.get("center")
    if center and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None


def load_points_file(path):
    points = []
    ids = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError("неверная строка точек: " + line)
            ids.append(parts[0])
            points.append((int(parts[1]), int(parts[2])))
    return ids, points


def save_points_file(path, ids, points):
    with open(path, "w", encoding="utf-8") as f:
        for oid, (x, y) in zip(ids, points):
            f.write(oid + " " + str(x) + " " + str(y) + "\n")


def load_district_file(path):
    rings = []
    current = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                if current:
                    rings.append(current)
                    current = []
                continue
            parts = stripped.split()
            current.append((int(parts[0]), int(parts[1])))
        if current:
            rings.append(current)
    return rings


def save_district_file(path, rings):
    with open(path, "w", encoding="utf-8") as f:
        for i, ring in enumerate(rings):
            if i > 0:
                f.write("\n")
            for x, y in ring:
                f.write(str(x) + " " + str(y) + "\n")


def normalize_ring_winding(ring, want_ccw):
    from algorithms import doubled_area

    da = doubled_area(ring)
    is_ccw = da > 0
    if is_ccw != want_ccw:
        return list(reversed(ring))
    return ring


def polygons_from_geojson(geojson):
    polygons = []
    features = geojson.get("features")
    if features is None:
        features = [geojson]
    for feature in features:
        geom = feature.get("geometry", feature)
        gtype = geom["type"]
        coords = geom["coordinates"]
        if gtype == "Polygon":
            polygons.append(coords)
        elif gtype == "MultiPolygon":
            for poly in coords:
                polygons.append(poly)
        else:
            raise ValueError("неподдерживаемый тип геометрии: " + gtype)
    return polygons


def project_osm(overpass_path, district_path, points_out, district_out, scale=COORD_SCALE):
    with open(overpass_path, encoding="utf-8") as f:
        data = json.load(f)
    elements = data.get("elements", [])

    latlons = []
    for elem in elements:
        ll = element_lat_lon(elem)
        if ll is not None:
            latlons.append(ll)
    if not latlons:
        raise ValueError("в выгрузке нет координат")

    lat0 = sum(lat for lat, _ in latlons) / len(latlons)
    lon0 = sum(lon for _, lon in latlons) / len(latlons)

    seen = set()
    ids = []
    points = []
    skipped_no_coords = 0
    skipped_dup = 0
    max_abs = 0

    for elem in elements:
        oid = osm_element_id(elem)
        if oid in seen:
            skipped_dup += 1
            continue
        seen.add(oid)
        ll = element_lat_lon(elem)
        if ll is None:
            skipped_no_coords += 1
            continue
        lat, lon = ll
        xm, ym = equirectangular(lat, lon, lat0, lon0)
        x, y = to_int_coords(xm, ym, scale)
        max_abs = max(max_abs, abs(x), abs(y))
        ids.append(oid)
        points.append((x, y))

    save_points_file(points_out, ids, points)

    with open(district_path, encoding="utf-8") as f:
        geo = json.load(f)

    out_rings = []
    for poly in polygons_from_geojson(geo):
        for ring_idx, ring_lonlat in enumerate(poly):
            if len(ring_lonlat) > 1 and ring_lonlat[0] == ring_lonlat[-1]:
                ring_lonlat = ring_lonlat[:-1]
            ring_xy = []
            for lon, lat in ring_lonlat:
                xm, ym = equirectangular(float(lat), float(lon), lat0, lon0)
                ring_xy.append(to_int_coords(xm, ym, scale))
            want_ccw = ring_idx == 0
            out_rings.append(normalize_ring_winding(ring_xy, want_ccw))

    save_district_file(district_out, out_rings)

    return {
        "total": len(elements),
        "written": len(points),
        "skipped_no_coords": skipped_no_coords,
        "skipped_dup": skipped_dup,
        "lat0": lat0,
        "lon0": lon0,
        "scale": scale,
        "max_abs": max_abs,
    }
