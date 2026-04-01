@echo off
:: ============================================================
::  FreedomForge AI — Windows Installer Launcher
::  Double-click this file to install FreedomForge AI
:: ============================================================
echo Starting FreedomForge AI installer...
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
