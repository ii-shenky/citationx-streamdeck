"""Shared pieces for building Stream Deck + XL profiles (9x4 keys, 6 dials) from Stream Deck + profiles.

A profile script loads the + pages with load_pages(), describes the XL pages as tables of
factories (one per key / dial) and calls build(). Row 0 of every page is the tab row: page
tabs in columns 0-3, keys common to all pages, then page keys from column 7.
"""
import copy, json, pathlib, re, uuid
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / 'Fonts'
XL_MODEL = '20GBX9901'

def namespace(seed):
    """Stable ids between builds, so a re-install overwrites the same files and keeps the aircraft mapping."""
    return lambda name: str(uuid.uuid5(seed, name))

def load_pages(profile_dir, pages):
    """{alias: first characters of the page folder} -> {alias: {'Keypad': {pos: action}, 'Encoder': {...}}}"""
    src = {}
    for name, g in pages.items():
        d = json.loads(next(pathlib.Path(profile_dir).glob(f'Profiles/{g}*/manifest.json')).read_bytes().decode('utf-8-sig'))
        src[name] = {c['Type']: c.get('Actions') or {} for c in d['Controllers']}
    return src

# ---- composite action helpers ---------------------------------------------------------------
def store(a): return a['Settings']['settingsStore']
def elements(a):
    """Display elements in drawing order (the keys are numbers stored as strings)."""
    return [e for _, e in sorted(store(a)['DisplayElements'].items(), key=lambda kv: int(kv[0]))]
def set_elements(a, lst): store(a)['DisplayElements'] = {str(i): e for i, e in enumerate(lst)}
def commands(a, kind): return [c for _, c in sorted(store(a)['ActionCommands'].get(kind, {}).items(), key=lambda kv: int(kv[0]))]
def set_commands(a, down=None, up=None):
    """Replace all commands of a key: `down` on press, `up` on release (lists of command objects from any source)."""
    ac = store(a)['ActionCommands']
    for k in ac: ac[k] = {}
    for kind, code, lst in (('KEY_DOWN', 0, down), ('KEY_UP', 1, up)):
        out = {}
        for i, c in enumerate(lst or []):
            c = copy.deepcopy(c); c['DeckCommandType'] = code; out[str(i)] = c
        ac[kind] = out
def no_title(a):
    for st in a.get('States') or []: st['Title'] = ''
def by_text(lst, t): return next(e for e in lst if e.get('Text') == t)
def by_val(lst, v): return next(e for e in lst if (e.get('ValueAddress') or '').startswith(v))

def at(e, cx, cy, fs=None, text=None, color=None):
    """Copy a text/value element (keeps its conditions) centred at (cx, cy) on a 144x144 key."""
    e = copy.deepcopy(e); e['Size'] = [144, 144]; e['Position'] = [cx - 72, cy - 72]
    e['TextHorizontalAlignment'] = 1; e['TextVerticalAlignment'] = 1
    if fs: e['FontSize'] = fs
    if text is not None: e['Text'] = text
    if color: e['Color'] = color
    return e
def img(e, cx, cy, w, h):
    """Copy an image element centred at (cx, cy) on a 144x144 key."""
    e = copy.deepcopy(e); e['Center'] = 3; e['Size'] = [w, h]; e['Position'] = [2 * (cx - 72), 2 * (cy - 72)]
    return e

def key_like(dial, shell, rename=None, down=None, up=None):
    """A strip display whose elements mirror those of a key (same kinds in the same order): the key's
    geometry with the dial's texts, colours and conditions. Push of the dial becomes the key press."""
    D, G = elements(dial), elements(shell)
    assert [e['ElementType'] for e in D] == [e['ElementType'] for e in G], 'element patterns differ'
    out = []
    for d, g in zip(D, G):
        d = copy.deepcopy(d)
        for f in ('Position', 'Size', 'Center', 'Scale', 'FontSize'): d[f] = g[f]
        if rename and d.get('Text') in rename: d['Text'] = rename[d['Text']]
        out.append(d)
    a = copy.deepcopy(shell); set_elements(a, out); no_title(a)
    set_commands(a, down if down is not None else commands(dial, 'DIAL_DOWN'), up if up is not None else commands(dial, 'DIAL_UP'))
    return a

def key_swap(key, addresses, texts=None):
    """A copy of a key bound to other variables: every address occurrence replaced, texts renamed."""
    s = json.dumps(key)
    for old, new in addresses.items(): s = s.replace(json.dumps(old)[1:-1], json.dumps(new)[1:-1])
    a = json.loads(s)
    for e in store(a)['DisplayElements'].values():
        if texts and e.get('Text') in texts: e['Text'] = texts[e['Text']]
    return a

def key_from_strip(dial, shell, kx=0.7, ky=1.3, sizes=None, texts=None, drop=(), down=None):
    """A text-only strip display (200x100) as a key: every text/value keeps its conditions and moves
    to the same relative place on the 144x144 canvas. `sizes` / `texts`: overrides by text or value address."""
    out = []
    for e in elements(dial):
        ident = e.get('Text') or e.get('ValueAddress') or ''
        if e['ElementType'] not in (4, 5) or ident in drop: continue
        w, h = e['Size']; w, h = (w or 200), (h or 100)
        cx, cy = e['Position'][0] + w / 2 - 100, e['Position'][1] + h / 2 - 50          # offset from the strip centre
        n = at(e, round(72 + cx * kx), round(72 + cy * ky))
        if sizes and ident in sizes: n['FontSize'] = sizes[ident]
        if texts and ident in texts: n['Text'] = texts[ident]
        out.append(n)
    a = copy.deepcopy(shell); set_elements(a, out); no_title(a)
    set_commands(a, down if down is not None else commands(dial, 'DIAL_DOWN'))
    return a

# ---- page tabs ------------------------------------------------------------------------------
def tab_image(name, sub, active, more=False):
    """more: the tab has further pages - a tap on the active tab goes to the next one (a » in the corner)."""
    S = 288; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, S - 14, S - 14], radius=30, fill=(34, 36, 42, 255) if active else (22, 23, 27, 255),
                        outline=(255, 176, 0, 255) if active else (68, 70, 78, 255), width=4 if active else 3)
    d.rounded_rectangle([40, 34, S - 40, 42], radius=4, fill=(255, 176, 0, 255) if active else (63, 205, 205, 255))
    f = ImageFont.truetype(str(FONTS / 'BarlowSemiCondensed-Bold.ttf'), 54 if len(name) <= 6 else 46)
    d.text((S / 2, 128), name, font=f, fill=(245, 240, 232, 255), anchor='mm')
    f2 = ImageFont.truetype(str(FONTS / 'BarlowSemiCondensed-Regular.ttf'), 22 if len(sub) > 16 else 26)
    d.text((S / 2, 214), sub, font=f2, fill=(255, 176, 0, 255) if active else (150, 152, 158, 255), anchor='mm')
    if more:
        f3 = ImageFont.truetype(str(FONTS / 'BarlowSemiCondensed-Bold.ttf'), 40)
        d.text((S - 44, 70), '»', font=f3, fill=(255, 176, 0, 255) if active else (150, 152, 158, 255), anchor='mm')
    return im
def tab_action(uid, i, name, active, page_name, target=None, fn=None):
    """target: 0-based index of the page the tab opens (default: page i)."""
    fn = fn or f"{name.replace('/', '')}{'_ON' if active else ''}.png"
    return {'ActionID': uid(f'{page_name}/tab{i}'), 'LinkedTitle': True, 'Name': 'Go to Page',
            'Plugin': {'Name': 'Pages', 'UUID': 'com.elgato.streamdeck.page', 'Version': '1.0'}, 'Resources': None,
            'Settings': {'PageIndex': (i if target is None else target) + 1}, 'State': 0,
            'States': [{'FontFamily': '', 'FontSize': 12, 'FontStyle': '', 'FontUnderline': False, 'Image': f'Images/{fn}',
                        'OutlineThickness': 2, 'ShowTitle': False, 'TitleAlignment': 'middle', 'TitleColor': '#ffffff'}],
            'UUID': 'com.elgato.streamdeck.page.goto'}, fn

def build(out_dir, device_uuid, minify, *, name, uid, tabs, common, layout, tab_col=0):
    """Write <out_dir>/<id>.sdProfile. tabs: [(page, subtitle)] or [(page, subtitle, [(sub-page, subtitle), ...])]:
    a tap on the active tab goes to its next sub-page and back (when swiping, sub-pages follow their tab's page);
    common: {column: factory} for row 0;
    layout: {page: {0: [factories from column 7] or {column: factory}, 1..3: [factory or None per column], 'dials': [...]}};
    tab_col: the column of the first tab (the tabs stay in the same place on every page)."""
    prof = pathlib.Path(out_dir) / f"{uid('profile').upper()}.sdProfile"
    dump = (lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))) if minify else (lambda o: json.dumps(o, ensure_ascii=False, indent=2) + '\n')
    groups = [[(t[0], t[1])] + list(t[2] if len(t) > 2 else []) for t in tabs]          # per tab: its pages (name, subtitle)
    pages = [p for g in groups for p in g]                                             # each tab's pages together, in tab order
    index = {p[0]: n for n, p in enumerate(pages)}
    group_of = {p[0]: ti for ti, g in enumerate(groups) for p in g}
    page_ids = []
    for pname, sub in pages:
        pid = uid(f'page/{pname}'); page_ids.append(pid); pdir = prof / 'Profiles' / pid.upper(); (pdir / 'Images').mkdir(parents=True, exist_ok=True)
        keys, dials = {}, {}
        if len(tabs) > 1:                                          # one page: no tabs, row 0 is free from column 0
            for i, g in enumerate(groups):
                tname, tsub = g[0]; active = i == group_of[pname]; more = len(g) > 1
                if active:
                    names = [p[0] for p in g]; nxt = names[(names.index(pname) + 1) % len(names)]
                    fn = f"{tname.replace('/', '')}{'' if pname == tname else '_' + pname.replace('/', '')}_ON.png"
                    keys[f'{i + tab_col},0'], fn = tab_action(uid, i, tname, True, pname, index[nxt], fn)
                    tab_image(tname, sub, True, more).save(pdir / 'Images' / fn)
                else:
                    keys[f'{i + tab_col},0'], fn = tab_action(uid, i, tname, False, pname, index[tname])
                    tab_image(tname, tsub, False, more).save(pdir / 'Images' / fn)
        for col, make in common.items(): keys[f'{col},0'] = make()
        top = layout[pname].get(0, [])
        for col, make in (top.items() if isinstance(top, dict) else enumerate(top, 7 if len(tabs) > 1 else 0)):
            if make: keys[f'{col},0'] = make()                     # the page's own row-0 keys win over the common ones
        for row in (1, 2, 3):
            for col, make in enumerate(layout[pname].get(row, [])):
                if make: keys[f'{col},{row}'] = make()             # None = empty slot
        for col, make in enumerate(layout[pname]['dials']):
            if make: dials[f'{col},0'] = make()
        for kind, acts in (('k', keys), ('e', dials)):
            for pos, a in acts.items():
                if a['UUID'] != 'com.elgato.streamdeck.page.goto': a['ActionID'] = uid(f'{pname}/{kind}/{pos}')
                for i, sub in enumerate(a.get('Actions') or []): sub['ActionID'] = uid(f'{pname}/{kind}/{pos}/{i}')   # dial stacks
        page = {'Controllers': [{'Actions': dials, 'Type': 'Encoder'}, {'Actions': keys, 'Type': 'Keypad'}], 'Icon': '', 'Name': pname}
        (pdir / 'manifest.json').write_text(dump(page), encoding='utf-8')
    default = uid('page/default'); ddir = prof / 'Profiles' / default.upper(); ddir.mkdir(parents=True, exist_ok=True)
    (ddir / 'manifest.json').write_text(dump({'Controllers': [{'Actions': None, 'Type': 'Keypad'}, {'Actions': None, 'Type': 'Encoder'}], 'Icon': '', 'Name': ''}), encoding='utf-8')
    # InstalledByPluginUUID / PreconfiguredName: what PilotsDeck's Profile Manager sets so the plugin may switch to the profile
    root = {'Device': {'Model': XL_MODEL, 'UUID': device_uuid}, 'InstalledByPluginUUID': 'com.extension.pilotsdeck', 'Name': name,
            'Pages': {'Current': page_ids[0], 'Default': default, 'Pages': page_ids}, 'PreconfiguredName': f'Profiles/{name}', 'Version': '3.0'}
    (prof / 'manifest.json').write_text(dump(root), encoding='utf-8')
    return prof
