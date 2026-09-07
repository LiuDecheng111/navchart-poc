import json

with open(r'D:\AAA CHART\navchart-poc\data\zbaa_airport_ground.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data['features']
print(f'总 Feature 数: {len(features)}')

# 坐标范围
all_lons = []
all_lats = []
for feat in features:
    geom = feat['geometry']
    if geom['type'] == 'Point':
        all_lons.append(geom['coordinates'][0])
        all_lats.append(geom['coordinates'][1])
    elif geom['type'] == 'LineString':
        for c in geom['coordinates']:
            all_lons.append(c[0])
            all_lats.append(c[1])
    elif geom['type'] == 'Polygon':
        for ring in geom['coordinates']:
            for c in ring:
                all_lons.append(c[0])
                all_lats.append(c[1])

print(f'经度范围: {min(all_lons):.5f} - {max(all_lons):.5f}')
print(f'纬度范围: {min(all_lats):.5f} - {max(all_lats):.5f}')

# 按 aeroway + 几何类型统计
from collections import Counter
combos = Counter()
for feat in features:
    aeroway = feat['properties'].get('aeroway', 'none')
    geom_type = feat['geometry']['type']
    combos[(aeroway, geom_type)] += 1

print(f'\naeroway + 几何类型统计:')
for (a, g), c in sorted(combos.items(), key=lambda x: -x[1]):
    print(f'  {a:20s} {g:12s}: {c}')

# 检查跑道数据
runways = [f for f in features if f['properties'].get('aeroway') == 'runway']
print(f'\n跑道详情:')
for r in runways:
    props = r['properties']
    geom = r['geometry']
    ref = props.get('ref', '?')
    gtype = geom['type']
    if gtype == 'LineString':
        ncoords = len(geom['coordinates'])
        start = geom['coordinates'][0]
        end = geom['coordinates'][-1]
        print(f'  ref={ref} type={gtype} coords={ncoords}')
        print(f'    起点: {start}')
        print(f'    终点: {end}')
    else:
        print(f'  ref={ref} type={gtype} (Polygon)')
