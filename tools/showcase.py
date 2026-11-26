#!/usr/bin/env python3
"""Marketing images: a page of the + XL profile rendered with a sample flight state inside a drawn Stream Deck + XL,
1920x1080 (flightsim.to, Elgato Marketplace). The key and strip images come from preview_render (PilotsDeck's own
drawing rules, the profile's fonts and artwork), so they match the deck closely; values are a scripted flight state.

Usage: python3 tools/showcase.py <out_dir> [PAGE ...]      PAGE = FLIGHT, NAV/COM, SYSTEMS, CONFIG, GROUND, CDU, A-Z
"""
import json, pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import preview_render as pr

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = str(ROOT / 'Fonts' / 'BarlowSemiCondensed-Bold.ttf')
FONT_R = str(ROOT / 'Fonts' / 'BarlowSemiCondensed-Regular.ttf')

# ---- sample states (strings, as PilotsDeck hands them to the renderer) -----------------------------------------------
POWER = {'(A:ELECTRICAL MAIN BUS VOLTAGE, Volts)': '28'}
COMMON = {
    '(A:MASTER CAUTION ACTIVE, Boolean)': '0', '(A:MASTER WARNING ACTIVE, Boolean)': '0',
    'lua:citx:AtcAlt': 'FL350', 'lua:citx:AtcMismatch': '0', 'lua:citx:QnhStr': 'STD', 'lua:citx:QnhBad': '0',
    'lua:citx:NextWpt': 'BALEN 42 NM', '(A:FLAPS CURRENT SPEED LIMITATION, knots)': '0', 'lua:citx:FlapOver': '0',
    '(A:TOTAL AIR TEMPERATURE, celsius)': '-24', 'lua:citx:IcingCond': '0', '(A:STRUCTURAL ICE PCT, percent)': '0',
    'L:PARKING_BRAKE_HANDLE': '0', '(A:SIM ON GROUND, Bool)': '0',
}
CRUISE = {
    **POWER, **COMMON,
    # autopilot: AP, YD, FD, ATS on; NAV (FMS) and VNAV
    '(A:AUTOPILOT MASTER, Bool)': '1', '(A:AUTOPILOT YAW DAMPER, Bool)': '1', '(A:AUTOPILOT FLIGHT DIRECTOR ACTIVE, Bool)': '1',
    'L:ATS_IS_ON': '1', '(A:AUTOPILOT NAV1 LOCK, Bool)': '1', 'L:VTX_VNAV_STATE': '1', '(A:GPS DRIVES NAV1, Bool)': '1',
    '(A:AUTOPILOT HEADING LOCK, Bool)': '0', '(A:AUTOPILOT ALTITUDE LOCK, Bool)': '1', '(A:AUTOPILOT FLIGHT LEVEL CHANGE, Bool)': '0',
    '(A:AUTOPILOT APPROACH HOLD, Bool)': '0', '(A:AUTOPILOT GLIDESLOPE ARM, Bool)': '0', '(A:AUTOPILOT GLIDESLOPE ACTIVE, Bool)': '0',
    '(A:AUTOPILOT BACKCOURSE HOLD, Bool)': '0', '(A:AUTOPILOT MAX BANK ID, Number)': '0',
    '(A:AUTOPILOT VERTICAL HOLD, Bool)': '0', '(A:AUTOPILOT VERTICAL HOLD VAR, feet)': '0',
    '(A:VERTICAL SPEED, feet per minute)': '0', 'lua:citx:VsAct': '0', 'lua:citx:AltSelTime': '',
    'L:KNOB_ATS_FMS_MAN': '0', '(A:AUTOPILOT MANAGED SPEED IN MACH, Bool)': '1', '(A:AUTOPILOT MACH HOLD VAR, Number)': '0.86',
    '(A:AUTOPILOT AIRSPEED HOLD VAR, Knots)': '290', '(A:AIRSPEED INDICATED, Knots)': '268', '(A:INDICATED ALTITUDE, feet)': '35000',
    'lua:citx:SpdInfo': 'GS 512   TAS 497',
    '(A:AUTOPILOT HEADING LOCK DIR, degrees)': '112', '(A:AMBIENT WIND VELOCITY, knots)': '46', 'lua:citx:HdgBugTxt': 'R4',
    'lua:citx:WindComp': 'TAIL 15',
    '(A:AUTOPILOT ALTITUDE LOCK VAR, Feet)': '35000', 'lua:citx:AltDir': '0',
    '(A:NAV OBS:1, degrees)': '112', '(A:NAV HAS NAV:1, Bool)': '1', '(A:NAV HAS GLIDE SLOPE:1, Bool)': '0',
    '(A:NAV HAS LOCALIZER:1, Bool)': '0', 'lua:citx:CdiSlot': '0', 'lua:citx:GsSlot': '0',
    '(A:KOHLSMAN SETTING HG, inHg)': '29.92', '(A:KOHLSMAN SETTING MB, Millibars)': '1013', 'lua:citx:BaroWarn': '0',
    'L:SD_CITX_TA': '6000',
    'lua:citx:EteStr': '1:42', 'lua:citx:FuelDest': '6 850',
    '(A:AMBIENT TEMPERATURE, celsius)': '-54', 'lua:citx:IsaDev': 'ISA +1', '(A:TOTAL WEIGHT, pounds)': '31 420',
    '(A:CG PERCENT, percent)': '21',
    '(A:NAV SOUND:1, Bool)': '0', '(A:NAV IDENT:1, String)': 'LCA',
    'L:nav_panel_L_brg_knob_1': '1', 'L:nav_panel_L_brg_knob_2': '3',
    'L:VTX_cabin_altitude': '7400', 'L:VTX_cabin_diff_pressure': '9.2',
    'lua:citx:DescNM': '105', 'lua:citx:DescVS': '2 400',
    'L:pfd-1-btn-ra-baro': '0', 'lua:citx:TimerStr': '00:00', 'lua:citx:TimerSec': '0', 'L:SD_TMR_RUN': '0',
    # radios
    'lua:citx:FreqStr(1)': '124.200', 'lua:citx:FreqStr(2)': '121.900', 'lua:citx:FreqStr(3)': '128.550',
    'lua:citx:FreqStr(4)': '122.800', 'L:SD_CITX_COM1_FINE': '0', 'L:SD_CITX_COM2_FINE': '0',
    'lua:citx:NavLbl': 'NAV1', 'lua:citx:NavStr(1)': '112.80', 'lua:citx:NavStr(2)': '110.30', 'L:SD_CITX_NAV1_FINE': '0',
    'lua:citx:NavDme': '38.2 NM', '(A:TRANSPONDER CODE:1, Bco16)': '4721', 'L:SD_CITX_XPDR_POS': '0',
    '(A:TRANSPONDER STATE:1, Enum)': '4', '(L:knob_wxr_radar, number)': '2', '(L:knob_wxr_tilt, number)': '44',
    'L:VTX_WX_AUTO_MODE': '0', '(A:SIMULATION RATE, number)': '1', 'L:knob_irs_l': '2', 'L:knob_irs_r': '2',
    'L:VTX_IRS_L_ALIGN_READY': '0', 'L:VTX_IRS_R_ALIGN_READY': '0', '(A:COM TRANSMIT:2, Bool)': '0',
    '(A:COM RECEIVE:2, Bool)': '1', 'L:SD_NEVER': '0', 'L:SD_CITX_NAVSEL': '0', '(A:TRANSPONDER IDENT:1, Bool)': '0',
    'L:push_pilot_1_mfdwx': '1',
    # CONFIG in cruise: checklists up to 10 000 FT done, the approach ones still open
    **{f'lua:citx:ClDone({k})': '1' for k in (11, 12, 1, 2, 3, 4, 13, 14)},
    **{f'lua:citx:ClItem({k * 10 + i})': '1' for k in (11, 12, 1, 2, 3, 4, 13, 14) for i in range(1, 5)},
    **{f'lua:citx:ClDone({k})': '0' for k in (5, 6, 7, 8)},
    'lua:citx:ClItem(51)': '1', 'lua:citx:ClItem(52)': '0', 'lua:citx:ClItem(53)': '0', 'lua:citx:ClItem(54)': '0',
    **{f'lua:citx:ClItem({k * 10 + i})': '0' for k in (6, 7, 8) for i in range(1, 5)},
    'lua:citx:Pair(1)': '0', 'lua:citx:Pair(2)': '1', 'lua:citx:Pair(3)': '0', 'lua:citx:Pair(4)': '0', 'L:switch_slats_ai': '1',
    'L:switch_landing_light_lh': '1', 'L:switch_landing_light_rh': '1', 'L:switch_landing_taxi': '1', 'L:switch_lights_recog': '1',
    'L:switch_lights_nav': '0', 'L:switch_lights_recognition_anticollision': '0', 'L:switch_lights_flood': '1',
    'L:switch_seatBelt': '1', 'L:lights_emerg_lt': '1',
    '(A:FLAPS HANDLE INDEX, Number)': '0', '(A:SPOILERS HANDLE POSITION, percent)': '0', 'spBreakSelected': '0',
    '(A:SPOILERS HANDLE POSITION, percent over 100)': '0', '(A:ELEVATOR TRIM PCT, percent)': '12', 'L:SD_TRIM_AX': '0',
    '(A:AILERON TRIM PCT, percent)': '0', '(A:RUDDER TRIM PCT, percent)': '0', 'lua:citx:MinStr': 'BARO 380',
    '(A:ELEVATOR TRIM POSITION, degrees)': '1.2',
}
# engine start on the ground: APU running, left engine started, right engine on its way
START = {
    **POWER, **COMMON, '(A:SIM ON GROUND, Bool)': '1', 'L:PARKING_BRAKE_HANDLE': '1', 'lua:citx:AtcAlt': 'FL350',
    'lua:citx:QnhStr': '1015', 'lua:citx:NextWpt': 'LCLK 25 · RW22',
    'L:electrical_switch_apu_master': '1', 'L:electrical_switch_apu_starter': '1', '(A:APU PCT RPM, Number)': '1.0',
    'L:switch_apu_bleed': '1', 'L:BLEED_PRESSURE_PSI': '38',
    'lua:citx:FuelLbs(0)': '9 600', 'lua:citx:FuelLbs(1)': '4 800', 'lua:citx:FuelLbs(2)': '4 800', 'lua:citx:FuelImb': '0',
    '(A:TURB ENG CORRECTED N2:1, Percent)': '52.4', '(A:TURB ENG CORRECTED N2:2, Percent)': '24.1',
    '(A:TURB ENG IS IGNITING:1, Bool)': '0', '(A:TURB ENG IS IGNITING:2, Bool)': '1',
    '(A:ENG FUEL FLOW PPH:1, Pounds per hour)': '610', '(A:ENG FUEL FLOW PPH:2, Pounds per hour)': '280',
    '(A:ENG OIL PRESSURE:1, psf)': '8350', '(A:ENG OIL PRESSURE:2, psf)': '3600',
    '(A:ENG OIL TEMPERATURE:1, Celsius)': '58', '(A:ENG OIL TEMPERATURE:2, Celsius)': '22',
    'L:knob_xfeed': '2', '(A:PRESSURIZATION CABIN ALTITUDE GOAL, feet)': '0', 'L:VTX_cabin_altitude': '0',
    'L:electrical_switch_avionics_master_1': '0', 'L:electrical_switch_avionics_master_2': '0',
    'L:electrical_switch_generator_l': '0', 'L:electrical_switch_generator_r': '0',
    'L:electrical_switch_battery_1': '0', 'L:electrical_switch_battery_2': '0', 'L:switch_load_shed': '1',
    'L:switch_stby_pwr': '0', 'L:electrical_switch_ext_pwr': '1', 'L:switch_fuel_boost_lh': '2', 'L:switch_fuel_boost_rh': '2',
    'L:switch_ignition_l': '2', 'L:switch_ignition_r': '2',
    '(A:GENERAL ENG STARTER ACTIVE:1, Bool)': '0', '(A:GENERAL ENG STARTER ACTIVE:2, Bool)': '1',
    'L:ENG_CUTOFF_1': '1', 'L:ENG_CUTOFF_2': '1', 'L:electrical_switch_apu': '0',
    'lua:citx:ClDone(15)': '1', **{f'lua:citx:ClItem({i})': '1' for i in range(151, 157)}, 'lua:citx:ClItem(111)': '1',
    'FADEC_MAX_N1_1': '92', 'FADEC_MAX_N1_2': '92', 'L:ATS_IS_ON': '0',
    '(A:TURB ENG CORRECTED N1:1, Number)': '0.246', '(A:TURB ENG CORRECTED N1:2, Number)': '0.081', '(A:ENG COMBUSTION:1, Bool)': '1', '(A:ENG COMBUSTION:2, Bool)': '0', '(A:TURB ENG THROTTLE COMMANDED N1:1, percent)': '24', '(A:TURB ENG THROTTLE COMMANDED N1:2, percent)': '0',
    '(A:TURB ENG ITT:1, Number)': '785', '(A:TURB ENG ITT:2, Number)': '661', 'FADEC_ITT_RED_1': '1000', 'FADEC_ITT_RED_2': '1000', 'L:SD_NEVER': '0',
    'L:switch_aux_pump': '1', 'L:SWITCH_ANTI_SKID': '1', 'L:switch_pac_bleed': '1',
    # GROUND: main door open, GPU connected, chocks and engine covers off, pitot covers still on
    'L:VTX_C750_MAIN_DOOR': '1', 'L:VTX_C750_LUGGAGE_DOOR': '0', 'L:VTX750_GROUND_POWER_CONN': '1',
    '(A:COVER ON:0, Bool)': '1', '(A:COVER ON:1, Bool)': '0', '(A:COVER ON:2, Bool)': '1', '(A:COVER ON:3, Bool)': '0',
    'L:XMLVAR_YokeHidden1': '0', 'L:XMLVAR_YokeHidden2': '1', '(A:TOTAL WEIGHT, pounds)': '33 900', '(A:CG PERCENT, percent)': '19',
    '(A:AMBIENT TEMPERATURE, celsius)': '22', 'lua:citx:IsaDev': 'ISA +7',
    '(A:FLAPS HANDLE INDEX, Number)': '2', '(A:SPOILERS HANDLE POSITION, percent)': '0', 'spBreakSelected': '0',
    '(A:SPOILERS HANDLE POSITION, percent over 100)': '0', '(A:ELEVATOR TRIM PCT, percent)': '18', 'L:SD_TRIM_AX': '0',
    '(A:AILERON TRIM PCT, percent)': '0', '(A:RUDDER TRIM PCT, percent)': '0', 'lua:citx:MinStr': 'BARO 380',
    '(A:SIMULATION RATE, number)': '1',
}
PAGES = {'FLIGHT': ('Autopilot panel as in the cockpit', CRUISE), 'NAV/COM': ('Radios, IRS, weather radar', CRUISE),
         'SYSTEMS': ('Engine start: checklist, START / RUN, engine table', START),
         'CONFIG': ('Twelve checklists that read the aircraft', CRUISE), 'GROUND': ('Doors, covers, chocks, GPU', START),
         'CDU': ('CDU: line select keys at the edges, as in the cockpit', CRUISE), 'A-Z': ('CDU keyboard', CRUISE)}

# ---- drawing -----------------------------------------------------------------------------------------------------------
KEY, GAP, DIAL = 144, 26, 118


def rounded(img, r):
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], r, fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0)); out.paste(img, (0, 0), m); return out


def device(page_manifest, state):
    """The page drawn as a Stream Deck + XL: 9 x 4 keys, the touch strip and six dials on a dark body."""
    pr.S.clear(); pr.S.update(state)
    d = json.loads(page_manifest.read_text(encoding='utf-8'))
    acts = {c['Type']: (c.get('Actions') or {}) for c in d['Controllers']}
    cols, rows, ndial = 9, 4, 6
    kw = cols * KEY + (cols - 1) * GAP
    strip_w, strip_h = 6 * 200, 100
    pad = 70
    W = kw + 2 * pad; H = pad + rows * KEY + (rows - 1) * GAP + 46 + strip_h + 40 + DIAL + pad
    body = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    for i in range(H):                                       # body: dark, a touch lighter at the top
        c = round(30 - 14 * i / H); bd.line([(0, i), (W, i)], fill=(c, c + 1, c + 4, 255))
    body = rounded(body, 46); bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([1, 1, W - 2, H - 2], 46, outline=(70, 72, 78, 255), width=2)
    page_dir = page_manifest.parent
    for pos, a in acts.get('Keypad', {}).items():
        x, y = map(int, pos.split(','))
        st = a['Settings'].get('settingsStore'); s0 = (a.get('States') or [{}])[0]
        if st: tile = pr.draw(st, KEY, KEY, s0)
        else:
            f = page_dir / (s0.get('Image') or '')
            tile = Image.open(f).convert('RGB').resize((KEY, KEY), Image.LANCZOS) if f.is_file() else Image.new('RGB', (KEY, KEY), 'black')
        X, Y = pad + x * (KEY + GAP), pad + y * (KEY + GAP)
        bd.rounded_rectangle([X - 5, Y - 5, X + KEY + 5, Y + KEY + 5], 22, fill=(8, 8, 10, 255))   # key well
        t = rounded(tile.convert('RGBA'), 18); body.alpha_composite(t, (X, Y))
    sy = pad + rows * KEY + (rows - 1) * GAP + 46; sx = (W - strip_w) // 2
    bd.rounded_rectangle([sx - 8, sy - 8, sx + strip_w + 8, sy + strip_h + 8], 14, fill=(8, 8, 10, 255))
    strip = Image.new('RGB', (strip_w, strip_h), 'black')
    for pos, a in acts.get('Encoder', {}).items():
        x = int(pos.split(',')[0]); st = a['Settings'].get('settingsStore')
        if st: strip.paste(pr.draw(st, 200, 100, (a.get('States') or [{}])[0]), (x * 200, 0))
    body.alpha_composite(rounded(strip.convert('RGBA'), 8), (sx, sy))
    dy = sy + strip_h + 40
    for i in range(ndial):                                   # dials: knurled ring, darker cap, a soft highlight
        cx = sx + i * 200 + 100; cy = dy + DIAL // 2; r = DIAL // 2
        bd.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=(6, 6, 8, 255))
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(48, 50, 55, 255))
        for k in range(48):
            import math
            ang = 2 * math.pi * k / 48
            bd.line([(cx + (r - 7) * math.cos(ang), cy + (r - 7) * math.sin(ang)), (cx + r * math.cos(ang), cy + r * math.sin(ang))],
                    fill=(30, 31, 35, 255), width=2)
        bd.ellipse([cx - r + 11, cy - r + 11, cx + r - 11, cy + r - 11], fill=(36, 37, 41, 255))
        bd.arc([cx - r + 11, cy - r + 11, cx + r - 11, cy + r - 11], 200, 320, fill=(72, 74, 80, 255), width=2)
    return body


def poster(dev, title, subtitle, page):
    W, H = 1920, 1080
    bg = Image.new('RGB', (W, H)); g = ImageDraw.Draw(bg)
    for y in range(H):                                        # deep blue-grey, darker at the bottom
        t = y / H; g.line([(0, y), (W, y)], fill=(round(28 - 16 * t), round(34 - 20 * t), round(46 - 26 * t)))
    glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).ellipse([W * 0.15, H * 0.25, W * 0.85, H * 1.1], fill=60)
    bg = Image.composite(Image.new('RGB', (W, H), (60, 80, 110)), bg, glow.filter(ImageFilter.GaussianBlur(160)))
    scale = min(1700 / dev.width, 860 / dev.height)
    d = dev.resize((round(dev.width * scale), round(dev.height * scale)), Image.LANCZOS)
    x, y = (W - d.width) // 2, H - d.height - 40
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x + 10, y + 30, x + d.width + 10, y + d.height + 40], 40, fill=(0, 0, 0, 170))
    bg = bg.convert('RGBA'); bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28))); bg.alpha_composite(d, (x, y))
    dr = ImageDraw.Draw(bg)
    dr.text((60, 52), title, font=ImageFont.truetype(FONT, 54), fill=(236, 236, 228))
    dr.text((62, 118), subtitle, font=ImageFont.truetype(FONT_R, 32), fill=(160, 170, 185))
    dr.text((W - 60, 66), page, font=ImageFont.truetype(FONT, 40), fill=(255, 176, 0), anchor='ra')
    return bg.convert('RGB')


def main():
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    want = sys.argv[2:] or list(PAGES)
    xl = next((ROOT / 'ProfileXL').glob('*.sdProfile'))
    for pid in json.loads((xl / 'manifest.json').read_text(encoding='utf-8'))['Pages']['Pages']:
        man = xl / 'Profiles' / pid.upper() / 'manifest.json'
        name = json.loads(man.read_text(encoding='utf-8'))['Name']
        if name not in want: continue
        sub, state = PAGES[name]
        img = poster(device(man, state), 'FlightFX Citation X  ·  Stream Deck + XL', sub, name)
        f = out / f"citx_xl_{name.replace('/', '').lower()}.png"; img.save(f); print(f)


if __name__ == '__main__':
    main()
