"""Key faces for the Citation X CDU pages, drawn after the cockpit CDU (Honeywell, FlightFX). Only the key caps are
pictures; labels are PilotsDeck text (Barlow Semi Condensed Bold, already installed with the profile fonts):
  lsk        - a dark key with the white bar of the line select keys
  fn         - a wide function key (PERF NAV FPL PROG DIR)
  fn_framed  - the same with the thin frame of PREV / NEXT (sized for a 4-letter label at FN_SIZE)
  square     - letter keys, DEL, CLR, SP
  round      - digits, . / -
  brg_<pos>  - the BRG source knob turned to off / vor / adf / fms (labels are text around it)
  irs_<pos>  - the IRS mode knob turned to off / align / nav / att
Writes PilotsDeck/Images/C750/c750_cdu_<face>.png (288 x 288, shown at 144 x 144).

python3 tools/cdu_keys.py [out_dir]"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'PilotsDeck' / 'Images' / 'C750'
S = 288
FACE_TOP, FACE_BOT = (74, 77, 82), (44, 46, 50)            # key face, lit from above
EDGE, SHADOW = (118, 122, 128), (12, 12, 14)
INK = (240, 236, 222)                                      # backlit label colour, also used for the bar and the frame
FN_SIZE = 26                                               # label size of the function keys on the 144 px key (build_xl.py)

def _face(box, shape):
    """A key cap in box (x0, y0, x1, y1): drop shadow, rim, vertical gradient face."""
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); x0, y0, x1, y1 = box
    draw = (lambda dd, b, **k: dd.ellipse(b, **k)) if shape == 'round' else (lambda dd, b, **k: dd.rounded_rectangle(b, radius=22, **k))
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), (x0 + 4, y0 + 10, x1 + 4, y1 + 10), fill=SHADOW + (200,))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    draw(ImageDraw.Draw(im), box, fill=EDGE + (255,))                       # rim
    grad = Image.new('RGBA', (S, S)); g = ImageDraw.Draw(grad)
    for y in range(S):
        t = min(max((y - y0) / max(y1 - y0, 1), 0), 1)
        g.line([(0, y), (S, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(FACE_TOP, FACE_BOT)) + (255,))
    mask = Image.new('L', (S, S), 0); draw(ImageDraw.Draw(mask), (x0 + 5, y0 + 5, x1 - 5, y1 - 5), fill=255)
    im.paste(grad, (0, 0), mask)
    return im

def lsk():
    im = _face((24, 92, S - 24, S - 92), 'rect')
    ImageDraw.Draw(im).rounded_rectangle((S / 2 - 52, S / 2 - 7, S / 2 + 52, S / 2 + 7), radius=4, fill=INK)
    return im

def fn(frame=False):
    im = _face((16, 70, S - 16, S - 70), 'rect')
    if frame:                                                              # the box around PREV / NEXT
        f = ImageFont.truetype(str(HERE.parent / 'Fonts' / 'BarlowSemiCondensed-Bold.ttf'), FN_SIZE * 2)
        d = ImageDraw.Draw(im); l, t, r, b = d.textbbox((S / 2, S / 2), 'NEXT', font=f, anchor='mm')
        d.rectangle((l - 22, t - 22, r + 22, b + 20), outline=INK, width=5)
    return im

FACES = {'lsk': lsk, 'fn': fn, 'fn_framed': lambda: fn(True),
         'square': lambda: _face((34, 34, S - 34, S - 34), 'rect'), 'round': lambda: _face((34, 34, S - 34, S - 34), 'round')}


# ---- BRG source knobs (nav source panel): a black knob with a white pointer, one picture per position ----
BRG_ANGLES = {'off': 180, 'vor': 120, 'adf': 60, 'fms': 0}   # pointer direction, degrees counter-clockwise from 3 o'clock
BRG_C, BRG_R = (144, 200), 50                               # knob centre and radius on the 288 px canvas (72, 100 / 25 on the key)

def brg_knob(angle):
    import math
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); cx, cy = BRG_C; r = BRG_R
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - r + 4, cy - r + 10, cx + r + 4, cy + r + 10), fill=SHADOW + (210,))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(52, 54, 58, 255))                 # skirt
    for i in range(0, 360, 15):                                                         # knurled edge
        a = math.radians(i); d.line([(cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)),
                                     (cx + (r - 9) * math.cos(a), cy + (r - 9) * math.sin(a))], fill=(30, 31, 34, 255), width=3)
    r2 = r - 12; grad = Image.new('RGBA', (S, S)); g = ImageDraw.Draw(grad)
    for y in range(cy - r2, cy + r2 + 1):
        t = (y - (cy - r2)) / (2 * r2); g.line([(0, y), (S, y)], fill=(int(38 - 18 * t),) * 3 + (255,))
    mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=255)
    im.paste(grad, (0, 0), mask)
    a = math.radians(angle); dx, dy = math.cos(a), -math.sin(a)                         # pointer: white line from the centre out
    d.line([(cx + dx * 6, cy + dy * 6), (cx + dx * (r - 4), cy + dy * (r - 4))], fill=INK, width=9)
    return im

FACES.update({f'brg_{k}': (lambda a=a: brg_knob(a)) for k, a in BRG_ANGLES.items()})
# IRS mode knob (OFF / ALIGN / NAV / ATT), the same knob drawing
IRS_ANGLES = {'off': 180, 'align': 135, 'nav': 90, 'att': 45}
FACES.update({f'irs_{k}': (lambda a=a: brg_knob(a)) for k, a in IRS_ANGLES.items()})

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in FACES.items(): draw().save(OUT / f'c750_cdu_{name}.png')
    print(len(FACES), 'faces ->', OUT)
