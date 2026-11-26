# Installs the fonts of the Citation X Stream Deck profiles for the current user (no administrator rights needed).
# Run "Install Fonts.cmd" next to this file. Restart Stream Deck afterwards so the plugin picks up the fonts.
$ErrorActionPreference = 'Stop'
Write-Host 'FONTS - INSTALLATION CHECKLIST'
$src  = Join-Path $PSScriptRoot 'Fonts'
$dst  = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$reg  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$fonts = [ordered]@{
  'BarlowSemiCondensed-Bold.ttf'    = 'Barlow Semi Condensed Bold (TrueType)'
  'BarlowSemiCondensed-Regular.ttf' = 'Barlow Semi Condensed Regular (TrueType)'
  'ShareTech-Regular.ttf'           = 'Share Tech Regular (TrueType)'
}
New-Item -ItemType Directory -Force -Path $dst | Out-Null
if (-not (Test-Path $reg)) { New-Item -Path $reg -Force | Out-Null }
foreach ($file in $fonts.Keys) {
  $name = $fonts[$file]
  $w = $name.Replace(' (TrueType)', '').ToUpper(); $dots = '.' * [Math]::Max(3, 40 - $w.Length)
  if (Test-Path (Join-Path $env:WINDIR "Fonts\$file")) { Write-Host "  $w $dots INSTALLED (all users)"; continue }
  $target = Join-Path $dst $file
  $from = Join-Path $src $file
  if ((Test-Path $target) -and ((Get-FileHash $target).Hash -eq (Get-FileHash $from).Hash)) { $state = 'INSTALLED (already)' }
  else {
    try { Copy-Item $from $target -Force; $state = 'INSTALLED' }
    catch { Write-Host "  $w $dots IN USE - existing copy kept" -ForegroundColor Yellow; continue }   # a loaded font is locked
  }
  New-ItemProperty -Path $reg -Name $name -Value $target -PropertyType String -Force | Out-Null
  Write-Host "  $w $dots $state"
}
Write-Host ''
Write-Host ('  STREAM DECK ' + ('.' * 29) + ' RESTART (tray icon -> Quit, then start)')
