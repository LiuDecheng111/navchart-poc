#!/usr/bin/env python3
"""将 OurAirports 全球机场 CSV 转换为分级 GeoJSON
按机场类型分级，不同缩放级别显示不同类型机场
"""
import csv
import json

input_file = r'D:\AAA CHART\navchart-poc\data\ourairports_airports.csv'
output_file = r'D:\AAA CHART\navchart-poc\data\global_airports.geojson'

# 机场类型分级配置
# minzoom: 该类型机场在哪个缩放级别开始显示
# size: 圆点大小
# color: 颜色
TYPE_CONFIG = {
    'large_airport': {
        'minzoom': 2,
        'size': 6,
        'color': '#4fc3f7',
        'label': '大型机场'
    },
    'medium_airport': {
        'minzoom': 4,
        'size': 5,
        'color': '#81c784',
        'label': '中型机场'
    },
    'small_airport': {
        'minzoom': 6,
        'size': 4,
        'color': '#ffb74d',
        'label': '小型机场'
    },
    'seaplane_base': {
        'minzoom': 7,
        'size': 4,
        'color': '#4dd0e1',
        'label': '水上机场'
    },
    'heliport': {
        'minzoom': 9,
        'size': 3,
        'color': '#ba68c8',
        'label': '直升机场'
    },
    'balloonport': {
        'minzoom': 10,
        'size': 3,
        'color': '#e57373',
        'label': '气球港'
    }
}

# 大洲名称映射
CONTINENT_NAMES = {
    'AF': '非洲',
    'AN': '南极洲',
    'AS': '亚洲',
    'EU': '欧洲',
    'NA': '北美洲',
    'OC': '大洋洲',
    'SA': '南美洲'
}

features = []
type_counts = {}
country_counts = {}

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # 跳过已关闭的机场
        if row['type'] == 'closed':
            continue
        
        # 跳过无效坐标
        try:
            lat = float(row['latitude_deg'])
            lon = float(row['longitude_deg'])
        except (ValueError, TypeError):
            continue
        
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            continue
        
        airport_type = row['type']
        config = TYPE_CONFIG.get(airport_type)
        if not config:
            continue
        
        # 统计
        type_counts[airport_type] = type_counts.get(airport_type, 0) + 1
        country = row.get('iso_country', '')
        country_counts[country] = country_counts.get(country, 0) + 1
        
        # ICAO 代码优先用 icao_code，其次用 ident
        icao = row.get('icao_code', '') or row.get('ident', '')
        iata = row.get('iata_code', '')
        
        # 只保留必要字段，减小文件体积
        props = {
            'icao': icao,
            'iata': iata,
            'name': row['name'],
            'type': airport_type,
            'type_label': config['label'],
            'minzoom': config['minzoom'],
            'color': config['color'],
            'size': config['size'],
            'continent': row.get('continent', ''),
            'continent_name': CONTINENT_NAMES.get(row.get('continent', ''), ''),
            'country': country,
            'region': row.get('iso_region', ''),
            'municipality': row.get('municipality', ''),
            'scheduled': row.get('scheduled_service', '') == 'yes',
            'elevation_ft': row.get('elevation_ft', '')
        }
        
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            },
            'properties': props
        })

output = {
    'type': 'FeatureCollection',
    'features': features
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f'生成全球机场 GeoJSON: {len(features)} 个机场')
print(f'输出文件: {output_file}')
print()

print('按类型统计:')
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    config = TYPE_CONFIG.get(t, {})
    print(f'  {config.get("label", t)} ({t}): {c} (zoom>={config.get("minzoom", "?")})')

print()
print(f'覆盖国家/地区数: {len(country_counts)}')
print(f'文件大小: {len(json.dumps(output, ensure_ascii=False).encode("utf-8")) / 1024 / 1024:.1f} MB')
