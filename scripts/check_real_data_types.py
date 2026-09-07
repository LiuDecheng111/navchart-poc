import json

with open(r'D:\AAA CHART\navchart-poc\data\china_airports_real.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 统计 type 属性值
from collections import Counter
type_counts = Counter()
geom_counts = Counter()
for feat in data['features']:
    t = feat['properties'].get('type', 'NO_TYPE')
    g = feat['geometry']['type']
    type_counts[t] += 1
    geom_counts[g] += 1

print("type 属性值统计:")
for k, v in type_counts.most_common():
    print(f"  {k}: {v}")

print("\ngeometry 类型统计:")
for k, v in geom_counts.most_common():
    print(f"  {k}: {v}")

# 检查第一个机场点的完整属性
print("\n第一个 Point 要素的完整属性:")
for feat in data['features']:
    if feat['geometry']['type'] == 'Point':
        print(json.dumps(feat['properties'], ensure_ascii=False, indent=2))
        break
