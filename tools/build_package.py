#!/usr/bin/env python3
"""Build the release: a PilotsDeck Profile Package (.ppp, a zip with package.json at the root) that the plugin's
Profile Manager installs - Images and Scripts into the plugin folder, the profiles through Stream Deck - plus
Extras (fonts with a per-user installer, README, LICENSE) that the Profile Manager puts on the desktop.

Usage: python3 tools/build_package.py [--version 1.0.0] [--url https://github.com/...] [--out dist]
The profiles are packed in Stream Deck's export format (.streamDeckProfile = zip of the <UUID>.sdProfile folder) without
the device serial; the XL profile is rebuilt from Profile/ first so the package always matches the source.
"""
import argparse, io, json, pathlib, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILES = [  # (source folder, name shown in Stream Deck, file name - the device type is in the name, Elgato does not export it)
    ('Profile', 'Citation X +', 'Citation X + (Stream Deck +).streamDeckProfile'),
    ('ProfileXL', 'Citation X XL', 'Citation X XL (Stream Deck + XL).streamDeckProfile'),
]
NOTES = ("FONTS: RUN 'Install Fonts.cmd' in the folder this package put on your desktop, then RESTART Stream Deck. "
         "MOBIFLIGHT WASM MODULE (Community folder): REQUIRED. FSUIPC7, free version: OPTIONAL, PAUSE key only. "
         "PROFILE MAPPING: aircraft string msfsffx-c750 -> Citation X XL / Citation X +.")


def profiles():
    """(profile folder, name in Stream Deck, export file name) of the main profiles and the + parts library."""
    out = [(next((ROOT / f).glob('*.sdProfile')), n, fn) for f, n, fn in PROFILES]
    for src in sorted((ROOT / 'ProfileParts').glob('*.sdProfile')):
        n = json.loads((src / 'manifest.json').read_text(encoding='utf-8'))['Name']
        out.append((src, n, f'{n} (Stream Deck +).streamDeckProfile'))
    return sorted(out, key=lambda x: x[1])


def profile_files(src: pathlib.Path, name: str, export: bool):
    """(relative path, bytes) of a profile folder without stale pages. Root manifest: no serial, the release name;
    export=True as Stream Deck exports it (no plugin install marks), else as PilotsDeck installs it (marks kept, so the
    Profile Mapping can switch to it - PreconfiguredName is the mapping's ProfilePath)."""
    root = json.loads((src / 'manifest.json').read_text(encoding='utf-8'))['Pages']
    live = {p.upper() for p in root['Pages'] + [root['Default']]}      # page folders Stream Deck still uses
    for f in sorted(src.rglob('*')):
        rel = f.relative_to(src)
        if f.is_dir() or (len(rel.parts) > 1 and rel.parts[0] == 'Profiles' and rel.parts[1].upper() not in live):
            continue                                                     # folders come with their files; stale pages skipped
        arc = f'{src.name}/{rel.as_posix()}'
        if f.suffix == '.json':
            m = json.loads(f.read_text(encoding='utf-8'))
            if f.parent == src:
                m.get('Device', {})['UUID'] = ''
                m['Name'] = name
                if export:
                    m.pop('InstalledByPluginUUID', None); m.pop('PreconfiguredName', None)
                else:
                    m['InstalledByPluginUUID'] = 'com.extension.pilotsdeck'; m['PreconfiguredName'] = f'Profiles/{name}'
            yield arc, json.dumps(m, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        else:
            yield arc, f.read_bytes()


def export_profile(src: pathlib.Path, name: str) -> bytes:
    """A .streamDeckProfile in memory: the profile folder zipped, root manifest as Stream Deck exports it."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for arc, data in profile_files(src, name, True):
            z.writestr(arc, data)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default='1.0.0')
    ap.add_argument('--url', default='')
    ap.add_argument('--out', default=str(ROOT / 'dist'))
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for tool in ('build_xl.py', 'build_parts.py'):
        subprocess.run([sys.executable, str(ROOT / 'tools' / tool)], check=True, stdout=subprocess.DEVNULL)
    pkg = {'packageformat': 1, 'title': 'FlightFX Citation X - Stream Deck + and + XL',
           'versionpackage': a.version, 'aircraft': 'FlightFX Cessna Citation X V2 (MSFS 2024)',
           'author': 'shiiden', 'url': a.url, 'notes': NOTES, 'versionplugin': '0.9.8.0'}
    target = out / f'CitationX-StreamDeck-{a.version}.ppp'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('package.json', json.dumps(pkg, indent=2, ensure_ascii=False))
        for src, name, fname in profiles():
            z.writestr(f'Profiles/{fname}', export_profile(src, name))
        for f in sorted((ROOT / 'PilotsDeck' / 'Images').rglob('*.png')):
            z.write(f, 'Images/' + f.relative_to(ROOT / 'PilotsDeck' / 'Images').as_posix())
        for f in sorted((ROOT / 'PilotsDeck' / 'Scripts').glob('*.lua')):
            z.write(f, 'Scripts/' + f.name)
        for f in sorted((ROOT / 'Fonts').iterdir()):
            z.write(f, 'Extras/Fonts/' + f.name)
        for f in ('Install Fonts.cmd', 'Install-Fonts.ps1'):
            z.write(ROOT / 'release' / f, 'Extras/' + f)
        z.write(ROOT / 'README.md', 'Extras/README.md')
        z.write(ROOT / 'LICENSE', 'Extras/LICENSE.txt')
    print(target)
    # the same content with the installer script (Install.cmd): fonts, artwork, script, profiles and mapping in one go
    target = out / f'CitationX-StreamDeck-{a.version}.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in ('Install.cmd', 'Install.ps1'):
            z.write(ROOT / 'release' / f, f)
        z.write(ROOT / 'README.md', 'README.md'); z.write(ROOT / 'LICENSE', 'LICENSE.txt')
        for f in sorted((ROOT / 'Fonts').iterdir()):
            z.write(f, 'Fonts/' + f.name)
        for f in sorted((ROOT / 'PilotsDeck').rglob('*')):
            if f.is_file():
                z.write(f, f.relative_to(ROOT).as_posix())
        for src, name, fname in profiles():
            for arc, data in profile_files(src, name, False):
                z.writestr(f'Profiles/{name}/{arc}', data)
            z.writestr(f'Profiles/{fname}', export_profile(src, name))
    print(target)


if __name__ == '__main__':
    main()
