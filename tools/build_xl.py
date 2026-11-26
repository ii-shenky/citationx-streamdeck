#!/usr/bin/env python3
"""Build the Stream Deck + XL profile (9x4 keys, 6 dials) from the Stream Deck + profile.

The + profile in Profile/ is the single source (shared machinery: xl_lib.py): every key and dial is copied from it
by position, a few strip-only displays are re-laid-out as keys, and the eleven pages
become four (FLIGHT, NAV/COM, SYSTEMS, CONFIG) with a permanent tab row on top.

Usage: python3 tools/build_xl.py [--device-uuid "@(1)[...]"] [--out ProfileXL]
"""
import argparse, copy, json, pathlib, re, uuid
from PIL import ImageFont
import xl_lib
from xl_lib import ROOT, FONTS, at, img, by_text, by_val

SRC = next((ROOT / 'Profile').glob('*.sdProfile'))
uid = xl_lib.namespace(uuid.UUID('6f0c1d1e-7a35-4f0b-9c0e-c750c750c750'))

PAGES = {'AP': '7236B526', 'AP+': 'BB434090', 'INFO': '7583E4EE', 'NAV': 'CDB410A9', 'RADIO': 'E0CF1A53',
         'LIGHTS': 'E894BDDE', 'FLAPS': '429405E6', 'ELEC': '28B8346E', 'ENG': 'A5C77AA2', 'CHECK': 'BA0FA051'}
src = xl_lib.load_pages(SRC, PAGES)

def K(page, pos): return copy.deepcopy(src[page]['Keypad'][pos])
def E(page, pos):
    """A dial from the + profile without its page-swipe labels (« PAGE / PAGE »)."""
    a = copy.deepcopy(src[page]['Encoder'][pos]); ss = a['Settings']['settingsStore']
    keep = [e for e in ss['DisplayElements'].values() if not re.match(r'^(«.*|.*»)$', (e.get('Text') or '').strip())]
    ss['DisplayElements'] = {str(i): e for i, e in enumerate(keep)}
    return a
def els(page, pos): return list(src[page]['Encoder'][pos]['Settings']['settingsStore']['DisplayElements'].values())

SHELL = src['INFO']['Keypad']['0,0']                              # ROUTE: a display-only key
TITLE = by_text(list(SHELL['Settings']['settingsStore']['DisplayElements'].values()), 'ROUTE')
PLAIN = copy.deepcopy(TITLE); PLAIN['Manipulators'] = {}
def title(t, fs=13): return at(PLAIN, 72, 14, fs, t)
def key(elements, down=None):
    a = copy.deepcopy(SHELL); ss = a['Settings']['settingsStore']
    ss['DisplayElements'] = {str(i): e for i, e in enumerate(elements)}
    ss['ActionCommands'] = {k: {} for k in ss['ActionCommands']}
    if down:
        cmds = {}
        for i, c in enumerate(down):
            c = copy.deepcopy(c); c['DeckCommandType'] = 0; cmds[str(i)] = c
        ss['ActionCommands']['KEY_DOWN'] = cmds
    for st in a.get('States') or []: st['Title'] = ''
    return a
def cmds(page, pos, kind): return list(src[page]['Encoder'][pos]['Settings']['settingsStore']['ActionCommands'][kind].values())

# ---- strip displays re-laid-out as keys -------------------------------------------------
def k_descent():
    L = els('AP+', '3,0')
    return key([title('DESCENT 3:1'), at(by_val(L, 'lua:citx:DescNM'), 72, 60, 24), at(by_val(L, 'lua:citx:DescVS'), 72, 102, 14),
                at(by_text(L, 'AT / BELOW ALT SEL'), 72, 78, 11)])
def k_timer():
    L = els('AP+', '2,0')
    return key([title('HOLD TIMER'), at(by_val(L, 'lua:citx:TimerStr'), 72, 66, 28), at(by_text(L, 'RUN'), 72, 114, 12),
                at(by_text(L, 'PUSH START/STOP · TAP RESET'), 72, 114, 10, 'PUSH START / STOP')], cmds('AP+', '2,0', 'DIAL_DOWN'))
def k_button(name, body, command):
    """A framed push button (the MIC key as the shell): title above, a text or a live value inside."""
    a = K('RADIO', '2,0'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values()); val = L[2]
    if isinstance(body, str): inner = at(PLAIN, 72, 84, 19, body, '#C7C7C7')
    else: inner = dict(copy.deepcopy(body), Position=val['Position'], Size=val['Size'], FontSize=19, Center=val['Center'],
                       FontName=val['FontName'], FontStyle=val['FontStyle'], Color=val['Color'], TextHorizontalAlignment=1, TextVerticalAlignment=1)
    out = [e for e in L if e['ElementType'] == 2] + [at(by_text(L, 'MIC'), 72, 14, None, name), inner]
    ss['DisplayElements'] = {str(i): e for i, e in enumerate(out)}
    ss['ActionCommands'] = {k: {} for k in ss['ActionCommands']}
    c = copy.deepcopy(command); c['DeckCommandType'] = 0
    ss['ActionCommands']['KEY_DOWN'] = {'0': c}
    return a
def k_timer_reset(): return k_button('HOLD TIMER', 'RESET', cmds('AP+', '2,0', 'TOUCH_TAP')[0])
def k_pause(): return k_button('SIM', 'PAUSE', cmds('INFO', '0,0', 'DIAL_DOWN')[0])                 # FSUIPC offset 0x0262
def k_xpdr_mode():                                                                                  # ALT <-> STBY, as the tap on the XPDR strip
    return k_button('XPDR MODE', by_val(els('RADIO', '3,0'), '(A:TRANSPONDER STATE'), cmds('RADIO', '3,0', 'TOUCH_TAP')[0])
def k_fuel():
    L, L1 = els('ENG', '0,0'), els('ENG', '1,0')
    return key([title('FUEL LBS'), at(by_text(L, 'TOT'), 28, 48, 12), at(by_val(L, 'lua:citx:FuelLbs(0)'), 90, 48, 21),
                at(by_text(L, 'L'), 38, 82, 12), at(by_text(L, 'L'), 106, 82, 12, 'R'),
                at(by_val(L, 'lua:citx:FuelLbs(1)'), 38, 108, 17), at(by_val(L1, 'lua:citx:FuelLbs(2)'), 106, 108, 17)])
def k_eng(n):
    L1, L2 = els('ENG', '1,0'), els('ENG', '2,0'); V = L1 if n == 1 else L2
    names = [e for e in L1 if e.get('Text') in ('N2', 'FUEL', 'OIL')]                       # N2, FUEL, OIL, OIL in order of rows
    names.sort(key=lambda e: e['Position'][1])
    rows = [('N2', '%', 'TURB ENG CORRECTED N2'), ('FF', 'PPH', 'ENG FUEL FLOW PPH'), ('OIL', 'PSI', 'ENG OIL PRESSURE'), ('OIL', '°C', 'ENG OIL TEMPERATURE')]
    out = [title('ENG L' if n == 1 else 'ENG R'), at(by_text(V, 'IGN'), 122, 14, 11)]
    for (nm, unit, var), src_name, y in zip(rows, names, (42, 68, 94, 120)):
        out += [at(src_name, 22, y, 11, nm), at(by_val(V, f'(A:{var}:{n}'), 78, y, 16), at(by_text(L2, unit), 126, y, 10)]
    return key(out)
def k_toconfig():
    L = els('FLAPS', '1,0')
    return key([title('T/O CONFIG'), at(by_text(L, 'FLAPS'), 40, 52, 15), at(by_text(L, 'BRAKE'), 104, 52, 15),
                at(by_text(L, 'SPLR'), 40, 86, 15), at(by_val(L, '(A:ELEVATOR TRIM POSITION'), 72, 118, 14),
                at(by_text(L, 'AIRBORNE'), 72, 70, 15)])
def k_check(pos):
    """A checklist from the strip (two columns) as a key (one column), in reading order."""
    L = els('CHECK', pos); head = L[0]
    items = sorted([e for e in L[1:] if e.get('Manipulators')], key=lambda e: (e['Position'][1], e['Position'][0]))
    dots = [e for e in L if e.get('Text') == '•']
    f = ImageFont.truetype(str(FONTS / 'BarlowSemiCondensed-Bold.ttf'), round(17 * 4 / 3))
    out = [at(head, 72, 15, 13)]
    for it, y in zip(items, (40, 63, 86, 109)):
        out.append(at(it, 72, y, 17))
        if any(d['Position'][1] == it['Position'][1] and 0 < it['Position'][0] - d['Position'][0] < 60 for d in dots):   # item the push sets
            out.append(at(dots[0], round(72 - f.getlength(it['Text']) / 2 - 8), y, 16))
    c = src['CHECK']['Encoder'][pos]['Settings']['settingsStore']['ActionCommands']['DIAL_DOWN']
    return key(out, list(c.values()) or None)
def k_cl(n, head, items, push):
    """A six-line checklist key (CL[n] in citx.lua): the strip checklist's elements, packed tighter.
    items: (text, set_by_push); each line turns green on ClItem(n*10+i), the head on ClDone(n)."""
    L = els('CHECK', '0,0'); h, it = L[0], L[1]
    dot = next(e for e in L if e.get('Text') == '•')
    f = ImageFont.truetype(str(FONTS / 'BarlowSemiCondensed-Bold.ttf'), round(15 * 4 / 3))
    h = at(h, 72, 9, 12, head); h['Manipulators']['0']['Conditions']['0']['Address'] = f'lua:citx:ClDone({n})'
    out = [h]
    for i, (text, dotted) in enumerate(items, 1):
        y = 9 + 20 * i
        e = at(it, 72, y, 15, text); e['Manipulators']['0']['Conditions']['0']['Address'] = f'lua:citx:ClItem({n * 10 + i})'
        out.append(e)
        if dotted: out.append(at(dot, round(72 - f.getlength(text) / 2 - 7), y, 14))
    c = copy.deepcopy(src['CHECK']['Encoder']['0,0']['Settings']['settingsStore']['ActionCommands']['DIAL_DOWN']['0'])
    c['Address'] = push
    return key(out, [c])
def k_eng_start():
    return k_cl(15, 'ENG START', [('BEACON', True), ('BOOST L+R', True), ('IGN L+R', True), ('APU BLEED', True),
                                  ('BUS > 21 V', False), ('BLEED > 10 PSI', False)],
                # push: beacon on; boost, ignition OFF -> NORM; APU bleed OFF -> ON (MAX and ON are left as they are)
                '0 (>L:switch_lights_recognition_anticollision) '
                '(L:switch_fuel_boost_lh) 1 == if{ 2 (>L:switch_fuel_boost_lh) } '
                '(L:switch_fuel_boost_rh) 1 == if{ 2 (>L:switch_fuel_boost_rh) } '
                '(L:switch_ignition_l) 1 == if{ 2 (>L:switch_ignition_l) } '
                '(L:switch_ignition_r) 1 == if{ 2 (>L:switch_ignition_r) } '
                '(L:switch_apu_bleed) 2 == if{ 1 (>L:switch_apu_bleed) }')
def k_light(pos, name, fs=19):
    """A push-only dial from the LIGHTS strip (EMER LT, SEAT BELT) as a key in the style of the light keys."""
    a = K('LIGHTS', '2,1'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values())      # BEACON as the shell
    val = copy.deepcopy(next(e for e in els('LIGHTS', pos) if e['ElementType'] == 5))
    val.update(Position=L[2]['Position'], Size=L[2]['Size'], FontSize=fs, Center=L[2]['Center'], FontName=L[2]['FontName'], FontStyle=L[2]['FontStyle'])
    L[1]['Text'] = name
    ss['DisplayElements'] = {str(i): e for i, e in enumerate([L[0], L[1], val])}
    c = copy.deepcopy(cmds('LIGHTS', pos, 'DIAL_DOWN')[0]); c['DeckCommandType'] = 0
    ss['ActionCommands'] = {k: {} for k in ss['ActionCommands']}; ss['ActionCommands']['KEY_DOWN'] = {'0': c}
    return a
def k_toggle(pos):
    """A toggle from the ELEC strip (LOAD SHED, BATT, APU GEN) as a key with the geometry of the other toggle keys."""
    L = [x for x in els('ELEC', pos) if not re.match(r'^(«.*|.*»)$', (x.get('Text') or '').strip())]
    texts = [x for x in L if x['ElementType'] == 4 and x.get('Text')]; images = [x for x in L if x['ElementType'] == 2]
    head, labels = texts[0], sorted(texts[1:], key=lambda x: x['Position'][1])
    has_mid = any('_mid.png' in x.get('Image', '') for x in images)
    ys = (-27, 5, 39) if has_mid else (-27, 39)                  # up / mid / down, as on the L GEN and AVION keys
    out = [dict(copy.deepcopy(head), Position=[0, -64], Size=[144, 144], FontSize=14)]
    out += [dict(copy.deepcopy(x), Position=[-38, y], Size=[144, 144], FontSize=14) for x, y in zip(labels, ys)]
    out += [dict(copy.deepcopy(x), Position=[58, 16], Size=[64, 127]) for x in images]
    return key(out, cmds('ELEC', pos, 'DIAL_DOWN'))
def k_antiskid():
    """ANTISKID (HubHop: L:SWITCH_ANTI_SKID): the AVION 1 toggle key with the variable swapped. Up = OFF, down = NORM as in the cockpit."""
    a = json.loads(json.dumps(src['ELEC']['Keypad']['2,0']).replace('L:electrical_switch_avionics_master_1', 'L:SWITCH_ANTI_SKID'))
    for x in a['Settings']['settingsStore']['DisplayElements'].values():
        x['Text'] = {'AVION 1': 'ANTISKID', 'ON': 'OFF', 'OFF': 'NORM'}.get(x.get('Text'), x.get('Text'))
    return a
def k_apu_bleed():
    """APU BLEED as a toggle key (the PAC BLEED key with the variable swapped): same push as on the APU dial, plus bleed pressure."""
    a = json.loads(json.dumps(src['ELEC']['Keypad']['0,1']).replace('L:switch_pac_bleed', 'L:switch_apu_bleed'))
    ss = a['Settings']['settingsStore']
    for x in ss['DisplayElements'].values():
        x['Text'] = {'PAC BLEED': 'APU BLEED', 'HP': 'MAX', 'NORM': 'ON'}.get(x.get('Text'), x.get('Text'))
    ss['DisplayElements'][str(len(ss['DisplayElements']))] = at(by_val(els('ENG', '3,0'), 'L:BLEED_PRESSURE_PSI'), 38, 134, 10)
    c = copy.deepcopy(cmds('ENG', '3,0', 'DIAL_DOWN')[0]); c['DeckCommandType'] = 0
    ss['ActionCommands']['KEY_DOWN'] = {'0': c}
    return a
def e_press():
    """Cabin pressurisation dial, new for the XL: turn = cabin altitude goal through the standard MSFS events (not verified on the C750)."""
    a = E('INFO', '0,0'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values())      # SIM RATE as the shell
    cab = [x for x in src['INFO']['Keypad']['1,0']['Settings']['settingsStore']['DisplayElements'].values() if x['ElementType'] == 5]
    def val(x, addr, fmt, cy, fs):
        x = copy.deepcopy(x); x['ValueAddress'] = addr; x['ValueFormat']['FormatString'] = fmt
        x.update(Size=[200, 100], Position=[0, cy - 50], FontSize=fs, TextHorizontalAlignment=1, TextVerticalAlignment=1)
        x['Manipulators'] = {k: m for k, m in x['Manipulators'].items() if m['ManipulatorType'] == 6}           # keep "powered", drop colour limits
        return x
    L[0]['Text'] = 'CABIN ALT SEL'; L[2]['Text'] = 'TURN = SET'
    goal = val(cab[0], '(A:PRESSURIZATION CABIN ALTITUDE GOAL, feet)', '%s ft', 42, 22); goal['Color'] = '#FFFFFF'
    ss['DisplayElements'] = {str(i): x for i, x in enumerate([L[0], goal, val(cab[0], 'L:VTX_cabin_altitude', 'CABIN %s ft', 72, 12), L[2]])}
    ac = ss['ActionCommands']; ac['DIAL_DOWN'] = {}
    ac['DIAL_LEFT']['0']['Address'] = 'PRESSURIZATION_PRESSURE_ALT_DEC'; ac['DIAL_RIGHT']['0']['Address'] = 'PRESSURIZATION_PRESSURE_ALT_INC'
    return a
_VIS = next(m for p in src.values() for kind in ('Keypad', 'Encoder') for a in p.get(kind, {}).values()
            for x in ((a.get('Settings') or {}).get('settingsStore') or {}).get('DisplayElements', {}).values()
            for m in x.get('Manipulators', {}).values() if m['ManipulatorType'] == 6)         # a visibility manipulator to copy

def e_wx(kind):
    """Weather radar dials (cockpit code from Behaviors 24.11), SIM RATE dial as the shell.
    RADAR: L:knob_wxr_radar 0..6 = OFF SBY WX RCT GMAP FP TST, one step a click; push = WX <-> SBY.
    TILT: L:knob_wxr_tilt 0..100, step 3, 50 = 0 deg (degrees per step assumed: +-15 deg over the range - check against
    T on the MFD); push = AUTO TILT on/off (B:ffx_knob_wxr_tilt_auto_Inc, as a click on the knob); AUTO from L:VTX_WX_AUTO_MODE (not verified)."""
    import xl_keys
    a = E('INFO', '0,0'); ss = a['Settings']['settingsStore']; T, V, H = list(ss['DisplayElements'].values())
    ac = ss['ActionCommands']
    def cmd(code, deck): c = xl_keys.calc(code); c['DeckCommandType'] = deck; return {'0': c}
    vf = V['ValueFormat']
    if kind == 'RADAR':
        v = 'L:knob_wxr_radar'
        T['Text'] = 'WX RADAR'; H['Text'] = 'TURN = MODE · PUSH WX/SBY'
        V['ValueAddress'] = f'({v}, number)'
        vf.update(FormatString='%s', Round=0, Mappings={'0': 'OFF', '1': 'SBY', '2': 'WX', '3': 'RCT', '4': 'GMAP', '5': 'FP', '6': 'TST'})
        ac['DIAL_LEFT'] = cmd(f'({v}, number) 1 - 6 min 0 max (>{v}, number)', 4)
        ac['DIAL_RIGHT'] = cmd(f'({v}, number) 1 + 6 min 0 max (>{v}, number)', 5)
        ac['DIAL_DOWN'] = cmd(f'({v}, number) 2 == if{{ 1 }} els{{ 2 }} (>{v}, number)', 2)
        ss['DisplayElements'] = {str(i): e for i, e in enumerate([T, V, H])}
    else:
        v = 'L:knob_wxr_tilt'
        T['Text'] = 'WX TILT'; H['Text'] = 'TURN = TILT · PUSH AUTO'
        V['ValueAddress'] = f'({v}, number)'
        vf.update(FormatString='%s°', Round=0, Offset=-50, OffsetFirst=True, Scalar=0.3, InsertSign=True, Mappings={})
        ac['DIAL_LEFT'] = cmd(f'({v}, number) 3 - 100 min 0 max (>{v}, number)', 4)
        ac['DIAL_RIGHT'] = cmd(f'({v}, number) 3 + 100 min 0 max (>{v}, number)', 5)
        ac['DIAL_DOWN'] = cmd('1 (>B:ffx_knob_wxr_tilt_auto_Inc)', 2)
        auto = copy.deepcopy(H); auto.update(Text='AUTO', FontSize=12, Color='#3CD070', Position=[60, -4])
        vis = copy.deepcopy(_VIS); vis['Conditions'] = {'0': dict(vis['Conditions']['0'], Address='L:VTX_WX_AUTO_MODE', Comparison=4, Value='1')}
        auto['Manipulators'] = {'0': vis}
        ss['DisplayElements'] = {str(i): e for i, e in enumerate([T, V, auto, H])}
    for k in ('DIAL_LEFT_PRESSED', 'DIAL_RIGHT_PRESSED', 'DIAL_UP', 'TOUCH_TAP'): ac[k] = {}
    return a

def k_master(which):
    L = els('NAV', '1,0'); low = which.lower()
    off, on = (next(e for e in L if e.get('Image', '').endswith(f'c750_{low}_{s}.png')) for s in ('off', 'on'))
    T = [e for e in L if e['ElementType'] == 4]
    c = [x for x in cmds('NAV', '1,0', 'DIAL_DOWN') if which in x['Address']]
    return key([img(off, 72, 72, 140, 112), img(on, 72, 72, 140, 112), at(by_text(T, 'MASTER'), 72, 52, 17),
                at(by_text(T, which), 72, 76, 16), at(by_text(T, 'RESET'), 72, 98, 10)], c)

# ---- layout: row 0 = ATC / INFO (page key), page tabs, MASTER CAUTION / WARNING, PAUSE; rows 1-3 per page ----
# The tabs sit in columns 1-5 on every page so that the CDU pages can have their line select keys in columns 0 and 8,
# four in a column as on the CDU (rows 0-3). A tap on the active CONFIG or CDU tab opens its next page:
# CONFIG -> GROUND -> CONFIG, CDU -> A-Z -> CDU.
TABS = [('FLIGHT', 'AP · PFD'), ('NAV/COM', 'RADIO · XPDR'), ('SYSTEMS', 'ELEC · ENG · FUEL'),
        ('CONFIG', 'CHECK · LIGHTS · ICE', [('GROUND', 'DOORS · COVERS')]),
        ('CDU', 'FMS · DIGITS', [('A-Z', 'LETTERS')])]
TAB_COL = 1
GLOBAL = {6: lambda: k_master('CAUTION'), 7: lambda: k_master('WARNING'), 8: k_pause}
ATC = lambda: K('AP+', '2,1')                                       # ATC / INFO display: column 0 of row 0, except on CONFIG / GROUND (PARK BRK)
# ---- CDU keys: key caps after the cockpit CDU (tools/cdu_keys.py -> Images/C750/c750_cdu_*.png), labels as text ----
_CDU_IMG = copy.deepcopy(next(e for e in els('NAV', '1,0') if e.get('Image', '').endswith('c750_caution_off.png')))
_CDU_IMG['Manipulators'] = {}
CDU_INK = '#F0ECDE'                                                # backlit label colour (as drawn in cdu_keys.py)
_CHAR = {'.': 'round', '/': 'round', '–': 'round'}
def ckey(face, label, size, down=(), up=(), small=None):
    """A CDU key: its cap (lsk, fn, fn_framed, square, round), the label, the commands on press (and release);
    small: a grey caption above the key (L1 ... R4 on the line select keys)."""
    e = copy.deepcopy(_CDU_IMG); e['Image'] = f'Images/C750/c750_cdu_{face}.png'
    parts = [img(e, 72, 72, 144, 144)]
    if label: parts.append(at(PLAIN, 72, 72 if face != 'round' else 74, size, label, CDU_INK))
    if small: parts.append(at(PLAIN, 72, 25, 14, small, '#96989E'))
    a = key(parts, list(down))
    if up:
        ups = {}
        for i, c in enumerate(up):
            c = copy.deepcopy(c); c['DeckCommandType'] = 1; ups[str(i)] = c
        a['Settings']['settingsStore']['ActionCommands']['KEY_UP'] = ups
    return a
def _bcmd(event):
    import xl_keys
    return xl_keys.bcmd('fmc_c750_1_' + event)                     # CDU input event fmc_c750_1_<event>
def fn(label, event):
    framed = label in ('PREV', 'NEXT')                               # 26 = FN_SIZE in cdu_keys.py (the frame fits it)
    return lambda: ckey('fn_framed' if framed else 'fn', label, 26 if framed else 30, [_bcmd(event)])
def clr():
    """CLR: the FMS reacts to the input event going 1 -> 0 (bindings _PUSH = 1, _RELEASE = 0; Behaviors 22.11),
    so push on key down and release on key up, as the cockpit key does. A plain trigger or a release alone did nothing."""
    import xl_keys
    return ckey('square', 'CLR', 30, [xl_keys.calc('(>B:FMC_C750_1_Button_CLR_Push)')], [xl_keys.calc('(>B:FMC_C750_1_Button_CLR_Release)')])
def dele():                                                        # DEL: an H-event in the cockpit (Behaviors 22.11); press DEL, then the LSK of the line
    import xl_keys
    return ckey('square', 'DEL', 30, [xl_keys.calc('(>H:C750_FMC_1_BTN_DEL)')])
def lsk(side, n): return lambda: ckey('lsk', '', 0, [_bcmd(f'softkey_{side}_{n}')], small=f'{side.upper()}{n}')
def ch(c, event=None):                                             # character key: letters square, digits and . / – round
    face = 'round' if (c.isdigit() or c in _CHAR) else 'square'
    size = 34 if len(c) > 1 else (64 if c == '.' else 52)
    return lambda: ckey(face, c, size, [_bcmd(event or f'keyboard_{c.lower()}')])

# ---- GROUND: doors, chocks, covers, yokes --------------------------------------------------------------------
# The hitbox input events only act (their own value always reads 1), so the state comes from other variables:
# covers and chocks A:COVER ON:n (0 chocks, 1 engines, 2 pitot), doors and yokes the aircraft's L-vars.
# One event moves a whole set: ENG / INSTR covers fired twice (L and R) put them on and took them off again.
def ground(title, event, text='OPEN', state=None):
    """state: (address, value[, comparison]) shown lit; without it the key has no indication."""
    def make():
        import xl_keys
        return xl_keys.button(title, [xl_keys.bvar('B:' + event)], lit=state, text=text, fs=17)
    return make
def k_irs(side):
    """IRS L / R as the cockpit mode knob (OFF ALIGN NAV ATT, pictures c750_cdu_irs_*.png), the selected label lit -
    ALIGN amber, NAV green; READY (green, bottom) while aligning and L:VTX_IRS_x_ALIGN_READY = 1 (checked 24.11).
    A press steps OFF -> ALIGN -> NAV and never back: no IRS lost by a slip in flight. Knob values: 0 OFF 1 ALIGN 2 NAV 3 ATT."""
    import xl_keys
    knob, ready = f'L:knob_irs_{side.lower()}', f'L:VTX_IRS_{side}_ALIGN_READY'
    parts = []
    for i, pos in enumerate(('off', 'align', 'nav', 'att')):
        e = copy.deepcopy(_CDU_IMG); e['Image'] = f'Images/C750/c750_cdu_irs_{pos}.png'; e = img(e, 72, 72, 144, 144)
        e['Manipulators'] = {'0': _when(6, knob, i)}; parts.append(e)
    for i, (label, x, y, lit) in enumerate((('OFF', 21, 100, '#F0ECDE'), ('ALIGN', 30, 62, '#FFB000'),
                                           ('NAV', 72, 46, '#3CD070'), ('ATT', 113, 62, '#F0ECDE'))):
        t = at(PLAIN, x, y, 14, label, '#7C7F86'); t['Manipulators'] = {'0': _when(1, knob, i, lit)}; parts.append(t)
    parts.append(at(PLAIN, 72, 16, 15, f'IRS {side}', '#C7C7C7'))
    rdy = at(PLAIN, 116, 128, 12, 'READY', '#3CD070'); vis = _when(6, knob, 1)
    vis['Conditions']['1'] = dict(vis['Conditions']['0'], Address=ready, Value='1'); rdy['Manipulators'] = {'0': vis}
    parts.append(rdy)
    return key(parts, [xl_keys.calc(f'({knob}) 1 < if{{ 1 (>{knob}) }} els{{ ({knob}) 1 == if{{ 2 (>{knob}) }} }}')])

_COLOR = next(m for p in src.values() for kind in ('Keypad', 'Encoder') for a in p.get(kind, {}).values()
              for x in ((a.get('Settings') or {}).get('settingsStore') or {}).get('DisplayElements', {}).values()
              for m in x.get('Manipulators', {}).values() if m['ManipulatorType'] == 1)       # a colour manipulator to copy
def _when(kind, addr, value, color=None):
    """A manipulator: kind 6 = visible while addr == value, 1 = this colour while addr == value."""
    m = copy.deepcopy(_VIS if kind == 6 else _COLOR); m['AnyCondition'] = False
    m['Conditions'] = {'0': dict(m['Conditions']['0'], Address=addr, Comparison=4, Value=str(value))}
    if color: m['Color'] = color
    return m

def k_brg(n):
    """BRG 1 / BRG 2: the source knob of a bearing pointer on the HSI / MFD (needle 1 single, needle 2 double) -
    OFF, VOR, ADF or FMS. Drawn as the cockpit knob turned to its position, the selected label lit; a press turns it on
    (L:nav_panel_L_brg_knob_n 0..3 = OFF VORn ADFn FMSn, as the old key)."""
    import xl_keys
    v = f'L:nav_panel_L_brg_knob_{n}'
    parts = []
    for i, pos in enumerate(('off', 'vor', 'adf', 'fms')):
        e = copy.deepcopy(_CDU_IMG); e['Image'] = f'Images/C750/c750_cdu_brg_{pos}.png'; e = img(e, 72, 72, 144, 144)
        e['Manipulators'] = {'0': _when(6, v, i)}; parts.append(e)
    for i, (label, x, y) in enumerate((('OFF', 21, 100), (f'VOR {n}', 42, 62), (f'ADF {n}', 102, 62), (f'FMS {n}', 123, 100))):
        t = at(PLAIN, x, y, 14, label, '#7C7F86'); t['Manipulators'] = {'0': _when(1, v, i, '#F0ECDE')}; parts.append(t)
    parts.append(at(PLAIN, 72, 16, 15, f'BRG {n}', '#C7C7C7'))
    return key(parts, [xl_keys.calc(f'({v}) 1 + 4 % (>{v})')])

def k_nav_ident():
    """NAV1 IDENT: the station's identifier (e.g. ILC) in the button and, under it, the Morse audio state;
    a press toggles the Morse ident audio (RADIO_VOR1_IDENT_TOGGLE). The identifier shows only while a station
    is received (NAV HAS NAV) - without one MSFS 2024 puts other text into NAV IDENT."""
    a = K('NAV', '1,0'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values())
    snd = L[2]; snd['FontSize'] = 12; snd['Position'] = [0, 34]
    ident = copy.deepcopy(snd); ident.update(ValueAddress='(A:NAV IDENT:1, String)', FontSize=26, Position=[0, 4], Color='#FFFFFF')
    ident['ValueFormat'] = dict(ident['ValueFormat'], Mappings={}, FormatString='')
    ident['Manipulators'] = {'0': _when(6, '(A:NAV HAS NAV:1, Bool)', 1)}
    ss['DisplayElements'] = {str(i): e for i, e in enumerate(L + [ident])}
    return a

def k_cdi(src):
    """CDI source as the two cockpit buttons NAV / FMS on the nav source panel (between the BRG knobs), drawn like them
    (framed label): each presses its own button (H:Generic_Upr_1_Push_NAV / _FMS) and its label is lit while it is the
    source (A:GPS DRIVES NAV1: 0 = NAV green, 1 = FMS magenta, as on the PFD)."""
    import xl_keys
    nav = src == 'NAV'
    a = ckey('fn_framed', src, 26, [xl_keys.calc(f'(>H:Generic_Upr_1_Push_{src})')], small='CDI')
    lab = next(e for e in a['Settings']['settingsStore']['DisplayElements'].values() if e.get('Text') == src)
    lab['Manipulators'] = {'0': _when(1, '(A:GPS DRIVES NAV1, Bool)', 0 if nav else 1, '#3CD070' if nav else '#E040E0')}
    return a

def k_mfd_wx():
    """MFD WX: the weather radar layer on the pilot MFD (cockpit button on the PFD/MFD controls, Behaviors 22.11:
    it toggles L:push_pilot_1_mfdwx; the MFD then shows WX/ON and the tilt, e.g. T-7A). Drawn as a framed cockpit
    button, the label lit green while the layer is on. The radar itself is the RADAR dial."""
    import xl_keys
    v = 'L:push_pilot_1_mfdwx'
    a = ckey('fn_framed', 'WX', 26, [xl_keys.calc(f'({v}, number) ! (>{v}, number)')], small='MFD')
    lab = next(e for e in a['Settings']['settingsStore']['DisplayElements'].values() if e.get('Text') == 'WX')
    lab['Manipulators'] = {'0': _when(1, v, 1, '#3CD070')}
    return a

def k_ats():
    """ATS (autothrottle) as on the cockpit ATS panel: the button drawn like the autopilot panel buttons (BANK as the
    shell: frame, indicator bar lit while L:ATS_IS_ON = 1 and the bus is powered), and above it the panel's display -
    amber OFF while disengaged. The press uses the sim's autothrottle events (as the + profile did on the VS dial push);
    the FMS/MAN knob is the push of the SPD dial."""
    import xl_keys
    v = 'L:ATS_IS_ON'
    a = K('AP+', '2,0'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values())
    L[1]['Manipulators']['0']['Conditions']['0'].update(Address=v, Comparison=4, Value='1')
    L[2]['Text'] = 'ATS'
    off = at(PLAIN, 72, 16, 17, 'OFF', '#FFB000'); off['Manipulators'] = {'0': _when(6, v, 0)}
    ss['DisplayElements'] = {str(i): x for i, x in enumerate(L + [off])}
    c = xl_keys.calc(f'({v}, Bool) if{{ (>K:AUTO_THROTTLE_DISCONNECT) }} els{{ (>K:AUTO_THROTTLE_ARM) }}'); c['DeckCommandType'] = 0
    ss['ActionCommands']['KEY_DOWN'] = {'0': c}
    return a
TAP = 6   # DeckCommandType of TOUCH_TAP (as on the SPD dial)
PASSIVE = '#9A9A9A'   # measured, not selected values (actual VS, time to ALT SEL): grey, so they never read as a pilot setting
def e_vs():
    """VS dial laid out like ALT / HDG (the + profile had the autothrottle on its right half; ATS has its own key now).
    Big number: the selected VS (cyan) in VS mode, otherwise the actual vertical speed (white, citx VsAct, 50 fpm steps).
    Bottom line: the actual VS in VS mode (left) and the time to ALT SEL at the current VS (right, citx AltSelTime)."""
    a = E('AP', '0,0'); ss = a['Settings']['settingsStore']; L = list(ss['DisplayElements'].values())
    alt = list(E('AP', '3,0')['Settings']['settingsStore']['DisplayElements'].values())
    hint = next(x for x in alt if x.get('Text') == 'PUSH 100/1000')
    lua = next(x for x in E('AP', '2,0')['Settings']['settingsStore']['DisplayElements'].values()
               if x.get('ValueAddress') == 'lua:citx:HdgBugTxt')
    hold = '(A:AUTOPILOT VERTICAL HOLD, Bool)'
    title, sel = L[0], L[1]
    title['Position'] = list(alt[0]['Position'])
    sel['Position'] = list(alt[1]['Position']); sel['TextVerticalAlignment'] = alt[1]['TextVerticalAlignment']
    def luav(addr, pos, fs, color, mode=None):
        x = copy.deepcopy(lua); x.update(ValueAddress=addr, Position=pos, FontSize=fs, Color=color)
        if mode is not None:
            c = x['Manipulators']['0']['Conditions']; c['1'] = dict(c['0'], Address=hold, Comparison=4, Value=str(mode))
        return x
    act_big = copy.deepcopy(sel); act_big.update(ValueAddress='lua:citx:VsAct', Color=PASSIVE, ValueFormat=copy.deepcopy(lua['ValueFormat']))
    act_big['Manipulators'] = {'0': copy.deepcopy(sel['Manipulators']['0'])}
    act_big['Manipulators']['0']['Conditions']['0'].update(Value='0')            # visible while VS mode is off (and powered)
    act_lbl = copy.deepcopy(hint); act_lbl.update(Text='ACT', Position=[-72, 31], FontSize=11)
    act_lbl['Manipulators'] = {'0': _when(6, hold, 1)}
    parts = [title, sel, act_big, act_lbl, luav('lua:citx:VsAct', [-34, 31], 12, PASSIVE, 1),
             luav('lua:citx:AltSelTime', [48, 31], 12, PASSIVE)]
    ss['DisplayElements'] = {str(i): x for i, x in enumerate(parts)}
    # push = VS SYNC (selected VS := actual, to 100 fpm), tap on the strip = VS 0 (level off); standard sim event, not verified on FlightFX
    import xl_keys
    ac = ss['ActionCommands']
    sync = xl_keys.calc('(A:VERTICAL SPEED, feet per minute) 100 / near 100 * (>K:AP_VS_VAR_SET_ENGLISH)'); sync['DeckCommandType'] = 2
    zero = xl_keys.calc('0 (>K:AP_VS_VAR_SET_ENGLISH)'); zero['DeckCommandType'] = TAP
    ac['DIAL_DOWN'] = {'0': sync}; ac['TOUCH_TAP'] = {'0': zero}
    return a
def e_spd():
    """SPD dial: push turns the ATS FMS/MAN knob through the aircraft's own input event (was a direct write of the L-var)."""
    import xl_keys
    a = E('AP', '1,0'); ss = a['Settings']['settingsStore']
    c = xl_keys.calc('(L:KNOB_ATS_FMS_MAN) if{ 1 (>B:ffx_knob_ats_fms_man_Dec) } els{ 1 (>B:ffx_knob_ats_fms_man_Inc) }')
    c['DeckCommandType'] = 2; ss['ActionCommands']['DIAL_DOWN'] = {'0': c}
    return a

def k_ext_pwr():
    """EXT PWR: the AVION 1 toggle key with the variable swapped (FlightFX L-var, written directly; the input event did nothing)."""
    a = json.loads(json.dumps(src['ELEC']['Keypad']['2,0']).replace('L:electrical_switch_avionics_master_1', 'L:electrical_switch_ext_pwr'))
    for x in a['Settings']['settingsStore']['DisplayElements'].values():
        x['Text'] = {'AVION 1': 'EXT PWR'}.get(x.get('Text'), x.get('Text'))
    return a

k = lambda p, pos: (lambda: K(p, pos))
e = lambda p, pos: (lambda: E(p, pos))
chk = lambda pos: (lambda: k_check(pos))
tg = lambda pos: (lambda: k_toggle(pos))
LAYOUT = {
    'FLIGHT': {
        0: {0: ATC},
        # 26.11: the autopilot block as on the cockpit's AP panel (Iurii's idea, his own try kept the same block):
        # columns 2-4 HDG ALT FLC / NAV VNAV C/O / APP BANK VS, column 5 AP YD BC; info left, display controller and timer right.
        # right: the nav source panel - CDI NAV / FMS as the two cockpit buttons, BRG 1 / BRG 2 either side of NAV1 IDENT
        1: [k('INFO', '0,0'), k_ats, k('AP', '2,1'), k('AP', '3,1'), k('AP', '1,1'), k('AP', '0,0'),        # ROUTE ATS | HDG ALT FLC | AP (ATS left of the AP panel, as in the cockpit)
            k('AP+', '0,1'), lambda: k_cdi('NAV'), lambda: k_cdi('FMS')],                                         # FD | CDI NAV  FMS
        2: [k('INFO', '3,0'), k('INFO', '2,0'), k('AP', '2,0'), k('AP', '1,0'), k('AP+', '0,0'), k('AP+', '1,0'), # AIR WEIGHT | NAV VNAV C/O | YD
            k_nav_ident, lambda: k_brg(1), lambda: k_brg(2)],                                                 # NAV1 IDENT | BRG 1 BRG 2 under CDI NAV FMS (Iurii, 26.11)
        3: [k('INFO', '1,0'), k_descent, k('AP', '3,0'), k('AP+', '2,0'), k('AP', '0,1'), k('AP+', '3,0'),             # CABIN DESCENT (above the VS dial) | APP BANK VS | BC
            k('NAV', '0,1'), k_timer, k_timer_reset],                                                              # RA/BARO, hold timer
        'dials': [e_vs, e_spd, e('AP', '2,0'), e('AP', '3,0'), e('AP+', '1,0'), e('AP+', '0,0')]},
    'NAV/COM': {
        0: {0: ATC},
        # 26.11, as Iurii arranged it on the deck: the nav source panel BRG 1 NAV FMS BRG 2 top left, IRS under it,
        # NAV1 IDENT and the hold timer on the right; row 3 = the radio keys above their dials and MFD WX above the radar.
        1: [lambda: k_brg(1), lambda: k_cdi('NAV'), lambda: k_cdi('FMS'), lambda: k_brg(2)],
        2: [lambda: k_irs('L'), lambda: k_irs('R'), None, None, None, None, k_nav_ident, k_timer, k_timer_reset],
        3: [k('RADIO', '2,0'), k('RADIO', '1,0'), k('RADIO', '1,1'), k('RADIO', '3,0'), k('RADIO', '2,1'),       # MIC, COM2 RX, COM2 SWAP, NAV KNOB, NAV SWAP
            k_xpdr_mode, k('RADIO', '0,0'), k('RADIO', '0,1'), k_mfd_wx],                                        # XPDR MODE, VFR 7000, IDENT, MFD WX
        # MFD RANGE L / R live on the CDU pages (route review); the radar sits here next to MFD WX
        'dials': [e('RADIO', '0,0'), e('RADIO', '1,0'), e('RADIO', '2,0'), e('RADIO', '3,0'), lambda: e_wx('RADAR'), lambda: e_wx('TILT')]},
    'SYSTEMS': {
        0: {0: ATC},
        # columns 2-5 are the core, left engine left and right engine right: generators/batteries, start, instruments.
        # Left of it avionics, pumps/ignition and the APU keys above the APU dial; right of it the rest.
        1: [k('ELEC', '2,0'), k('ELEC', '3,0'), k('ELEC', '0,0'), tg('1,0'), tg('2,0'), k('ELEC', '1,0'), tg('0,0'), k('ELEC', '2,1'), k_ext_pwr],          # EXT PWR moved here from GROUND (26.11)
        2: [k('INFO', '0,1'), k('FLAPS', '1,1'), k('ENG', '0,1'), k('ENG', '0,0'), k('ENG', '3,0'), k('ENG', '3,1'), k('FLAPS', '2,1'), k('INFO', '1,1'), k_eng_start],  # ENG START checklist (CL[15] in citx.lua)
        3: [tg('3,0'), k_apu_bleed, k('ENG', '1,0'), k('ENG', '1,1'), k('ENG', '2,1'), k('ENG', '2,0'), k('ELEC', '1,1'), k_antiskid, k('ELEC', '0,1')],
        # strip: APU, then fuel and the engine table across three segments (as on the + ENG page), then XFEED and cabin altitude
        'dials': [e('ENG', '3,0'), e('ENG', '0,0'), e('ENG', '1,0'), e('ENG', '2,0'), e('INFO', '1,0'), e_press]},
    'CONFIG': {                                                    # checklists in flight order, then what they check
        0: {0: k('AP+', '1,1')},                                   # PARK BRK
        1: [chk('0,0'), chk('1,0'), k('CHECK', '0,0'), k('CHECK', '1,0'), k('CHECK', '2,0'), k('CHECK', '3,0'), chk('2,0'), chk('3,0'), k('CHECK', '0,1')],
        2: [k('CHECK', '1,1'), k('CHECK', '2,1'), k('CHECK', '3,1'), k_toconfig, k('FLAPS', '0,0'), k('FLAPS', '1,0'), k('FLAPS', '2,0'), k('FLAPS', '3,0'), k('FLAPS', '0,1')],
        3: [k('LIGHTS', '0,0'), k('LIGHTS', '1,0'), k('LIGHTS', '0,1'), k('LIGHTS', '2,0'), k('LIGHTS', '1,1'), k('LIGHTS', '2,1'), k('LIGHTS', '3,0'),
            lambda: k_light('2,0', 'SEAT BELT', 16), lambda: k_light('1,0', 'EMER LT')],
        'dials': [e('FLAPS', '0,0'), e('FLAPS', '2,0'), e('NAV', '0,0'), e('INFO', '0,0')]},
    # CDU (experiment 26.11, Iurii's idea): line select keys in columns as on the CDU - L1-L4 in column 0, R1-R4 in
    # column 8 (rows 0-3); between them the digits and, in the bottom row, the cockpit's function keys in the cockpit's order.
    # Event names come from another FMS: NAV = button_idx, FPL = button_fpln, PROG = button_msg. CLR acts on its
    # _Release binding, DEL is an H-event (Behaviors 22.11). Dead in the FlightFX CDU: softkeys 5-6, LEGS, DSPL MENU,
    # MFD ADV, EXEC. Left out (no such keys on the cockpit panel): DEP ARR, TUN, MFD DATA (hides the track on the MFD).
    'CDU': {
        0: {0: lsk('l', 1), 8: lsk('r', 1)},
        1: [lsk('l', 2)] + [ch(c) for c in '12345'] + [ch('.', 'button_dot'), ch('/', 'button_div'), lsk('r', 2)],   # digits as Iurii
        2: [lsk('l', 3)] + [ch(c) for c in '67890'] + [dele, clr, lsk('r', 3)],                                       # set them (26.11)
        3: [lsk('l', 4), fn('PERF', 'button_perf'), fn('NAV', 'button_idx'), fn('PREV', 'button_prevpage'),
            fn('NEXT', 'button_nextpage'), fn('FPL', 'button_fpln'), fn('PROG', 'button_msg'), fn('DIR', 'button_dir'),
            lsk('r', 4)],
        'dials': [e('RADIO', '0,0'), e('RADIO', '1,0'), e('RADIO', '2,0'), e('RADIO', '3,0'), e('NAV', '2,0'), e('NAV', '3,0')]},
    'A-Z': {                                                       # letters in alphabetical rows; – and CLR in row 0, SP at the end (Iurii, 26.11)
        0: {0: ch('–', 'button_plusminus'), 8: clr},
        1: [ch(c) for c in 'ABCDEFGHI'],
        2: [ch(c) for c in 'JKLMNOPQR'],
        3: [ch(c) for c in 'STUVWXYZ'] + [ch('SP', 'button_sp')],
        'dials': [e('RADIO', '0,0'), e('RADIO', '1,0'), e('RADIO', '2,0'), e('RADIO', '3,0'), e('NAV', '2,0'), e('NAV', '3,0')]},
    'GROUND': {                                                    # walk-around items left, power and engines right
        0: {0: k('AP+', '1,1')},                                   # PARK BRK, as on CONFIG
        # CKPT DOOR (unknown_cockpit_door_hitb) only moved the camera into the cockpit; GND IDLE: no switch found in the cockpit
        1: [ground('MAIN DOOR', 'unknown_main_door_hitbox', state=('L:VTX_C750_MAIN_DOOR', '0', 2)),
            ground('BAGGAGE', 'unknown_hitbox_luggage_door', state=('L:VTX_C750_LUGGAGE_DOOR', '0', 2)), None, None,
            ground('GPU', 'unknown_hitbox_gpu_door', 'CONN', state=('L:VTX750_GROUND_POWER_CONN', '0', 2)), None, k_fuel, k('INFO', '2,0'), k('INFO', '3,0')],      # ... FUEL, WEIGHT, AIR
        2: [ground('CHOCKS', 'unknown_chocks', 'SET', state=('(A:COVER ON:0, Bool)', '1')),
            ground('PITOT CVR', 'unknown_pitot_cover_left_front_hitb', 'ON', state=('(A:COVER ON:2, Bool)', '1')),
            ground('ENG CVR', 'unknown_engine_cover_container_l_hitb', 'ON', state=('(A:COVER ON:1, Bool)', '1')),
            ground('INSTR CVR', 'unknown_instruments_covers_left_1_hitb', 'ON', state=('(A:COVER ON:3, Bool)', '1')), None, None, None,   # COVER ON:3 = instrument covers (checked 26.11)
            ground('YOKE L', 'handling_yoke_hider_1', 'HIDDEN', state=('L:XMLVAR_YokeHidden1', '1')),
            ground('YOKE R', 'handling_yoke_hider_2', 'HIDDEN', state=('L:XMLVAR_YokeHidden2', '1'))],
        'dials': [e('FLAPS', '0,0'), e('FLAPS', '2,0'), e('NAV', '0,0'), e('INFO', '0,0')]},
}

def build(out_dir, device_uuid, minify):
    return xl_lib.build(out_dir, device_uuid, minify, name='Citation X XL', uid=uid, tabs=TABS, common=GLOBAL, layout=LAYOUT, tab_col=TAB_COL)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'ProfileXL')); ap.add_argument('--device-uuid', default='')
    ap.add_argument('--minify', action='store_true', help='one-line JSON, as Stream Deck writes it')
    o = ap.parse_args()
    print(build(pathlib.Path(o.out), o.device_uuid, o.minify))
