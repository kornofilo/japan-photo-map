"""Trace each train leg of the trip along real track geometry (MLIT N02 railway data).

Each leg names the allowed lines and the two stations; the path is the shortest
route over those lines only, so a Shinkansen leg cannot drift onto local track.
"""
import json, math, heapq, sys
from shapely.geometry import LineString, Point
from shapely.ops import substring

SEC = json.load(open('g/out/railroad_section_detail.geojson'))['features']
STA = json.load(open('g/out/station_detail.geojson'))['features']

def hav(a, b):
    R = 6371.0; t = math.pi / 180
    dlat = (b[1] - a[1]) * t; dlon = (b[0] - a[0]) * t
    x = math.sin(dlat / 2) ** 2 + math.cos(a[1] * t) * math.cos(b[1] * t) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def station(name, line):
    for f in STA:
        p = f['properties']
        if p['name'] == name and p['rr_name'] == line:
            c = LineString(f['geometry']['coordinates']).centroid
            return (c.x, c.y)
    raise KeyError(f'{name} / {line}')

def key(c):
    return (round(c[0], 6), round(c[1], 6))

def route(lines, a, b):
    """lines: set of (oper, name) or names; a, b: (lon, lat)."""
    segs = [f for f in SEC if f['properties']['name'] in lines or (f['properties']['oper_name'], f['properties']['name']) in lines]
    if not segs:
        raise ValueError(f'no sections for {lines}')
    # split every section into point-to-point edges so a station in mid-section is reachable
    adj = {}
    pts = {}
    for f in segs:
        cs = f['geometry']['coordinates']
        for i in range(1, len(cs)):
            u, v = key(cs[i - 1]), key(cs[i])
            d = hav(cs[i - 1], cs[i])
            adj.setdefault(u, []).append((v, d)); adj.setdefault(v, []).append((u, d))
            pts[u] = cs[i - 1]; pts[v] = cs[i]
    # join endpoints that are close but not identical (line changes at the same station)
    keys = list(pts)
    grid = {}
    for k in keys:
        grid.setdefault((round(k[0], 2), round(k[1], 2)), []).append(k)
    for k in keys:
        if len(adj[k]) > 1:
            continue
        gx, gy = round(k[0], 2), round(k[1], 2)
        for dx in (-0.01, 0, 0.01):
            for dy in (-0.01, 0, 0.01):
                for o in grid.get((round(gx + dx, 2), round(gy + dy, 2)), []):
                    if o != k and hav(pts[k], pts[o]) < 0.35:
                        adj[k].append((o, 0.05)); adj[o].append((k, 0.05))
    def snap(p):
        return min(keys, key=lambda k: hav(p, pts[k]))
    sa, sb = snap(a), snap(b)
    dist = {sa: 0}; prev = {}; h = [(0, sa)]
    while h:
        d, u = heapq.heappop(h)
        if u == sb:
            break
        if d > dist.get(u, 1e18):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd; prev[v] = u; heapq.heappush(h, (nd, v))
    if sb not in dist:
        raise RuntimeError(f'no path {lines}')
    path = [sb]
    while path[-1] != sa:
        path.append(prev[path[-1]])
    path.reverse()
    coords = [pts[k] for k in path]
    return coords, dist[sb], hav(a, pts[sa]), hav(b, pts[sb])

def simplify(coords, tol=0.0003):
    ls = LineString(coords).simplify(tol, preserve_topology=False)
    return [[round(y, 5), round(x, 5)] for x, y in ls.coords]  # -> [lat, lon] for Leaflet

S = station
SHINK_E = {'東北新幹線', '北海道新幹線'}
LEGS = [
  # id, day, label, mode, lines, from, to, confirmed
  ('l01', '2024-10-28', 'Haneda → Asakusa (Keikyu y línea Asakusa)', 'urban', {('京浜急行電鉄','空港線'),('京浜急行電鉄','本線'),('東京都','1号線浅草線')}, S('羽田空港第3ターミナル','空港線'), S('浅草','1号線浅草線'), False),
  ('l02', '2024-10-29', 'Asakusa → Ueno (Ginza)', 'urban', {('東京地下鉄','3号線銀座線')}, S('浅草','3号線銀座線'), S('上野','3号線銀座線'), False),
  ('l03', '2024-10-29', 'Ueno → Shin-Hakodate-Hokuto (Tohoku y Hokkaido Shinkansen)', 'hs', SHINK_E, S('上野','東北新幹線'), S('新函館北斗','北海道新幹線'), True),
  ('l04', '2024-10-29', 'Shin-Hakodate-Hokuto → Hakodate', 'rail', {('北海道旅客鉄道','函館線')}, S('新函館北斗','函館線'), S('函館','函館線'), True),
  ('l05', '2024-10-30', 'Hakodate → Shin-Hakodate-Hokuto', 'rail', {('北海道旅客鉄道','函館線')}, S('函館','函館線'), S('新函館北斗','函館線'), True),
  ('l06', '2024-10-30', 'Hayabusa 22: Shin-Hakodate-Hokuto → Morioka', 'hs', SHINK_E, S('新函館北斗','北海道新幹線'), S('盛岡','東北新幹線'), True),
  ('l07', '2024-10-30', 'Komachi 23 / 40: Morioka ⇄ Kakunodate', 'rail', {('東日本旅客鉄道','田沢湖線')}, S('盛岡','田沢湖線'), S('角館','田沢湖線'), True),
  ('l08', '2024-10-31', 'Morioka → Kōriyama (Tōhoku Shinkansen)', 'hs', {'東北新幹線'}, S('盛岡','東北新幹線'), S('郡山','東北新幹線'), False),
  ('l08b', '2024-10-31', 'Kōriyama → Aizu-Wakamatsu (Ban\'etsu Oeste)', 'rail', {('東日本旅客鉄道','磐越西線')}, S('郡山','磐越西線'), S('会津若松','磐越西線'), False),
  ('l09', '2024-11-01', 'Aizu-Wakamatsu → Niigata (Ban\'etsu Oeste, por el río Agano)', 'rail', {('東日本旅客鉄道','磐越西線'),('東日本旅客鉄道','信越線')}, S('会津若松','磐越西線'), S('新潟','信越線'), True),
  ('l10', '2024-11-03', 'Niigata → Tokio (Joetsu y Tohoku Shinkansen)', 'hs', {'上越新幹線','東北新幹線'}, S('新潟','上越新幹線'), S('東京','東北新幹線'), False),
  ('l11', '2024-11-03', 'Tokio → Kioto (Tokaido Shinkansen)', 'hs', {'東海道新幹線'}, S('東京','東海道新幹線'), S('京都','東海道新幹線'), False),
  ('l12', '2024-11-04', 'Kioto ⇄ Osaka (JR Kioto)', 'rail', {('西日本旅客鉄道','東海道線')}, S('京都','東海道線'), S('大阪','東海道線'), False),
  ('l13', '2024-11-04', 'Umeda ⇄ Namba (Midosuji) para el EDION Arena', 'urban', {('大阪市高速電気軌道','1号線(御堂筋線)')}, S('梅田','1号線(御堂筋線)'), (135.5013, 34.6652), False),
  ('l14', '2024-11-05', 'Kioto ⇄ Saga-Arashiyama (Sagano)', 'rail', {('西日本旅客鉄道','山陰線')}, S('京都','山陰線'), S('嵯峨嵐山','山陰線'), False),
  ('l15', '2024-11-05', 'Hikari 515: Kioto → Okayama', 'hs', {'東海道新幹線','山陽新幹線'}, S('京都','東海道新幹線'), S('岡山','山陽新幹線'), True),
  ('l16', '2024-11-05', 'Okayama → Imabari (Seto-Ōhashi y Yosan)', 'rail', {('西日本旅客鉄道','宇野線'),('西日本旅客鉄道','本四備讃線'),('四国旅客鉄道','本四備讃線'),('四国旅客鉄道','予讃線')}, S('岡山','宇野線'), S('今治','予讃線'), True),
  ('l17', '2024-11-06', 'Onomichi → Fukuyama (San\'yō)', 'rail', {('西日本旅客鉄道','山陽線')}, S('尾道','山陽線'), S('福山','山陽線'), False),
  ('l18', '2024-11-06', 'Sakura 565: Fukuyama → Hiroshima', 'hs', {'山陽新幹線'}, S('福山','山陽新幹線'), S('広島','山陽新幹線'), True),
  ('l19', '2024-11-08', 'Kodama 849: Hiroshima → Hakata', 'hs', {'山陽新幹線'}, S('広島','山陽新幹線'), S('博多','山陽新幹線'), True),
  ('l20', '2024-11-09', 'Relay Kamome 81: Hakata → Takeo-Onsen', 'rail', {('九州旅客鉄道','鹿児島線'),('九州旅客鉄道','長崎線'),('九州旅客鉄道','佐世保線')}, S('博多','鹿児島線'), S('武雄温泉','佐世保線'), True),
  ('l21', '2024-11-09', 'Kamome: Takeo-Onsen → Nagasaki (Nishi-Kyushu Shinkansen)', 'hs', {'西九州新幹線'}, S('武雄温泉','西九州新幹線'), S('長崎','西九州新幹線'), True),
  ('l22', '2024-11-10', 'Nagasaki → Takeo-Onsen (Nishi-Kyushu Shinkansen)', 'hs', {'西九州新幹線'}, S('長崎','西九州新幹線'), S('武雄温泉','西九州新幹線'), True),
  ('l23', '2024-11-10', 'Relay Kamome: Takeo-Onsen → Tosu', 'rail', {('九州旅客鉄道','長崎線'),('九州旅客鉄道','佐世保線')}, S('武雄温泉','佐世保線'), S('鳥栖','長崎線'), True),
  ('l24', '2024-11-10', 'Yufu 3: Tosu → Yufuin (Kyūdai)', 'rail', {('九州旅客鉄道','鹿児島線'),('九州旅客鉄道','久大線')}, S('鳥栖','鹿児島線'), S('由布院','久大線'), True),
  ('l25', '2024-11-11', 'Yufu 2: Yufuin → Kurume (pasa por Bungo-Mori)', 'rail', {('九州旅客鉄道','久大線')}, S('由布院','久大線'), S('久留米','久大線'), True),
  ('l26', '2024-11-11', 'Sakura 545: Kurume → Kumamoto', 'hs', {'九州新幹線'}, S('久留米','九州新幹線'), S('熊本','九州新幹線'), True),
  ('l27', '2024-11-12', 'Haneda → Hamamatsuchō (Monorriel) → Ueno', 'urban', {('東京モノレール','東京モノレール羽田線'),('東日本旅客鉄道','東北線'),('東日本旅客鉄道','東海道線')}, S('羽田空港第2ターミナル','東京モノレール羽田線'), S('上野','東北線'), False),
  ('l28', '2024-11-07', 'Hiroshima → Miyajimaguchi (San\'yō)', 'rail', {('西日本旅客鉄道','山陽線')}, S('広島','山陽線'), (132.3036, 34.3116), False),
  ('l29', '2024-11-16', 'Ueno → Hamamatsuchō → Haneda (Monorriel)', 'urban', {('東京モノレール','東京モノレール羽田線'),('東日本旅客鉄道','東北線'),('東日本旅客鉄道','東海道線')}, S('上野','東北線'), S('羽田空港第3ターミナル','東京モノレール羽田線'), False),
]

out = []
for lid, day, label, mode, lines, a, b, conf in LEGS:
    coords, km, ea, eb = route(lines, a, b)
    straight = hav(a, b)
    pts = simplify(coords)
    out.append({'id': lid, 'day': day, 'label': label, 'mode': mode, 'confirmed': conf, 'km': round(km, 1), 'pts': pts})
    print(f'{lid} {label[:46]:46s} {km:7.1f} km (recta {straight:6.1f}) snap {ea:.2f}/{eb:.2f} km  {len(pts)} pts', file=sys.stderr)
json.dump(out, open('rail_legs.json', 'w'), ensure_ascii=False, separators=(',', ':'))
