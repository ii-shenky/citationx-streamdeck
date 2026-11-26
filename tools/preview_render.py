#!/usr/bin/env python3
"""Rough preview of one Stream Deck page with PilotsDeck composite actions.

Usage: python3 tools/preview_render.py <page manifest> <out.png> [address=value ...]
Elements whose visibility depends on an address without a sample value are drawn.
Images are looked up in PilotsDeck/ of this repository, then in $PD_PLUGIN (a copy of the
plugin folder). Positioning follows PilotsDeck's Renderer: Center 0 = rectangle as given,
3 = canvas centre + Position/2 (1 / 2 = one axis only); Size 0 = whole canvas (text) or the
image's own size.
"""
import json, sys, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, '..', 'Fonts') + '/'
ROOTS = [os.path.join(HERE, '..', 'PilotsDeck') + '/'] + ([os.environ['PD_PLUGIN'].rstrip('/') + '/'] if os.environ.get('PD_PLUGIN') else [])
LIB = '/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf'
S = dict(a.split('=', 1) for a in sys.argv[3:]) if __name__ == '__main__' else {}

def cond(c):
    v = S.get(c['Address'])
    if v is None: return None
    try: a, b = float(v), float(c['Value'])
    except ValueError: a, b = v, c['Value']
    try: return {0: a < b, 1: a <= b, 2: a > b, 3: a >= b, 4: a == b, 5: a != b}[c['Comparison']]
    except (TypeError, KeyError): return None
def holds(m, default):
    r = [cond(c) for c in m['Conditions'].values()]
    if any(x is None for x in r) or not r: return default
    return any(r) if m.get('AnyCondition') else all(r)
def ok(e):
    return all(holds(m, True) for m in e.get('Manipulators', {}).values() if m['ManipulatorType'] == 6)
def color(e):
    col = e.get('Color', '#ffffff')
    for m in e.get('Manipulators', {}).values():
        if m['ManipulatorType'] == 1 and holds(m, False): col = m['Color']
    return col if col.startswith('#') else 'silver'
_CMAP = {}
def has_glyphs(fn, txt):
    if fn not in _CMAP:
        from fontTools.ttLib import TTFont
        _CMAP[fn] = set(TTFont(fn).getBestCmap())
    return all(ord(ch) in _CMAP[fn] for ch in txt if not ch.isspace())
def font(e, size, txt=''):
    name = e.get('FontName') or ''
    if name == 'Share Tech': fn = FD + 'ShareTech-Regular.ttf'
    elif name.startswith('Barlow'): fn = FD + 'BarlowSemiCondensed-Bold.ttf'
    else: fn = LIB % ('Bold' if e.get('FontStyle') == 1 else 'Regular')
    if txt and not has_glyphs(fn, txt):                           # Windows falls back to another font for such glyphs
        fn = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    return ImageFont.truetype(fn, max(6, round(size * 4 / 3)))
def find(path):
    for r in ROOTS:
        if os.path.exists(r + path): return r + path
def rect(e, W, H, natural=None):
    x, y = e['Position']; w, h = e['Size']
    if natural:
        if w == 0 and h == 0: w, h = natural
    else:
        if w == 0: w = W
        if h == 0: h = H
    c = e.get('Center', 0)
    if c in (1, 3): x = W / 2 - w / 2 + x / 2
    if c in (2, 3): y = H / 2 - h / 2 + y / 2
    return x, y, w, h

def fmt_value(v, vf):
    """Approximation of PilotsDeck's ValueFormat: offset / scalar, rounding, sign, mappings (strings pass through)."""
    if v != '?' and vf.get('Mappings', {}).get(v) is not None: return vf['Mappings'][v]
    try: x = float(v)
    except (TypeError, ValueError): return v
    off, sc = vf.get('Offset', 0) or 0, vf.get('Scalar', 1) or 1
    x = (x + off) * sc if vf.get('OffsetFirst') else x * sc + off
    if vf.get('UseAbsoluteValue'): x = abs(x)
    r = vf.get('Round', -1)
    if r is not None and r >= 0: x = round(x, r)
    dt = vf.get('DigitsTrailing', -1)
    if dt is not None and dt >= 0: t = f'{x:.{dt}f}'
    elif float(x).is_integer(): t = str(int(x))
    else: t = f'{x:g}'
    m = vf.get('Mappings', {})
    if t in m: return m[t]
    if vf.get('InsertSign') and x > 0: t = '+' + t
    return t

def gauge_arc(dr, e, W, H):
    """Arc gauge (approximation): coloured ranges or the base colour, markers, and the indicator manipulators
    (type 4 = needle, others = a small mark on the arc)."""
    import math
    d, th = e['Size']; px, py = e['Position']
    cx, cy = W / 2 + px, H / 2 + py; r = d / 2
    a0, sw = e.get('GaugeAngleStart', 135), e.get('GaugeAngleSweep', 180)
    lo, hi = e.get('GaugeValueMin', 0), e.get('GaugeValueMax', 100)
    ang = lambda v: a0 + sw * (min(max(v, lo), hi) - lo) / ((hi - lo) or 1)
    box = [cx - r, cy - r, cx + r, cy + r]; th = max(2, round(th))
    ranges = e.get('GaugeColorRanges') or []
    if ranges:
        for rg in ranges: dr.arc(box, ang(rg['Range'][0]), ang(rg['Range'][1]), fill=rg['Color'], width=th)
    else: dr.arc(box, a0, a0 + sw, fill=color(e), width=th)
    for mk in e.get('GaugeMarkers') or []:
        t = math.radians(ang(mk['ValuePosition'])); L = mk.get('Height', 10)
        dr.line([(cx + (r - L / 2) * math.cos(t), cy + (r - L / 2) * math.sin(t)), (cx + (r + L / 2) * math.cos(t), cy + (r + L / 2) * math.sin(t))],
                fill=mk['Color'], width=max(2, round(mk.get('Size', 4) / 3)))
    for m in e.get('Manipulators', {}).values():
        if m['ManipulatorType'] != 3 or not holds(m, True): continue
        v = S.get(m.get('IndicatorAddress'))
        try: v = float(v)
        except (TypeError, ValueError): continue
        if hi >= 50 and 0 < v <= 1.5: v *= 100                       # ratio-type sim values on a percent gauge
        t = math.radians(ang(v)); col = m.get('IndicatorColor', '#c7c7c7')
        if m.get('IndicatorType') == 4:
            dr.line([(cx, cy), (cx + (r - 2) * math.cos(t), cy + (r - 2) * math.sin(t))], fill=col, width=max(2, m.get('IndicatorLineSize', 3)))
            dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=col)
        else:
            sz = min(10, m.get('IndicatorSize', 10)) / 2 + 2; ox, oy = cx + (r + sz) * math.cos(t), cy + (r + sz) * math.sin(t)
            ix, iy = cx + (r - 1) * math.cos(t), cy + (r - 1) * math.sin(t); nx, ny = -math.sin(t) * sz, math.cos(t) * sz
            dr.polygon([(ix, iy), (ox + nx, oy + ny), (ox - nx, oy - ny)], fill=col)

def draw(st, W, H, title=None):
    im = Image.new('RGB', (W, H), 'black'); dr = ImageDraw.Draw(im)
    for e in st['DisplayElements'].values():
        if not ok(e): continue
        t = e['ElementType']
        if t == 2:
            p = find(e.get('Image', ''))
            if not p or p.endswith('Empty.png'): continue
            src = Image.open(p).convert('RGBA')
            if e['Size'] == [0, 0] and (src.width > W or src.height > H):   # larger than the key: PilotsDeck fits it
                k = min(W / src.width, H / src.height); src = src.resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
            x, y, w, h = rect(e, W, H, src.size)
            if w == 0: w = src.size[0]
            if h == 0: h = src.size[1]
            src = src.resize((max(1, round(w)), max(1, round(h))), Image.LANCZOS)
            im.paste(src, (round(x), round(y)), src)
        elif t == 1 and e.get('GaugeIsArc'):
            gauge_arc(dr, e, W, H)
        elif t == 3:
            x, y, w, h = rect(e, W, H); box = [x, y, x + w, y + h]; col = color(e); ls = max(1, round(e.get('LineSize', 2)))
            pt = e.get('PrimitiveType', 2)
            if pt == 1: dr.line(box, fill=col, width=ls)
            elif pt == 2: dr.rectangle(box, outline=col, width=ls)
            elif pt == 3: dr.rectangle(box, fill=col)
            elif pt == 4: dr.ellipse(box, outline=col, width=ls)
            else: dr.ellipse(box, fill=col)
        elif t in (4, 5):
            if t == 4: txt = e.get('Text', '')
            else:
                v = fmt_value(S.get(e.get('ValueAddress'), '?'), e['ValueFormat'])
                txt = e['ValueFormat']['FormatString'].replace('%s', v) if e['ValueFormat'].get('FormatString') else v
            if not txt: continue
            f = font(e, e['FontSize'], txt); x, y, w, h = rect(e, W, H)
            ha, va = e.get('TextHorizontalAlignment', 1), e.get('TextVerticalAlignment', 1)
            ax, tx = {0: ('l', x), 2: ('r', x + w)}.get(ha, ('m', x + w / 2))
            ay, ty = {0: ('a', y), 2: ('d', y + h)}.get(va, ('m', y + h / 2))
            dr.text((tx, ty), txt, font=f, fill=color(e), anchor=ax + ay)
    if title:                                                     # native Stream Deck title over the image
        tt = (title.get('Title') or '').strip('\n')
        if tt.strip() and title.get('ShowTitle', True):
            f = ImageFont.truetype(LIB % 'Bold', round(title.get('FontSize', 12) * 2))
            lines = (title.get('Title') or '').split('\n'); lh = f.size + 4
            y0 = {'top': 6, 'bottom': H - 6 - lh * len(lines)}.get(title.get('TitleAlignment'), (H - lh * len(lines)) / 2)
            for i, ln in enumerate(lines):
                dr.text((W / 2, y0 + i * lh), ln.strip(), font=f, fill=title.get('TitleColor', '#ffffff'), anchor='ma')
    return im

def main():
    d = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    acts = {c['Type']: (c.get('Actions') or {}) for c in d['Controllers']}
    cols = max([int(p.split(',')[0]) for p in acts.get('Keypad', {})] + [3]) + 1
    rows = max([int(p.split(',')[1]) for p in acts.get('Keypad', {})] + [1]) + 1
    ndial = 6 if cols > 4 else 4
    KW = cols * 150; SW = ndial * 200 if cols > 4 else KW        # XL: strip segments at 1:1, centred under the keys
    out = Image.new('RGB', (KW + 10, rows * 150 + 110), '#333')
    page_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
    for kind, A in acts.items():
        for pos, a in A.items():
            x, y = map(int, pos.split(','))
            st = a['Settings'].get('settingsStore'); state = (a.get('States') or [{}])[0]
            if not st:
                f = state.get('Image')                                # native key (page tab): its own image
                W, H = (144, 144) if kind == 'Keypad' else (200, 100)
                tile = Image.new('RGB', (W, H), '#181818')
                if f and os.path.exists(os.path.join(page_dir, f)):
                    tile = Image.open(os.path.join(page_dir, f)).convert('RGB').resize((W, H), Image.LANCZOS)
                else:                                                 # legacy PilotsDeck action or dial stack: a labelled tile
                    sm = a['Settings'].get('settingsModel') or {}
                    t = (state.get('Title') or '').strip() or os.path.basename(sm.get('DefaultImage') or sm.get('OnImage') or '').rsplit('.', 1)[0]
                    t = t.split(' SDP - ')[-1] if t not in ('Empty', 'Arrow', 'None', '') else (sm.get('AddressAction') or sm.get('Address') or '')[-18:]
                    if a['UUID'].endswith('dial.stack'): t = 'STACK: ' + ' / '.join((x.get('States') or [{}])[0].get('Title', '').strip() or x.get('Name', '') for x in a.get('Actions', []))
                    dr = ImageDraw.Draw(tile); fnt = ImageFont.truetype(LIB % 'Bold', 13)
                    lines = [t[i:i + 16] for i in range(0, len(t), 16)][:4] or ['?']
                    for i, ln in enumerate(lines): dr.text((W / 2, H / 2 + (i - (len(lines) - 1) / 2) * 17), ln, fill='#9ad', anchor='mm', font=fnt)
                    dr.text((4, H - 4), a.get('Name', '')[:22], fill='#666', anchor='ld', font=ImageFont.truetype(LIB % 'Regular', 10))
                if kind == 'Keypad': out.paste(tile, (x * 150, y * 150))
                elif cols > 4: out.paste(tile, ((KW - SW) // 2 + x * 200, rows * 150 + 5))
                else: out.paste(tile.resize((150, 75)), (x * 152, rows * 150 + 5))
                continue
            if kind == 'Keypad': out.paste(draw(st, 144, 144, state), (x * 150, y * 150))
            elif cols > 4: out.paste(draw(st, 200, 100, state), ((KW - SW) // 2 + x * 200, rows * 150 + 5))
            else: out.paste(draw(st, 200, 100, state).resize((150, 75)), (x * 152, rows * 150 + 5))
    out.save(sys.argv[2])


if __name__ == '__main__':
    main()
