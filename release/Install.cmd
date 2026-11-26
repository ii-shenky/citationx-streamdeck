@echo off
rem Installs the Citation X Stream Deck profiles for PilotsDeck (current user, no administrator rights needed).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1"
pause
