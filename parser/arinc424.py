"""
ARINC 424 导航数据解析器 (POC 版本)
支持解析标准 ARINC 424 固定宽度格式，输出结构化 GeoJSON。

支持的记录类型:
  - P  机场 (Airport / Heliport)
  - D  航路点 (Enroute Waypoint)
  - E  终端航路点 (Terminal Waypoint)
  - H  导航台 (Enroute Navaid)
  - I  终端导航台 (Terminal Navaid)
  - R  航路 (Airway / Route)
  - T  终端程序 (SID / STAR / Approach)
  - U  空域 (Controlled / Restricted Airspace)

参考: ARINC 424-22 Specification
"""

import json
import math
from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
#  坐标工具
# ============================================================

def parse_dms_lat(raw: str) -> Optional[float]:
    """解析 ARINC 424 纬度格式: N/S DDMMSS.ss (11字符)"""
    raw = raw.strip()
    if len(raw) < 9 or not raw:
        return None
    try:
        hemi = raw[0]
        deg = int(raw[1:3])
        minute = int(raw[3:5])
        sec = float(raw[5:])
        val = deg + minute / 60.0 + sec / 3600.0
        return -val if hemi == 'S' else val
    except (ValueError, IndexError):
        return None


def parse_dms_lon(raw: str) -> Optional[float]:
    """解析 ARINC 424 经度格式: E/W DDDMMSS.ss (12字符)"""
    raw = raw.strip()
    if len(raw) < 10 or not raw:
        return None
    try:
        hemi = raw[0]
        deg = int(raw[1:4])
        minute = int(raw[4:6])
        sec = float(raw[6:])
        val = deg + minute / 60.0 + sec / 3600.0
        return -val if hemi == 'W' else val
    except (ValueError, IndexError):
        return None


def haversine(lat1, lon1, lat2, lon2):
    """两点间大圆距离 (海里)"""
    R = 3440.065  # Earth radius in nautical miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ============================================================
#  数据类
# ============================================================

@dataclass
class Airport:
    icao: str
    name: str = ""
    lat: float = 0.0
    lon: float = 0.0
    elevation: int = 0  # feet
    transition_alt: int = 0
    speed_limit: int = 0
    speed_limit_alt: int = 0
    ifr_capability: str = ""
    runway_count: int = 0


@dataclass
class Waypoint:
    ident: str
    lat: float
    lon: float
    region: str = ""
    usage: str = ""  # E=Enroute, T=Terminal, B=Both
    magnetic_variation: float = 0.0


@dataclass
class Navaid:
    ident: str
    name: str
    type: str  # VOR, DME, NDB, VORDME, ILS, etc.
    lat: float
    lon: float
    frequency: str = ""
    elevation: int = 0
    range: int = 0  # NM
    magnetic_variation: float = 0.0


@dataclass
class Airway:
    ident: str
    type: str  # H=High, L=Low
    direction: str  # F=Forward, B=Backward, N=Both
    fix_ident: str
    fix_lat: float
    fix_lon: float
    seq_number: int = 0
    outbound_course: float = 0.0
    inbound_course: float = 0.0
    distance: float = 0.0  # NM
    min_altitude: int = 0
    max_altitude: int = 0


@dataclass
class ProcedureLeg:
    """终端程序航段 (SID/STAR/Approach)"""
    type: str  # SID, STAR, APPROACH
    proc_ident: str
    transition: str = ""
    seq: int = 0
    leg_type: str = ""  # IF, TF, DF, CF, FA, FC, FD, FM, VA, VD, VI, VM, VR, CI, CR, RF, PI, HA, HF, HM
    fix_ident: str = ""
    fix_lat: float = 0.0
    fix_lon: float = 0.0
    recommended_navaid: str = ""
    arc_radius: float = 0.0
    theta: float = 0.0  # magnetic bearing
    rho: float = 0.0    # distance NM
    outbound_course: float = 0.0
    inbound_course: float = 0.0
    turn_direction: str = ""  # L/R
    altitude: int = 0
    altitude2: int = 0
    speed_limit: int = 0
    vertical_angle: float = 0.0
    center_fix: str = ""
    rnp: float = 0.0


@dataclass
class Airspace:
    ident: str
    type: str  # A=Class A, B=Class B, C=Class C, D=Class D, E=Class E, G=Class G, R=Restricted, D=Danger, P=Prohibited, T=CTR, F=FIR
    name: str = ""
    boundary_points: list = field(default_factory=list)  # [(lat, lon), ...]
    upper_limit: int = 0
    lower_limit: int = 0
    upper_unit: str = "FL"
    lower_unit: str = "FT"


# ============================================================
#  ARINC 424 主解析器
# ============================================================

class ARINC424Parser:
    """ARINC 424 固定宽度格式解析器"""

    def __init__(self):
        self.airports: dict[str, Airport] = {}
        self.waypoints: dict[str, Waypoint] = {}
        self.navaids: dict[str, Navaid] = {}
        self.airways: list[Airway] = []
        self.procedures: list[ProcedureLeg] = []
        self.airspaces: list[Airspace] = []
        self.raw_records: list[str] = []

    def parse_file(self, filepath: str) -> None:
        """解析 ARINC 424 数据文件"""
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n\r')
                if len(line) < 6:
                    continue
                self.raw_records.append(line)
                self._dispatch(line)

    def _dispatch(self, line: str) -> None:
        """根据 Section Code 分发到对应解析器"""
        section_code = line[4:5] if len(line) > 4 else ''
        sub_code = line[5:6] if len(line) > 5 else ''

        handlers = {
            'P': self._parse_airport,
            'D': self._parse_waypoint,
            'E': self._parse_terminal_waypoint,
            'H': self._parse_navaid,
            'I': self._parse_terminal_navaid,
            'R': self._parse_airway,
            'T': self._parse_procedure,
            'U': self._parse_airspace,
        }
        handler = handlers.get(section_code)
        if handler:
            try:
                handler(line, sub_code)
            except Exception as e:
                pass  # POC: skip malformed records

    # --- 机场 (P) ---
    def _parse_airport(self, line: str, sub: str) -> None:
        if sub == 'A':  # Airport Reference Point
            icao = line[6:10].strip()
            if not icao:
                return
            lat = parse_dms_lat(line[32:43])
            lon = parse_dms_lon(line[43:55])
            elev = 0
            try:
                elev = int(line[22:27].strip() or 0)
            except ValueError:
                pass
            name = line[93:123].strip()
            ta = 0
            try:
                ta = int(line[83:88].strip() or 0)
            except ValueError:
                pass

            ap = self.airports.get(icao, Airport(icao=icao))
            ap.icao = icao
            ap.name = name or ap.name
            if lat is not None:
                ap.lat = lat
            if lon is not None:
                ap.lon = lon
            ap.elevation = elev or ap.elevation
            ap.transition_alt = ta or ap.transition_alt
            self.airports[icao] = ap

    # --- 航路点 (D) ---
    def _parse_waypoint(self, line: str, sub: str) -> None:
        if sub == 'B':  # Waypoint
            ident = line[6:11].strip()
            if not ident:
                return
            lat = parse_dms_lat(line[32:43])
            lon = parse_dms_lon(line[43:55])
            region = line[11:13].strip()
            usage = line[19:20].strip()
            if lat is None or lon is None:
                return
            self.waypoints[ident] = Waypoint(
                ident=ident, lat=lat, lon=lon,
                region=region, usage=usage or 'E'
            )

    def _parse_terminal_waypoint(self, line: str, sub: str) -> None:
        if sub == 'B':
            ident = line[6:11].strip()
            icao = line[11:15].strip()
            if not ident:
                return
            lat = parse_dms_lat(line[32:43])
            lon = parse_dms_lon(line[43:55])
            if lat is None or lon is None:
                return
            key = f"{icao}.{ident}" if icao else ident
            self.waypoints[key] = Waypoint(
                ident=ident, lat=lat, lon=lon,
                region=icao, usage='T'
            )

    # --- 导航台 (H/I) ---
    def _parse_navaid(self, line: str, sub: str) -> None:
        if sub == ' ':
            ident = line[6:10].strip()
            if not ident:
                return
            lat = parse_dms_lat(line[32:43])
            lon = parse_dms_lon(line[43:55])
            name = line[93:123].strip()
            freq = line[22:27].strip()
            ntype = line[19:20].strip()
            elev = 0
            try:
                elev = int(line[64:69].strip() or 0)
            except ValueError:
                pass
            if lat is None or lon is None:
                return
            self.navaids[ident] = Navaid(
                ident=ident, name=name, type=ntype or 'VOR',
                lat=lat, lon=lon, frequency=freq, elevation=elev
            )

    def _parse_terminal_navaid(self, line: str, sub: str) -> None:
        self._parse_navaid(line, sub)

    # --- 航路 (R) ---
    def _parse_airway(self, line: str, sub: str) -> None:
        if sub == ' ':
            ident = line[6:11].strip()
            if not ident:
                return
            seq = 0
            try:
                seq = int(line[11:15].strip() or 0)
            except ValueError:
                pass
            fix_ident = line[15:20].strip()
            lat = parse_dms_lat(line[32:43])
            lon = parse_dms_lon(line[43:55])
            direction = line[20:21].strip() or 'N'
            rtype = line[21:22].strip() or 'L'
            out_course = 0.0
            try:
                out_course = float(line[55:59].strip() or 0)
            except ValueError:
                pass
            in_course = 0.0
            try:
                in_course = float(line[59:63].strip() or 0)
            except ValueError:
                pass
            dist = 0.0
            try:
                dist = float(line[63:67].strip() or 0)
            except ValueError:
                pass
            min_alt = 0
            try:
                min_alt = int(line[73:78].strip() or 0)
            except ValueError:
                pass
            max_alt = 0
            try:
                max_alt = int(line[78:83].strip() or 0)
            except ValueError:
                pass

            if lat is None or lon is None:
                return
            self.airways.append(Airway(
                ident=ident, type=rtype, direction=direction,
                fix_ident=fix_ident, fix_lat=lat, fix_lon=lon,
                seq_number=seq, outbound_course=out_course,
                inbound_course=in_course, distance=dist,
                min_altitude=min_alt, max_altitude=max_alt
            ))

    # --- 终端程序 (T) ---
    def _parse_procedure(self, line: str, sub: str) -> None:
        """解析 SID/STAR/进近程序航段"""
        proc_type_map = {'D': 'SID', 'E': 'STAR', 'F': 'APPROACH'}
        if sub not in proc_type_map:
            return
        proc_type = proc_type_map[sub]

        icao = line[6:10].strip()
        proc_ident = line[10:15].strip()
        transition = line[15:19].strip()
        seq = 0
        try:
            seq = int(line[19:22].strip() or 0)
        except ValueError:
            pass
        leg_type = line[22:24].strip()
        fix_ident = line[24:29].strip()
        lat = parse_dms_lat(line[32:43])
        lon = parse_dms_lon(line[43:55])
        rec_navaid = line[29:32].strip()
        out_course = 0.0
        try:
            out_course = float(line[55:59].strip() or 0)
        except ValueError:
            pass
        turn = line[59:60].strip()
        alt = 0
        try:
            alt = int(line[69:74].strip() or 0)
        except ValueError:
            pass
        alt2 = 0
        try:
            alt2 = int(line[74:79].strip() or 0)
        except ValueError:
            pass
        speed = 0
        try:
            speed = int(line[79:82].strip() or 0)
        except ValueError:
            pass
        center_fix = line[62:67].strip()
        rnp = 0.0
        try:
            rnp = float(line[87:90].strip() or 0) / 10.0
        except ValueError:
            pass

        if lat is None or lon is None:
            lat, lon = 0.0, 0.0

        self.procedures.append(ProcedureLeg(
            type=proc_type, proc_ident=proc_ident,
            transition=transition, seq=seq, leg_type=leg_type,
            fix_ident=fix_ident, fix_lat=lat, fix_lon=lon,
            recommended_navaid=rec_navaid,
            outbound_course=out_course, turn_direction=turn,
            altitude=alt, altitude2=alt2, speed_limit=speed,
            center_fix=center_fix, rnp=rnp
        ))

    # --- 空域 (U) ---
    def _parse_airspace(self, line: str, sub: str) -> None:
        if sub == ' ':
            ident = line[6:10].strip()
            if not ident:
                return
            atype = line[10:11].strip()
            name = line[11:31].strip()
            seq = 0
            try:
                seq = int(line[31:34].strip() or 0)
            except ValueError:
                pass
            lat = parse_dms_lat(line[34:45])
            lon = parse_dms_lon(line[45:57])
            upper = 0
            try:
                upper = int(line[63:68].strip() or 0)
            except ValueError:
                pass
            lower = 0
            try:
                lower = int(line[68:73].strip() or 0)
            except ValueError:
                pass

            # 查找或创建空域
            existing = None
            for a in self.airspaces:
                if a.ident == ident and a.type == atype:
                    existing = a
                    break
            if existing is None:
                existing = Airspace(ident=ident, type=atype, name=name)
                self.airspaces.append(existing)
            if lat is not None and lon is not None:
                existing.boundary_points.append((lat, lon))
            existing.upper_limit = upper or existing.upper_limit
            existing.lower_limit = lower or existing.lower_limit

    # ============================================================
    #  输出 GeoJSON
    # ============================================================

    def to_geojson(self) -> dict:
        """将所有解析数据导出为 GeoJSON FeatureCollection"""
        features = []

        # 机场
        for icao, ap in self.airports.items():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [ap.lon, ap.lat]},
                "properties": {
                    "class": "airport", "icao": icao, "name": ap.name,
                    "elevation": ap.elevation, "transition_alt": ap.transition_alt,
                    "marker-symbol": "airport"
                }
            })

        # 航路点
        for ident, wp in self.waypoints.items():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [wp.lon, wp.lat]},
                "properties": {
                    "class": "waypoint", "ident": ident,
                    "region": wp.region, "usage": wp.usage,
                    "marker-symbol": "waypoint"
                }
            })

        # 导航台
        for ident, nav in self.navaids.items():
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [nav.lon, nav.lat]},
                "properties": {
                    "class": "navaid", "ident": ident, "name": nav.name,
                    "type": nav.type, "frequency": nav.frequency,
                    "elevation": nav.elevation, "marker-symbol": "navaid"
                }
            })

        # 航路 (按 ident 分组为 LineString)
        airway_groups: dict[str, list] = {}
        for aw in self.airways:
            key = f"{aw.ident}_{aw.type}"
            if key not in airway_groups:
                airway_groups[key] = []
            airway_groups[key].append(aw)

        for key, legs in airway_groups.items():
            legs.sort(key=lambda x: x.seq_number)
            coords = [[aw.fix_lon, aw.fix_lat] for aw in legs
                      if aw.fix_lat != 0 and aw.fix_lon != 0]
            if len(coords) < 2:
                continue
            ident = legs[0].ident
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "class": "airway", "ident": ident,
                    "type": legs[0].type, "direction": legs[0].direction,
                    "min_altitude": legs[0].min_altitude,
                    "max_altitude": legs[0].max_altitude
                }
            })

        # 终端程序 (按 机场+程序类型+程序名+过渡 分组)
        proc_groups: dict[str, list] = {}
        for leg in self.procedures:
            key = f"{leg.type}_{leg.proc_ident}_{leg.transition}"
            if key not in proc_groups:
                proc_groups[key] = []
            proc_groups[key].append(leg)

        for key, legs in proc_groups.items():
            legs.sort(key=lambda x: x.seq)
            coords = [[leg.fix_lon, leg.fix_lat] for leg in legs
                      if leg.fix_lat != 0 and leg.fix_lon != 0]
            if len(coords) < 2:
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "class": "procedure", "type": legs[0].type,
                    "proc_ident": legs[0].proc_ident,
                    "transition": legs[0].transition,
                    "legs": [asdict(l) for l in legs]
                }
            })

        # 空域 (Polygon)
        for a in self.airspaces:
            if len(a.boundary_points) < 3:
                continue
            coords = [[lon, lat] for lat, lon in a.boundary_points]
            coords.append(coords[0])  # 闭合
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": {
                    "class": "airspace", "ident": a.ident,
                    "type": a.type, "name": a.name,
                    "upper_limit": a.upper_limit, "lower_limit": a.lower_limit
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "airport_count": len(self.airports),
                "waypoint_count": len(self.waypoints),
                "navaid_count": len(self.navaids),
                "airway_count": len(airway_groups),
                "procedure_count": len(proc_groups),
                "airspace_count": len(self.airspaces),
                "raw_record_count": len(self.raw_records)
            }
        }


# ============================================================
#  CLI 入口
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python arinc424.py <input.dat> [output.geojson]")
        sys.exit(1)

    parser = ARINC424Parser()
    parser.parse_file(sys.argv[1])

    geojson = parser.to_geojson()
    meta = geojson['metadata']
    print(f"[ARINC424] 解析完成:")
    print(f"  原始记录: {meta['raw_record_count']}")
    print(f"  机场: {meta['airport_count']}")
    print(f"  航路点: {meta['waypoint_count']}")
    print(f"  导航台: {meta['navaid_count']}")
    print(f"  航路: {meta['airway_count']}")
    print(f"  终端程序: {meta['procedure_count']}")
    print(f"  空域: {meta['airspace_count']}")

    out_path = sys.argv[2] if len(sys.argv) > 2 else 'output.geojson'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"\n已输出: {out_path}")
