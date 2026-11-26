-- PilotsDeck: helper functions for the Citation X profile
-- Register each variable once: PilotsDeck logs a warning on a repeated SimVar
local REG = {}
local function Reg(v) if not REG[v] then REG[v] = true; SimVar(v) end end
-- PilotsDeck's Lua string.format does not support %d: integers are formatted with %.0f
local function I(x) return string.format("%.0f", math.floor(x + 0.5)) end
local function I2(x) local t = I(x); if #t < 2 then t = "0" .. t end; return t end
-- Decimal numbers as strings with a dot regardless of the Windows locale: string.format with decimals
-- in NeoLua follows the current .NET culture and gives a comma on ru-RU ("118,50")
local function Fx(v, n)
    local m = 10 ^ n
    local t = math.floor(math.abs(v) * m + 0.5)
    local ip = math.floor(t / m)
    local fs = I(t - ip * m)
    while #fs < n do fs = "0" .. fs end
    return (v < 0 and t > 0 and "-" or "") .. I(ip) .. "." .. fs
end
Reg("(A:INDICATED ALTITUDE, feet)")
Reg("(A:AUTOPILOT ALTITUDE LOCK VAR, feet)")
Reg("(A:KOHLSMAN SETTING MB:1, mbars)")
Reg("L:SD_CITX_TA")
Reg("(A:KOHLSMAN SETTING STD:1, Bool)")
-- FlightFX STD = K:BAROMETRIC_STD_PRESSURE, i.e. exactly 1013.25 hPa (no separate STD mode).
-- The dial sets pressure in 0.01 inHg steps (29.92 = 1013.19 hPa), so exactly 1013.25 means STD.
local function StdOf(flag, mb) return flag == 1 or math.abs(mb - 1013.25) < 0.02 end
local function IsStd() return StdOf(SimRead("(A:KOHLSMAN SETTING STD:1, Bool)"), SimRead("(A:KOHLSMAN SETTING MB:1, mbars)") or 0) end

-- 1 = ALT SEL above the aircraft, -1 = below, 0 = about at the current altitude (±200 ft)
function AltDir()
    local cur = SimRead("(A:INDICATED ALTITUDE, feet)") or 0
    local sel = SimRead("(A:AUTOPILOT ALTITUDE LOCK VAR, feet)") or 0
    if sel > cur + 200 then return 1 end
    if sel < cur - 200 then return -1 end
    return 0
end

-- 1 = altimeter setting does not match the flight phase relative to the transition altitude (TA)
function BaroWarn()
    local ta = SimRead("L:SD_CITX_TA") or 0
    if ta <= 0 then return 0 end
    local alt = SimRead("(A:INDICATED ALTITUDE, feet)") or 0
    local mb  = SimRead("(A:KOHLSMAN SETTING MB:1, mbars)") or 0
    local std = IsStd()
    if alt > ta + 1000 and not std then return 1 end   -- climbed above TA and forgot STD
    if alt < ta and std then return 1 end              -- below TA and still on STD
    return 0
end

-- Wind: arrow angle relative to the nose (the arrow points where the wind blows to)
Reg("(A:AMBIENT WIND DIRECTION, degrees)")
Reg("(A:PLANE HEADING DEGREES TRUE, degrees)")
function WindArrow()
    local wd = SimRead("(A:AMBIENT WIND DIRECTION, degrees)") or 0
    local hd = SimRead("(A:PLANE HEADING DEGREES TRUE, degrees)") or 0
    return (wd - hd + 180) % 360
end

-- Flaps: handle position -> degrees (for the arrow, like the EICAS scale)
Reg("(A:FLAPS HANDLE INDEX, Number)")
-- UP and SLT (slats only) sit at the UP mark. No table keyed [0]: in NeoLua math.floor
-- returns a double, and key 0.0 does not match integer key [0] -> nil -> the arrow jumped to 35.
function FlapsDeg()
    local i = math.floor((SimRead("(A:FLAPS HANDLE INDEX, Number)") or 0) + 0.5)
    if i <= 1 then return 0 end
    if i == 2 then return 5 end
    if i == 3 then return 15 end
    return 35
end

-- Fuel in pounds, rounded to 10 like EICAS: 0 = total, 1 = left, 2 = right
Reg("(A:FUEL TOTAL QUANTITY WEIGHT, pounds)")
Reg("(A:FUEL LEFT QUANTITY, gallons)")
Reg("(A:FUEL RIGHT QUANTITY, gallons)")
Reg("(A:FUEL WEIGHT PER GALLON, pounds)")
function FuelLbs(tank)
    local lbs
    if tank == 1 then
        lbs = (SimRead("(A:FUEL LEFT QUANTITY, gallons)") or 0) * (SimRead("(A:FUEL WEIGHT PER GALLON, pounds)") or 0)
    elseif tank == 2 then
        lbs = (SimRead("(A:FUEL RIGHT QUANTITY, gallons)") or 0) * (SimRead("(A:FUEL WEIGHT PER GALLON, pounds)") or 0)
    else
        lbs = SimRead("(A:FUEL TOTAL QUANTITY WEIGHT, pounds)") or 0
    end
    return math.floor(lbs / 10 + 0.5) * 10
end

-- Frequencies as strings: 1/2 = COM1 active/stby, 3/4 = COM2, 5/6 = NAV1
local FREQ = {
  [1] = {"(A:COM ACTIVE FREQUENCY:1, MHz)", 3}, [2] = {"(A:COM STANDBY FREQUENCY:1, MHz)", 3},
  [3] = {"(A:COM ACTIVE FREQUENCY:2, MHz)", 3}, [4] = {"(A:COM STANDBY FREQUENCY:2, MHz)", 3},
  [5] = {"(A:NAV ACTIVE FREQUENCY:1, MHz)", 2}, [6] = {"(A:NAV STANDBY FREQUENCY:1, MHz)", 2},
}
for _, f in pairs(FREQ) do Reg(f[1]) end
function FreqStr(n)
    local f = FREQ[n]
    if not f then return "" end
    return Fx(SimRead(f[1]) or 0, f[2])
end

-- The NAV dial works with NAV1 or NAV2: L:SD_CITX_NAVSEL = 0/1
Reg("L:SD_CITX_NAVSEL")
Reg("(A:NAV ACTIVE FREQUENCY:2, MHz)")
Reg("(A:NAV STANDBY FREQUENCY:2, MHz)")
for i = 1, 2 do Reg("(A:NAV DME:" .. i .. ", nautical miles)"); Reg("(A:NAV HAS DME:" .. i .. ", Bool)") end
local function navN() return (SimRead("L:SD_CITX_NAVSEL") == 1) and 2 or 1 end
function NavLbl() return "NAV" .. navN() end
function NavStr(w)   -- 1 = active, 2 = standby
    local kind = (w == 2) and "STANDBY" or "ACTIVE"
    return Fx(SimRead("(A:NAV " .. kind .. " FREQUENCY:" .. navN() .. ", MHz)") or 0, 2)
end
function NavDme()
    local n = navN()
    if (SimRead("(A:NAV HAS DME:" .. n .. ", Bool)") or 0) ~= 1 then return "" end
    return "DME " .. Fx(SimRead("(A:NAV DME:" .. n .. ", nautical miles)") or 0, 1)
end

-- ===== Stopwatch (for holds). State lives in L-vars and is changed only
-- by the key commands (PUSH start/stop, TAP reset); Lua only reads it, so parallel calls
-- cannot corrupt it, and the timer survives page changes and script reloads.
--   L:SD_TMR_RUN 0/1, L:SD_TMR_T0 = sim time at start, L:SD_TMR_ACC = seconds accumulated before start
Reg("L:SD_TMR_RUN")
Reg("L:SD_TMR_T0")
Reg("L:SD_TMR_ACC")
Reg("(A:SIMULATION TIME, seconds)")
function TimerSec()
    local acc = SimRead("L:SD_TMR_ACC") or 0
    if (SimRead("L:SD_TMR_RUN") or 0) ~= 1 then return math.floor(acc) end
    local now, t0 = SimRead("(A:SIMULATION TIME, seconds)"), SimRead("L:SD_TMR_T0")
    if now == nil or t0 == nil then return math.floor(acc) end
    return math.floor(acc + math.max(0, now - t0))   -- sim time: honours sim rate
end
function TimerStr()
    local s = TimerSec()
    return I(math.floor(s / 60)) .. ":" .. I2(s % 60)
end

-- ===== 3:1 descent: miles needed to ALT SEL and the VS for a 3 degree path
Reg("(A:GROUND VELOCITY, knots)")
function DescNM()
    local d = (SimRead("(A:INDICATED ALTITUDE, feet)") or 0) - (SimRead("(A:AUTOPILOT ALTITUDE LOCK VAR, feet)") or 0)
    if d < 500 then return 0 end
    return math.floor(d / 1000 * 3 + 0.5)
end
function DescVS()
    local gs = SimRead("(A:GROUND VELOCITY, knots)") or 0
    return math.floor(gs * 5.3 / 100 + 0.5) * 100
end

-- ===== Wind components relative to aircraft heading: "HW8 XW12R" / "TW3 XW5L"
Reg("(A:AMBIENT WIND VELOCITY, knots)")
function WindComp()
    local ws = SimRead("(A:AMBIENT WIND VELOCITY, knots)") or 0
    if ws < 1 then return "" end
    local rel = math.rad((SimRead("(A:AMBIENT WIND DIRECTION, degrees)") or 0) - (SimRead("(A:PLANE HEADING DEGREES TRUE, degrees)") or 0))
    local hw, xw = ws * math.cos(rel), ws * math.sin(rel)
    local h = hw >= 0 and "HW" .. I(hw) or "TW" .. I(-hw)
    return h .. " XW" .. I(math.abs(xw)) .. (xw >= 0 and "R" or "L")
end

-- ===== Fuel imbalance: 1 if left/right differ by more than IMB_LIMIT pounds
local IMB_LIMIT = 200   -- check against the Citation X AFM
function FuelImb()
    return math.abs(FuelLbs(1) - FuelLbs(2)) > IMB_LIMIT and 1 or 0
end

-- ===== Heading bug relative to the nose: arrow angle and label "R25"/"L40"
Reg("(A:HEADING INDICATOR, degrees)")
Reg("(A:AUTOPILOT HEADING LOCK DIR, degrees)")
local function bugRel()
    return ((SimRead("(A:AUTOPILOT HEADING LOCK DIR, degrees)") or 0) - (SimRead("(A:HEADING INDICATOR, degrees)") or 0)) % 360
end
function HdgBugRel()
    local r = bugRel()
    if r < 0.01 then r = 0.01 end
    return r
end
function HdgBugTxt()
    local r = bugRel()
    if r < 2 or r > 358 then return "ON HDG" end
    if r <= 180 then return "R" .. I(r) end
    return "L" .. I(360 - r)
end

-- ===== Mini CDI: course and glideslope needle position in steps -4..4 (2 steps = 1 dot)
Reg("(A:NAV CDI:1, Number)")
Reg("(A:NAV GSI:1, Number)")
local function slot(v, full)
    local s = math.floor(v / full * 4 + 0.5)
    if s > 4 then s = 4 elseif s < -4 then s = -4 end
    return s
end
function CdiSlot() return slot(SimRead("(A:NAV CDI:1, Number)") or 0, 127) end
function GsSlot()  return slot(SimRead("(A:NAV GSI:1, Number)") or 0, 119) end

-- ===== INFO page
-- Time to destination (sim flight plan) and fuel on arrival
Reg("(A:GPS ETE, seconds)")
Reg("(A:ENG FUEL FLOW PPH:1, Pounds per hour)")
Reg("(A:ENG FUEL FLOW PPH:2, Pounds per hour)")
function EteStr()
    local s = SimRead("(A:GPS ETE, seconds)") or 0
    if s <= 0 then return "--:--" end
    return I(math.floor(s / 3600)) .. ":" .. I2(math.floor((s % 3600) / 60))
end
function FuelDest()
    -- -1 = no estimate ("--"): a source is missing, no route or no fuel flow
    local s   = SimRead("(A:GPS ETE, seconds)")
    local ff1 = SimRead("(A:ENG FUEL FLOW PPH:1, Pounds per hour)")
    local ff2 = SimRead("(A:ENG FUEL FLOW PPH:2, Pounds per hour)")
    local tot = SimRead("(A:FUEL TOTAL QUANTITY WEIGHT, pounds)")
    if s == nil or ff1 == nil or ff2 == nil or tot == nil then return -1 end
    if s <= 0 or tot < 0 or ff1 < 0 or ff2 < 0 or ff1 + ff2 <= 0 then return -1 end   -- 0 on one engine is allowed
    local f = tot - (ff1 + ff2) * s / 3600
    return math.max(0, math.floor(f / 10 + 0.5) * 10)
end
-- Next waypoint of the sim flight plan and its distance
Reg("(A:GPS WP NEXT ID, string)")
Reg("(A:GPS WP DISTANCE, nautical miles)")
function NextWpt()
    local id = SimRead("(A:GPS WP NEXT ID, string)")
    if id == nil or id == "" or id == 0 then return "--" end
    return string.format("%s %.0f", tostring(id), SimRead("(A:GPS WP DISTANCE, nautical miles)") or 0)
end
-- ATC altitude (built-in MSFS ATC): use whichever variable is non-zero
Reg("(A:ATC ASSIGNED ALTITUDE, feet)")
function AtcAlt()
    local a = SimRead("(A:ATC ASSIGNED ALTITUDE, feet)") or 0
    return math.floor(a + 0.5)
end
function AtcMismatch()
    local a = AtcAlt()
    if a <= 0 then return 0 end
    return math.abs(a - (SimRead("(A:AUTOPILOT ALTITUDE LOCK VAR, feet)") or 0)) > 50 and 1 or 0
end
-- Actual QNH from the weather and a check of the set value
Reg("(A:SEA LEVEL PRESSURE, millibars)")
function QnhStr() return I(SimRead("(A:SEA LEVEL PRESSURE, millibars)") or 0) end
function QnhBad()
    local set = SimRead("(A:KOHLSMAN SETTING MB:1, mbars)") or 0
    if IsStd() then return 0 end
    return math.abs(set - (SimRead("(A:SEA LEVEL PRESSURE, millibars)") or set)) > 1 and 1 or 0
end
-- Flap speed limit
Reg("(A:FLAPS CURRENT SPEED LIMITATION, knots)")
Reg("(A:AIRSPEED INDICATED, knots)")
function FlapOver()
    local lim = SimRead("(A:FLAPS CURRENT SPEED LIMITATION, knots)") or 0
    return (lim > 0 and (SimRead("(A:AIRSPEED INDICATED, knots)") or 0) > lim) and 1 or 0
end
-- Icing: TAT and in-cloud conditions
Reg("(A:TOTAL AIR TEMPERATURE, celsius)")
Reg("(A:AMBIENT IN CLOUD, Bool)")
Reg("(A:AMBIENT TEMPERATURE, celsius)")
Reg("(A:PRESSURE ALTITUDE, feet)")
function IcingCond()
    return ((SimRead("(A:TOTAL AIR TEMPERATURE, celsius)") or 20) <= 10 and (SimRead("(A:AMBIENT IN CLOUD, Bool)") or 0) == 1) and 1 or 0
end
function IsaDev()
    local h = SimRead("(A:PRESSURE ALTITUDE, feet)") or 0
    local isa = (h < 36089) and (15 - 1.98 * h / 1000) or -56.5
    local t = SimRead("(A:AMBIENT TEMPERATURE, celsius)")
    if t == nil then return "ISA --" end
    local d = t - isa
    return "ISA " .. (d >= -0.5 and "+" or "-") .. I(math.abs(d))
end

-- Small line under the speed: ground speed and true airspeed
Reg("(A:GROUND VELOCITY, knots)")
Reg("(A:AIRSPEED TRUE, knots)")
function SpdInfo()
    return "GS " .. I(SimRead("(A:GROUND VELOCITY, knots)") or 0) .. "   TAS " .. I(SimRead("(A:AIRSPEED TRUE, knots)") or 0)
end

-- ===== VS dial: actual vertical speed and time to the selected altitude
Reg("(A:VERTICAL SPEED, feet per minute)")
local function vsNow() return SimRead("(A:VERTICAL SPEED, feet per minute)") or 0 end
function VsAct()   -- actual vertical speed rounded to 50 fpm, signed ("+1850", "-700", "0")
    local v = math.floor(vsNow() / 50 + 0.5) * 50
    if v == 0 then return "0" end
    return (v > 0 and "+" or "") .. I(v)
end
function AltSelTime()   -- "ALT SEL 2:10" while climbing / descending towards ALT SEL, else ""
    local vs = vsNow()
    local d = (SimRead("(A:AUTOPILOT ALTITUDE LOCK VAR, feet)") or 0) - (SimRead("(A:INDICATED ALTITUDE, feet)") or 0)
    if math.abs(vs) < 100 or math.abs(d) < 100 or (d > 0) ~= (vs > 0) then return "" end
    local s = math.floor(d / vs * 60 + 0.5)
    if s >= 6000 then return "" end
    local m = math.floor(s / 60)
    return "ALT SEL " .. I(m) .. ":" .. I2(s - m * 60)
end

-- ===== Checklists: ClItem(kk*10+i) = 1 if item i of key kk is done; ClDone(kk) = all items done
local CV = {
  FI = "(A:FLAPS HANDLE INDEX, Number)", SPL = "(A:SPOILERS HANDLE POSITION, percent)",
  PB = "L:PARKING_BRAKE_HANDLE", TS = "(A:TRANSPONDER STATE:1, Enum)",
  PITL = "L:switch_pitot_static_lh", PITR = "L:switch_pitot_static_rh",
  WSL = "L:switch_windshield_lh", WSR = "L:switch_windshield_rh",
  IGNL = "L:switch_ignition_l", IGNR = "L:switch_ignition_r",
  FD = "(A:AUTOPILOT FLIGHT DIRECTOR ACTIVE, Bool)", ATS = "L:ATS_IS_ON", TA = "L:SD_CITX_TA",
  SB = "L:switch_seatBelt", TAXI = "L:switch_landing_taxi",
  LDGL = "L:switch_landing_light_lh", LDGR = "L:switch_landing_light_rh",
  AC = "L:switch_lights_recognition_anticollision", NAVL = "L:switch_lights_nav",
  GPS = "(A:GPS DRIVES NAV1, Bool)", LOC = "(A:NAV HAS LOCALIZER:1, Bool)",
  APPR = "(A:AUTOPILOT APPROACH HOLD, Bool)", GH = "(A:GEAR HANDLE POSITION, Bool)",
  GE = "(A:GEAR TOTAL PCT EXTENDED, percent)", APU = "L:electrical_switch_apu_master",
  C1 = "(A:GENERAL ENG COMBUSTION:1, Bool)", C2 = "(A:GENERAL ENG COMBUSTION:2, Bool)",
  B1 = "L:electrical_switch_battery_1", B2 = "L:electrical_switch_battery_2",
  STBY = "L:switch_stby_pwr", IRSL = "L:knob_irs_l", IRSR = "L:knob_irs_r",
  YD = "(A:AUTOPILOT YAW DAMPER, Bool)",
  AV1 = "L:electrical_switch_avionics_master_1", AV2 = "L:electrical_switch_avionics_master_2",
  APUGEN = "L:electrical_switch_apu", APUBLEED = "L:switch_apu_bleed",
  IAS = "(A:AIRSPEED INDICATED, knots)", ALT = "(A:INDICATED ALTITUDE, feet)",
  KMB = "(A:KOHLSMAN SETTING MB:1, mbars)", SLP = "(A:SEA LEVEL PRESSURE, millibars)",
  KSTD = "(A:KOHLSMAN SETTING STD:1, Bool)",
  BSTL = "L:switch_fuel_boost_lh", BSTR = "L:switch_fuel_boost_rh",
  BUS = "(A:ELECTRICAL MAIN BUS VOLTAGE, Volts)", BLEEDP = "L:BLEED_PRESSURE_PSI",
}
local STBY_ON = 0   -- L:switch_stby_pwr: 0 = ON, 1 = OFF (verified in the sim), 2 = TEST
for _, v in pairs(CV) do Reg(v) end
-- "No data" = an error whose text contains "no data:". Detected by text, not by a shared flag:
-- PilotsDeck calls script functions in parallel (Task.Run per variable).
-- Any other error is a script error.
local function rv(addr)   -- strict read: nil -> abort the check as "unknown"
    local v = SimRead(addr)
    if v == nil then error("no data: " .. addr) end
    return v
end
local function r(k) return rv(CV[k]) end
local LOGGED = {}
local function logOnce(msg)   -- write to log/lua.log once per error text
    if LOGGED[msg] or not Log then return end
    if pcall(function() Log(msg) end) then LOGGED[msg] = true end   -- count as logged only after Log succeeded
end
-- Altimeter for checklists: strict reads only, no default values
local function ClStd() return StdOf(r("KSTD"), r("KMB")) end
local function ClBaroOk(needTa)   -- altimeter matches the flight phase relative to TA
    local ta = r("TA")
    if ta <= 0 then return not needTa end   -- TA not set: nothing to check in climb / at 10,000
    local alt, std = r("ALT"), ClStd()
    if alt > ta + 1000 and not std then return false end
    if alt < ta and std then return false end
    return true
end
local function ClQnhOk()   -- not STD, actual pressure set, no TA phase violation
    if ClStd() then return false end
    if math.abs(r("KMB") - r("SLP")) > 1 then return false end
    return ClBaroOk(false)
end
local function both(a, b, v) return r(a) == v and r(b) == v end
local CL = {
  [1] = { function() return r("FI") == 2 or r("FI") == 3 end,              -- FLAPS 5/15
          function() return r("SPL") < 1 end,                               -- SPDBRK STOWED
          function() return r("PB") == 0 end,                               -- PRK BRK OFF
          function() return r("TS") == 4 end },                             -- XPDR ALT
  [2] = { function() return both("PITL", "PITR", 0) end,                    -- PITOT ON
          function() return both("WSL", "WSR", 0) end,                      -- WSHLD ON
          function() local l, rr = r("IGNL"), r("IGNR"); return (l == 0 or l == 2) and (rr == 0 or rr == 2) end, -- IGN NORM/ON
          function() return r("FD") == 1 end },                             -- FD ON
  [3] = { function() return r("ATS") == 1 end,                              -- ATS ARM
          function() return r("TA") > 0 end,                                -- TA SET
          function() return r("SB") ~= 2 end,                               -- SEAT BELT
          function() return both("IRSL", "IRSR", 2) end },                  -- IRS NAV
  [4] = { function() return r("TAXI") == 0 end,                             -- TAXI
          function() return both("LDGL", "LDGR", 0) end,                    -- LDG L+R
          function() return r("AC") == 0 end,                               -- ANTI-COL
          function() return r("NAVL") == 0 end },                           -- NAV
  [5] = { function() return r("SB") ~= 2 end,                               -- SEAT BELT
          function() return ClQnhOk() end,                                  -- QNH = actual
          function() return r("LOC") == 0 or r("GPS") == 0 end,             -- CDI VLOC (if ILS)
          function() return r("APPR") == 1 end },                           -- APPR ARM
  [6] = { function() return r("GH") == 1 and r("GE") > 99 end,              -- GEAR DN
          function() return r("FI") == 4 end,                               -- FLAPS 35
          function() return r("SPL") < 1 end,                               -- SPDBRK
          function() return both("LDGL", "LDGR", 0) end },                  -- LDG LT
  [7] = { function() return r("FI") == 0 end,                               -- FLAPS UP
          function() return both("LDGL", "LDGR", 1) end,                    -- LDG OFF
          function() return r("APU") == 1 end,                              -- APU ON
          function() return r("TS") == 1 end },                             -- XPDR STBY
  [8] = { function() return r("PB") == 1 end,                               -- PRK BRK SET
          function() return r("C1") == 0 and r("C2") == 0 end,              -- ENG STOP
          function() return r("AC") == 2 end,                               -- BEACON OFF
          function() return both("B1", "B2", 1) end },                      -- BATT OFF
  [11] = { function() return both("B1", "B2", 0) end,                       -- BATT ON
           function() return r("STBY") == STBY_ON end,                      -- STBY PWR ON
           function() return r("APUGEN") == 0 end,                          -- APU GEN ON
           function() return r("AC") == 0 end },                            -- BEACON
  [12] = { function() return r("C1") == 1 and r("C2") == 1 end,             -- ENG RUN
           function() return both("IRSL", "IRSR", 2) end,                   -- IRS NAV
           function() return r("APUBLEED") == 2 end,                        -- APU BLEED OFF
           function() return r("FD") == 1 end },                            -- FD ON
  [13] = { function() return r("GH") == 0 and r("GE") < 1 end,                              -- GEAR UP
           function() return r("FI") == 0 end,                              -- FLAPS UP
           function() return r("YD") == 1 end,                              -- YD ON
           function() return ClBaroOk(true) end },                         -- BARO (TA)
  [14] = { function() return both("LDGL", "LDGR", 1) end,                   -- 10 000 FT: LDG OFF
           function() return r("TAXI") == 1 end,                            -- TAXI OFF
           function() return ClBaroOk(true) end,                           -- BARO (TA)
           function() return r("ALT") >= 10000 or r("IAS") <= 255 end },    -- 250 KT below FL100
  [15] = { function() return r("AC") == 0 end,                              -- ENG START: BEACON
           function() return r("BSTL") ~= 1 and r("BSTR") ~= 1 end,         -- BOOST ON/NORM (1 = OFF)
           function() return r("IGNL") ~= 1 and r("IGNR") ~= 1 end,         -- IGN ON/NORM (1 = OFF)
           function() return r("APUBLEED") ~= 2 end,                        -- APU BLEED ON/MAX (2 = OFF)
           function() return r("BUS") > 21 end,                             -- BUS > 21 V
           function() return r("BLEEDP") > 10 end },                        -- BLEED > 10 PSI
}
-- 1 = done, 0 = not done, 2 = no data or script error (never turns green)
function ClRun(f, id)
    local ok, res = pcall(f)
    if ok then return res and 1 or 0 end
    if not string.find(tostring(res), "no data:", 1, true) then
        logOnce("citx ClItem(" .. tostring(id) .. ") script error: " .. tostring(res))
    end
    return 2
end
function ClItem(id)
    local k, i = math.floor(id / 10), id % 10
    local f = CL[k] and CL[k][i]
    if not f then return 0 end
    return ClRun(f, id)
end
function ClDone(k)
    local l = CL[k]
    if not l then return 0 end
    for i, f in ipairs(l) do
        if ClRun(f, k * 10 + i) ~= 1 then return 0 end
    end
    return 1
end

-- ===== Paired systems: 0/1/2 = position of both sides, 9 = sides differ (MIXED)
local PAIRS = {
  [1] = {"L:switch_engine_ai_lh", "L:switch_engine_ai_rh"},
  [2] = {"L:switch_stabilizer_ai_lh", "L:switch_stabilizer_ai_rh"},
  [3] = {"L:switch_pitot_static_lh", "L:switch_pitot_static_rh"},
  [4] = {"L:switch_windshield_lh", "L:switch_windshield_rh"},
}
for _, p in pairs(PAIRS) do Reg(p[1]); Reg(p[2]) end
function Pair(n)
    local p = PAIRS[n]
    if not p then return 9 end
    local l, r = SimRead(p[1]), SimRead(p[2])
    if l == nil or r == nil then return 8 end   -- no data
    if l ~= r then return 9 end
    return l
end

-- ===== Minimums: value for the selected RA/BARO mode (MSFS variables; FlightFX may not fill them)
Reg("L:pfd-1-btn-ra-baro")
Reg("(A:DECISION HEIGHT, feet)")
Reg("(A:DECISION ALTITUDE MSL, feet)")
function MinStr()
    local ra = (SimRead("L:pfd-1-btn-ra-baro") or 0) == 1
    local v = ra and (SimRead("(A:DECISION HEIGHT, feet)") or 0) or (SimRead("(A:DECISION ALTITUDE MSL, feet)") or 0)
    if v <= 0 then return (ra and "RA" or "BARO") .. " --" end
    return (ra and "RA " or "BARO ") .. I(v)
end

-- ===== APU (FlightFX): MASTER 0 OFF / 1 ON; APU START switch top to bottom 0 START / 1 NORM / 2 STOP.
-- Turn right: OFF -> ON; the next click = START (spring-loaded: back to NORM after 1.5 s).
-- Each START gets a sequence number; only the latest one returns the switch to NORM, and only if it is still
-- in START (STOP/NORM not selected by hand). The spring returns to NORM even with MASTER off, as in the cockpit.
-- A repeated click during START is ignored (if the value has already updated).
Reg("L:electrical_switch_apu_master")
Reg("L:electrical_switch_apu_starter")
local APU_SEQ = 0
function ApuRight()
    if (SimRead("L:electrical_switch_apu_master") or 0) == 0 then
        SimWrite("L:electrical_switch_apu_master", 1)
        return
    end
    if (SimRead("L:electrical_switch_apu_starter") or 1) == 0 then return end   -- already in START
    APU_SEQ = APU_SEQ + 1
    local my = APU_SEQ
    SimWrite("L:electrical_switch_apu_starter", 0)
    Sleep(1500)
    if my ~= APU_SEQ then return end
    if (SimRead("L:electrical_switch_apu_starter") or 0) ~= 0 then return end   -- STOP/NORM selected by hand
    SimWrite("L:electrical_switch_apu_starter", 1)
end
