# Citation X Stream Deck profiles - installer (current user, no administrator rights needed).
# Start it with Install.cmd. It installs the fonts, copies the artwork and the script into PilotsDeck, installs the
# profile for each Stream Deck + / + XL it finds, and maps them to the FlightFX Citation X (aircraft string msfsffx-c750).
# Everything it replaces is moved to %APPDATA%\Elgato\StreamDeck\_backup\<date> first.
$ErrorActionPreference = 'Stop'
$here    = $PSScriptRoot
$sd      = Join-Path $env:APPDATA 'Elgato\StreamDeck'
$plugin  = Join-Path $sd 'Plugins\com.extension.pilotsdeck.sdPlugin'
$profV3  = Join-Path $sd 'ProfilesV3'
$backup  = Join-Path $sd ('_backup\' + (Get-Date -Format 'yyyy-MM-dd_HHmmss'))
$utf8    = New-Object System.Text.UTF8Encoding($false)
$aircraft = 'msfsffx-c750'
# device type in PilotsDeck's DeviceInfo.json -> profile folder(s) in this package, Stream Deck model, mapped to the aircraft
$profiles = @(
  @{ Type = 13; Folders = @('Citation X XL'); Model = '20GBX9901'; DeckName = 'Stream Deck + XL'; Map = $true
     Label = 'the profile for the Stream Deck + XL' },
  @{ Type = 7;  Folders = @('Citation X +');  Model = '20GBD9901'; DeckName = 'Stream Deck +'; Map = $true
     Label = 'the profile for the Stream Deck +' },
  @{ Type = 7;  Folders = @('Citation X + Parts 1', 'Citation X + Parts 2', 'Citation X + Parts 3'); Model = '20GBD9901'
     DeckName = 'Stream Deck +'; Map = $false
     Label = 'the parts library for the Stream Deck + (every XL key and dial, to copy into your own pages)' }
)

function Step($t) { Write-Host ''; Write-Host $t.ToUpper() -ForegroundColor Cyan }
function Item($what, $state, $color = 'Gray') {   # checklist line: WHAT ........ STATE
  $w = $what.ToUpper(); Write-Host ('  ' + $w + ' ' + ('.' * [Math]::Max(3, 44 - $w.Length)) + ' ' + $state) -ForegroundColor $color
}
function Backup($path) {
  if (-not (Test-Path $path)) { return }
  $rel = $path.Substring($sd.Length).TrimStart('\')
  $dst = Join-Path $backup $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Move-Item $path $dst -Force
}
function Fail($t) { Write-Host ''; Write-Host $t -ForegroundColor Red; exit 1 }

Write-Host 'FLIGHTFX CITATION X - STREAM DECK PROFILES - INSTALLATION CHECKLIST' -ForegroundColor White

# --- PilotsDeck and Stream Deck ---------------------------------------------------------------
if (-not (Test-Path $plugin)) { Fail "PilotsDeck is not installed ($plugin). Install PilotsDeck 0.9.8.0 or newer first." }
try {
  $ver = [version]((Get-Content (Join-Path $plugin 'version.json') -Raw | ConvertFrom-Json).Version)
  if ($ver -lt [version]'0.9.8.0') { Item 'PilotsDeck' "$ver - 0.9.8.0 OR LATER REQUIRED FOR + XL" Yellow } else { Item 'PilotsDeck' "$ver - CHECKED" }
} catch { }
while (Get-Process StreamDeck -ErrorAction SilentlyContinue) {
  Write-Host ''
  Item 'Stream Deck' 'QUIT (tray icon -> Quit Stream Deck), then press Enter' Yellow
  Write-Host '  (or type C and Enter to close it now)'
  if ((Read-Host) -match '^[cC]') { Get-Process StreamDeck -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep 2 }
}
Item 'Stream Deck' 'QUIT - CHECKED'

# --- which decks -------------------------------------------------------------------------------
$decks = @()
$devInfo = Join-Path $plugin 'Profiles\DeviceInfo.json'
if (Test-Path $devInfo) { $decks = @(Get-Content $devInfo -Raw | ConvertFrom-Json | ForEach-Object { $_ }) }   # PS 5 passes a JSON array as one object
$todo = @($profiles | Where-Object { $t = $_.Type; @($decks | Where-Object { $_.type -eq $t }).Count -gt 0 })
if ($todo.Count -eq 0) {
  Item 'Stream Deck + / + XL' 'NOT KNOWN TO PILOTSDECK YET - all profiles offered' Yellow
  $todo = $profiles
}
if ($todo.Count -gt 1) {   # PilotsDeck remembers every deck it has seen, not only the connected ones: let the user choose
  Write-Host ''
  $todo = @($todo | Where-Object { (Read-Host "  Install $($_.Label)? [Y/n]") -notmatch '^[nN]' })
  if ($todo.Count -eq 0) { Fail 'No profile selected - nothing installed.' }
}

# --- fonts --------------------------------------------------------------------------------------
Step 'Fonts'
$fontDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$fontReg = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$fonts = [ordered]@{
  'BarlowSemiCondensed-Bold.ttf'    = 'Barlow Semi Condensed Bold (TrueType)'
  'BarlowSemiCondensed-Regular.ttf' = 'Barlow Semi Condensed Regular (TrueType)'
  'ShareTech-Regular.ttf'           = 'Share Tech Regular (TrueType)'
}
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
if (-not (Test-Path $fontReg)) { New-Item -Path $fontReg -Force | Out-Null }
foreach ($f in $fonts.Keys) {
  if (Test-Path (Join-Path $env:WINDIR "Fonts\$f")) { Item ($fonts[$f].Replace(' (TrueType)', '')) 'INSTALLED (all users)'; continue }
  $target = Join-Path $fontDir $f
  $src = Join-Path $here "Fonts\$f"
  $label = $fonts[$f].Replace(' (TrueType)', '')
  if ((Test-Path $target) -and ((Get-FileHash $target).Hash -eq (Get-FileHash $src).Hash)) { $state = 'INSTALLED (already)' }
  else {
    try { Copy-Item $src $target -Force; $state = 'INSTALLED' }
    catch { Item $label 'IN USE - existing copy kept' Yellow; continue }   # a loaded font file is locked by Windows
  }
  New-ItemProperty -Path $fontReg -Name $fonts[$f] -Value $target -PropertyType String -Force | Out-Null
  Item $label $state
}

# --- artwork and script ---------------------------------------------------------------------------
Step 'Artwork and script'
New-Item -ItemType Directory -Force -Path (Join-Path $plugin 'Images\C750'), (Join-Path $plugin 'Scripts') | Out-Null
Copy-Item (Join-Path $here 'PilotsDeck\Images\C750\*') (Join-Path $plugin 'Images\C750') -Force
$lua = Join-Path $plugin 'Scripts\citx.lua'
$new = Join-Path $here 'PilotsDeck\Scripts\citx.lua'
if ((Test-Path $lua) -and ((Get-FileHash $lua).Hash -ne (Get-FileHash $new).Hash)) { Backup $lua }
Copy-Item $new $lua -Force
Item "Artwork Images\C750 ($(@(Get-ChildItem (Join-Path $here 'PilotsDeck\Images\C750')).Count) files)" 'INSTALLED'
Item 'Script citx.lua' 'INSTALLED'

# --- profiles -------------------------------------------------------------------------------------
Step 'Profiles'
New-Item -ItemType Directory -Force -Path $profV3 | Out-Null
$installed = @()
foreach ($p in $todo) { foreach ($folder in $p.Folders) {
  $src = Get-ChildItem (Join-Path $here "Profiles\$folder") -Directory -Filter '*.sdProfile' | Select-Object -First 1
  $dst = Join-Path $profV3 $src.Name
  # the serial of this kind of deck, taken from another profile Stream Deck already made for it
  $serial = ''
  foreach ($m in Get-ChildItem $profV3 -Directory -Filter '*.sdProfile' | ForEach-Object { Join-Path $_.FullName 'manifest.json' } | Where-Object { Test-Path $_ }) {
    try { $j = Get-Content $m -Raw | ConvertFrom-Json } catch { continue }
    if ($j.Device.Model -eq $p.Model -and $j.Device.UUID) { $serial = $j.Device.UUID; break }
  }
  Backup $dst
  Copy-Item $src.FullName $dst -Recurse -Force
  $rootFile = Join-Path $dst 'manifest.json'
  $root = Get-Content $rootFile -Raw | ConvertFrom-Json
  $root.Device.UUID = $serial
  [IO.File]::WriteAllText($rootFile, ($root | ConvertTo-Json -Depth 10 -Compress), $utf8)
  if ($p.Map) { $installed += @{ P = $p; Uuid = ($src.Name -replace '\.sdProfile$', '' -replace '-', '').ToUpper(); Name = $root.Name; Path = $root.PreconfiguredName } }
  if ($serial) { Item $root.Name "INSTALLED - $($p.DeckName)" }
  else { Item $root.Name 'INSTALLED - device not identified; if it does not show, import Profiles\*.streamDeckProfile' Yellow }
} }

# --- automatic switching (PilotsDeck Profile Mapping) ---------------------------------------------
Step 'Automatic switching (PilotsDeck profile mapping)'
$mapFile = Join-Path $plugin 'Profiles\ProfileMappings.json'
$maps = @()
if (Test-Path $mapFile) { $maps = @(Get-Content $mapFile -Raw | ConvertFrom-Json | ForEach-Object { $_ }); Copy-Item $mapFile "$mapFile.bak" -Force }
foreach ($i in $installed) {
  $deck = @($decks | Where-Object { $_.type -eq $i.P.Type }) | Select-Object -First 1
  if (-not $deck) { Item $i.Name 'NOT MAPPED - map later: Profile Manager -> Profile Mapping' Yellow; continue }
  $maps = @($maps | Where-Object { $_.ProfileUUID -ne $i.Uuid -and $_.ProfilePath -ne $i.Path })   # replaces earlier mappings of this profile
  $maps += [pscustomobject][ordered]@{
    DeckId = $deck.id.ToUpper(); DeckName = $deck.name; DeckType = $i.P.Type
    ProfileName = $i.Name; ProfileUUID = $i.Uuid; ProfilePath = $i.Path
    DefaultProfile = $false; DefaultSimulator = -1; AircraftProfile = $true
    AircraftStrings = @($aircraft); SwitchBackProfile = $false
  }
  Item "$($i.Name) mapping" "SET - $aircraft"
}
New-Item -ItemType Directory -Force -Path (Split-Path $mapFile) | Out-Null
[IO.File]::WriteAllText($mapFile, (ConvertTo-Json -InputObject @($maps) -Depth 10), $utf8)

# --- done -----------------------------------------------------------------------------------------
Write-Host ''
Write-Host 'INSTALLATION CHECKLIST COMPLETE' -ForegroundColor Green
if (Test-Path $backup) { Item 'Replaced files' "MOVED TO $backup" }
Item 'MobiFlight WASM module (Community folder)' 'REQUIRED - CHECK'
Item 'FSUIPC7, free version' 'OPTIONAL - PAUSE key only'
$exe = Join-Path $env:ProgramFiles 'Elgato\StreamDeck\StreamDeck.exe'
if ((Test-Path $exe) -and ((Read-Host 'Start Stream Deck now? [Y/n]') -notmatch '^[nN]')) { Start-Process $exe }
