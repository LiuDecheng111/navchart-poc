import json
import os

os.chdir(r"D:\AAA CHART\navchart-poc\data")

# 读取三个部分
with open('china_airports_part1.txt', 'r', encoding='utf-8') as f:
    part1 = f.read()
with open('china_airports_part2.txt', 'r', encoding='utf-8') as f:
    part2 = f.read()
with open('china_airports_part3.txt', 'r', encoding='utf-8') as f:
    part3 = f.read()

# 拼接
full = part1 + part2 + part3
print(f'拼接后总长度: {len(full)} 字符')
print(f'开头: {full[:100]}')
print(f'结尾: {full[-100:]}')

# 验证 JSON
try:
    data = json.loads(full)
    print(f'\nJSON 验证成功!')
    print(f'  type: {data["type"]}')
    print(f'  source: {data["properties"]["source"]}')
    print(f'  effective: {data["properties"]["effective"]}')
    print(f'  airport_count: {data["properties"]["airport_count"]}')
    print(f'  feature_count: {data["properties"]["feature_count"]}')
    print(f'  实际 features: {len(data["features"])}')
    
    # 统计各类 feature
    categories = {}
    airports = []
    for feat in data['features']:
        cat = feat['properties']['category']
        categories[cat] = categories.get(cat, 0) + 1
        if cat == 'airport':
            airports.append(feat['properties']['icao'] + ' ' + feat['properties']['name_cn'])
    
    print(f'\n  Feature 分类统计:')
    for cat, count in sorted(categories.items()):
        print(f'    {cat}: {count}')
    
    print(f'\n  机场列表 ({len(airports)}个):')
    for a in sorted(airports):
        print(f'    {a}')
    
    # 保存最终 GeoJSON
    with open('china_airports_real.geojson', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: china_airports_real.geojson')
    
    size = os.path.getsize('china_airports_real.geojson')
    print(f'文件大小: {size} 字节')
    
except json.JSONDecodeError as e:
    print(f'\nJSON 解析失败: {e}')
    pos = e.pos
    print(f'错误位置: {pos}')
    print(f'上下文: ...{full[max(0,pos-50):pos+50]}...')
