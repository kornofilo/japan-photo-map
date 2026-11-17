"""Build data.json for the Nihon 2024 map from the Drive folder listing and route files.

Inputs (same folder):
  list.txt        name|driveId|dateColumn  (from the folder's embedded view)
  rail_legs.json  train legs traced on real track (rail.py)
  bike.json       Shimanami Kaido cycling route (OSM relation 2236106)
  car_kmj.json    bus Kumamoto -> Kumamoto airport (OSRM)
"""
import json, re, math, sys, datetime as dt

LIST = sys.argv[1] if len(sys.argv) > 1 else 'list.txt'
J = lambda s: dt.datetime.strptime(s, '%Y-%m-%d %H:%M')

PLACES = {
  'asakusa':   ('Asakusa, Tokio', 35.7148, 139.7967),
  'hakodate':  ('Hakodate', 41.7687, 140.7288),
  'morioka':   ('Morioka', 39.7036, 141.1527),
  'kakunodate':('Kakunodate', 39.5997, 140.5617),
  'niigata':   ('Niigata', 37.9161, 139.0364),
  'kioto':     ('Kioto', 35.0116, 135.7681),
  'arashiyama':('Arashiyama, Kioto', 35.0094, 135.6668),
  'osaka':     ('Osaka · EDION Arena', 34.6610, 135.5009),
  'imabari':   ('Imabari', 34.0660, 132.9978),
  'onomichi':  ('Onomichi', 34.4089, 133.2050),
  'fukuyama':  ('Fukuyama', 34.4893, 133.3626),
  'hiroshima': ('Hiroshima · Parque de la Paz', 34.3955, 132.4536),
  'miyajima':  ('Miyajima', 34.2960, 132.3198),
  'fukuoka':   ('Fukuoka', 33.5902, 130.4017),
  'nagasaki':  ('Nagasaki', 32.7503, 129.8777),
  'yufuin':    ('Yufuin', 33.2640, 131.3560),
  'bungomori': ('Bungo-Mori', 33.2840, 131.1550),
  'kumamoto':  ('Kumamoto', 32.8031, 130.7079),
  'tokio':     ('Tokio · Ueno', 35.7138, 139.7740),
}

# ---------- legs ----------
RAIL = {l['id']: l for l in json.load(open('rail_legs.json'))}
BIKE = json.load(open('bike.json'))
CAR = json.load(open('car_kmj.json'))

def gc(a, b, n=64):
    """great-circle points between a and b ([lat, lon]), longitudes unwrapped eastward."""
    t = math.pi / 180
    la1, lo1, la2, lo2 = a[0]*t, a[1]*t, b[0]*t, b[1]*t
    d = 2*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
    out = []; prev = None
    for i in range(n+1):
        f = i/n; A = math.sin((1-f)*d)/math.sin(d); B = math.sin(f*d)/math.sin(d)
        x = A*math.cos(la1)*math.cos(lo1) + B*math.cos(la2)*math.cos(lo2)
        y = A*math.cos(la1)*math.sin(lo1) + B*math.cos(la2)*math.sin(lo2)
        z = A*math.sin(la1) + B*math.sin(la2)
        lat = math.atan2(z, math.sqrt(x*x+y*y))/t; lon = math.atan2(y, x)/t
        if prev is not None:
            while lon - prev > 180: lon -= 360
            while lon - prev < -180: lon += 360
        prev = lon; out.append([round(lat, 4), round(lon, 4)])
    return out

HND, KMJ, ORD, LAX = [35.5494, 139.7798], [32.8373, 130.8551], [41.9786, -87.9048 + 360], [33.9416, -118.4085 + 360]
def clip_east(pts, maxlon=150.5):
    return [p for p in pts if p[1] <= maxlon]

LEGS = []
def leg(id, day, mode, label, pts, km=None, confirmed=True, note=None):
    LEGS.append({'id': id, 'day': day, 'mode': mode, 'label': label, 'pts': pts, 'km': km, 'ok': confirmed, 'note': note})

leg('f1', '2024-10-28', 'flight', 'NH111 Chicago → Haneda', clip_east(gc(ORD, HND, 160)[::-1])[::-1], confirmed=True)
for l in RAIL.values():
    mode = {'hs': 'hs', 'rail': 'rail', 'urban': 'urban'}[l['mode']]
    leg(l['id'], l['day'], mode, l['label'], l['pts'], l['km'], l['confirmed'])
leg('b1', '2024-11-06', 'bike', 'Bicicleta por el Shimanami Kaidō: Imabari → Mukaishima', BIKE['pts'], BIKE['km'], True)
leg('x1', '2024-11-06', 'ferry', 'Ferry Mukaishima → Onomichi', BIKE['ferry'], 0.6, True)
leg('x2', '2024-11-07', 'ferry', 'Ferry Miyajimaguchi → Miyajima', [[34.3116, 132.3036], [34.2988, 132.3203]], 1.8, False)
leg('c1', '2024-11-12', 'bus', 'Bus Kumamoto → aeropuerto', CAR, 17.8, False)
leg('f2', '2024-11-12', 'flight', 'Solaseed Air 16: Kumamoto → Haneda', gc(KMJ, HND, 48), 900, True)
leg('f3', '2024-11-16', 'flight', 'NH106 Haneda → Los Ángeles', clip_east(gc(HND, LAX, 160)), confirmed=True)
LEGBY = {l['id']: l for l in LEGS}

# ---------- days ----------
DAYS = [
 ('2024-10-28', 'Llegada a Tokio', ['f1', 'l01'], 'Aterrizaje en Haneda por la noche y primera noche en Asakusa. La cámara seguía en hora de Panamá, así que sus fotos del templo Sensō-ji son de la madrugada del 29.'),
 ('2024-10-29', 'Tokio → Hakodate', ['l02', 'l03', 'l04'], 'Primer día del Japan Rail Pass: Tōhoku y Hokkaidō Shinkansen bajo el estrecho de Tsugaru hasta Hokkaidō. Atardecer y noche en el fuerte Goryōkaku.'),
 ('2024-10-30', 'Hakodate → Kakunodate → Morioka', ['l05', 'l06', 'l07'], 'Mañana en las cuestas de Motomachi. Hayabusa 22 de Shin-Hakodate-Hokuto (10:53) a Morioka (12:45), Komachi 23 a Kakunodate (14:35 a 15:25), el barrio samurái, y vuelta en el Komachi 40 (17:18 a 18:14).'),
 ('2024-10-31', 'Morioka', [], 'Día completo en Morioka, con el santuario Sakurayama.'),
 ('2024-11-01', 'Morioka → Niigata', ['l08', 'l09'], 'Día de tren. Las fotos de la mañana son por la ventana. No hay reserva del trayecto: el trazo por Ōmiya es la ruta más probable en shinkansen.'),
 ('2024-11-02', 'Niigata', [], 'Bosques de cedros, escalinatas de piedra y un santuario; de noche, el letrero de Niigata.'),
 ('2024-11-03', 'Niigata → Kioto', ['l10', 'l11'], 'A mediodía, otra función de lucha libre en Niigata. Por la tarde, shinkansen hasta Kioto: la ruta por Tokio es la más probable, pero no hay reserva que la confirme.'),
 ('2024-11-04', 'Osaka: NJPW Power Struggle', ['l12', 'l13'], 'Día en Osaka: mañana entre tiendas de manga y, desde la tarde, la función de New Japan Pro-Wrestling en el EDION Arena (entradas 2F reservadas).'),
 ('2024-11-05', 'Arashiyama → Okayama → Imabari', ['l14', 'l15', 'l16'], 'Mañana en Arashiyama: el puente Togetsukyō y el tranvía Randen. Hikari 515 de Kioto (16:43) a Okayama (18:02) y de ahí cruzando el Seto-Ōhashi hasta Imabari, en Shikoku.'),
 ('2024-11-06', 'Shimanami Kaidō en bici', ['b1', 'x1', 'l17', 'l18'], 'Unos 74 km pedaleando de Imabari a Mukaishima por seis puentes: Kurushima-Kaikyō, Hakata-Ōshima, Ōmishima, Tatara, Ikuchi e Innoshima. Ferry a Onomichi al atardecer, tren a Fukuyama (con el castillo iluminado desde el andén) y Sakura 565 a Hiroshima.'),
 ('2024-11-07', 'Hiroshima y Miyajima', ['l28', 'x2'], 'Mañana en el Parque Memorial de la Paz y la Cúpula de la Bomba Atómica; tarde en Miyajima, con el torii flotante de Itsukushima.'),
 ('2024-11-08', 'Hiroshima → Fukuoka', ['l19'], 'Kodama 849 de Hiroshima (14:08) a Hakata.'),
 ('2024-11-09', 'Fukuoka → Nagasaki', ['l20', 'l21'], 'Relay Kamome 81 de Hakata (11:13) a Takeo-Onsen y el Nishi-Kyūshū Shinkansen hasta Nagasaki.'),
 ('2024-11-10', 'Nagasaki → Yufuin', ['l22', 'l23', 'l24'], 'Mañana en Nagasaki, regreso a Tosu y el Yufu 3 (12:39) por la línea Kyūdai hasta Yufuin (14:39).'),
 ('2024-11-11', 'Yufuin → Kumamoto', ['l25', 'l26'], 'Yufu 2 de Yufuin (09:07): por la ventana, la cochera de locomotoras de Bungo-Mori. Sakura 545 de Kurume a Kumamoto. Tarde con las estatuas de One Piece y el castillo de Kumamoto de noche.'),
 ('2024-11-12', 'Kumamoto → Tokio', ['c1', 'f2', 'l27'], 'Bus al aeropuerto, vuelo de Solaseed Air a Haneda (13:10) y monorriel hasta Ueno.'),
 ('2024-11-13', 'Tokio', [], 'Tarde y noche en la ciudad.'),
 ('2024-11-14', 'Tokio', [], 'Recorrido de día y, por la noche, otra función de lucha libre.'),
 ('2024-11-15', 'Tokio', [], 'Último día completo.'),
 ('2024-11-16', 'Regreso a Panamá', ['l29', 'f3'], 'Vuelo NH106 de Haneda a Los Ángeles y conexión a Panamá.'),
]
DAYIDX = {d[0]: i for i, d in enumerate(DAYS)}

# ---------- camera ranges (checked visually against thumbnails) ----------
CAM = [  # first, last, day, place or leg, label
 (1836, 1899, '2024-10-28', 'asakusa', 'Sensō-ji de noche'),
 (1900, 1943, '2024-10-29', 'hakodate', 'Hakodate al atardecer y Goryōkaku'),
 (1944, 2042, '2024-10-30', 'hakodate', 'Hakodate por la mañana'),
 (2043, 2270, '2024-10-30', 'kakunodate', 'Kakunodate y su estación'),
 (2271, 2379, '2024-10-31', 'morioka', 'Morioka'),
 (2380, 2523, '2024-11-01', 'leg:l08', 'Por la ventana del tren'),
 (2524, 2738, '2024-11-02', 'niigata', 'Niigata'),
 (2739, 3106, '2024-11-04', 'osaka', 'NJPW Power Struggle'),
 (3107, 3121, '2024-11-05', 'arashiyama', 'Arashiyama'),
 (3229, 3576, '2024-11-06', 'leg:b1', 'Shimanami Kaidō'),
 (3577, 3581, '2024-11-06', 'onomichi', 'Ferry a Onomichi'),
 (3582, 3588, '2024-11-06', 'fukuyama', 'Castillo de Fukuyama desde el andén'),
 (3589, 3600, '2024-11-07', 'hiroshima', 'Parque de la Paz'),
 (3601, 3626, '2024-11-07', 'miyajima', 'Miyajima e Itsukushima'),
 (3627, 3859, None, None, None),  # Nov 7 evening - Nov 10 morning: not in Drive yet
 (3860, 3885, '2024-11-10', 'nagasaki', 'Nagasaki'),
 (3886, 3977, '2024-11-11', 'leg:l25', 'Yufuin y Bungo-Mori desde el tren'),
 (3978, 4040, '2024-11-11', 'kumamoto', 'Kumamoto'),
 (4041, 4137, '2024-11-13', 'tokio', 'Tokio'),
 (4138, 4272, '2024-11-14', 'tokio', 'Tokio y lucha libre'),
]
# approximate start time (JST) of each camera batch, for ordering when no anchor applies
HINT = {1836:'2024-10-29 00:56',1900:'2024-10-29 16:10',1944:'2024-10-30 07:49',2043:'2024-10-30 15:58',2271:'2024-10-31 06:50',
        2380:'2024-11-01 10:14',2524:'2024-11-02 11:28',2739:'2024-11-04 14:37',3107:'2024-11-05 11:09',3229:'2024-11-06 08:43',
        3577:'2024-11-06 17:19',3582:'2024-11-06 17:40',3589:'2024-11-07 11:05',3601:'2024-11-07 13:00',3860:'2024-11-10 09:00',
        3886:'2024-11-11 09:03',3978:'2024-11-11 15:20',4041:'2024-11-13 16:38',4138:'2024-11-14 09:06'}
# capture-time anchors (Drive modifiedTime, UTC) used to place train/bike photos along a route
ANCH = {1900:'2024-10-29T07:10',1920:'2024-10-29T08:28',2380:'2024-11-01T15:14',2450:'2024-11-01T15:42',2523:'2024-11-01T17:03',
        3229:'2024-11-06T13:43',3300:'2024-11-06T15:20',3380:'2024-11-06T15:59',3446:'2024-11-06T16:48',3500:'2024-11-06T18:57',
        3530:'2024-11-06T19:29',3549:'2024-11-06T21:18',3560:'2024-11-06T21:53',3570:'2024-11-06T22:18',
        3886:'2024-11-11T14:03',3950:'2024-11-11T14:33',3970:'2024-11-11T14:33',3978:'2024-11-11T20:20'}
def cam_time(n):
    """camera clock: Drive stores it as if it were Panama time (UTC-5); after 1943 the camera was on Japan time."""
    ks = sorted(ANCH)
    lo = max([k for k in ks if k <= n], default=None); hi = min([k for k in ks if k >= n], default=None)
    if lo is None or hi is None: return None
    if lo // 1000 != hi // 1000 and abs(hi - lo) > 120: return None
    a = dt.datetime.fromisoformat(ANCH[lo]); b = dt.datetime.fromisoformat(ANCH[hi])
    if (b - a).total_seconds() > 6 * 3600: return None
    t = a if hi == lo else a + (b - a) * ((n - lo) / (hi - lo))
    return t + dt.timedelta(hours=9 if n <= 1943 else -5)  # -> JST

# ---------- phone timeline (JST) ----------
TL = [
 ('2024-10-28 20:00', 'asakusa', '2024-10-28'), ('2024-10-29 10:30', 'leg:l03', '2024-10-29'), ('2024-10-29 14:40', 'leg:l04', '2024-10-29'),
 ('2024-10-29 15:10', 'hakodate', '2024-10-29'), ('2024-10-30 00:00', 'hakodate', '2024-10-30'), ('2024-10-30 10:10', 'leg:l05', '2024-10-30'),
 ('2024-10-30 10:40', 'leg:l06', '2024-10-30'), ('2024-10-30 12:45', 'morioka', '2024-10-30'), ('2024-10-30 14:35', 'leg:l07', '2024-10-30'),
 ('2024-10-30 15:25', 'kakunodate', '2024-10-30'), ('2024-10-30 17:18', 'leg:l07r', '2024-10-30'), ('2024-10-30 18:14', 'morioka', '2024-10-30'),
 ('2024-10-31 00:00', 'morioka', '2024-10-31'), ('2024-11-01 00:00', 'morioka', '2024-11-01'), ('2024-11-01 10:00', 'leg:l08', '2024-11-01'),
 ('2024-11-01 13:00', 'leg:l09', '2024-11-01'), ('2024-11-01 15:30', 'niigata', '2024-11-01'), ('2024-11-02 00:00', 'niigata', '2024-11-02'),
 ('2024-11-03 00:00', 'niigata', '2024-11-03'), ('2024-11-03 15:15', 'leg:l10', '2024-11-03'), ('2024-11-03 17:20', 'leg:l11', '2024-11-03'),
 ('2024-11-03 19:45', 'kioto', '2024-11-03'), ('2024-11-04 00:00', 'kioto', '2024-11-04'), ('2024-11-04 09:00', 'leg:l12', '2024-11-04'),
 ('2024-11-04 09:40', 'osaka', '2024-11-04'), ('2024-11-05 00:00', 'kioto', '2024-11-05'), ('2024-11-05 09:30', 'arashiyama', '2024-11-05'),
 ('2024-11-05 14:00', 'kioto', '2024-11-05'), ('2024-11-05 16:43', 'leg:l15', '2024-11-05'), ('2024-11-05 18:05', 'leg:l16', '2024-11-05'),
 ('2024-11-05 20:40', 'imabari', '2024-11-05'), ('2024-11-06 00:00', 'imabari', '2024-11-06'), ('2024-11-06 08:30', 'leg:b1', '2024-11-06'),
 ('2024-11-06 17:15', 'onomichi', '2024-11-06'), ('2024-11-06 17:40', 'fukuyama', '2024-11-06'), ('2024-11-06 18:27', 'leg:l18', '2024-11-06'),
 ('2024-11-06 18:50', 'hiroshima', '2024-11-06'), ('2024-11-07 00:00', 'hiroshima', '2024-11-07'), ('2024-11-07 12:30', 'miyajima', '2024-11-07'),
 ('2024-11-07 18:30', 'hiroshima', '2024-11-07'), ('2024-11-08 00:00', 'hiroshima', '2024-11-08'), ('2024-11-08 14:08', 'leg:l19', '2024-11-08'),
 ('2024-11-08 15:15', 'fukuoka', '2024-11-08'), ('2024-11-09 00:00', 'fukuoka', '2024-11-09'), ('2024-11-09 11:13', 'leg:l20', '2024-11-09'),
 ('2024-11-09 12:10', 'leg:l21', '2024-11-09'), ('2024-11-09 12:45', 'nagasaki', '2024-11-09'), ('2024-11-10 00:00', 'nagasaki', '2024-11-10'),
 ('2024-11-10 11:00', 'leg:l22', '2024-11-10'), ('2024-11-10 11:30', 'leg:l23', '2024-11-10'), ('2024-11-10 12:39', 'leg:l24', '2024-11-10'),
 ('2024-11-10 14:39', 'yufuin', '2024-11-10'), ('2024-11-11 00:00', 'yufuin', '2024-11-11'), ('2024-11-11 09:07', 'leg:l25', '2024-11-11'),
 ('2024-11-11 10:47', 'leg:l26', '2024-11-11'), ('2024-11-11 11:16', 'kumamoto', '2024-11-11'), ('2024-11-12 00:00', 'kumamoto', '2024-11-12'),
 ('2024-11-12 11:30', 'leg:c1', '2024-11-12'), ('2024-11-12 13:10', 'leg:f2', '2024-11-12'), ('2024-11-12 14:45', 'leg:l27', '2024-11-12'),
 ('2024-11-12 15:40', 'tokio', '2024-11-12'), ('2024-11-13 00:00', 'tokio', '2024-11-13'), ('2024-11-14 00:00', 'tokio', '2024-11-14'),
 ('2024-11-15 00:00', 'tokio', '2024-11-15'), ('2024-11-16 00:00', 'tokio', '2024-11-16'), ('2024-11-16 08:00', 'leg:l29', '2024-11-16'),
 ('2024-11-16 10:50', 'leg:f3', '2024-11-16'), ('2024-11-16 23:59', None, None),
]
TL = [(J(a), p, d) for a, p, d in TL]
def where(t):
    for i in range(len(TL) - 1):
        if TL[i][0] <= t < TL[i + 1][0]:
            nxt = TL[i + 1][0]
            return TL[i][1], TL[i][2], TL[i][0], nxt
    return None, None, None, None

def along(pts, f):
    """point at fraction f (0..1) of a polyline, by length."""
    f = max(0.0, min(1.0, f))
    seg = [math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts))]
    tot = sum(seg); target = f * tot; acc = 0
    for i, s in enumerate(seg):
        if acc + s >= target:
            r = (target - acc) / s if s else 0
            a, b = pts[i], pts[i + 1]
            return [round(a[0] + (b[0] - a[0]) * r, 5), round(a[1] + (b[1] - a[1]) * r, 5)]
        acc += s
    return pts[-1]

# leg windows in JST for camera photos placed along a route
LEGWIN = {'l08': ('2024-11-01 10:00', '2024-11-01 13:00'), 'b1': ('2024-11-06 08:30', '2024-11-06 17:00'), 'l25': ('2024-11-11 09:07', '2024-11-11 10:47')}

# ---------- read the folder listing ----------
seen = set(); photos = []
skipped = {'dup': 0, 'other': 0, 'pre': 0, 'post': 0, 'gap': 0}
for line in open(LIST, encoding='utf8'):
    parts = line.rstrip('\n').split('|')
    if len(parts) < 2: continue
    name, fid = parts[0], parts[1]
    base = re.sub(r' \(\d+\)(?=\.\w+$)', '', name)
    if base in seen: skipped['dup'] += 1; continue
    seen.add(base)
    ext = base.rsplit('.', 1)[-1].lower()
    kind = 'v' if ext in ('mp4', 'mov') else 'p'
    m = re.match(r'DSC_(\d{4})\.', base)
    if m:
        n = int(m.group(1))
        r = next((c for c in CAM if c[0] <= n <= c[1]), None)
        if r is None:
            skipped['post' if n > 4272 else 'gap'] += 1; continue
        if r[2] is None: skipped['gap'] += 1; continue
        t = cam_time(n)
        photos.append({'id': fid, 'n': base, 'k': kind, 'day': r[2], 'at': r[3], 'lab': r[4], 'num': n, 't': t, 'src': 'cam'})
        continue
    m = re.match(r'(?:VideoCapture_)?(\d{8})[_-](\d{6})', base)
    if m and not base.lower().startswith('screenshot'):
        t = dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
        if t < TL[0][0]:
            photos.append({'id': fid, 'n': base, 'k': kind, 'day': '2024-10-28', 'at': 'way', 'lab': 'De camino', 'num': None, 't': t, 'src': 'phone'})
            skipped['pre'] += 1; continue
        at, day, t0, t1 = where(t)
        if at is None: skipped['post'] += 1; continue
        photos.append({'id': fid, 'n': base, 'k': kind, 'day': day, 'at': at, 'lab': None, 'num': None, 't': t, 'src': 'phone', 'win': (t0, t1)})
        continue
    skipped['other'] += 1

# ---------- place each photo on the map ----------
def leg_pts(key):
    rev = key.endswith('r'); lid = key[:-1] if rev else key
    pts = LEGBY[lid]['pts']
    return pts[::-1] if rev else pts

for p in photos:
    p['pos'] = None; p['approx'] = False
    if p['at'] == 'way': continue
    if p['at'].startswith('leg:'):
        key = p['at'][4:]
        pts = leg_pts(key)
        if p['src'] == 'phone':
            t0, t1 = p['win']
        else:
            w = LEGWIN.get(key); t0, t1 = (J(w[0]), J(w[1])) if w else (None, None)
        if p['t'] and t0 and t1 > t0:
            f = (p['t'] - t0).total_seconds() / (t1 - t0).total_seconds()
        else:
            f = 0.5
        p['pos'] = along(pts, f); p['approx'] = True
    else:
        _, la, lo = PLACES[p['at']]; p['pos'] = [la, lo]

for p in photos:
    if p['t']: p['sort'] = p['t']
    elif p['num']:
        st = max(k for k in HINT if k <= p['num']); p['sort'] = J(HINT[st]) + dt.timedelta(seconds=20 * (p['num'] - st))
    else: p['sort'] = dt.datetime.fromisoformat(p['day'] + 'T12:00')

def place_label(at):
    if at == 'way': return 'De camino a Japón'
    if at.startswith('leg:'):
        k = at[4:]
        lab = LEGBY[k]['label'].split(':')[-1].strip()
        return {'bike': 'En bici', 'flight': 'En el avión', 'bus': 'En bus'}.get(LEGBY[k]['mode'], 'En el tren') + ' · ' + lab
    return PLACES[at][0]

byk = {}
for p in photos:
    at = p['at'][:-1] if p['at'].endswith('r') and p['at'][4:-1] in LEGBY else p['at']
    byk.setdefault((p['day'], at), []).append(p)
groups = []
for (day, at), ps in byk.items():
    ps.sort(key=lambda p: (p['sort'], p['num'] or 0))
    groups.append({'day': day, 'at': at, 'name': place_label(at), 'ph': ps, 'first': ps[0]['sort']})
groups.sort(key=lambda g: (g['day'], g['first']))

# ---------- output ----------
def ser(p):
    t = p['t'].strftime('%H:%M') if (p['src'] == 'phone' and p['t']) else ''
    pos = p['pos'] if p['approx'] else 0
    return [p['id'], p['n'].replace('DSC_', '').rsplit('.', 1)[0], p['k'] + ('c' if p['src'] == 'cam' else 'm'), t, pos]

out = {
  'places': {k: [v[0], v[1], v[2]] for k, v in PLACES.items()},
  'legs': LEGS,
  'days': [{'d': d, 't': t, 'legs': l, 'x': x} for d, t, l, x in DAYS],
  'groups': [{'day': g['day'], 'at': g['at'], 'name': g['name'], 'ph': [ser(p) for p in g['ph']]} for g in groups],
  'missing': '3627–3859',
}
json.dump(out, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
tot = sum(len(g['ph']) for g in out['groups'])
print('photos', tot, 'groups', len(groups), 'skipped', skipped)
for d, *_ in DAYS:
    gs = [g for g in out['groups'] if g['day'] == d]
    print(d, sum(len(g['ph']) for g in gs), ' | '.join(f"{g['name'][:28]}:{len(g['ph'])}" for g in gs))
