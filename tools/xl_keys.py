"""New keys for the XL profiles, made from the Citation X key shells (C750 artwork in the plugin's Images/C750).

toggle()  - a cockpit toggle (2 or 3 positions) showing the state of a variable
button()  - a framed push button; lit text while a condition holds, or a live value
label()   - a display-only key with a caption (row headers)
Commands: calc(code) - calculator (RPN) code; bvar(name, on, off) - an input event (B-var) toggled between two values.
"""
import copy, json
import build_xl
from xl_lib import elements, set_elements, set_commands, no_title, at

_TOGGLE = build_xl.src['ELEC']['Keypad']['2,0']          # AVION 1: title, ON / OFF, white toggle up / down
_BUTTON = build_xl.src['LIGHTS']['Keypad']['2,1']        # BEACON: frame, title, lit "ON"
_VAR = 'L:electrical_switch_avionics_master_1'

def _cmd_template():
    from xl_lib import commands
    return copy.deepcopy(commands(_TOGGLE, 'KEY_DOWN')[0])

def calc(code):
    c = _cmd_template(); c.update(CommandType=9, Address=code, WriteValue='', ResetValue='', ResetSwitch=False)
    return c
def bvar(name, on='1', off='0'):
    c = _cmd_template(); c.update(CommandType=13, Address=name, WriteValue=on, ResetValue=off, ResetSwitch=False, DoNotRequestBvar=False)
    return c

def _cond(e, addr, value):
    for m in e.get('Manipulators', {}).values():
        for c in m['Conditions'].values():
            if c['Address'] == _VAR: c['Address'] = addr; c['Value'] = value; c['Comparison'] = 4
    return e

def toggle(title, state, cmds, up=('ON', '1'), down=('OFF', '0'), mid=None, color='white'):
    """up / down / mid: (label, value of `state` in that position)."""
    a = copy.deepcopy(_TOGGLE); T, U, D, IU, ID = elements(a)
    T['Text'] = title
    U['Text'] = up[0]; _cond(U, state, up[1]); D['Text'] = down[0]; _cond(D, state, down[1])
    _cond(IU, state, up[1]); _cond(ID, state, down[1])
    out = [T, U, D, IU, ID]
    if mid:
        M = _cond(copy.deepcopy(D), state, '__'); M['Text'] = mid[0]; M['Position'] = [M['Position'][0], 5]
        for m in M['Manipulators'].values():
            for c in m['Conditions'].values(): c['Value'] = mid[1]
        IM = copy.deepcopy(ID); IM['Image'] = IM['Image'].replace('_down.', '_mid.')
        for m in IM['Manipulators'].values():
            for c in m['Conditions'].values(): c['Value'] = mid[1]
        out = [T, U, M, D, IU, IM, ID]
    for e in out:
        if e['ElementType'] == 2: e['Image'] = e['Image'].replace('toggle_white', f'toggle_{color}')
    set_elements(a, out); set_commands(a, cmds)
    return a

def button(title, cmds, lit=None, text='ON', value=None, mappings=None, fs=19, lit_color=None):
    """lit: (address, value[, comparison]) - `text` shown lit while the condition holds (default ==; 2 is >);
    value: an address shown live (with mappings)."""
    a = copy.deepcopy(_BUTTON); IMG, T, V, X = elements(a)
    T['Text'] = title
    out = [IMG, T]
    if lit:
        cmp = lit[2] if len(lit) > 2 else 4
        X = copy.deepcopy(X); X['Text'] = text; X['FontSize'] = fs
        if lit_color: X['Color'] = lit_color
        for m in X['Manipulators'].values():
            for c in m['Conditions'].values(): c['Address'], c['Value'], c['Comparison'] = lit[0], lit[1], cmp
        dim = copy.deepcopy(X); dim['Color'] = '#5A5A5A'                 # the same text unlit when the condition is false
        for m in dim['Manipulators'].values():
            for c in m['Conditions'].values(): c['Comparison'] = {0: 3, 1: 2, 2: 1, 3: 0, 4: 5, 5: 4}[cmp]
        out += [dim, X]
    elif value:
        V = copy.deepcopy(V); V['ValueAddress'] = value; V['FontSize'] = fs
        V['Manipulators'] = {k: m for k, m in V['Manipulators'].items() if m['ManipulatorType'] == 6}
        V['ValueFormat']['Mappings'] = mappings or {}; V['ValueFormat']['FormatString'] = ''
        out.append(V)
    else:
        X = copy.deepcopy(X); X['Text'] = text; X['FontSize'] = fs; X['Manipulators'] = {}; X['Color'] = '#C7C7C7'
        out.append(X)
    set_elements(a, out); set_commands(a, cmds)
    return a

def label(text, sub=''):
    a = copy.deepcopy(_BUTTON); IMG, T, V, X = elements(a)
    big = copy.deepcopy(T); big.update(Text=text, FontSize=26, Color='#FFB000', Position=[0, -12])
    small = copy.deepcopy(T); small.update(Text=sub, FontSize=11, Color='#969696', Position=[0, 22])
    set_elements(a, [big, small] if sub else [big]); set_commands(a)
    return a

# ---- commands and keys shared by several profiles ------------------------------------------
_BCMD = next(c for c in __import__('xl_lib').commands(build_xl.src['AP']['Encoder']['2,0'], 'DIAL_DOWN')
             if c['Address'] == 'B:autopilot_heading_sync')          # a B-event command, verified on the Citation
def bcmd(name):
    """Fire an input event (command only), e.g. bcmd('fmc_c750_1_button_exec')."""
    c = copy.deepcopy(_BCMD); c['Address'] = 'B:' + name
    return c

def k_swap(radio, event):        return button(radio, [calc(f'(>K:{event})')], text='SWAP', fs=17)
def k_tx(n):
    return button(f'COM {n}', [calc(f'(>K:COM{n}_TRANSMIT_SELECT)')], lit=(f'(A:COM TRANSMIT:{n}, Bool)', '1'), text='MIC', fs=17)
def k_rx(n):
    return button(f'COM {n} RX', [calc(f'(A:COM RECEIVE:{n}, Bool) if{{ 0 }} els{{ 1 }} (>K:COM{n}_RECEIVE_SELECT)')],
                  lit=(f'(A:COM RECEIVE:{n}, Bool)', '1'), text='ON', fs=17)
def k_ident():                   return button('XPDR', [calc('(>K:XPNDR_IDENT_ON)')], text='IDENT', fs=17)
def k_xpdr_mode():
    """STBY <-> ALT through the writable sim variable (as on the Citation X)."""
    return button('XPDR MODE', [calc('(A:TRANSPONDER STATE:1, Enum) 4 == if{ 1 } els{ 4 } (>A:TRANSPONDER STATE:1, Enum)')],
                  value='(A:TRANSPONDER STATE:1, Enum)', mappings={'0': 'OFF', '1': 'STBY', '2': 'TEST', '3': 'ON', '4': 'ALT'}, fs=17)
