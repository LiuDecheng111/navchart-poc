/**
 * VATSIM 实时数据加载器
 * 获取全球在线飞机和管制员数据，在地图上渲染
 * 支持自动刷新、点击查询详情、图层控制
 */
(function(global) {
    'use strict';

    // ===== 配置 =====
    const VATSIM_DATA_URL = 'https://data.vatsim.net/v3/vatsim-data.json';
    const REFRESH_INTERVAL = 30000; // 30秒自动刷新
    const LABEL_MIN_ZOOM = 5; // 缩放>=5时显示呼号标注
    const AIRCRAFT_ICON_SIZE = 1.2; // 飞机图标大小倍率

    // ===== 状态 =====
    let mapInstance = null;
    let vatsimData = null;
    let refreshTimer = null;
    let sourceAdded = false;
    let onStatusChange = null;
    let isEnabled = true;

    // ===== 公共 API =====

    /**
     * 初始化 VATSIM 数据加载器
     */
    function init(map, statusCallback) {
        mapInstance = map;
        onStatusChange = statusCallback || function() {};

        ensureSourceAndLayers();
        refreshData();
        startAutoRefresh();

        // 点击飞机查询详情
        map.on('click', 'vatsim-aircraft', function(e) {
            if (e.features && e.features.length > 0) {
                showAircraftPopup(e.features[0], e.lngLat);
            }
        });

        // 鼠标悬停显示指针
        map.on('mouseenter', 'vatsim-aircraft', function() {
            map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'vatsim-aircraft', function() {
            map.getCanvas().style.cursor = '';
        });
    }

    /**
     * 刷新 VATSIM 数据
     */
    async function refreshData() {
        if (!isEnabled) return;

        try {
            onStatusChange('loading', null, '正在获取 VATSIM 实时数据...');

            const resp = await fetch(VATSIM_DATA_URL, { cache: 'no-store' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

            vatsimData = await resp.json();
            const aircraftGeoJSON = convertPilotsToGeoJSON(vatsimData.pilots || []);
            const controllersGeoJSON = convertControllersToGeoJSON(vatsimData.controllers || []);

            // 更新数据源
            if (mapInstance.getSource('vatsim-aircraft')) {
                mapInstance.getSource('vatsim-aircraft').setData(aircraftGeoJSON);
            }
            if (mapInstance.getSource('vatsim-controllers')) {
                mapInstance.getSource('vatsim-controllers').setData(controllersGeoJSON);
            }

            const pilotCount = (vatsimData.pilots || []).length;
            const controllerCount = (vatsimData.controllers || []).length;
            onStatusChange('loaded', null,
                `VATSIM 实时数据已更新: ${pilotCount} 架飞机, ${controllerCount} 名管制`);

            console.log(`[VATSIM] 数据更新: ${pilotCount} pilots, ${controllerCount} controllers`);
        } catch (e) {
            console.warn('[VATSIM] 数据获取失败:', e.message);
            onStatusChange('error', null, `VATSIM 数据获取失败: ${e.message}`);
        }
    }

    /**
     * 启动自动刷新
     */
    function startAutoRefresh() {
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(refreshData, REFRESH_INTERVAL);
    }

    /**
     * 停止自动刷新
     */
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    /**
     * 启用/禁用 VATSIM 数据
     */
    function setEnabled(enabled) {
        isEnabled = enabled;
        if (mapInstance) {
            const layers = ['vatsim-aircraft', 'vatsim-aircraft-labels',
                           'vatsim-controllers', 'vatsim-controller-labels'];
            layers.forEach(id => {
                if (mapInstance.getLayer(id)) {
                    mapInstance.setLayoutProperty(id, 'visibility', enabled ? 'visible' : 'none');
                }
            });
        }
        if (enabled) {
            refreshData();
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    }

    /**
     * 获取当前数据统计
     */
    function getStats() {
        if (!vatsimData) return { pilots: 0, controllers: 0, updated: null };
        return {
            pilots: (vatsimData.pilots || []).length,
            controllers: (vatsimData.controllers || []).length,
            atis: (vatsimData.atis || []).length,
            updated: vatsimData.general?.update_timestamp || null
        };
    }

    // ===== 内部函数 =====

    /**
     * 确保数据源和图层已添加
     */
    function ensureSourceAndLayers() {
        if (!mapInstance || sourceAdded) return;

        // 飞机数据源
        if (!mapInstance.getSource('vatsim-aircraft')) {
            mapInstance.addSource('vatsim-aircraft', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] }
            });
        }

        // 管制员数据源
        if (!mapInstance.getSource('vatsim-controllers')) {
            mapInstance.addSource('vatsim-controllers', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] }
            });
        }

        // 飞机图标图层（使用 symbol 图层，根据航向旋转）
        if (!mapInstance.getLayer('vatsim-aircraft')) {
            mapInstance.addLayer({
                id: 'vatsim-aircraft',
                type: 'symbol',
                source: 'vatsim-aircraft',
                minzoom: 2,
                layout: {
                    'icon-image': 'aircraft-icon',
                    'icon-size': AIRCRAFT_ICON_SIZE,
                    'icon-rotate': ['get', 'heading'],
                    'icon-allow-overlap': true,
                    'icon-ignore-placement': true,
                    'icon-rotation-alignment': 'map'
                },
                paint: {
                    'icon-color': [
                        'match', ['get', 'flight_type'],
                        'departure', '#4fc3f7',
                        'arrival', '#81c784',
                        'cruise', '#ffb74d',
                        '#4fc3f7'
                    ],
                    'icon-halo-color': '#0a0e1a',
                    'icon-halo-width': 1
                }
            });
        }

        // 飞机呼号标注图层
        if (!mapInstance.getLayer('vatsim-aircraft-labels')) {
            mapInstance.addLayer({
                id: 'vatsim-aircraft-labels',
                type: 'symbol',
                source: 'vatsim-aircraft',
                minzoom: LABEL_MIN_ZOOM,
                layout: {
                    'text-field': ['get', 'label'],
                    'text-size': 10,
                    'text-offset': [0, 1.5],
                    'text-allow-overlap': false,
                    'text-optional': true
                },
                paint: {
                    'text-color': '#b0bec5',
                    'text-halo-color': '#0a0e1a',
                    'text-halo-width': 1.5
                }
            });
        }

        // 管制员图标图层
        if (!mapInstance.getLayer('vatsim-controllers')) {
            mapInstance.addLayer({
                id: 'vatsim-controllers',
                type: 'circle',
                source: 'vatsim-controllers',
                minzoom: 3,
                paint: {
                    'circle-radius': 5,
                    'circle-color': [
                        'match', ['get', 'facility_type'],
                        'ATIS', '#78909c',
                        'DEL', '#90a4ae',
                        'GND', '#4caf50',
                        'TWR', '#2196f3',
                        'APP', '#ff9800',
                        'CTR', '#f44336',
                        '#9e9e9e'
                    ],
                    'circle-stroke-color': '#0a0e1a',
                    'circle-stroke-width': 1.5,
                    'circle-opacity': 0.95
                }
            });
        }

        // 管制员呼号标注图层
        if (!mapInstance.getLayer('vatsim-controller-labels')) {
            mapInstance.addLayer({
                id: 'vatsim-controller-labels',
                type: 'symbol',
                source: 'vatsim-controllers',
                minzoom: 4,
                layout: {
                    'text-field': ['get', 'callsign'],
                    'text-size': 10,
                    'text-offset': [0, 1.2],
                    'text-allow-overlap': false
                },
                paint: {
                    'text-color': '#b0bec5',
                    'text-halo-color': '#0a0e1a',
                    'text-halo-width': 1.5
                }
            });
        }

        // 加载飞机图标（使用 SVG data URL）
        loadAircraftIcon();

        sourceAdded = true;
    }

    /**
     * 加载飞机图标（SVG）
     */
    function loadAircraftIcon() {
        if (!mapInstance || mapInstance.hasImage('aircraft-icon')) return;

        // 简单的飞机俯视图 SVG
        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path d="M12 2 L13 9 L21 12 L13 13 L12 22 L11 13 L3 12 L11 9 Z"
                      fill="currentColor" stroke="currentColor" stroke-width="0.5"/>
            </svg>
        `;

        const img = new Image();
        img.onload = function() {
            if (mapInstance && !mapInstance.hasImage('aircraft-icon')) {
                mapInstance.addImage('aircraft-icon', img);
            }
        };
        img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }

    /**
     * 将飞行员数据转换为 GeoJSON
     */
    function convertPilotsToGeoJSON(pilots) {
        const features = [];

        for (const p of pilots) {
            // 跳过无效坐标或在地面的飞机（可选，这里保留所有）
            if (p.latitude == null || p.longitude == null) continue;
            if (p.latitude < -90 || p.latitude > 90 || p.longitude < -180 || p.longitude > 180) continue;

            const fp = p.flight_plan || {};
            const altitude = p.altitude || 0;

            // 判断飞行阶段
            let flightType = 'cruise';
            if (altitude < 3000) flightType = 'departure'; // 低空视为起飞/进近
            else if (fp.arrival && altitude < 10000) flightType = 'arrival';

            // 构建标注文本：呼号 + 高度（如果有飞行计划）
            let label = p.callsign || '';
            if (altitude > 0) {
                label += ` ${Math.round(altitude/100)}`;
            }

            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [p.longitude, p.latitude]
                },
                properties: {
                    callsign: p.callsign || '',
                    cid: p.cid,
                    name: p.name || '',
                    heading: p.heading || 0,
                    altitude: altitude,
                    groundspeed: p.groundspeed || 0,
                    transponder: p.transponder || '',
                    departure: fp.departure || '',
                    arrival: fp.arrival || '',
                    aircraft: fp.aircraft_short || fp.aircraft || '',
                    cruise_altitude: fp.altitude || '',
                    route: fp.route || '',
                    remarks: fp.remarks || '',
                    flight_type: flightType,
                    label: label,
                    server: p.server || '',
                    last_updated: p.last_updated || ''
                }
            });
        }

        return { type: 'FeatureCollection', features };
    }

    /**
     * 将管制员数据转换为 GeoJSON
     */
    function convertControllersToGeoJSON(controllers) {
        const features = [];

        for (const c of controllers) {
            if (c.latitude == null || c.longitude == null) continue;
            if (c.latitude < -90 || c.latitude > 90 || c.longitude < -180 || c.longitude > 180) continue;

            // 解析设施类型
            const facilityMap = {
                0: 'Unknown', 1: 'ATIS', 2: 'DEL', 3: 'GND',
                4: 'TWR', 5: 'APP', 6: 'CTR', 7: 'FSS'
            };
            const facilityType = facilityMap[c.facility] || 'Unknown';

            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [c.longitude, c.latitude]
                },
                properties: {
                    callsign: c.callsign || '',
                    cid: c.cid,
                    name: c.name || '',
                    facility_type: facilityType,
                    frequency: c.frequency || '',
                    rating: c.rating || 0,
                    server: c.server || '',
                    last_updated: c.last_updated || ''
                }
            });
        }

        return { type: 'FeatureCollection', features };
    }

    /**
     * 显示飞机详情弹窗
     */
    function showAircraftPopup(feature, lngLat) {
        const p = feature.properties;

        let html = `<div style="min-width:220px;font-size:13px;">`;
        html += `<div style="font-size:16px;font-weight:bold;color:#4fc3f7;margin-bottom:8px;">${p.callsign}</div>`;

        if (p.name) {
            html += `<div style="color:#90a4ae;margin-bottom:6px;">${p.name}</div>`;
        }

        html += `<table style="width:100%;border-collapse:collapse;">`;

        if (p.departure || p.arrival) {
            html += `<tr><td style="color:#78909c;padding:2px 0;">航线</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.departure || '?'} → ${p.arrival || '?'}</td></tr>`;
        }
        if (p.aircraft) {
            html += `<tr><td style="color:#78909c;padding:2px 0;">机型</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.aircraft}</td></tr>`;
        }
        html += `<tr><td style="color:#78909c;padding:2px 0;">高度</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.altitude.toLocaleString()} ft</td></tr>`;
        html += `<tr><td style="color:#78909c;padding:2px 0;">速度</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.groundspeed} kt</td></tr>`;
        html += `<tr><td style="color:#78909c;padding:2px 0;">航向</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.heading}°</td></tr>`;
        if (p.transponder) {
            html += `<tr><td style="color:#78909c;padding:2px 0;">应答机</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.transponder}</td></tr>`;
        }
        if (p.cruise_altitude) {
            html += `<tr><td style="color:#78909c;padding:2px 0;">巡航高度</td><td style="color:#e0e0e0;padding:2px 0;text-align:right;">${p.cruise_altitude} ft</td></tr>`;
        }
        html += `</table>`;

        if (p.route) {
            html += `<div style="margin-top:8px;color:#78909c;font-size:11px;">航路: ${p.route.substring(0, 100)}${p.route.length > 100 ? '...' : ''}</div>`;
        }

        html += `</div>`;

        new maplibregl.Popup({ closeButton: true, closeOnClick: false, maxWidth: '300px' })
            .setLngLat(lngLat)
            .setHTML(html)
            .addTo(mapInstance);
    }

    // 导出到全局
    global.VATSIMLoader = {
        init,
        refreshData,
        setEnabled,
        getStats,
        startAutoRefresh,
        stopAutoRefresh
    };

})(window);
