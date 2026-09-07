/**
 * 机场地面数据按需加载器
 * 当放大到机场时，动态从 OpenStreetMap Overpass API 加载跑道、滑行道、停机坪等矢量数据
 * 支持全球所有机场，带缓存避免重复加载
 */
(function(global) {
    'use strict';

    // ===== 配置 =====
    const OVERPASS_MIRRORS = [
        'https://overpass-api.de/api/interpreter',
        'https://overpass.kumi.systems/api/interpreter',
        'https://overpass.private.coffee/api/interpreter'
    ];
    const SEARCH_RADIUS = 3000; // 机场周围搜索半径（米）
    const LOAD_ZOOM_THRESHOLD = 12; // 达到此缩放级别开始加载地面数据
    const MAX_CONCURRENT_LOADS = 2; // 最大并发加载数

    // 中国 30 个机场已有预加载 OSM 数据，跳过按需加载避免重复
    const CHINA_PRELOADED_AIRPORTS = new Set([
        'ZBAA','ZBDS','ZBER','ZBYN','ZGGG','ZGKL','ZGSZ','ZGZJ','ZHEC','ZHHH',
        'ZJQH','ZLIC','ZLLL','ZPPP','ZSFZ','ZSHC','ZSNB','ZSNJ','ZSNT','ZSOF',
        'ZSPD','ZSSS','ZSTX','ZSZS','ZUCK','ZULS','ZWWW','ZYHB','ZYJM','ZYTL'
    ]);

    // ===== 状态 =====
    const loadedCache = {};      // 已加载的机场地面数据 {icao: geojson}
    const loadingSet = new Set(); // 正在加载的机场 ICAO
    const failedSet = new Set();  // 加载失败的机场 ICAO
    let mirrorIndex = 0;
    let currentLoads = 0;
    let mapInstance = null;
    let sourceAdded = false;
    let onStatusChange = null;

    // ===== OSM 要素类型到渲染样式的映射 =====
    const AEROWAY_TYPES = {
        runway: { layer: 'og-runway', type: 'line' },
        taxiway: { layer: 'og-taxiway', type: 'line' },
        apron: { layer: 'og-apron', type: 'fill' },
        parking_position: { layer: 'og-parking', type: 'point' },
        gate: { layer: 'og-gate', type: 'point' },
        jet_bridge: { layer: 'og-jetbridge', type: 'line' },
        terminal: { layer: 'og-terminal', type: 'fill' },
        navigationaid: { layer: 'og-navaid', type: 'point' },
        stopway: { layer: 'og-stopway', type: 'fill' },
        windsock: { layer: 'og-windsock', type: 'point' },
        aerodrome: { layer: 'og-aerodrome', type: 'fill' },
        hangar: { layer: 'og-hangar', type: 'fill' },
        tower: { layer: 'og-tower', type: 'point' },
        helipad: { layer: 'og-helipad', type: 'fill' }
    };

    // ===== 公共 API =====

    /**
     * 初始化加载器，绑定地图实例
     */
    function init(map, statusCallback) {
        mapInstance = map;
        onStatusChange = statusCallback || function() {};

        // 监听地图缩放和移动事件
        map.on('zoomend', checkAndLoad);
        map.on('moveend', checkAndLoad);

        // 确保数据源和图层已添加
        ensureSourceAndLayers();
    }

    /**
     * 检查当前视图并加载附近机场的地面数据
     */
    function checkAndLoad() {
        if (!mapInstance || !mapInstance.getSource('global-airports')) return;

        const zoom = mapInstance.getZoom();
        if (zoom < LOAD_ZOOM_THRESHOLD) return;

        // 查询当前视图范围内的机场点
        const features = mapInstance.queryRenderedFeatures({
            layers: ['global-airport-point']
        });

        // 去重并筛选未加载的机场（跳过中国预加载机场）
        const airportsToLoad = [];
        const seen = new Set();
        for (const f of features) {
            const icao = f.properties.icao;
            if (!icao || seen.has(icao)) continue;
            if (CHINA_PRELOADED_AIRPORTS.has(icao)) continue; // 跳过中国预加载机场
            if (loadedCache[icao] || loadingSet.has(icao) || failedSet.has(icao)) continue;
            seen.add(icao);
            airportsToLoad.push({
                icao: icao,
                lat: f.geometry.coordinates[1],
                lon: f.geometry.coordinates[0]
            });
        }

        // 按距离视图中心排序，优先加载中心附近的机场
        const center = mapInstance.getCenter();
        airportsToLoad.sort((a, b) => {
            const da = Math.hypot(a.lon - center.lng, a.lat - center.lat);
            const db = Math.hypot(b.lon - center.lng, b.lat - center.lat);
            return da - db;
        });

        // 限制每次最多加载的机场数
        const maxLoads = Math.max(0, MAX_CONCURRENT_LOADS - currentLoads);
        const toLoad = airportsToLoad.slice(0, Math.max(1, maxLoads + 2));

        for (const airport of toLoad) {
            loadAirportGround(airport.icao, airport.lat, airport.lon);
        }
    }

    /**
     * 加载单个机场的地面数据
     */
    async function loadAirportGround(icao, lat, lon) {
        if (loadedCache[icao] || loadingSet.has(icao) || failedSet.has(icao)) return;
        if (currentLoads >= MAX_CONCURRENT_LOADS) return;

        loadingSet.add(icao);
        currentLoads++;
        onStatusChange('loading', icao, `正在加载 ${icao} 机场地面数据...`);

        try {
            const geojson = await fetchOSMData(lat, lon);
            loadedCache[icao] = geojson;
            renderToMap(geojson);
            onStatusChange('loaded', icao, `${icao} 机场地面数据已加载 (${geojson.features.length} 要素)`);
        } catch (e) {
            console.warn(`[AirportGround] 加载 ${icao} 失败:`, e.message);
            failedSet.add(icao);
            onStatusChange('error', icao, `${icao} 地面数据加载失败`);
        } finally {
            loadingSet.delete(icao);
            currentLoads--;
            // 继续加载队列中的其他机场
            setTimeout(checkAndLoad, 500);
        }
    }

    /**
     * 从 Overpass API 获取 OSM 数据并转换为 GeoJSON
     */
    async function fetchOSMData(lat, lon) {
        const query = buildOverpassQuery(lat, lon);

        let lastError = null;
        for (let attempt = 0; attempt < OVERPASS_MIRRORS.length * 2; attempt++) {
            const url = OVERPASS_MIRRORS[mirrorIndex % OVERPASS_MIRRORS.length];
            mirrorIndex++;

            try {
                const controller = new AbortController();
                const timeout = setTimeout(() => controller.abort(), 30000);

                const resp = await fetch(url, {
                    method: 'POST',
                    body: 'data=' + encodeURIComponent(query),
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    signal: controller.signal
                });
                clearTimeout(timeout);

                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const osmData = await resp.json();
                return convertOSMToGeoJSON(osmData);
            } catch (e) {
                lastError = e;
                console.warn(`[AirportGround] Overpass镜像失败 (${url}):`, e.message);
                await sleep(1000);
            }
        }
        throw lastError || new Error('所有 Overpass 镜像均失败');
    }

    /**
     * 构建 Overpass API 查询
     */
    function buildOverpassQuery(lat, lon) {
        return `[out:json][timeout:25];
(
  way["aeroway"](around:${SEARCH_RADIUS},${lat},${lon});
  node["aeroway"](around:${SEARCH_RADIUS},${lat},${lon});
  relation["aeroway"](around:${SEARCH_RADIUS},${lat},${lon});
);
out geom;`;
    }

    /**
     * 将 OSM JSON 转换为 GeoJSON
     */
    function convertOSMToGeoJSON(osmData) {
        const features = [];
        const nodes = {};

        // 先收集所有 node 的坐标
        for (const el of osmData.elements) {
            if (el.type === 'node') {
                nodes[el.id] = [el.lon, el.lat];
            }
        }

        for (const el of osmData.elements) {
            if (!el.tags || !el.tags.aeroway) continue;
            const aerowayType = el.tags.aeroway;

            if (el.type === 'node') {
                features.push({
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [el.lon, el.lat] },
                    properties: { ...el.tags, osm_type: 'node', osm_id: el.id }
                });
            } else if (el.type === 'way') {
                // 使用 geometry 字段（out geom 返回的）
                let coords;
                if (el.geometry && el.geometry.length > 0) {
                    coords = el.geometry.map(p => [p.lon, p.lat]);
                } else if (el.nodes && el.nodes.length > 0) {
                    coords = el.nodes.map(nid => nodes[nid]).filter(Boolean);
                } else {
                    continue;
                }

                if (coords.length < 2) continue;

                // 判断是否为闭合多边形（第一个和最后一个坐标相同）
                const isClosed = coords.length > 3 &&
                    coords[0][0] === coords[coords.length - 1][0] &&
                    coords[0][1] === coords[coords.length - 1][1];

                // 某些类型强制作为线处理（即使闭合也不转面）
                const forceLine = ['runway', 'taxiway', 'jet_bridge'];
                // 某些类型强制作为面处理
                const forcePolygon = ['apron', 'terminal', 'hangar', 'aerodrome', 'stopway', 'helipad'];

                if (!forceLine.includes(aerowayType) && (isClosed || forcePolygon.includes(aerowayType))) {
                    // 确保闭合
                    if (!isClosed && coords.length > 2) {
                        coords.push([...coords[0]]);
                    }
                    features.push({
                        type: 'Feature',
                        geometry: { type: 'Polygon', coordinates: [coords] },
                        properties: { ...el.tags, osm_type: 'way', osm_id: el.id }
                    });
                } else {
                    features.push({
                        type: 'Feature',
                        geometry: { type: 'LineString', coordinates: coords },
                        properties: { ...el.tags, osm_type: 'way', osm_id: el.id }
                    });
                }
            }
            // relation 类型暂不处理（复杂多边形）
        }

        return { type: 'FeatureCollection', features };
    }

    /**
     * 确保数据源和图层已添加到地图
     */
    function ensureSourceAndLayers() {
        if (!mapInstance || sourceAdded) return;

        // 添加空数据源
        if (!mapInstance.getSource('og-ground')) {
            mapInstance.addSource('og-ground', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] }
            });
        }

        // 按类型添加图层
        const layerDefs = [
            // 面图层（先绘制，在底层）
            { id: 'og-aerodrome', type: 'fill', aeroway: 'aerodrome', color: '#1a1a1a', opacity: 0.6 },
            { id: 'og-apron', type: 'fill', aeroway: 'apron', color: '#3a3a3a', opacity: 0.9 },
            { id: 'og-terminal', type: 'fill', aeroway: 'terminal', color: '#5a5a5a', opacity: 0.95 },
            { id: 'og-hangar', type: 'fill', aeroway: 'hangar', color: '#4a4a4a', opacity: 0.9 },
            { id: 'og-stopway', type: 'fill', aeroway: 'stopway', color: '#2a2a2a', opacity: 0.8 },
            { id: 'og-helipad', type: 'fill', aeroway: 'helipad', color: '#2a2a4a', opacity: 0.8 },

            // 线图层（大幅增加线宽模拟面效果）
            { id: 'og-runway', type: 'line', aeroway: 'runway', color: '#ffffff', width: 18, opacity: 0.95 },
            { id: 'og-taxiway', type: 'line', aeroway: 'taxiway', color: '#b8b8b8', width: 10, opacity: 0.9 },
            { id: 'og-jetbridge', type: 'line', aeroway: 'jet_bridge', color: '#888', width: 3, opacity: 0.8 },

            // 点图层（最后绘制，在顶层）
            // 停机位：只显示有 ref/name 标注的，避免 OSM 中位置不准确的未标注点形成大量蓝色圆点
            { id: 'og-parking', type: 'circle', aeroway: 'parking_position', color: '#4fc3f7', radius: 2.5, minzoom: 15,
              filter: ['all', ['==', ['get', 'aeroway'], 'parking_position'],
                ['any', ['has', 'ref'], ['has', 'name']]] },
            { id: 'og-gate', type: 'circle', aeroway: 'gate', color: '#81c784', radius: 4 },
            { id: 'og-navaid', type: 'circle', aeroway: 'navigationaid', color: '#ffd54f', radius: 3 },
            { id: 'og-windsock', type: 'circle', aeroway: 'windsock', color: '#ff8a65', radius: 2.5 },
            { id: 'og-tower', type: 'circle', aeroway: 'tower', color: '#ba68c8', radius: 3 }
        ];

        for (const def of layerDefs) {
            if (mapInstance.getLayer(def.id)) continue;

            const layer = {
                id: def.id,
                source: 'og-ground',
                filter: def.filter || ['==', ['get', 'aeroway'], def.aeroway],
                minzoom: def.minzoom || 11,
                layout: { visibility: 'visible' }
            };

            if (def.type === 'fill') {
                layer.type = 'fill';
                layer.paint = {
                    'fill-color': def.color,
                    'fill-opacity': def.opacity
                };
            } else if (def.type === 'line') {
                layer.type = 'line';
                // line-cap 和 line-join 是 layout 属性，不是 paint 属性！
                layer.layout['line-cap'] = 'round';
                layer.layout['line-join'] = 'round';
                layer.paint = {
                    'line-color': def.color,
                    'line-width': def.width,
                    'line-opacity': def.opacity
                };
            } else if (def.type === 'circle') {
                layer.type = 'circle';
                layer.paint = {
                    'circle-radius': def.radius,
                    'circle-color': def.color,
                    'circle-stroke-color': '#0a0e1a',
                    'circle-stroke-width': 1,
                    'circle-opacity': 0.9
                };
            }

            try {
                mapInstance.addLayer(layer);
            } catch (e) {
                console.error(`[GroundLoader] 图层添加失败 ${def.id}:`, e.message);
            }
        }

        // ===== 标注图层（高缩放级别显示） =====
        const labelLayers = [
            // 跑道号标注（zoom>=14）
            {
                id: 'og-runway-label',
                type: 'symbol',
                source: 'og-ground',
                filter: ['all', ['==', ['get', 'aeroway'], 'runway'], ['!=', ['get', 'ref'], '']],
                minzoom: 14,
                layout: {
                    'text-field': ['get', 'ref'],
                    'text-size': 12,
                    'text-offset': [0, 0],
                    'text-allow-overlap': true,
                    'text-ignore-placement': true
                },
                paint: {
                    'text-color': '#000000',
                    'text-halo-color': '#ffffff',
                    'text-halo-width': 2
                }
            },
            // 滑行道代号标注（zoom>=15）
            {
                id: 'og-taxiway-label',
                type: 'symbol',
                source: 'og-ground',
                filter: ['all', ['==', ['get', 'aeroway'], 'taxiway'], ['!=', ['get', 'ref'], '']],
                minzoom: 15,
                layout: {
                    'text-field': ['get', 'ref'],
                    'text-size': 10,
                    'text-offset': [0, 0],
                    'text-allow-overlap': false,
                    'text-optional': true
                },
                paint: {
                    'text-color': '#ffffff',
                    'text-halo-color': '#000000',
                    'text-halo-width': 1.5
                }
            },
            // 机位号标注（zoom>=16）
            {
                id: 'og-parking-label',
                type: 'symbol',
                source: 'og-ground',
                filter: ['all',
                    ['==', ['get', 'aeroway'], 'parking_position'],
                    ['any', ['!=', ['get', 'ref'], ''], ['!=', ['get', 'name'], '']]
                ],
                minzoom: 16,
                layout: {
                    'text-field': ['coalesce', ['get', 'ref'], ['get', 'name'], ''],
                    'text-size': 9,
                    'text-offset': [0, 1.2],
                    'text-allow-overlap': false,
                    'text-optional': true
                },
                paint: {
                    'text-color': '#4fc3f7',
                    'text-halo-color': '#0a0e1a',
                    'text-halo-width': 1.5
                }
            },
            // 登机口标注（zoom>=15）
            {
                id: 'og-gate-label',
                type: 'symbol',
                source: 'og-ground',
                filter: ['all',
                    ['==', ['get', 'aeroway'], 'gate'],
                    ['any', ['!=', ['get', 'ref'], ''], ['!=', ['get', 'name'], '']]
                ],
                minzoom: 15,
                layout: {
                    'text-field': ['coalesce', ['get', 'ref'], ['get', 'name'], ''],
                    'text-size': 10,
                    'text-offset': [0, 1.2],
                    'text-allow-overlap': false,
                    'text-optional': true
                },
                paint: {
                    'text-color': '#81c784',
                    'text-halo-color': '#0a0e1a',
                    'text-halo-width': 1.5
                }
            }
        ];

        for (const def of labelLayers) {
            if (mapInstance.getLayer(def.id)) continue;
            try {
                mapInstance.addLayer(def);
            } catch (e) {
                console.error(`[GroundLoader] 标注图层添加失败 ${def.id}:`, e.message);
            }
        }

        // 同步页面图层面板的复选框状态（如果页面上存在对应复选框）
        const checkboxSync = [
            ['layer-apron', ['og-aerodrome', 'og-apron', 'og-terminal', 'og-hangar', 'og-stopway', 'og-helipad']],
            ['layer-runway', ['og-runway', 'og-runway-label']],
            ['layer-taxiway', ['og-taxiway', 'og-taxiway-label']],
            ['layer-parking', ['og-parking', 'og-parking-label']],
            ['layer-gate', ['og-gate', 'og-gate-label']]
        ];
        checkboxSync.forEach(([checkboxId, layerIds]) => {
            const checkbox = document.getElementById(checkboxId);
            if (checkbox && !checkbox.checked) {
                layerIds.forEach(id => {
                    if (mapInstance.getLayer(id)) {
                        mapInstance.setLayoutProperty(id, 'visibility', 'none');
                    }
                });
            }
        });

        sourceAdded = true;
    }

    /**
     * 将 GeoJSON 数据渲染到地图（合并到现有数据源）
     */
    function renderToMap(geojson) {
        if (!mapInstance || !mapInstance.getSource('og-ground')) return;

        const source = mapInstance.getSource('og-ground');
        const existingData = source._data || { type: 'FeatureCollection', features: [] };

        // 合并新要素，去重（按 osm_id）
        const existingIds = new Set(existingData.features.map(f => f.properties?.osm_id));
        const newFeatures = geojson.features.filter(f => !existingIds.has(f.properties?.osm_id));

        if (newFeatures.length > 0) {
            source.setData({
                type: 'FeatureCollection',
                features: [...existingData.features, ...newFeatures]
            });
        }
    }

    /**
     * 获取加载统计
     */
    function getStats() {
        return {
            loaded: Object.keys(loadedCache).length,
            loading: loadingSet.size,
            failed: failedSet.size,
            totalFeatures: Object.values(loadedCache).reduce((sum, g) => sum + g.features.length, 0)
        };
    }

    /**
     * 工具函数：延时
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 导出到全局
    global.AirportGroundLoader = {
        init,
        checkAndLoad,
        loadAirportGround,
        getStats,
        loadedCache
    };

})(window);
