#!/usr/bin/env python3
"""从 Natural Earth 国家数据中提取标注点坐标，创建 Point GeoJSON"""
import json

input_file = r'D:\AAA CHART\navchart-poc\data\ne_110m_countries.geojson'
output_file = r'D:\AAA CHART\navchart-poc\data\country_labels.geojson'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

features = []
for feat in data['features']:
    props = feat['properties']
    name = props.get('NAME', '')
    label_x = props.get('LABEL_X')
    label_y = props.get('LABEL_Y')
    
    if name and label_x is not None and label_y is not None:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [label_x, label_y]
            },
            'properties': {
                'name': name,
                'name_long': props.get('NAME_LONG', name),
                'continent': props.get('CONTINENT', ''),
                'region_un': props.get('REGION_UN', '')
            }
        })

output = {
    'type': 'FeatureCollection',
    'features': features
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f'生成国家标注点: {len(features)} 个')
print(f'输出文件: {output_file}')
