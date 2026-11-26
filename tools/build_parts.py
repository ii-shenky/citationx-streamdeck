#!/usr/bin/env python3
"""Build "Citation X + Parts 1..3": every key and dial of the + XL profile laid out on Stream Deck + pages (8 keys, 4 dials),
so a Stream Deck + owner can copy what they want into their own pages (Stream Deck: right click -> Copy, then Paste).
The XL profile is device-bound and does not show on a +; this one does. Page tabs are left out, duplicates appear once.

Usage: python3 tools/build_parts.py   (reads ProfileXL/, writes ProfileParts/; run tools/build_xl.py first)
"""
import copy, json, math, pathlib, shutil, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME = 'Citation X + Parts'
NS = uuid.UUID('5d0c5b6e-3f0e-4b0a-9a51-7c1e0c750001')       # stable ids: rebuilding gives the same folders
GOTO = 'com.elgato.streamdeck.page.goto'
MAX_PAGES = 10


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(parts)))


def signature(a):
    s = copy.deepcopy(a); s.pop('ActionID', None)
    return json.dumps(s, sort_keys=True)


def main():
    xl = next((ROOT / 'ProfileXL').glob('*.sdProfile'))
    pages = json.loads((xl / 'manifest.json').read_text(encoding='utf-8'))['Pages']['Pages']
    seen, groups = set(), []
    for pid in pages:
        m = json.loads((xl / 'Profiles' / pid.upper() / 'manifest.json').read_text(encoding='utf-8'))
        keys, dials = [], []
        for ctl in m['Controllers']:
            acts = ctl.get('Actions') or {}
            order = sorted(acts, key=lambda p: (int(p.split(',')[1]), int(p.split(',')[0])))   # reading order: row, column
            for p in order:
                a = acts[p]
                if a['UUID'] == GOTO or signature(a) in seen:
                    continue
                seen.add(signature(a))
                (keys if ctl['Type'] == 'Keypad' else dials).append(a)
        groups.append((m['Name'], keys, dials))

    out = ROOT / 'ProfileParts'
    if out.exists():
        shutil.rmtree(out)
    # Stream Deck allows 10 pages per profile: whole groups go into profiles of up to 10 pages each
    sized = [(g, max(math.ceil(len(g[1]) / 8), math.ceil(len(g[2]) / 4))) for g in groups]
    packs, cur, n = [], [], 0
    for g, pages_needed in sized:
        if cur and n + pages_needed > MAX_PAGES:
            packs.append(cur); cur, n = [], 0
        cur.append(g); n += pages_needed
    packs.append(cur)
    for k, pack in enumerate(packs, 1):
        name = f'{NAME} {k}'
        prof = out / (uid('profile', str(k)).upper() + '.sdProfile')
        ids = []
        for gname, keys, dials in pack:
            n = max(math.ceil(len(keys) / 8), math.ceil(len(dials) / 4))
            for i in range(n):
                title = f'{gname} {i + 1}/{n}' if n > 1 else gname
                pid = uid('page', title)
                kp = {f'{j % 4},{j // 4}': dict(a, ActionID=uid('key', title, str(j))) for j, a in enumerate(keys[8 * i:8 * i + 8])}
                en = {f'{j},0': dict(a, ActionID=uid('dial', title, str(j))) for j, a in enumerate(dials[4 * i:4 * i + 4])}
                page = {'Controllers': [{'Actions': kp, 'Type': 'Keypad'}, {'Actions': en, 'Type': 'Encoder'}], 'Icon': '', 'Name': title}
                d = prof / 'Profiles' / pid.upper(); d.mkdir(parents=True)
                (d / 'manifest.json').write_text(json.dumps(page, indent=1, ensure_ascii=False), encoding='utf-8')
                ids.append(pid)
        default = uid('page', 'default', str(k))
        d = prof / 'Profiles' / default.upper(); d.mkdir(parents=True)
        (d / 'manifest.json').write_text(json.dumps({'Controllers': [{'Actions': None, 'Type': 'Keypad'}, {'Actions': None, 'Type': 'Encoder'}],
                                                     'Icon': '', 'Name': ''}, indent=1), encoding='utf-8')
        root = {'Device': {'Model': '20GBD9901', 'UUID': ''}, 'InstalledByPluginUUID': 'com.extension.pilotsdeck', 'Name': name,
                'Pages': {'Current': ids[0], 'Default': default, 'Pages': ids}, 'PreconfiguredName': f'Profiles/{name}', 'Version': '3.0'}
        (prof / 'manifest.json').write_text(json.dumps(root, indent=1, ensure_ascii=False), encoding='utf-8')
        print(f'{name}: {len(ids)} pages - ' + ', '.join(f'{g[0]} ({len(g[1])} keys, {len(g[2])} dials)' for g in pack))


if __name__ == '__main__':
    main()
