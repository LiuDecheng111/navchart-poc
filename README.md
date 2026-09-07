## 🎯 最新进展：全国30机场地面数据已完成！(参考 vatsim-radar 风格)

基于 **OpenStreetMap (OSM) aeroway 矢量数据**的全国机场地面细节渲染已验证成功，放大到一定程度后可见完整的滑行道、机位、跑道、停机坪、航站楼、登机桥等地面要素，效果对标 vatsim-radar.com。

- **数据来源**：OpenStreetMap Overpass API（aeroway 标签，全球覆盖、开源免费）
- **数据规模**：全国 **30 个主要机场**，共 **20,095 个 GeoJSON Feature**，文件 8.8MB
  - 最大机场：ZSPD 上海浦东(2149)、ZPPP 昆明长水(2076)、ZGGG 广州白云(1928)、ZUCK 重庆江北(1627)、ZBAA 北京首都(1659)
  - 要素类型：跑道 / 滑行道 / 机位 / 停机坪 / 航站楼 / 登机桥 / 登机口 / 导航设施 / 机库 / 塔台 / 停止道 / 风向袋等
- **渲染引擎**：MapLibre GL JS（19 个图层、分级 LOD、昼夜模式、点击查询、图层独立开关、机场快速跳转）
- **访问地址**：http://localhost:8765/web/index_airport.html
- **整合页面（推荐）**：http://localhost:8765/web/index_unified.html（全球渐进式渲染 + e-AIP真实数据 + OSM地面数据 双数据源整合）

### 整合页面渐进式 LOD 渲染 (index_unified.html)
从全球视角逐步放大，数据分层级出现，类似 Navigraph Charts / vatsim-radar 体验：

**底图**：支持两种底图切换（点击"🛰️ 卫星图"/"🗺️ 简化图"按钮）
- **卫星图**：Esri World_Imagery 卫星影像（不透明度 0.55），显示真实地形/地貌/水系
- **简化图**：Natural Earth 矢量数据（海洋中灰 #2a2a2a、陆地深黑 #141414、国家边界浅灰线、国家名称灰色标注），类似 VATSIM 风格

| 缩放级别 | 显示内容 | 数据源 |
|---------|---------|--------|
| zoom 2-3 | 全球卫星影像底图 | Esri |
| zoom 3-4 | 机场点（青色圆点 + ICAO 标注） | e-AIP |
| zoom 5-7 | 导航台（黄色 VOR/DME、红色 NDB + 名称标注） | e-AIP |
| zoom 8-9 | 跑道概略线（橙色）+ 机场边界 | e-AIP + OSM |
| zoom 10-11 | 精确跑道（白色）+ 停机坪 + 航站楼 + 机库 | OSM |
| zoom 11-12 | 滑行道网络 + 停止道 + 导航设施 | OSM |
| zoom 12-13 | 机位 + 登机口 + 跑道/航站楼标注 | OSM |
| zoom 13-14 | 滑行道中心线 + 登机桥 + 滑行道/登机口标注 | OSM |
| zoom 14+ | 机位编号标注 | OSM |

**双数据源叠加**：e-AIP 跑道概略线（橙色）与 OSM 精确跑道（白色）在 zoom 8-12 叠加显示，可对比真实数据精度差异。

### 机场地面渲染特性
- **机场快速跳转**：顶部下拉菜单选择任意机场，一键 flyTo 跳转（全国30机场全覆盖）
- **跑道**：白色粗线 + 中心线虚线 + 跑道编号标注，zoom≥11 可见
- **滑行道**：灰色线条 + 黄色中心线（虚线）+ 滑行道编号标注，zoom≥12 可见
- **停机坪**：深灰色填充面，zoom≥11 可见
- **机位**：彩色圆点（按机型大小着色）+ 机位编号标注，zoom≥13 可见
- **登机口**：绿色圆点 + 编号标注，zoom≥13 可见
- **登机桥**：紫色线条，zoom≥14 可见
- **航站楼**：棕色填充面 + 名称标注，zoom≥11 可见
- **导航设施**：黄色圆点，zoom≥12 可见
- **机场边界**：深蓝色填充面，zoom≥10 可见
- **分级 LOD**：不同缩放级别显示不同细节，避免低缩放时画面混乱
- **点击查询**：点击任意要素显示详细信息（ref、aeroway 类型、坐标等）
- **图层控制**：10 类图层独立开关 + 标注文字总开关
- **昼夜模式**：一键切换深色/浅色主题

### 全国30机场数据统计
| 机场 | ICAO | Feature数 | 机场 | ICAO | Feature数 |
|------|------|-----------|------|------|-----------|
| 上海浦东 | ZSPD | 2149 | 南京禄口 | ZSNJ | 811 |
| 昆明长水 | ZPPP | 2076 | 乌鲁木齐 | ZWWW | 685 |
| 广州白云 | ZGGG | 1928 | 兰州中川 | ZLLL | 630 |
| 北京首都 | ZBAA | 1659 | 哈尔滨太平 | ZYHB | 601 |
| 重庆江北 | ZUCK | 1627 | 太原武宿 | ZBYN | 424 |
| 深圳宝安 | ZGSZ | 1559 | 拉萨贡嘎 | ZULS | 349 |
| 武汉天河 | ZHHH | 1159 | 鄂州花湖 | ZHEC | 336 |
| 上海虹桥 | ZSSS | 1043 | 大连周水子 | ZYTL | 319 |
| 杭州萧山 | ZSHC | 1001 | 福州长乐 | ZSFZ | 319 |
| 合肥新桥 | ZSOF | 300 | 桂林两江 | ZGKL | 261 |
| 宁波栎社 | ZSNB | 256 | 湛江吴川 | ZGZJ | 107 |
| 南通兴东 | ZSNT | 107 | 银川河东 | ZLIC | 96 |
| 舟山普陀山 | ZSZS | 72 | 鄂尔多斯 | ZBDS | 71 |
| 琼海博鳌 | ZJQH | 69 | 佳木斯 | ZYJM | 38 |
| 二连浩特 | ZBER | 24 | 黄山屯溪 | ZSTX | 19 |

### OSM 数据获取技术方案
1. 从 e-AIP 真实数据提取30个机场的坐标（airport_coords.json）
2. 通过 Overpass API 查询每个机场周边 6km 范围内所有 `aeroway` 标签的要素（way/node/relation）
3. 多镜像轮换（overpass-api.de / kumi.systems / openstreetmap.fr）+ 3次重试 + 速率控制（3-8秒）
4. 坐标转换：OSM 节点坐标直接使用（WGS84 十进制度）
5. 几何判断：闭合 way → Polygon，非闭合 way → LineString，node → Point
6. 批量合并为单个 GeoJSON 文件（china_airports_ground.geojson，8.8MB）
7. 抓取成功率：100%（29个新抓取 + 1个已有，0失败）

---

## 🎯 进展二：中国民航真实数据已接入！

基于 **CAAC e-AIP (中国民航电子航空资料汇编)** 真实数据的矢量航图渲染已验证成功！

- **数据来源**：CAAC e-AIP EAIP2026-09.V1.3（生效 2026-09-02）
- **数据规模**：30 个中国主要机场、126 个导航台、48 条跑道，共 204 个 GeoJSON Feature
- **渲染引擎**：MapLibre GL JS（无级缩放、图层可控、昼夜模式、点击查询）
- **访问地址**：http://localhost:8765/web/index_real.html

### 真实数据覆盖的机场 (30个)
北京首都 ZBAA、鄂尔多斯 ZBDS、二连浩特 ZBER、太原 ZBYN、广州白云 ZGGG、桂林两江 ZGKL、深圳宝安 ZGSZ、湛江吴川 ZGZJ、鄂州花湖 ZHEC、武汉天河 ZHHH、琼海博鳌 ZJQH、银川河东 ZLIC、兰州中川 ZLLL、昆明长水 ZPPP、福州长乐 ZSFZ、杭州萧山 ZSHC、宁波栎社 ZSNB、南京禄口 ZSNJ、南通兴东 ZSNT、合肥新桥 ZSOF、上海浦东 ZSPD、上海虹桥 ZSSS、黄山屯溪 ZSTX、舟山普陀山 ZSZS、重庆江北 ZUCK、拉萨贡嘎 ZULS、乌鲁木齐天山 ZWWW、哈尔滨太平 ZYHB、佳木斯松江 ZYJM、大连周水子 ZYTL

### 真实数据渲染特性
- **机场点**：青绿色圆点，显示 ICAO 代码和中文名，全球可见
- **导航台点**：按类型颜色区分 — VOR/DME 黄色、NDB 红色、ILS 紫色，缩放 ≥4 可见
- **跑道线**：橙色线条，显示跑道号和长度，缩放 ≥5 可见
- **图层控制**：机场/导航台/跑道/标注文字 独立开关
- **点击查询**：点击任意要素显示详细信息（坐标、标高、频率、道面等）
- **昼夜模式**：一键切换深色/浅色主题

### 数据获取技术方案
1. 登录 e-AIP 网站（https://www.eaipchina.cn/e-AIP）
2. 从 `JsonPath/AMDT.JSON` 获取 362 个数据节点的完整索引（含 ICAO 和 jsId）
3. 通过 iframe 加载每个机场的 `AOI_AIP.html` 页面
4. 从 iframe 全局变量 `AD_AIP` 提取 24 个章节的结构化 JSON 数据
5. 坐标转换（度分格式 → 十进制度）、跑道端点计算、导航台分类
6. 输出标准 GeoJSON FeatureCollection

---

## 项目概述
本项目是类 Navigraph Charts 航图软件的**第一步核心可行性 POC 验证**，已完成两个阶段：
1. **合成数据阶段**：全球 46 机场模拟数据，验证 ARINC 424 解析 + 矢量渲染链路
2. **真实数据阶段**：中国民航 e-AIP 真实数据，30 机场/126 导航台/48 跑道

验证两条生死线：
1. **航空导航数据能正确解析** — ARINC 424 / e-AIP JSON → 结构化 GeoJSON
2. **矢量航图能流畅渲染** — MapLibre GL JS 无级缩放、图层可控、交互完整

## 目录结构
```
navchart-poc/
├── data/
│   ├── zbaa_airport_ground.geojson  # ✨ 机场地面细节 GeoJSON (1659 Feature, 616KB)
│   ├── zbaa_osm_raw.json            # OSM Overpass API 原始数据 (10294 元素)
│   ├── china_airports_real.geojson  # 中国民航真实数据 GeoJSON (204 Feature, 110KB)
│   ├── global_sample.dat             # 全球模拟 ARINC 424 数据 (1355条记录)
│   ├── global_chart.geojson          # 全球解析后的 GeoJSON (568个Feature, 650KB)
│   ├── zuuu_sample.dat               # ZUUU单机场样本 (88条记录, 保留参考)
│   └── zuuu_chart.geojson            # ZUUU解析结果 (40个Feature, 保留参考)
├── parser/
│   └── arinc424.py                   # ARINC 424 解析器 (支持8种记录类型)
├── scripts/
│   ├── fetch_osm_aeroway.py          # ✨ OSM aeroway 数据抓取脚本 (Overpass API)
│   ├── osm_to_geojson.py             # ✨ OSM 数据转 GeoJSON 脚本
│   ├── check_ground_data.py          # ✨ 机场地面数据检查脚本
│   ├── generate_global_data.py       # 全球数据生成器 (46机场/24航路/21FIR)
│   ├── generate_sample_data.py       # ZUUU单机场数据生成器 (保留参考)
│   └── merge_geojson.py              # 真实数据分块拼接脚本
├── web/
│   ├── index_airport.html            # ✨ 机场地面细节渲染页面 (vatsim-radar 风格)
│   ├── index.html                    # MapLibre 渲染页面 (全球合成数据版)
│   └── index_real.html               # MapLibre 渲染页面 (中国民航真实数据版)
├── start_server.bat                  # Windows 启动脚本
└── README.md                         # 本文件
```

## 快速开始

### 1. 启动本地服务器
双击运行 `start_server.bat`，或手动执行：
```bash
cd navchart-poc
python -m http.server 8765
```

### 2. 打开浏览器
访问: http://localhost:8765/web/index.html

## 全球数据覆盖

### 数据规模 (1355条 ARINC 424 记录 → 568个 GeoJSON Feature)

| 数据类型 | 数量 | 覆盖范围 |
|---------|------|---------|
| 机场 (P-A) | 46 | 六大洲主要枢纽 (亚洲18/欧洲10/北美8/大洋洲3/非洲3/南美3) |
| 导航台 (H) | 36 | 各区域主要 VOR/DME |
| 航路点 (D-B/E-B) | 338 | 62个航路航路点 + 276个终端航路点 |
| 高空航路 (R) | 24条 | 亚洲内部/欧亚/跨大西洋/北美内部/跨太平洋/大洋洲/非洲/南美 |
| 终端程序 (T-D/E/F) | 93套 | 每机场 SID+STAR+ILS进近 (138套程序定义) |
| 空域 (U) | 31个 | 21个 FIR 飞行情报区 + 10个 CTR 终端管制区 |

### 覆盖的主要机场
- **亚洲**: 北京/上海/广州/成都/西安/东京/大阪/首尔/香港/新加坡/曼谷/吉隆坡/马尼拉/德里/孟买/迪拜/多哈/利雅得
- **欧洲**: 伦敦/巴黎/法兰克福/阿姆斯特丹/莫斯科/罗马/马德里/慕尼黑/盖特威克/奥利
- **北美**: 纽约/洛杉矶/芝加哥/旧金山/亚特兰大/达拉斯/温哥华/多伦多
- **大洋洲**: 悉尼/墨尔本/奥克兰
- **非洲**: 开罗/约翰内斯堡/内罗毕
- **南美**: 圣保罗/布宜诺斯艾利斯/墨西哥城

## 已验证功能

### 数据解析 (ARINC 424 → GeoJSON)
- ✅ 8种记录类型全覆盖 (机场/航路点/终端航路点/导航台/航路/SID/STAR/进近/空域)
- ✅ ARINC 424 标准 DMS 坐标解析 (N/S DDMMSS.ss + E/W DDDMMSS.ss)
- ✅ 终端程序航段序列排序、程序分组、过渡航线解析
- ✅ 空域多边形边界点提取与闭合
- ✅ 1355条记录解析耗时 < 1秒，输出标准 GeoJSON

### 航图渲染 (全球大数据量优化)
- ✅ 无级缩放 (zoom 1.5-16)，矢量图形不模糊
- ✅ **缩放级别图层控制** (LOD):
  - zoom 1.5-2.5: 全球视角 → 机场 + FIR空域
  - zoom 2.5-3.5: 大洲视角 → + 高空航路 + 航路标注
  - zoom 3.5-5: 区域视角 → + 导航台 + 机场标注
  - zoom 5-7: 终端区视角 → + 航路点 + 低空航路 + CTR空域
  - zoom 7+: 近进视角 → + SID/STAR程序 + 进近程序 + 程序标注
- ✅ 11个独立图层可控开关
- ✅ 昼夜模式切换
- ✅ 点击要素显示详情 (6类要素)
- ✅ 650KB 全球数据加载流畅，渲染无卡顿
- ✅ 海里制比例尺、罗盘导航、实时坐标显示

## 数据说明
> ⚠️ **重要**: 当前使用的是**合成模拟数据**，基于全球真实机场坐标的合理推算，航路、程序、空域均为技术验证用途的模拟数据，**不可用于真实飞行**。
>
> 接入真实 Jeppesen / 国内民航数据后，只需替换 `data/global_sample.dat`，重新运行解析器即可，渲染层无需任何改动。

## 重新生成数据
```bash
# 生成全球 ARINC 424 数据
python scripts/generate_global_data.py

# 解析为 GeoJSON
python parser/arinc424.py data/global_sample.dat data/global_chart.geojson
```

## 下一步 (第二步)
1. **自动化数据处理管线** — AIRAC 28天周期自动校验、差分更新、矢量瓦片(MBTiles)生成
2. **双端基础框架** — Web(React+TS) + Electron桌面端，渲染内核100%复用
3. **SimBrief 全链路** — API对接、飞行计划解析、航路+SID/STAR高亮渲染
4. **数据分发服务** — 在线瓦片加载 + 桌面端离线全量下载
5. **性能优化** — 矢量瓦片切片、视口裁剪、大数据量增量渲染
