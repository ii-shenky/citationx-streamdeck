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
S = dict(a.split('=', 1) for a in sys.argv[3:])

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
def font(e, size):
    name = e.get('FontName') or ''
    if name == 'Share Tech': fn = FD + 'ShareTech-Regular.ttf'
    elif name.startswith('Barlow'): fn = FD + 'BarlowSemiCondensed-Bold.ttf'
    else: fn = LIB % ('Bold' if e.get('FontStyle') == 1 else 'Regular')
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

def draw(st, W, H, title=None):
    im = Image.new('RGB', (W, H), 'black'); dr = ImageDraw.Draw(im)
    for e in st['DisplayElements'].values():
        if not ok(e): continue
        t = e['ElementType']
        if t == 2:
            p = find(e.get('Image', ''))
            if not p or p.endswith('Empty.png'): continue
            src = Image.open(p).convert('RGBA'); x, y, w, h = rect(e, W, H, src.size)
            if w == 0: w = src.size[0]
            if h == 0: h = src.size[1]
            src = src.resize((max(1, round(w)), max(1, round(h))), Image.LANCZOS)
            im.paste(src, (round(x), round(y)), src)
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
                v = S.get(e.get('ValueAddress'), '?'); vf = e['ValueFormat']; v = vf.get('Mappings', {}).get(v, v)
                txt = vf['FormatString'].replace('%s', v) if vf.get('FormatString') else v
            if not txt: continue
            f = font(e, e['FontSize']); x, y, w, h = rect(e, W, H)
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
