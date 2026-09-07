import json
import os

os.chdir(r'D:\AAA CHART\navchart-poc\data')

# 读取 OSM 原始数据
with open('zbaa_osm_raw.json', 'r', encoding='utf-8') as f:
    osm_data = json.load(f)

elements = osm_data.get('elements', [])
print(f"总元素数: {len(elements)}")

# 构建 node 坐标映射
node_coords = {}
for e in elements:
    if e['type'] == 'node':
        node_coords[e['id']] = [e['lon'], e['lat']]

print(f"Node 坐标数: {len(node_coords)}")

# 转换为 GeoJSON Feature
features = []

for e in elements:
    if e['type'] == 'node':
        # Point
        tags = e.get('tags', {})
        if not tags:
            continue
        feature = {
            'type': 'Feature',
            'properties': {**tags, 'osm_id': e['id'], 'osm_type': 'node'},
            'geometry': {
                'type': 'Point',
                'coordinates': [e['lon'], e['lat']]
            }
        }
        features.append(feature)
    
    elif e['type'] == 'way':
        # LineString 或 Polygon
        nodes = e.get('nodes', [])
        if len(nodes) < 2:
            continue
        
        coords = []
        valid = True
        for nid in nodes:
            if nid in node_coords:
                coords.append(node_coords[nid])
            else:
                valid = False
                break
        
        if not valid or len(coords) < 2:
            continue
        
        tags = e.get('tags', {})
        
        # 判断是否闭合（Polygon）
        is_closed = coords[0] == coords[-1] and len(coords) >= 4
        
        if is_closed:
            geometry = {
                'type': 'Polygon',
                'coordinates': [coords]
            }
        else:
            geometry = {
                'type': 'LineString',
                'coordinates': coords
            }
        
        feature = {
            'type': 'Feature',
            'properties': {**tags, 'osm_id': e['id'], 'osm_type': 'way', 'geom_type': 'polygon' if is_closed else 'linestring'},
            'geometry': geometry
        }
        features.append(feature)
    
    elif e['type'] == 'relation':
        # Relation 暂不处理（太复杂，通常机场边界用）
        pass

print(f"转换后 Feature 数: {len(features)}")

# 按 aeroway 类型统计
from collections import Counter
aeroway_counts = Counter(f['properties'].get('aeroway', 'none') for f in features)
print(f"\naeroway 分类统计:")
for k, v in sorted(aeroway_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

# 按几何类型统计
geom_counts = Counter(f['geometry']['type'] for f in features)
print(f"\n几何类型统计: {dict(geom_counts)}")

# 保存 GeoJSON
geojson = {
    'type': 'FeatureCollection',
    'properties': {
        'source': 'OpenStreetMap (Overpass API)',
        'airport': 'ZBAA Beijing Capital',
        'query_radius': '6000m',
        'feature_count': len(features)
    },
    'features': features
}

with open('zbaa_airport_ground.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False)

size = os.path.getsize('zbaa_airport_ground.geojson')
print(f"\n已保存: zbaa_airport_ground.geojson ({size} 字节)")
