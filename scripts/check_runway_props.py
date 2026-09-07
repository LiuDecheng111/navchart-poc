import json

with open(r'D:\AAA CHART\navchart-poc\data\china_airports_real.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 检查跑道(LineString)的属性
print("LineString 要素的属性:")
for feat in data['features']:
    if feat['geometry']['type'] == 'LineString':
        print(json.dumps(feat['properties'], ensure_ascii=False, indent=2))
        break

# 检查导航台的属性
print("\n导航台 (type=VOR/DME) 的属性:")
for feat in data['features']:
    if feat['properties'].get('type') == 'VOR/DME':
        print(json.dumps(feat['properties'], ensure_ascii=False, indent=2))
        break

# 统计所有 type 值
from collections import Counter
all_types = Counter()
for feat in data['features']:
    t = feat['properties'].get('type', '')
    all_types[t] += 1
print("\n所有 type 值统计:")
for k, v in all_types.most_common():
    print(f"  '{k}': {v}")
