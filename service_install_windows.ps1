param(
    [string]$TaskName = "Phonotify",
    [ValidateSet("install","uninstall")][string]$Action = "install"
)

$ErrorActionPreference = 'Stop'

# Project root
$Root = $PSScriptRoot

function Write-Ok($m){ Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Err($m){ Write-Host "[ERR] $m" -ForegroundColor Red }

if ($Action -eq 'uninstall'){
    Write-Host "Uninstalling scheduled task '$TaskName' and removing run wrapper..."
    schtasks /Delete /TN $TaskName /F 2>$null | Out-Null
    $bat = Join-Path $Root "run_phonotify.bat"
    if (Test-Path $bat){ Remove-Item $bat -Force; Write-Ok "Removed $bat" }
    Write-Ok "Uninstall complete."
    exit 0
}

Write-Host "Installing Phonotify (Windows)..."

# Ensure logs directory
$logs = Join-Path $Root "logs"
if (-not (Test-Path $logs)) { New-Item -ItemType Directory -Path $logs | Out-Null; Write-Ok "Created logs dir" }

# Determine Python
$venvPython = Join-Path $Root "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $Python = $venvPython
    Write-Ok "Using existing venv Python: $Python"
} else {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $pyCmd) { Write-Err "Python is not installed or not on PATH. Install Python 3.8+ and re-run."; exit 1 }
    $Python = $pyCmd.Path
    Write-Ok "Using system Python: $Python"

    # Create venv
    Write-Host "Creating virtual environment..."
    & $Python -m venv (Join-Path $Root 'venv')
    if (-not (Test-Path $venvPython)) { Write-Err "Failed to create venv"; exit 1 }
    $Python = $venvPython
    Write-Ok "Created venv: $venvPython"
}

# Upgrade pip and install requirements
$req = Join-Path $Root "requirements.txt"
if (Test-Path $req) {
    Write-Host "Installing Python dependencies from requirements.txt..."
    & $Python -m pip install -U pip
    & $Python -m pip install -r $req
    Write-Ok "Dependencies installed"
} else {
    Write-Err "No requirements.txt found in project root."; exit 1
}

# Create a batch wrapper that runs the app and logs output
$batPath = Join-Path $Root "run_phonotify.bat"
$batContent = "@echo off`r`ncd /d %~dp0`r`nvenv\\Scripts\\python.exe "%~dp0\\src\\main.py" >> "%~dp0\\logs\\service.log" 2>&1"
Set-Content -Path $batPath -Value $batContent -Encoding ASCII
Write-Ok "Created run wrapper: $batPath"

# Register scheduled task to run at user logon (highest privileges)
Write-Host "Registering scheduled task '$TaskName' to run at logon..."
$escapedBat = $batPath
$tr = '"C:\Windows\System32\cmd.exe" /c "' + $escapedBat + '"'
schtasks /Create /SC ONLOGON /RL HIGHEST /F /TN $TaskName /TR $tr | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Ok "Scheduled task created: $TaskName" } else { Write-Err "Failed creating scheduled task (exit code $LASTEXITCODE)" }

# Start the task once now
try {
    schtasks /Run /TN $TaskName | Out-Null
    Write-Ok "Started task $TaskName"
} catch {
    Write-Err "Could not start scheduled task immediately; it will run at next login."
}

Write-Host "-------------------------------------------------------"
Write-Host "Installation complete."
Write-Host "- To uninstall run: powershell -ExecutionPolicy Bypass -File service_install_windows.ps1 -Action uninstall"
Write-Host "- Logs: logs\\service.log"
Write-Host "-------------------------------------------------------"
