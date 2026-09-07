"""
全球 ARINC 424 数据生成器 (POC 验证用)

生成覆盖六大洲的全球导航数据:
  - 全球主要枢纽机场 (~40个)
  - 主干高空航路 (~20条, 连接各洲枢纽)
  - 航路点 (~150个)
  - 导航台 (~40个 VOR/DME/NDB)
  - 终端程序 (每机场 SID+STAR+ILS进近)
  - 主要飞行情报区 FIR 和终端管制区 CTR

注意: 这是合成数据，基于真实机场坐标的合理推算，仅用于技术验证，不可用于真实飞行。
"""

import math
import random

random.seed(2024)


# ============================================================
#  坐标工具
# ============================================================

def lat_to_dms(lat: float) -> str:
    hemi = 'N' if lat >= 0 else 'S'
    lat = abs(lat)
    deg = int(lat)
    minute = int((lat - deg) * 60)
    sec = ((lat - deg) * 60 - minute) * 60
    return f"{hemi}{deg:02d}{minute:02d}{sec:05.2f}"


def lon_to_dms(lon: float) -> str:
    hemi = 'E' if lon >= 0 else 'W'
    lon = abs(lon)
    deg = int(lon)
    minute = int((lon - deg) * 60)
    sec = ((lon - deg) * 60 - minute) * 60
    return f"{hemi}{deg:03d}{minute:02d}{sec:05.2f}"


def offset_coord(lat, lon, d_nm, bearing_deg):
    R = 3440.065
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    d = d_nm / R
    lat2 = math.asin(math.sin(lat1) * math.cos(d) +
                      math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1),
                              math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return round(math.degrees(lat2), 5), round(math.degrees(lon2), 5)


def pad(s, width):
    return str(s).ljust(width)[:width]


# ============================================================
#  全球主要机场 (ICAO, name, lat, lon, elev_ft, runway_hdg)
# ============================================================

AIRPORTS = [
    # 亚洲 - 中国
    ("ZBAA", "BEIJING CAPITAL INTL", 40.0799, 116.6031, 1165, 180),
    ("ZSPD", "SHANGHAI PUDONG INTL", 31.1443, 121.8083, 13, 170),
    ("ZGGG", "GUANGZHOU BAIYUN INTL", 23.3924, 113.2988, 36, 180),
    ("ZUUU", "CHENGDU SHUANGLIU INTL", 30.5785, 103.9470, 1625, 200),
    ("ZSSS", "SHANGHAI HONGQIAO INTL", 31.1979, 121.3363, 10, 180),
    ("ZLXY", "XI AN XIANYANG INTL", 34.4471, 108.7516, 1572, 180),
    # 亚洲 - 东北亚/东南亚
    ("RJTT", "TOKYO HANEDA INTL", 35.5494, 139.7798, 21, 160),
    ("RJBB", "OSAKA KANSAI INTL", 34.4347, 135.2330, 26, 180),
    ("RKSI", "SEOUL INCHEON INTL", 37.4602, 126.4407, 23, 180),
    ("VHHH", "HONG KONG INTL", 22.3080, 113.9185, 28, 180),
    ("WSSS", "SINGAPORE CHANGI INTL", 1.3644, 103.9915, 22, 180),
    ("VTBS", "BANGKOK SUVARNABHUMI", 13.6900, 100.7501, 5, 190),
    ("WMKK", "KUALA LUMPUR INTL", 2.7456, 101.7099, 70, 180),
    ("RPLL", "MANILA NINOY AQUINO INTL", 14.5086, 121.0195, 75, 180),
    # 亚洲 - 南亚/中东
    ("VIDP", "DELHI INDIRA GANDHI INTL", 28.5562, 77.1000, 776, 180),
    ("VABB", "MUMBAI CHHATRAPATI SHIVAJI", 19.0896, 72.8656, 10, 180),
    ("OMDB", "DUBAI INTL", 25.2532, 55.3657, 62, 180),
    ("OTHH", "DOHA HAMAD INTL", 25.2731, 51.6080, 13, 180),
    ("OERK", "RIYADH KING KHALID INTL", 24.9577, 46.6992, 2050, 180),
    # 欧洲
    ("EGLL", "LONDON HEATHROW", 51.4700, -0.4543, 83, 180),
    ("LFPG", "PARIS CHARLES DE GAULLE", 49.0097, 2.5479, 392, 180),
    ("EDDF", "FRANKFURT AM MAIN", 50.0379, 8.5622, 364, 180),
    ("EHAM", "AMSTERDAM SCHIPHOL", 52.3105, 4.7683, -11, 180),
    ("UUEE", "MOSCOW SHEREMETYEVO", 55.9726, 37.4146, 748, 180),
    ("LIRF", "ROME FIUMICINO", 41.8003, 12.2389, 8, 160),
    ("LEMD", "MADRID BARAJAS", 40.4719, -3.5626, 1998, 180),
    ("EDDM", "MUNICH FRANZ JOSEF STRAUSS", 48.3537, 11.7861, 1487, 180),
    ("EGKK", "LONDON GATWICK", 51.1481, -0.1903, 202, 180),
    ("LFPO", "PARIS ORLY", 48.7233, 2.3794, 290, 180),
    # 北美
    ("KJFK", "NEW YORK JOHN F KENNEDY INTL", 40.6413, -73.7781, 13, 180),
    ("KLAX", "LOS ANGELES INTL", 33.9416, -118.4085, 126, 180),
    ("KORD", "CHICAGO OHARE INTL", 41.9742, -87.9073, 668, 180),
    ("KSFO", "SAN FRANCISCO INTL", 37.6213, -122.3790, 13, 190),
    ("KATL", "ATLANTA HARTSFIELD JACKSON", 33.6407, -84.4277, 1026, 180),
    ("KDFW", "DALLAS FORT WORTH INTL", 32.8998, -97.0403, 607, 180),
    ("CYVR", "VANCOUVER INTL", 49.1947, -123.1839, 13, 180),
    ("CYYZ", "TORONTO PEARSON INTL", 43.6777, -79.6248, 569, 180),
    # 大洋洲
    ("YSSY", "SYDNEY KINGSFORD SMITH", -33.9461, 151.1772, 21, 160),
    ("YMML", "MELBOURNE TULLAMARINE", -37.6690, 144.8410, 434, 180),
    ("NZAA", "AUCKLAND INTL", -37.0082, 174.7850, 23, 180),
    # 非洲
    ("HECA", "CAIRO INTL", 30.1219, 31.4056, 389, 180),
    ("FAOR", "JOHANNESBURG OR TAMBO INTL", -26.1392, 28.2460, 5558, 180),
    ("HKJK", "NAIROBI JOMO KENYATTA INTL", -1.3192, 36.9278, 5327, 180),
    # 南美
    ("SBGR", "SAO PAULO GUARULHOS INTL", -23.4356, -46.4731, 2451, 180),
    ("SAEZ", "BUENOS AIRES EZEIZA INTL", -34.8222, -58.5358, 67, 180),
    ("MMMX", "MEXICO CITY BENITO JUAREZ INTL", 19.4361, -99.0719, 7316, 180),
]

# ============================================================
#  全球主要导航台
# ============================================================

NAVAIDS = [
    # ident, name, type, lat, lon, freq, elev, range
    ("CTU", "CHENGDU VOR/DME", "V", 30.5785, 103.9470, "114.70", 1625, 100),
    ("PEK", "BEIJING VOR/DME", "V", 40.0799, 116.6031, "114.10", 1165, 120),
    ("PVG", "SHANGHAI VOR/DME", "V", 31.1443, 121.8083, "115.50", 13, 120),
    ("CAN", "GUANGZHOU VOR/DME", "V", 23.3924, 113.2988, "113.20", 36, 100),
    ("HND", "TOKYO VOR/DME", "V", 35.5494, 139.7798, "115.10", 21, 100),
    ("KIX", "OSAKA VOR/DME", "V", 34.4347, 135.2330, "114.30", 26, 100),
    ("ICN", "SEOUL VOR/DME", "V", 37.4602, 126.4407, "113.90", 23, 100),
    ("HKG", "HONG KONG VOR/DME", "V", 22.3080, 113.9185, "114.50", 28, 100),
    ("SIN", "SINGAPORE VOR/DME", "V", 1.3644, 103.9915, "115.70", 22, 100),
    ("BKK", "BANGKOK VOR/DME", "V", 13.6900, 100.7501, "114.90", 5, 100),
    ("DEL", "DELHI VOR/DME", "V", 28.5562, 77.1000, "112.80", 776, 100),
    ("BOM", "MUMBAI VOR/DME", "V", 19.0896, 72.8656, "113.50", 10, 100),
    ("DXB", "DUBAI VOR/DME", "V", 25.2532, 55.3657, "114.80", 62, 120),
    ("DOH", "DOHA VOR/DME", "V", 25.2731, 51.6080, "113.10", 13, 100),
    ("LHR", "LONDON VOR/DME", "V", 51.4700, -0.4543, "115.30", 83, 100),
    ("CDG", "PARIS VOR/DME", "V", 49.0097, 2.5479, "114.20", 392, 100),
    ("FRA", "FRANKFURT VOR/DME", "V", 50.0379, 8.5622, "114.40", 364, 100),
    ("AMS", "AMSTERDAM VOR/DME", "V", 52.3105, 4.7683, "113.70", -11, 100),
    ("SVO", "MOSCOW VOR/DME", "V", 55.9726, 37.4146, "114.60", 748, 100),
    ("FCO", "ROME VOR/DME", "V", 41.8003, 12.2389, "115.20", 8, 100),
    ("JFK", "NEW YORK VOR/DME", "V", 40.6413, -73.7781, "115.90", 13, 100),
    ("LAX", "LOS ANGELES VOR/DME", "V", 33.9416, -118.4085, "113.60", 126, 100),
    ("ORD", "CHICAGO VOR/DME", "V", 41.9742, -87.9073, "113.40", 668, 100),
    ("SFO", "SAN FRANCISCO VOR/DME", "V", 37.6213, -122.3790, "115.60", 13, 100),
    ("ATL", "ATLANTA VOR/DME", "V", 33.6407, -84.4277, "114.00", 1026, 100),
    ("YVR", "VANCOUVER VOR/DME", "V", 49.1947, -123.1839, "112.90", 13, 100),
    ("YYZ", "TORONTO VOR/DME", "V", 43.6777, -79.6248, "113.30", 569, 100),
    ("SYD", "SYDNEY VOR/DME", "V", -33.9461, 151.1772, "114.10", 21, 100),
    ("MEL", "MELBOURNE VOR/DME", "V", -37.6690, 144.8410, "115.40", 434, 100),
    ("AKL", "AUCKLAND VOR/DME", "V", -37.0082, 174.7850, "113.80", 23, 100),
    ("CAI", "CAIRO VOR/DME", "V", 30.1219, 31.4056, "112.70", 389, 100),
    ("JNB", "JOHANNESBURG VOR/DME", "V", -26.1392, 28.2460, "114.50", 5558, 100),
    ("NBO", "NAIROBI VOR/DME", "V", -1.3192, 36.9278, "113.10", 5327, 100),
    ("GRU", "SAO PAULO VOR/DME", "V", -23.4356, -46.4731, "115.20", 2451, 100),
    ("EZE", "BUENOS AIRES VOR/DME", "V", -34.8222, -58.5358, "114.30", 67, 100),
    ("MEX", "MEXICO CITY VOR/DME", "V", 19.4361, -99.0719, "113.70", 7316, 100),
]

# ============================================================
#  全球主干高空航路网络
#  每条航路: (ident, [(fix_ident, lat, lon), ...])
# ============================================================

AIRWAYS = [
    # 亚洲内部
    ("A593", [
        ("TARGO", 31.50, 103.80), ("GOSOD", 31.00, 103.20),
        ("DUMET", 31.20, 104.50), ("AGNAV", 30.80, 104.80),
        ("IGONO", 30.20, 105.20), ("OMBLI", 29.50, 105.00),
    ]),
    ("B330", [
        ("WX203", 30.90, 104.20), ("WX108", 30.30, 104.60),
        ("OMBLI", 29.50, 105.00), ("SADER", 28.50, 106.00),
        ("KMR", 27.50, 107.00),
    ]),
    ("A461", [
        ("PEK", 40.08, 116.60), ("DALIM", 38.50, 118.00),
        ("TNA", 36.80, 117.50), ("PVG", 31.14, 121.81),
    ]),
    ("A599", [
        ("PVG", 31.14, 121.81), ("NIBOG", 29.00, 123.00),
        ("HND", 35.55, 139.78),
    ]),
    ("R460", [
        ("HND", 35.55, 139.78), ("KIX", 34.43, 135.23),
        ("ICN", 37.46, 126.44),
    ]),
    ("B458", [
        ("HKG", 22.31, 113.92), ("SIN", 1.36, 103.99),
        ("BKK", 13.69, 100.75),
    ]),
    ("W50", [
        ("BATUL", 29.80, 103.50), ("NOPDA", 30.00, 102.80),
        ("GOSOD", 31.00, 103.20),
    ]),
    # 欧亚航路
    ("A326", [
        ("DEL", 28.56, 77.10), ("DXB", 25.25, 55.37),
        ("CAI", 30.12, 31.41),
    ]),
    ("M735", [
        ("DXB", 25.25, 55.37), ("DOH", 25.27, 51.61),
        ("BAH", 26.27, 50.63), ("FRA", 50.04, 8.56),
    ]),
    ("L888", [
        ("FRA", 50.04, 8.56), ("CDG", 49.01, 2.55),
        ("LHR", 51.47, -0.45),
    ]),
    ("B900", [
        ("SVO", 55.97, 37.41), ("FRA", 50.04, 8.56),
        ("AMS", 52.31, 4.77),
    ]),
    # 跨大西洋
    ("NAT-A", [
        ("LHR", 51.47, -0.45), ("BOMRA", 52.00, -20.00),
        ("GANDER", 49.00, -45.00), ("JFK", 40.64, -73.78),
    ]),
    ("NAT-B", [
        ("CDG", 49.01, 2.55), ("MALOT", 50.00, -25.00),
        ("STEPTOE", 47.00, -50.00), ("YYZ", 43.68, -79.62),
    ]),
    # 北美内部
    ("J80", [
        ("JFK", 40.64, -73.78), ("ORD", 41.97, -87.91),
        ("MSP", 44.88, -93.22), ("YVR", 49.19, -123.18),
    ]),
    ("J6", [
        ("LAX", 33.94, -118.41), ("SFO", 37.62, -122.38),
        ("SEA", 47.45, -122.31), ("YVR", 49.19, -123.18),
    ]),
    ("J54", [
        ("ATL", 33.64, -84.43), ("DFW", 32.90, -97.04),
        ("LAX", 33.94, -118.41),
    ]),
    ("J174", [
        ("JFK", 40.64, -73.78), ("ATL", 33.64, -84.43),
        ("MIA", 25.79, -80.29),
    ]),
    # 跨太平洋
    ("PAC-A", [
        ("LAX", 33.94, -118.41), ("HNL", 21.32, -157.92),
        ("MAJ", 7.00, 171.00), ("HND", 35.55, 139.78),
    ]),
    ("PAC-B", [
        ("SFO", 37.62, -122.38), ("HNL", 21.32, -157.92),
        ("GUM", 13.48, 144.80), ("PVG", 31.14, 121.81),
    ]),
    # 大洋洲
    ("A460", [
        ("SYD", -33.95, 151.18), ("MEL", -37.67, 144.84),
        ("AKL", -37.01, 174.79),
    ]),
    ("R590", [
        ("SIN", 1.36, 103.99), ("JKT", -6.13, 106.66),
        ("PER", -31.94, 115.97), ("SYD", -33.95, 151.18),
    ]),
    # 非洲
    ("UY100", [
        ("CAI", 30.12, 31.41), ("JNB", -26.14, 28.25),
        ("NBO", -1.32, 36.93),
    ]),
    # 南美
    ("UW500", [
        ("GRU", -23.44, -46.47), ("EZE", -34.82, -58.54),
        ("SCL", -33.39, -70.79),
    ]),
    ("UM770", [
        ("MEX", 19.44, -99.07), ("GRU", -23.44, -46.47),
    ]),
]

# ============================================================
#  全球主要 FIR 飞行情报区
# ============================================================

FIR_LIST = [
    ("ZJFIR", "CHENGDU FIR", "F", [(33,100),(33,108),(30,110),(27,108),(26,103),(28,99)], 600, 0),
    ("ZBPE", "BEIJING FIR", "F", [(45,110),(45,125),(40,128),(35,125),(35,110),(38,108)], 600, 0),
    ("ZSHA", "SHANGHAI FIR", "F", [(35,118),(35,130),(30,132),(25,128),(25,118),(28,116)], 600, 0),
    ("ZGZU", "GUANGZHOU FIR", "F", [(28,108),(28,120),(22,122),(18,118),(18,108),(22,106)], 600, 0),
    ("RJJT", "TOKYO FIR", "F", [(45,135),(45,150),(35,155),(30,150),(30,135),(35,132)], 600, 0),
    ("VHHK", "HONG KONG FIR", "F", [(25,112),(25,120),(20,122),(15,118),(15,112),(20,110)], 600, 0),
    ("WSJC", "SINGAPORE FIR", "F", [(5,100),(5,110),(0,112),(-5,108),(-5,100),(0,98)], 600, 0),
    ("OMAE", "DUBAI FIR", "F", [(30,50),(30,60),(25,62),(20,58),(20,50),(25,48)], 600, 0),
    ("EGTT", "LONDON FIR", "F", [(60,-10),(60,5),(50,8),(48,2),(48,-10),(52,-12)], 600, 0),
    ("LFEE", "PARIS FIR", "F", [(55,-5),(55,10),(45,12),(42,8),(42,-5),(48,-8)], 600, 0),
    ("EDUU", "FRANKFURT FIR", "F", [(55,5),(55,15),(48,17),(45,12),(45,5),(50,3)], 600, 0),
    ("KZNY", "NEW YORK FIR", "F", [(50,-80),(50,-60),(40,-55),(35,-65),(35,-80),(42,-85)], 600, 0),
    ("KZLA", "LOS ANGELES FIR", "F", [(50,-130),(50,-115),(35,-110),(30,-118),(30,-130),(40,-135)], 600, 0),
    ("KZAU", "CHICAGO FIR", "F", [(50,-100),(50,-80),(40,-75),(35,-85),(35,-100),(42,-105)], 600, 0),
    ("CZQM", "TORONTO FIR", "F", [(70,-100),(70,-60),(50,-55),(45,-70),(45,-100),(55,-110)], 600, 0),
    ("YBBB", "BRISBANE FIR", "F", [(-10,140),(-10,160),(-30,165),(-40,155),(-40,140),(-25,135)], 600, 0),
    ("NZZC", "AUCKLAND FIR", "F", [(-25,160),(-25,180),(-50,180),(-50,160),(-40,155),(-30,158)], 600, 0),
    ("HECC", "CAIRO FIR", "F", [(35,25),(35,40),(25,42),(20,35),(20,25),(28,22)], 600, 0),
    ("FAJO", "JOHANNESBURG FIR", "F", [(-10,15),(-10,35),(-30,40),(-35,30),(-35,15),(-20,10)], 600, 0),
    ("SBAO", "SAO PAULO FIR", "F", [(0,-50),(0,-35),(-25,-30),(-35,-40),(-35,-55),(-15,-60)], 600, 0),
    ("MMFR", "MEXICO FIR", "F", [(30,-105),(30,-85),(15,-80),(10,-95),(10,-110),(20,-115)], 600, 0),
]


# ============================================================
#  记录生成
# ============================================================

def make_record(section, sub, fields: dict, total_len=132) -> str:
    record = [' '] * total_len
    record[0] = 'S'
    if len(section) == 1:
        record[4] = section
    if len(sub) == 1:
        record[5] = sub
    for start, value in fields.items():
        val_str = str(value)
        for i, ch in enumerate(val_str):
            pos = start + i
            if pos < total_len:
                record[pos] = ch
    return ''.join(record)


def gen_airport_records() -> list:
    records = []
    for icao, name, lat, lon, elev, hdg in AIRPORTS:
        rec = make_record('P', 'A', {
            6: icao,
            22: f"{elev:05d}",
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            83: "09800",
            93: pad(name, 30),
        })
        records.append(rec)
    return records


def gen_navaid_records() -> list:
    records = []
    for ident, name, ntype, lat, lon, freq, elev, rng in NAVAIDS:
        rec = make_record('H', ' ', {
            6: pad(ident, 4),
            19: ntype,
            22: freq,
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            64: f"{elev:05d}",
            93: pad(name, 30),
        })
        records.append(rec)
    return records


def gen_airway_records() -> list:
    records = []
    for ident, legs in AIRWAYS:
        for seq, (fix_ident, lat, lon) in enumerate(legs, 1):
            # 计算与上一点的距离和航向
            dist = 0
            out_c = 0
            in_c = 0
            if seq > 1:
                prev_lat, prev_lon = legs[seq-2][1], legs[seq-2][2]
                dist = round(haversine(prev_lat, prev_lon, lat, lon), 1)
                out_c = round(bearing(prev_lat, prev_lon, lat, lon), 1)
                in_c = (out_c + 180) % 360
            rec = make_record('R', ' ', {
                6: pad(ident, 5),
                11: f"{seq:04d}",
                15: pad(fix_ident, 5),
                20: "N",
                21: "H",
                32: lat_to_dms(lat),
                43: lon_to_dms(lon),
                55: f"{out_c:04.1f}",
                59: f"{in_c:04.1f}",
                63: f"{dist:04.1f}",
                73: "07800",
                78: "12500",
            })
            records.append(rec)
    return records


def haversine(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def gen_terminal_procedures() -> list:
    """为每个机场生成 SID + STAR + ILS 进近程序"""
    records = []
    for icao, name, lat, lon, elev, hdg in AIRPORTS:
        # 生成终端航路点
        n_lat, n_lon = offset_coord(lat, lon, 30, 0)    # 北
        s_lat, s_lon = offset_coord(lat, lon, 30, 180)  # 南
        e_lat, e_lon = offset_coord(lat, lon, 30, 90)   # 东
        w_lat, w_lon = offset_coord(lat, lon, 30, 270)  # 西

        iaf_n_lat, iaf_n_lon = offset_coord(lat, lon, 12, 0)
        iaf_s_lat, iaf_s_lon = offset_coord(lat, lon, 12, 180)
        faf_n_lat, faf_n_lon = offset_coord(lat, lon, 6, 0)
        faf_s_lat, faf_s_lon = offset_coord(lat, lon, 6, 180)
        map_n_lat, map_n_lon = offset_coord(lat, lon, 1, 0)
        map_s_lat, map_s_lon = offset_coord(lat, lon, 1, 180)

        twy_points = [
            (f"{icao}N", n_lat, n_lon),
            (f"{icao}S", s_lat, s_lon),
            (f"{icao}E", e_lat, e_lon),
            (f"{icao}W", w_lat, w_lon),
            (f"{icao}IAFN", iaf_n_lat, iaf_n_lon),
            (f"{icao}IAFS", iaf_s_lat, iaf_s_lon),
            (f"{icao}FAFN", faf_n_lat, faf_n_lon),
            (f"{icao}FAFS", faf_s_lat, faf_s_lon),
        ]
        for ident, tlat, tlon in twy_points:
            rec = make_record('E', 'B', {
                6: pad(ident, 5),
                11: icao,
                32: lat_to_dms(tlat),
                43: lon_to_dms(tlon),
            })
            records.append(rec)

        # SID 离场 (向北)
        sid_legs = [
            (1, "IF", icao, lat, lon, 0, elev, 0),
            (2, "CF", f"{icao}N", n_lat, n_lon, 0, 5000, 220),
            (3, "TF", f"{icao}IAFN", iaf_n_lat, iaf_n_lon, 0, 8000, 0),
        ]
        for seq, leg_t, fix, flat, flon, out_c, alt, spd in sid_legs:
            rec = make_record('T', 'D', {
                6: icao,
                10: pad(f"{icao}1D", 5),
                15: pad(f"{icao}N", 4),
                19: f"{seq:03d}",
                22: pad(leg_t, 2),
                24: pad(fix, 5),
                32: lat_to_dms(flat),
                43: lon_to_dms(flon),
                55: f"{out_c:04.1f}",
                69: f"{alt:05d}",
                79: f"{spd:03d}",
            })
            records.append(rec)

        # STAR 进场 (从北)
        star_legs = [
            (1, "IF", f"{icao}N", n_lat, n_lon, 0, 12500, 0),
            (2, "TF", f"{icao}IAFN", iaf_n_lat, iaf_n_lon, 180, 10000, 0),
            (3, "CF", f"{icao}FAFN", faf_n_lat, faf_n_lon, 180, 6000, 250),
            (4, "TF", icao, lat, lon, 180, 4000, 220),
        ]
        for seq, leg_t, fix, flat, flon, out_c, alt, spd in star_legs:
            rec = make_record('T', 'E', {
                6: icao,
                10: pad(f"{icao}1A", 5),
                15: pad(f"{icao}N", 4),
                19: f"{seq:03d}",
                22: pad(leg_t, 2),
                24: pad(fix, 5),
                32: lat_to_dms(flat),
                43: lon_to_dms(flon),
                55: f"{out_c:04.1f}",
                69: f"{alt:05d}",
                79: f"{spd:03d}",
            })
            records.append(rec)

        # ILS 进近 (向北跑道 36)
        app_legs = [
            (1, "IF", f"{icao}IAFN", iaf_n_lat, iaf_n_lon, 0, 4000, 220),
            (2, "CF", f"{icao}FAFN", faf_n_lat, faf_n_lon, 180, 3000, 180),
            (3, "FA", icao, lat, lon, 180, elev, 0),
            (4, "CA", icao, lat, lon, 180, elev, 0),
            (5, "TF", f"{icao}N", n_lat, n_lon, 0, 5000, 0),
        ]
        for seq, leg_t, fix, flat, flon, out_c, alt, spd in app_legs:
            rec = make_record('T', 'F', {
                6: icao,
                10: pad("ILS36", 5),
                15: pad("    ", 4),
                19: f"{seq:03d}",
                22: pad(leg_t, 2),
                24: pad(fix, 5),
                32: lat_to_dms(flat),
                43: lon_to_dms(flon),
                55: f"{out_c:04.1f}",
                69: f"{alt:05d}",
                79: f"{spd:03d}",
            })
            records.append(rec)

    return records


def gen_enroute_waypoints() -> list:
    """从航路中提取所有航路点，生成航路点记录"""
    records = []
    seen = set()
    for ident, legs in AIRWAYS:
        for fix_ident, lat, lon in legs:
            if fix_ident in seen:
                continue
            seen.add(fix_ident)
            # 跳过机场名作为航路点的情况
            is_airport = any(a[0] == fix_ident for a in AIRPORTS)
            if is_airport:
                continue
            rec = make_record('D', 'B', {
                6: pad(fix_ident, 5),
                11: "ZZ",
                19: "E",
                32: lat_to_dms(lat),
                43: lon_to_dms(lon),
            })
            records.append(rec)
    return records


def gen_airspace_records() -> list:
    records = []
    for ident, name, atype, points, upper, lower in FIR_LIST:
        for seq, (lat, lon) in enumerate(points, 1):
            rec = make_record('U', ' ', {
                6: pad(ident, 4),
                10: atype,
                11: pad(name, 20),
                31: f"{seq:03d}",
                34: lat_to_dms(lat),
                45: lon_to_dms(lon),
                63: f"{upper:05d}",
                68: f"{lower:05d}",
            })
            records.append(rec)

    # 为前10个机场生成 CTR 终端管制区
    for i, (icao, name, lat, lon, elev, hdg) in enumerate(AIRPORTS[:10]):
        ctr_points = []
        for angle in range(0, 360, 45):
            clat, clon = offset_coord(lat, lon, 25, angle)
            ctr_points.append((clat, clon))
        for seq, (clat, clon) in enumerate(ctr_points, 1):
            rec = make_record('U', ' ', {
                6: pad(f"{icao}T", 4),
                10: "T",
                11: pad(f"{icao} CTR", 20),
                31: f"{seq:03d}",
                34: lat_to_dms(clat),
                45: lon_to_dms(clon),
                63: "01000",
                68: "00000",
            })
            records.append(rec)

    return records


# ============================================================
#  主函数
# ============================================================

def main():
    all_records = []
    all_records.extend(gen_airport_records())
    all_records.extend(gen_navaid_records())
    all_records.extend(gen_enroute_waypoints())
    all_records.extend(gen_airway_records())
    all_records.extend(gen_terminal_procedures())
    all_records.extend(gen_airspace_records())

    output_path = r"D:\AAA CHART\navchart-poc\data\global_sample.dat"
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in all_records:
            f.write(rec + '\n')

    # 统计
    airport_count = len(AIRPORTS)
    navaid_count = len(NAVAIDS)
    airway_count = len(AIRWAYS)
    fir_count = len(FIR_LIST)
    ctr_count = 10

    # 统计航路点
    wp_set = set()
    for ident, legs in AIRWAYS:
        for fix_ident, lat, lon in legs:
            if not any(a[0] == fix_ident for a in AIRPORTS):
                wp_set.add(fix_ident)

    print(f"[全球数据生成] 完成")
    print(f"  输出文件: {output_path}")
    print(f"  总记录数: {len(all_records)}")
    print(f"  机场: {airport_count} (六大洲)")
    print(f"  导航台: {navaid_count}")
    print(f"  航路点: {len(wp_set)}")
    print(f"  高空航路: {airway_count} 条")
    print(f"  终端程序: {airport_count * 3} 套 (每机场 SID+STAR+ILS)")
    print(f"  空域: {fir_count} FIR + {ctr_count} CTR")
    print(f"\n  注意: 这是合成数据，仅用于技术验证，不可用于真实飞行。")


if __name__ == '__main__':
    main()
