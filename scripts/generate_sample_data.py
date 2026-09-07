"""
模拟 ARINC 424 数据生成器 (POC 验证用)

生成基于成都双流机场 (ZUUU) 周边的合成导航数据，包含:
  - 机场参考点 (P-A)
  - 航路点 (D-B / E-B)
  - 导航台 (H)
  - 航路 (R)
  - SID 离场程序 (T-D)
  - STAR 进场程序 (T-E)
  - ILS 进近程序 (T-F)
  - 管制空域 (U)

注意: 这是合成数据，仅用于技术验证，不可用于真实飞行。
坐标基于真实地理位置的合理推算。
"""

import math
import random

random.seed(42)  # 固定种子保证可复现


# ============================================================
#  坐标工具
# ============================================================

def lat_to_dms(lat: float) -> str:
    """十进制度 -> ARINC 424 纬度格式 N/S DDMMSS.ss"""
    hemi = 'N' if lat >= 0 else 'S'
    lat = abs(lat)
    deg = int(lat)
    minute = int((lat - deg) * 60)
    sec = ((lat - deg) * 60 - minute) * 60
    return f"{hemi}{deg:02d}{minute:02d}{sec:05.2f}"


def lon_to_dms(lon: float) -> str:
    """十进制度 -> ARINC 424 经度格式 E/W DDDMMSS.ss"""
    hemi = 'E' if lon >= 0 else 'W'
    lon = abs(lon)
    deg = int(lon)
    minute = int((lon - deg) * 60)
    sec = ((lon - deg) * 60 - minute) * 60
    return f"{hemi}{deg:03d}{minute:02d}{sec:05.2f}"


def offset_coord(lat, lon, d_nm, bearing_deg):
    """从某点按方位角和距离(海里)偏移"""
    R = 3440.065
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    d = d_nm / R
    lat2 = math.asin(math.sin(lat1) * math.cos(d) +
                      math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1),
                              math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def pad(s, width):
    return str(s).ljust(width)[:width]


# ============================================================
#  基础地理数据 (成都双流 ZUUU 周边)
# ============================================================

ZUUU_LAT = 30.5785
ZUUU_LON = 103.9470
ZUUU_ELEV = 1625  # ft

# 真实导航台 (成都区域)
NAVAIDS = [
    # ident, name, type, lat, lon, freq, elev, range
    ("CTU", "CHENGDU VOR/DME", "V", 30.5785, 103.9470, "114.70", 1625, 100),
    ("MIG", "MIANZHU VOR/DME", "V", 31.4500, 104.1500, "115.30", 2200, 80),
    ("YIN", "YIBIN VOR/DME", "V", 28.7500, 104.5500, "113.80", 1200, 90),
    ("LIA", "LIANGSHAN VOR", "V", 27.9000, 102.2500, "112.50", 5000, 80),
    ("NQZ", "NANCHONG NDB", "N", 30.8500, 106.1000, "355.0", 1200, 50),
]

# 航路点 (成都区域主要报告点)
WAYPOINTS = [
    # ident, lat, lon, region, usage
    ("DUMET", 31.2000, 104.5000, "ZJ", "E"),
    ("AGNAV", 30.8000, 104.8000, "ZJ", "E"),
    ("IGONO", 30.2000, 105.2000, "ZJ", "E"),
    ("OMBLI", 29.5000, 105.0000, "ZJ", "E"),
    ("BATUL", 29.8000, 103.5000, "ZJ", "E"),
    ("NOPDA", 30.0000, 102.8000, "ZJ", "E"),
    ("GOSOD", 31.0000, 103.2000, "ZJ", "E"),
    ("TARGO", 31.5000, 103.8000, "ZJ", "E"),
    ("WX203", 30.9000, 104.2000, "ZJ", "E"),
    ("WX108", 30.3000, 104.6000, "ZJ", "E"),
]

# 终端航路点 (ZUUU 进场/离场点)
TERMINAL_WAYPOINTS = [
    # ident, icao, lat, lon
    ("P281", "ZUUU", 30.8500, 103.9470),  # 北进场
    ("P282", "ZUUU", 30.3000, 103.9470),  # 南进场
    ("P283", "ZUUU", 30.5785, 104.4000),  # 东进场
    ("P284", "ZUUU", 30.5785, 103.5000),  # 西进场
    ("IM02R", "ZUUU", 30.6500, 103.9470),  # 02R 起始进近
    ("IM20L", "ZUUU", 30.5000, 103.9470),  # 20L 起始进近
    ("FAF02R", "ZUUU", 30.6200, 103.9470),  # 02R 最后进近点
    ("FAF20L", "ZUUU", 30.5300, 103.9470),  # 20L 最后进近点
    ("MAP02R", "ZUUU", 30.5850, 103.9470),  # 02R 复飞点
    ("MAP20L", "ZUUU", 30.5720, 103.9470),  # 20L 复飞点
]

# 航路定义 (高空航路)
AIRWAYS = [
    # ident, type, direction, [(fix_ident, lat, lon, seq, out_course, in_course, dist, min_alt, max_alt)]
    ("A593", "H", "N", [
        ("TARGO", 31.5000, 103.8000, 1, 180, 0, 35, 7800, 12500),
        ("GOSOD", 31.0000, 103.2000, 2, 135, 315, 42, 7800, 12500),
        ("DUMET", 31.2000, 104.5000, 3, 180, 0, 38, 7800, 12500),
        ("AGNAV", 30.8000, 104.8000, 4, 180, 0, 36, 7800, 12500),
        ("IGONO", 30.2000, 105.2000, 5, 225, 45, 40, 7800, 12500),
    ]),
    ("B330", "H", "N", [
        ("WX203", 30.9000, 104.2000, 1, 180, 0, 25, 7200, 12500),
        ("WX108", 30.3000, 104.6000, 2, 225, 45, 30, 7200, 12500),
        ("OMBLI", 29.5000, 105.0000, 3, 225, 45, 45, 7200, 12500),
    ]),
    ("W50", "L", "N", [
        ("BATUL", 29.8000, 103.5000, 1, 0, 180, 50, 3000, 6000),
        ("NOPDA", 30.0000, 102.8000, 2, 45, 225, 40, 3000, 6000),
        ("GOSOD", 31.0000, 103.2000, 3, 90, 270, 55, 3000, 6000),
    ]),
]


# ============================================================
#  记录生成器
# ============================================================

def make_record(section, sub, fields: dict, total_len=132) -> str:
    """
    构造一条 ARINC 424 记录 (固定宽度 132 字符)

    标准字段位置:
      0-4:   Record Type (S=Standard)
      4-5:   Section Code
      5-6:   Subsection Code
      6-...: 各类型特定字段
    """
    record = [' '] * total_len

    # Record Type
    record[0] = 'S'
    # Section Code
    if len(section) == 1:
        record[4] = section
    # Subsection Code
    if len(sub) == 1:
        record[5] = sub

    # 写入各字段
    for start, value in fields.items():
        val_str = str(value)
        for i, ch in enumerate(val_str):
            pos = start + i
            if pos < total_len:
                record[pos] = ch

    return ''.join(record)


def gen_airport_records() -> list:
    """生成机场参考点记录 (P-A)"""
    records = []
    # ZUUU 成都双流
    rec = make_record('P', 'A', {
        6: "ZUUU",           # Airport ICAO
        22: f"{ZUUU_ELEV:05d}",  # Elevation
        32: lat_to_dms(ZUUU_LAT),
        43: lon_to_dms(ZUUU_LON),
        83: "09800",         # Transition Altitude
        93: pad("CHENGDU SHUANGLIU INTL", 30),
    })
    records.append(rec)

    # ZUCK 重庆江北 (邻近机场)
    rec = make_record('P', 'A', {
        6: "ZUCK",
        22: "01350",
        32: lat_to_dms(29.7192),
        43: lon_to_dms(106.6417),
        83: "09800",
        93: pad("CHONGQING JIANGBEI INTL", 30),
    })
    records.append(rec)

    # ZLXY 西安咸阳
    rec = make_record('P', 'A', {
        6: "ZLXY",
        22: "01572",
        32: lat_to_dms(34.4471),
        43: lon_to_dms(108.7516),
        83: "09800",
        93: pad("XI AN XIANYANG INTL", 30),
    })
    records.append(rec)

    return records


def gen_waypoint_records() -> list:
    """生成航路点记录 (D-B)"""
    records = []
    for ident, lat, lon, region, usage in WAYPOINTS:
        rec = make_record('D', 'B', {
            6: pad(ident, 5),
            11: region,
            19: usage,
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
        })
        records.append(rec)
    return records


def gen_terminal_waypoint_records() -> list:
    """生成终端航路点记录 (E-B)"""
    records = []
    for ident, icao, lat, lon in TERMINAL_WAYPOINTS:
        rec = make_record('E', 'B', {
            6: pad(ident, 5),
            11: icao,
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
        })
        records.append(rec)
    return records


def gen_navaid_records() -> list:
    """生成导航台记录 (H)"""
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
    """生成航路记录 (R)"""
    records = []
    for ident, atype, direction, legs in AIRWAYS:
        for fix_ident, lat, lon, seq, out_c, in_c, dist, min_a, max_a in legs:
            rec = make_record('R', ' ', {
                6: pad(ident, 5),
                11: f"{seq:04d}",
                15: pad(fix_ident, 5),
                20: direction,
                21: atype,
                32: lat_to_dms(lat),
                43: lon_to_dms(lon),
                55: f"{out_c:04.1f}",
                59: f"{in_c:04.1f}",
                63: f"{dist:04.1f}",
                73: f"{min_a:05d}",
                78: f"{max_a:05d}",
            })
            records.append(rec)
    return records


def gen_sid_records() -> list:
    """生成 SID 离场程序记录 (T-D)"""
    records = []

    # SID: CTU2D - 成都双流 02R 跑道标准仪表离场
    sid_legs = [
        # seq, leg_type, fix_ident, lat, lon, rec_navaid, out_course, turn, alt, alt2, speed, center, rnp
        (1, "IF", "CTU", ZUUU_LAT, ZUUU_LON, "", 0, "", 1625, 0, 0, "", 0),
        (2, "CF", "P281", 30.8500, 103.9470, "CTU", 0, "", 5000, 0, 220, "", 0),
        (3, "TF", "DUMET", 31.2000, 104.5000, "", 45, "", 8000, 0, 0, "", 0),
        (4, "TF", "AGNAV", 30.8000, 104.8000, "", 135, "", 10000, 0, 0, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in sid_legs:
        rec_line = make_record('T', 'D', {
            6: "ZUUU",
            10: pad("CTU2D", 5),
            15: pad("DUMET", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            62: pad(center, 5),
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
            87: f"{rnp:03d}",
        })
        records.append(rec_line)

    # SID: BATU1D - 向西离场
    sid2_legs = [
        (1, "IF", "CTU", ZUUU_LAT, ZUUU_LON, "", 0, "", 1625, 0, 0, "", 0),
        (2, "CF", "P284", 30.5785, 103.5000, "CTU", 270, "", 5000, 0, 220, "", 0),
        (3, "TF", "BATUL", 29.8000, 103.5000, "", 180, "", 8000, 0, 0, "", 0),
        (4, "TF", "NOPDA", 30.0000, 102.8000, "", 270, "", 10000, 0, 0, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in sid2_legs:
        rec_line = make_record('T', 'D', {
            6: "ZUUU",
            10: pad("BATU1D", 5),
            15: pad("BATUL", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
        })
        records.append(rec_line)

    return records


def gen_star_records() -> list:
    """生成 STAR 进场程序记录 (T-E)"""
    records = []

    # STAR: DUMET1A - 从 DUMET 进场
    star_legs = [
        (1, "IF", "DUMET", 31.2000, 104.5000, "", 0, "", 12500, 0, 0, "", 0),
        (2, "TF", "AGNAV", 30.8000, 104.8000, "", 180, "", 10000, 0, 0, "", 0),
        (3, "TF", "WX203", 30.9000, 104.2000, "", 270, "", 8000, 0, 0, "", 0),
        (4, "CF", "P281", 30.8500, 103.9470, "CTU", 225, "", 6000, 0, 250, "", 0),
        (5, "TF", "IM02R", 30.6500, 103.9470, "", 180, "", 4000, 0, 220, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in star_legs:
        rec_line = make_record('T', 'E', {
            6: "ZUUU",
            10: pad("DUM1A", 5),
            15: pad("DUMET", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
        })
        records.append(rec_line)

    # STAR: BATUL1B - 从 BATUL 进场
    star2_legs = [
        (1, "IF", "BATUL", 29.8000, 103.5000, "", 0, "", 12500, 0, 0, "", 0),
        (2, "TF", "NOPDA", 30.0000, 102.8000, "", 0, "", 10000, 0, 0, "", 0),
        (3, "CF", "P282", 30.3000, 103.9470, "CTU", 45, "", 6000, 0, 250, "", 0),
        (4, "TF", "IM20L", 30.5000, 103.9470, "", 0, "", 4000, 0, 220, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in star2_legs:
        rec_line = make_record('T', 'E', {
            6: "ZUUU",
            10: pad("BAT1B", 5),
            15: pad("BATUL", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
        })
        records.append(rec_line)

    return records


def gen_approach_records() -> list:
    """生成进近程序记录 (T-F)"""
    records = []

    # ILS 02R 进近
    app_legs = [
        (1, "IF", "IM02R", 30.6500, 103.9470, "", 0, "", 4000, 0, 220, "", 0),
        (2, "CF", "FAF02R", 30.6200, 103.9470, "CTU", 180, "", 3000, 0, 180, "", 0),
        (3, "FA", "MAP02R", 30.5850, 103.9470, "CTU", 180, "", 1625, 0, 0, "", 0),
        (4, "CA", "MAP02R", 30.5850, 103.9470, "CTU", 180, "", 1625, 0, 0, "", 0),
        (5, "TF", "P281", 30.8500, 103.9470, "", 0, "", 5000, 0, 0, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in app_legs:
        rec_line = make_record('T', 'F', {
            6: "ZUUU",
            10: pad("ILS02R", 5),
            15: pad("    ", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
        })
        records.append(rec_line)

    # ILS 20L 进近
    app2_legs = [
        (1, "IF", "IM20L", 30.5000, 103.9470, "", 0, "", 4000, 0, 220, "", 0),
        (2, "CF", "FAF20L", 30.5300, 103.9470, "CTU", 0, "", 3000, 0, 180, "", 0),
        (3, "FA", "MAP20L", 30.5720, 103.9470, "CTU", 0, "", 1625, 0, 0, "", 0),
        (4, "CA", "MAP20L", 30.5720, 103.9470, "CTU", 0, "", 1625, 0, 0, "", 0),
        (5, "TF", "P282", 30.3000, 103.9470, "", 180, "", 5000, 0, 0, "", 0),
    ]
    for seq, leg_t, fix, lat, lon, rec, out_c, turn, alt, alt2, spd, center, rnp in app2_legs:
        rec_line = make_record('T', 'F', {
            6: "ZUUU",
            10: pad("ILS20L", 5),
            15: pad("    ", 4),
            19: f"{seq:03d}",
            22: pad(leg_t, 2),
            24: pad(fix, 5),
            29: pad(rec, 3),
            32: lat_to_dms(lat),
            43: lon_to_dms(lon),
            55: f"{out_c:04.1f}",
            59: turn,
            69: f"{alt:05d}",
            74: f"{alt2:05d}",
            79: f"{spd:03d}",
        })
        records.append(rec_line)

    return records


def gen_airspace_records() -> list:
    """生成空域记录 (U)"""
    records = []

    # ZUUU 终端管制区 (TMA) - 圆形多边形近似
    tma_center_lat = ZUUU_LAT
    tma_center_lon = ZUUU_LON
    tma_radius_nm = 40  # 半径40海里
    tma_points = []
    for i in range(12):
        bearing = i * 30
        lat, lon = offset_coord(tma_center_lat, tma_center_lon, tma_radius_nm, bearing)
        tma_points.append((lat, lon))

    for seq, (lat, lon) in enumerate(tma_points, 1):
        rec = make_record('U', ' ', {
            6: pad("ZUUUTMA", 4),
            10: "T",
            11: pad("CHENGDU TMA", 20),
            31: f"{seq:03d}",
            34: lat_to_dms(lat),
            45: lon_to_dms(lon),
            63: "01000",  # upper limit FL100
            68: "00000",  # lower limit SFC
        })
        records.append(rec)

    # 成都飞行情报区 (FIR) - 大致范围
    fir_points = [
        (33.0, 100.0), (33.0, 108.0), (30.0, 110.0),
        (27.0, 108.0), (26.0, 103.0), (28.0, 99.0),
    ]
    for seq, (lat, lon) in enumerate(fir_points, 1):
        rec = make_record('U', ' ', {
            6: pad("ZJFIR", 4),
            10: "F",
            11: pad("CHENGDU FIR", 20),
            31: f"{seq:03d}",
            34: lat_to_dms(lat),
            45: lon_to_dms(lon),
            63: "06000",  # FL600
            68: "00000",
        })
        records.append(rec)

    # 限制区 (Restricted)
    restr_points = [
        (31.0, 104.0), (31.5, 104.5), (31.2, 105.0), (30.8, 104.8),
    ]
    for seq, (lat, lon) in enumerate(restr_points, 1):
        rec = make_record('U', ' ', {
            6: pad("R201", 4),
            10: "R",
            11: pad("RESTRICTED AREA 201", 20),
            31: f"{seq:03d}",
            34: lat_to_dms(lat),
            45: lon_to_dms(lon),
            63: "02000",
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
    all_records.extend(gen_waypoint_records())
    all_records.extend(gen_terminal_waypoint_records())
    all_records.extend(gen_navaid_records())
    all_records.extend(gen_airway_records())
    all_records.extend(gen_sid_records())
    all_records.extend(gen_star_records())
    all_records.extend(gen_approach_records())
    all_records.extend(gen_airspace_records())

    output_path = r"D:\AAA CHART\navchart-poc\data\zuuu_sample.dat"
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in all_records:
            f.write(rec + '\n')

    print(f"[数据生成] 完成")
    print(f"  输出文件: {output_path}")
    print(f"  总记录数: {len(all_records)}")
    print(f"  机场: 3 (ZUUU, ZUCK, ZLXY)")
    print(f"  航路点: {len(WAYPOINTS)} 航路 + {len(TERMINAL_WAYPOINTS)} 终端")
    print(f"  导航台: {len(NAVAIDS)}")
    print(f"  航路: {len(AIRWAYS)} (A593, B330, W50)")
    print(f"  SID: 2 (CTU2D, BATU1D)")
    print(f"  STAR: 2 (DUM1A, BAT1B)")
    print(f"  进近: 2 (ILS02R, ILS20L)")
    print(f"  空域: 3 (TMA, FIR, R201)")
    print(f"\n  注意: 这是合成数据，仅用于技术验证，不可用于真实飞行。")


if __name__ == '__main__':
    main()
