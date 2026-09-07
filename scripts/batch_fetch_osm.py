import urllib.request
import urllib.parse
import json
import time
import os
import sys

os.chdir(r'D:\AAA CHART\navchart-poc\data')

# 读取机场坐标
with open('airport_coords.json', 'r', encoding='utf-8') as f:
    airports = json.load(f)

# Overpass API 镜像列表（轮换使用，避免单镜像限流）
MIRRORS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.openstreetmap.fr/api/interpreter',
]

def fetch_osm_aeroway(lat, lon, radius=6000, mirror_idx=0, retries=3):
    """从 Overpass API 获取机场周边 aeroway 数据"""
    query = f"""
[out:json][timeout:30];
(
  way["aeroway"](around:{radius},{lat},{lon});
  node["aeroway"](around:{radius},{lat},{lon});
  relation["aeroway"](around:{radius},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    
    for attempt in range(retries):
        url = MIRRORS[mirror_idx % len(MIRRORS)]
        req = urllib.request.Request(url, data=data)
        req.add_header('User-Agent', 'NavChart-POC/1.0 (batch fetch)')
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            return result, mirror_idx
        except Exception as e:
            print(f"    尝试 {attempt+1}/{retries} 失败 (镜像 {mirror_idx % len(MIRRORS)}): {e}")
            mirror_idx += 1
            if attempt < retries - 1:
                time.sleep(3)
    
    return None, mirror_idx

def osm_to_geojson(osm_data, icao, name):
    """将 OSM 数据转换为 GeoJSON"""
    elements = osm_data.get('elements', [])
    
    # 构建 node 坐标映射
    node_coords = {}
    for e in elements:
        if e['type'] == 'node':
            node_coords[e['id']] = [e['lon'], e['lat']]
    
    features = []
    
    for e in elements:
        if e['type'] == 'node':
            tags = e.get('tags', {})
            if not tags:
                continue
            feature = {
                'type': 'Feature',
                'properties': {**tags, 'osm_id': e['id'], 'osm_type': 'node', 'airport': icao, 'airport_name': name},
                'geometry': {'type': 'Point', 'coordinates': [e['lon'], e['lat']]}
            }
            features.append(feature)
        
        elif e['type'] == 'way':
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
            is_closed = coords[0] == coords[-1] and len(coords) >= 4
            
            if is_closed:
                geometry = {'type': 'Polygon', 'coordinates': [coords]}
            else:
                geometry = {'type': 'LineString', 'coordinates': coords}
            
            feature = {
                'type': 'Feature',
                'properties': {**tags, 'osm_id': e['id'], 'osm_type': 'way',
                              'geom_type': 'polygon' if is_closed else 'linestring',
                              'airport': icao, 'airport_name': name},
                'geometry': geometry
            }
            features.append(feature)
    
    return features

# ========== 主流程 ==========
print(f"=== 批量抓取 OSM 机场地面数据 ===")
print(f"共 {len(airports)} 个机场，ZBAA 已有数据将跳过\n")

all_features = []
mirror_idx = 0
success_count = 0
skip_count = 0
fail_count = 0

# 先加载已有的 ZBAA 数据
with open('zbaa_airport_ground.geojson', 'r', encoding='utf-8') as f:
    zbaa_data = json.load(f)
for feat in zbaa_data['features']:
    feat['properties']['airport'] = 'ZBAA'
    feat['properties']['airport_name'] = '北京/首都'
all_features.extend(zbaa_data['features'])
print(f"[跳过] ZBAA 北京/首都 - 已有数据 ({len(zbaa_data['features'])} Feature)")
skip_count += 1

# 逐个抓取其他机场
for i, airport in enumerate(airports):
    icao = airport['icao']
    name = airport['name']
    lat = airport['lat']
    lon = airport['lon']
    
    if icao == 'ZBAA':
        continue
    
    print(f"\n[{i+1}/{len(airports)}] {icao} {name} ({lat:.4f}, {lon:.4f})")
    
    # 抓取 OSM 数据
    osm_data, mirror_idx = fetch_osm_aeroway(lat, lon, mirror_idx=mirror_idx)
    
    if osm_data is None:
        print(f"  ❌ 抓取失败，已跳过")
        fail_count += 1
        continue
    
    elem_count = len(osm_data.get('elements', []))
    print(f"  ✅ 获取 {elem_count} 个 OSM 元素 (镜像 {mirror_idx % len(MIRRORS)})")
    
    # 转换为 GeoJSON
    features = osm_to_geojson(osm_data, icao, name)
    print(f"  📐 转换为 {len(features)} 个 GeoJSON Feature")
    
    # 统计 aeroway 类型
    from collections import Counter
    aeroway_counts = Counter(f['properties'].get('aeroway', 'none') for f in features)
    summary = ', '.join(f"{k}:{v}" for k, v in sorted(aeroway_counts.items(), key=lambda x: -x[1])[:5])
    print(f"  📊 {summary}")
    
    all_features.extend(features)
    success_count += 1
    
    # 速率控制：大机场后多等一会，小机场少等
    if elem_count > 5000:
        wait = 8
    elif elem_count > 2000:
        wait = 5
    else:
        wait = 3
    print(f"  ⏳ 等待 {wait} 秒...")
    time.sleep(wait)

# 保存合并后的 GeoJSON
geojson = {
    'type': 'FeatureCollection',
    'properties': {
        'source': 'OpenStreetMap (Overpass API)',
        'description': '中国30个主要机场地面矢量数据',
        'airport_count': success_count + skip_count,
        'feature_count': len(all_features)
    },
    'features': all_features
}

output_file = 'china_airports_ground.geojson'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False)

size = os.path.getsize(output_file)
print(f"\n{'='*50}")
print(f"✅ 批量抓取完成！")
print(f"  成功: {success_count} 个机场")
print(f"  跳过: {skip_count} 个机场 (已有数据)")
print(f"  失败: {fail_count} 个机场")
print(f"  总 Feature 数: {len(all_features)}")
print(f"  文件大小: {size/1024:.1f} KB")
print(f"  输出文件: {output_file}")

# 按机场统计
print(f"\n各机场 Feature 数:")
airport_counts = Counter(f['properties'].get('airport', 'unknown') for f in all_features)
for icao, count in sorted(airport_counts.items()):
    print(f"  {icao}: {count}")
