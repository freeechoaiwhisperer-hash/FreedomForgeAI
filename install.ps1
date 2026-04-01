# ============================================================
#  FreedomForge AI — One-Click Installer (Windows)
#  Copyright (c) 2026 Ryan Dennison
#  Licensed under AGPL-3.0 + Commons Clause
#
#  Dedicated to Miranda.  She will never be forgotten.
#
#  Run this from PowerShell:
#    Right-click install.ps1 → Run with PowerShell
#  Or from cmd:
#    powershell -ExecutionPolicy Bypass -File install.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$APP_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VENV = "$APP_DIR\.venv"

function ok($msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function info($msg) { Write-Host "        $msg" -ForegroundColor Cyan }
function step($msg) { Write-Host "`n  --- $msg ---" -ForegroundColor Yellow }

Clear-Host
Write-Host ""
Write-Host "  FreedomForge AI -- Installer" -ForegroundColor Yellow
Write-Host "  Free. Private. Yours. For Everyone." -ForegroundColor Cyan
Write-Host "  Dedicated to Miranda. She will never be forgotten." -ForegroundColor Cyan
Write-Host "  -------------------------------------------------"
Write-Host ""

Set-Location $APP_DIR

# ── Python check ─────────────────────────────────────────────
step "Checking Python"

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pythonCmd = $cmd
                ok "Python $major.$minor found ($cmd)"
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  [ERR] Python 3.10+ not found." -ForegroundColor Red
    Write-Host "        Download from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "        Tick 'Add Python to PATH' during install." -ForegroundColor White
    Write-Host ""
    Write-Host "  Press any key to open the Python download page..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# ── Virtual environment ──────────────────────────────────────
step "Virtual environment"

if (-not (Test-Path "$VENV")) {
    info "Creating .venv..."
    & $pythonCmd -m venv "$VENV"
} else {
    info "Reusing existing .venv"
}

$pip = "$VENV\Scripts\pip.exe"
$python = "$VENV\Scripts\python.exe"

& $pip install --upgrade pip setuptools wheel --quiet
ok ".venv ready"

# ── Core Python packages ─────────────────────────────────────
step "Installing Python packages"

$packages = @(
    "customtkinter>=5.2.0",
    "psutil>=5.9.0",
    "setuptools>=68.0.0",
    "requests>=2.28.0",
    "SpeechRecognition>=3.10.0",
    "pyttsx3>=2.90",
    "cryptography>=41.0.0",
    "Pillow>=10.0.0"
)

info "Installing core packages..."
& $pip install @packages --quiet
ok "Core packages installed"

info "Installing GPU utilities..."
& $pip install "gputil>=1.4.0" --quiet 2>$null
if ($LASTEXITCODE -eq 0) { ok "GPU utilities installed" } else { warn "GPUtil optional -- GPU% monitor disabled" }

info "Installing audio packages..."
# PyAudio on Windows needs a pre-built wheel — try pipwin first, then direct
& $pip install pipwin --quiet 2>$null
$audioOk = $false
if ($LASTEXITCODE -eq 0) {
    & pipwin install pyaudio 2>$null
    if ($LASTEXITCODE -eq 0) { $audioOk = $true }
}
if (-not $audioOk) {
    # Fallback: pre-built wheel from Christoph Gohlke's collection
    $pyVer = (& $pythonCmd -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')" 2>$null).Trim()
    $arch  = if ([Environment]::Is64BitProcess) { "win_amd64" } else { "win32" }
    $whlUrl = "https://files.pythonhosted.org/packages/py3/P/PyAudio/PyAudio-0.2.14-cp${pyVer}-cp${pyVer}-${arch}.whl"
    & $pip install $whlUrl --quiet 2>$null
    if ($LASTEXITCODE -eq 0) { $audioOk = $true }
}
if (-not $audioOk) {
    & $pip install "pyaudio>=0.2.13" --quiet 2>$null
    if ($LASTEXITCODE -eq 0) { $audioOk = $true }
}
if ($audioOk) { ok "PyAudio installed — microphone ready" } else { warn "PyAudio optional — run: pip install pyaudio  to enable mic" }

# ── AI engine ────────────────────────────────────────────────
step "AI engine (llama-cpp-python)"

# Check for NVIDIA GPU
$hasNvidia = $false
try {
    $nvsmi = & nvidia-smi 2>$null
    if ($LASTEXITCODE -eq 0) { $hasNvidia = $true }
} catch {}

if ($hasNvidia) {
    info "NVIDIA GPU detected -- building with CUDA support..."
    $env:CMAKE_ARGS = "-DGGML_CUDA=on"
    $env:FORCE_CMAKE = "1"
    & $pip install "llama-cpp-python>=0.2.0" --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        $env:CMAKE_ARGS = ""
        $env:FORCE_CMAKE = ""
        & $pip install "llama-cpp-python>=0.2.0" --quiet 2>$null
    }
} else {
    info "CPU build (no NVIDIA GPU detected)..."
    & $pip install "llama-cpp-python>=0.2.0" --quiet `
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $pip install "llama-cpp-python>=0.2.0" --quiet 2>$null
    }
}

$llama_ok = & $python -c "import llama_cpp" 2>$null
if ($LASTEXITCODE -eq 0) { ok "AI engine ready" } else { warn "AI engine not installed -- app runs but cannot load models yet" }

# ── Launch script ─────────────────────────────────────────────
step "Creating launch script"

$launchBat = @"
@echo off
cd /d "$APP_DIR"
"$VENV\Scripts\python.exe" "$APP_DIR\main.py" %*
"@
$launchBat | Set-Content "$APP_DIR\launch.bat" -Encoding ASCII
ok "launch.bat created"

# ── Desktop shortcut ──────────────────────────────────────────
step "Desktop shortcut"

try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut("$desktop\FreedomForge AI.lnk")
    $shortcut.TargetPath = "$VENV\Scripts\python.exe"
    $shortcut.Arguments = "`"$APP_DIR\main.py`""
    $shortcut.WorkingDirectory = $APP_DIR
    $shortcut.Description = "FreedomForge AI -- Free local AI for everyone"
    $iconPath = "$APP_DIR\assets\icon.ico"
    if (Test-Path $iconPath) { $shortcut.IconLocation = $iconPath }
    $shortcut.Save()
    ok "Desktop shortcut created"
} catch {
    warn "Could not create desktop shortcut: $_"
}

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "  -------------------------------------------------"
ok "FreedomForge AI is installed!"
Write-Host ""
Write-Host "  To launch:" -ForegroundColor Yellow
Write-Host "    Double-click 'FreedomForge AI' on your Desktop" -ForegroundColor Cyan
Write-Host "    or run: $APP_DIR\launch.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dedicated to Miranda." -ForegroundColor Cyan
Write-Host "  She will never be forgotten." -ForegroundColor Cyan
Write-Host "  -------------------------------------------------"
Write-Host ""

$launch = Read-Host "  Launch now? [Y/n]"
if (-not $launch -or $launch -match "^[Yy]") {
    info "Launching FreedomForge AI..."
    Start-Process $python -ArgumentList "`"$APP_DIR\main.py`"" -WorkingDirectory $APP_DIR
}
