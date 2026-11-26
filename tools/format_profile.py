#!/usr/bin/env python3
"""Pretty-print Stream Deck profile JSON so git diffs are readable.

Stream Deck saves manifest.json as one line; it reads indented JSON just as well.
Usage: python3 tools/format_profile.py [--check] [dir ...]   (default: Profile/)
--check: only report files that are not formatted (exit 1 if any).
"""
import json, pathlib, sys

def fmt(path):
    raw = path.read_bytes()
    bom = raw.startswith(b'\xef\xbb\xbf')
    data = json.loads(raw.decode('utf-8-sig'))
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    out = (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')
    return raw, out

def main(argv):
    check = '--check' in argv
    dirs = [a for a in argv if a != '--check'] or [pathlib.Path(__file__).resolve().parent.parent / 'Profile']
    bad = 0
    for d in map(pathlib.Path, dirs):
        for p in sorted(d.rglob('*.json')):
            raw, out = fmt(p)
            if raw == out:
                continue
            bad += 1
            if check:
                print('not formatted:', p)
            else:
                p.write_bytes(out)
                print('formatted:', p)
    return 1 if check and bad else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
