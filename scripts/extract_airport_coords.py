import json

# 从中国民航真实数据中提取机场坐标
with open(r'D:\AAA CHART\navchart-poc\data\china_airports_real.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

airports = []
for feat in data['features']:
    if feat['properties'].get('type') == 'airport' or feat['geometry']['type'] == 'Point':
        props = feat['properties']
        icao = props.get('icao', props.get('id', ''))
        name = props.get('name', props.get('name_cn', ''))
        coords = feat['geometry']['coordinates']
        if icao and len(coords) == 2:
            airports.append({
                'icao': icao,
                'name': name,
                'lon': coords[0],
                'lat': coords[1]
            })

print(f"提取到 {len(airports)} 个机场:")
for a in sorted(airports, key=lambda x: x['icao']):
    print(f"  {a['icao']:6s} {a['name']:20s} ({a['lat']:.4f}, {a['lon']:.4f})")

# 保存机场坐标列表
with open(r'D:\AAA CHART\navchart-poc\data\airport_coords.json', 'w', encoding='utf-8') as f:
    json.dump(airports, f, ensure_ascii=False, indent=2)
print(f"\n已保存到 airport_coords.json")
