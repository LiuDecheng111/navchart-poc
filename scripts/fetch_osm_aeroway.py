import urllib.request
import urllib.parse
import json

# Overpass API 查询：ZBAA 周边 6km 的 aeroway 数据
query = """
[out:json][timeout:30];
(
  way["aeroway"](around:6000,40.073,116.598);
  node["aeroway"](around:6000,40.073,116.598);
  relation["aeroway"](around:6000,40.073,116.598);
);
out body;
>;
out skel qt;
"""

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data)
req.add_header('User-Agent', 'NavChart-POC/1.0')

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    elements = result.get('elements', [])
    print(f"元素总数: {len(elements)}")
    
    # 类型统计
    from collections import Counter
    type_counts = Counter(e['type'] for e in elements)
    print(f"类型统计: {dict(type_counts)}")
    
    # aeroway 分类统计
    aeroway_counts = Counter(e.get('tags', {}).get('aeroway', 'none') for e in elements if e.get('tags'))
    print(f"aeroway 分类:")
    for k, v in sorted(aeroway_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    
    # 保存原始数据
    with open(r'D:\AAA CHART\navchart-poc\data\zbaa_osm_raw.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n原始数据已保存: zbaa_osm_raw.json")
    
except Exception as e:
    print(f"错误: {e}")
