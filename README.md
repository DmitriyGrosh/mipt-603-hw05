# mipt-603-hw05

ДЗ5: геометрия по выгрузке OpenStreetMap (Ростов-на-Дону, **аптеки**, Октябрьский район).

Требования: Python 3. Алгоритмы в `algorithms.py` и `geo_osm.py` без scipy/shapely.  
`verify.py` — отдельная проверка через Shapely (`requirements.txt`).

## Данные

- Точки: `data/pharmacy_rostov.json` (Overpass, запрос в `data/overpass_query.txt`)
- Тег: `amenity=pharmacy`
- Прямоугольник bbox города в OSM: `(47.1533773,39.4709911,47.3555733,39.8513903)` — **311** аптек на дату `2026-09-01`
- Район: `data/octyabrsky_district.geojson` ([relation/2228342](https://www.openstreetmap.org/relation/2228342))
- После `project`: `data/points.txt`, `data/district.txt`

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 geo_osm.py project data/pharmacy_rostov.json data/octyabrsky_district.geojson
python3 geo_osm.py hull data/points.txt
python3 geo_osm.py closest data/points.txt
python3 geo_osm.py closest data/points.txt --bruteforce
python3 geo_osm.py inside data/points.txt data/district.txt
python3 geo_osm.py plot data/points.txt data/district.txt data/map.png
```

Проверка Shapely:

```bash
python3 verify.py data/points.txt data/district.txt
```

## Решения (кратко)

- Точка объекта: центр из `out center`; один id OSM — одна строка в файле.
- Проекция: равнопромежуточная, центр — среднее lat/lon набора; округление до **дециметра** (`scale=10`).
- Коллинеарные точки на ребре оболочки **не** входят в оболочку (`cross <= 0` при снятии со стека).
- Все объекты из bbox Overpass **оставляем** (без отсечения по границе relation города).
