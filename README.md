# FlightFX Citation X — Stream Deck + / + XL Profiles (PilotsDeck)

**Pilot's Operating Handbook — Supplement.** Two [PilotsDeck](https://github.com/Fragtality/PilotsDeck) profiles for
the **FlightFX Cessna Citation X V2**, **MSFS 2024**: Stream Deck **+ XL** (5 tabs, 7 pages) and Stream Deck **+**
(menu-driven, 11 pages). Autopilot panel laid out as in the cockpit, radios, CDU, weather radar, electrical, engine start,
anti-ice, lights, ground equipment, and checklists that turn green from actual aircraft state.

## Section 1 — Required Equipment

| Item | Status |
|---|---|
| MSFS 2024 + FlightFX Cessna Citation X V2 | REQUIRED |
| Stream Deck + XL and/or Stream Deck + | REQUIRED (at least one) |
| [PilotsDeck](https://github.com/Fragtality/PilotsDeck/releases) 0.9.8.0 or later | REQUIRED |
| [MobiFlight WASM module](https://github.com/MobiFlight/MobiFlight-WASM-Module/releases) in the Community folder | REQUIRED — L-variable access |
| [FSUIPC7](https://www.fsuipc.com/), free (unregistered) version | OPTIONAL — PAUSE key only. May be inoperative for all other functions |

## Section 2 — Installation (Normal Procedures)

**2.1 Installer — recommended.** Release asset `CitationX-StreamDeck-<version>.zip`.
```
RELEASE ZIP .................................. DOWNLOADED, EXTRACTED
STREAM DECK .................................. QUIT (tray icon → Quit Stream Deck)
Install.cmd .................................. RUN
  Fonts, artwork, script ..................... INSTALLED (current user, no admin rights)
  Profile for each + / + XL known to PilotsDeck  INSTALLED
  Parts library (Stream Deck +) ............... INSTALLED (optional, see Section 5)
  Profile mapping msfsffx-c750 ............... SET
STREAM DECK .................................. START
CITATION X ................................... LOAD — deck switches automatically
```
Anything replaced is moved to `%APPDATA%\Elgato\StreamDeck\_backup\<date>`.

**2.2 PilotsDeck Profile Manager — alternate.** Release asset `CitationX-StreamDeck-<version>.ppp`.
```
PROFILE MANAGER .............................. OPEN (PilotsDeck tray icon)
.ppp FILE .................................... DROP ON, INSTALL
PROFILE LINKS ................................ CLICK for each device, CONFIRM in Stream Deck
Install Fonts.cmd (desktop folder) ........... RUN
STREAM DECK .................................. RESTART
PROFILE MAPPING .............................. msfsffx-c750 → Citation X XL / Citation X +
```

**2.3 Manual — if the above are inoperative.** From the extracted zip, Stream Deck quit:
```
PilotsDeck folder contents ... COPY to %APPDATA%\Elgato\StreamDeck\Plugins\com.extension.pilotsdeck.sdPlugin\
Fonts ........................ INSTALL (right click → Install)
STREAM DECK .................. START
Profiles\*.streamDeckProfile . DOUBLE-CLICK to import
PROFILE MAPPING .............. msfsffx-c750 → profile (Profile Manager)
```

**2.4 Update.** Same procedure. Do not rename the profiles (*Citation X XL*, *Citation X +*): old profiles are then
replaced and the mapping is retained.

## Section 3 — Panel Description: Stream Deck + XL

**Top row:** ATC / INFO (PARK BRK on CONFIG and GROUND) · page tabs **FLIGHT, NAV/COM, SYSTEMS, CONFIG, CDU** (active tab
amber) · MASTER CAUTION · MASTER WARNING · PAUSE (FSUIPC7). A `»` on a tab indicates a second page: press the active tab
again (CONFIG → GROUND, CDU → A-Z).

- **FLIGHT** — autopilot panel as in the cockpit: ATS, HDG ALT FLC, AP, FD / NAV VNAV C/O, YD / APP BANK VS, BC.
  CDI NAV and FMS (cockpit buttons), NAV1 IDENT (station identifier), BRG 1 / BRG 2 selectors, RA/BARO, HOLD TIMER;
  ROUTE, AIR, WEIGHT, CABIN, DESCENT 3:1.
  Dials: **VS** — push SYNC to actual V/S, tap V/S 0; grey figures are actual V/S and time to ALT SEL ·
  **SPD** — push FMS/MAN, tap SPD/MACH · **HDG** · **ALT** · **CRS1** · **BARO**.
- **NAV/COM** — BRG 1, CDI NAV / FMS, BRG 2, IRS L / R (OFF → ALIGN → NAV; READY when aligned), NAV1 IDENT, HOLD TIMER;
  MIC, COM2 RX / SWAP, NAV KNOB / SWAP, XPDR MODE, VFR 7000, IDENT, MFD WX.
  Dials: COM1 · COM2 · NAV · XPDR · WX RADAR (push WX/SBY) · WX TILT (push AUTO).
- **SYSTEMS** — left engine left, right engine right: AVIONICS, GEN, BATT, LOAD SHED, STBY PWR, EXT PWR / BOOST, IGN,
  START / RUN, **ENG START** checklist (BEACON, BOOST, IGN, APU BLEED, BUS > 21 V, BLEED > 10 PSI) / APU GEN, APU BLEED,
  N1 / ITT, AUX PUMP, ANTISKID, PAC BLEED. Strip: APU, fuel and engine table, XFEED, cabin altitude.
- **CONFIG** — twelve checklists in flight sequence, T/O CONFIG, anti-ice, lights, SEAT BELT, EMER LT;
  dials FLAPS · TRIM · MINIMUMS · SIM RATE.
  **GROUND** — main and baggage doors, GPU, chocks, pitot / engine / instrument covers, yoke hide, fuel, weight, air data.
- **CDU** — as the cockpit CDU: L1–L4 left edge, R1–R4 right edge, digits, `.` `/` DEL CLR, PERF NAV PREV NEXT FPL PROG
  DIR; dials COM1 · COM2 · NAV · XPDR · MFD RANGE L · R. **A-Z** — letters, `–`, SP, CLR.

## Section 4 — Panel Description: Stream Deck +

Last flight-tested October 2026; not actively maintained since. Keys and dials function as on the + XL.

**Navigation.** Page 1 is the **MENU**: AUTOPILOT, NAV/PFD, RADIO, INFO, LIGHTS, FLAPS/ICE, START, CHECKLISTS.
Swipe order: MENU, AP, AP+, INFO, NAV/PFD, RADIO, LIGHTS, FLAPS/ICE, ELEC, ENG, CHECK. MENU page dials are the
autopilot dials (VS · SPD · HDG · ALT). The bottom-right **MENU** key returns to the menu on every page except AP,
CHECK and ENG, each one swipe away from it. The strip shows the adjacent pages in its top corners (`« PREV`, `NEXT »`).

## Section 5 — Custom Pages (Parts Library)

Every key and dial is self-contained: copy it into any other profile (Stream Deck: right-click → **Copy**, then
**Paste** on the target) and it keeps working, provided the artwork and the script are installed. Page tabs are the only
exception — they belong to their own profile.
```
STREAM DECK + XL .... copy directly from Citation X XL into your own profile
STREAM DECK + ....... the XL profile is not shown on a +: install the PARTS LIBRARY
```
**Citation X + Parts 1–3** (Stream Deck +) hold every key and dial of the XL profile, 8 keys and 4 dials per page,
duplicates removed — Parts 1: FLIGHT, NAV/COM, SYSTEMS · Parts 2: CONFIG, GROUND, CDU · Parts 3: A-Z.
Browse the pages in the Stream Deck app and copy what you need into *Citation X +* or your own profile.
The installer offers the library when it finds a Stream Deck +; the `.ppp` contains it as three more profiles.

## Section 6 — Annunciations and Conventions

- Encoders: **TURN** — set · **PUSH** — mode / select · **TAP** strip — secondary function (labelled).
- **Cyan** — pilot-selected value. **Grey** — measured or computed value.
- Checklist keys: **amber** — not complete · **green** — complete (read from the aircraft) · **grey** — no data
  (never shown as complete). Cyan **•** — item set by pressing the key; all others are check only.
  Gear, flaps, engines and batteries are never moved by a checklist.
- Rotary selectors (XFEED, APU, BRG, IRS) are drawn as the cockpit knob; the selected position is lit.
- Paired switches (ENG AI, STAB, PITOT, WSHLD) annunciate **MIXED** when L and R differ; a press sets both sides alike.

## Section 7 — Limitations

- MINIMUMS uses sim variables DECISION HEIGHT / DECISION ALTITUDE MSL; `--` if FlightFX does not set them.
- ATC ALT — built-in MSFS ATC only.
- FUEL @DEST ≈ — estimate: fuel on board minus current fuel flow × ETE of the sim flight plan; `--` without a route.

## Section 8 — Open Items

- Not yet confirmed in flight: CABIN ALT SEL dial; VS push / tap and SPD push (FMS/MAN) on all FlightFX versions.
- Parts library and the + profile not yet checked on a Stream Deck + with this release.
- Squawks welcome via Issues.

## Credits
- Profiles, script and artwork: **shiiden** (Iurii Boreev) — MIT License (see `LICENSE`)
- PilotsDeck: **Fragtality**
- Inspired by the Longitude profile by **aimoii**
- Fonts: Barlow Semi Condensed, Share Tech — SIL Open Font License (see `Fonts`)
- Unofficial community profile; not affiliated with FlightFX, Textron Aviation, Elgato or Microsoft.

## Maintenance Manual — repository layout
- `PilotsDeck/Scripts/citx.lua` — Lua functions used by the profiles (display logic, checklists, APU start).
- `PilotsDeck/Images/C750` — the artwork; `tools/cdu_keys.py` draws the CDU key caps and knobs.
- `Profile/…sdProfile/` — the Stream Deck + profile, stored indented for readable diffs
  (after copying it back from Stream Deck run `python3 tools/format_profile.py`).
- `ProfileXL/…sdProfile/` — the + XL profile, **generated** from `Profile/` by `python3 tools/build_xl.py`
  (layout table `LAYOUT` in the script; `tools/xl_lib.py` and `tools/xl_keys.py` hold the shared machinery).
- `ProfileParts/` — the Stream Deck + parts library, **generated** from `ProfileXL/` by `python3 tools/build_parts.py`.
- `python3 tools/build_package.py --version X.Y.Z` — builds the release package in `dist/`;
  `tools/preview_render.py` — rough page preview.

| + page folder | Page |
|---|---|
| `26F12B10-…` | MENU |
| `7236B526-…` | AP |
| `BB434090-…` | AP+ |
| `7583E4EE-…` | INFO |
| `CDB410A9-…` | NAV/PFD |
| `E0CF1A53-…` | RADIO |
| `E894BDDE-…` | LIGHTS |
| `429405E6-…` | FLAPS/ICE |
| `28B8346E-…` | ELEC |
| `A5C77AA2-…` | ENG |
| `BA0FA051-…` | CHECK |
| `D2FE5929-…` | default page (Stream Deck) |
