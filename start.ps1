# ============================================
# Smart Expense Tracker - Startup Script
# ============================================
# Run this file: Right-click > Run with PowerShell
# Or from terminal: powershell -ExecutionPolicy Bypass -File start.ps1
# ============================================
# Works on a fresh laptop — handles missing venv,
# dependencies, node_modules, data folder, etc.
# ============================================

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$VENV = Join-Path $ROOT "venv"
$DATA = Join-Path $ROOT "data"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Smart Expense Tracker - Starting Up..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ══════════════════════════════════════════════
# Step 1: Check Python
# ══════════════════════════════════════════════
Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
$pythonCmd = $null
# Try 'python' first, then 'python3' (some systems alias differently)
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python\s+(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 9) {
                $pythonCmd = $cmd
                Write-Host "  OK: $ver" -ForegroundColor Green
                break
            } else {
                Write-Host "  Found $ver but need Python 3.9+" -ForegroundColor Yellow
            }
        }
    } catch { }
}
if (-Not $pythonCmd) {
    Write-Host ""
    Write-Host "  ERROR: Python 3.9+ not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install Python:" -ForegroundColor White
    Write-Host "    1. Go to https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host "    2. Download Python 3.10 or newer" -ForegroundColor Gray
    Write-Host '    3. IMPORTANT: Check "Add Python to PATH" during install' -ForegroundColor Gray
    Write-Host "    4. Restart this script after installation" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ══════════════════════════════════════════════
# Step 2: Check Node.js & npm
# ══════════════════════════════════════════════
Write-Host "[2/7] Checking Node.js & npm..." -ForegroundColor Yellow
try {
    $nodeVer = node --version 2>&1
    if ($nodeVer -match "v(\d+)\.") {
        $nodeMajor = [int]$Matches[1]
        if ($nodeMajor -lt 16) {
            Write-Host "  Found Node.js $nodeVer but need v16+" -ForegroundColor Red
            Write-Host "  Download from https://nodejs.org/" -ForegroundColor Gray
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    Write-Host "  OK: Node.js $nodeVer" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "  ERROR: Node.js not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install Node.js:" -ForegroundColor White
    Write-Host "    1. Go to https://nodejs.org/" -ForegroundColor Gray
    Write-Host "    2. Download the LTS version (18.x or newer)" -ForegroundColor Gray
    Write-Host "    3. Run the installer (npm is included)" -ForegroundColor Gray
    Write-Host "    4. Restart this script after installation" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    $npmVer = npm --version 2>&1
    Write-Host "  OK: npm v$npmVer" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: npm not found. It should come with Node.js. Try reinstalling Node.js." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ══════════════════════════════════════════════
# Step 3: Create data directory
# ══════════════════════════════════════════════
Write-Host "[3/7] Ensuring data directory exists..." -ForegroundColor Yellow
if (-Not (Test-Path $DATA)) {
    New-Item -ItemType Directory -Path $DATA | Out-Null
    Write-Host "  Created data/ directory (SQLite DB will be auto-created on first run)" -ForegroundColor Green
} else {
    $dbPath = Join-Path $DATA "expense_tracker.db"
    if (Test-Path $dbPath) {
        $dbSize = (Get-Item $dbPath).Length
        $dbSizeKB = [math]::Round($dbSize / 1024, 1)
        Write-Host "  OK: data/ exists (database: ${dbSizeKB} KB)" -ForegroundColor Green
    } else {
        Write-Host "  OK: data/ exists (database will be created on first run)" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════
# Step 4: Setup Python Virtual Environment
# ══════════════════════════════════════════════
Write-Host "[4/7] Setting up Python virtual environment..." -ForegroundColor Yellow
$venvPython = Join-Path $VENV "Scripts\python.exe"
$venvPip = Join-Path $VENV "Scripts\pip.exe"

if (-Not (Test-Path $venvPython)) {
    Write-Host "  No virtual environment found. Creating one..." -ForegroundColor Gray
    try {
        & $pythonCmd -m venv $VENV
        if (-Not (Test-Path $venvPython)) {
            throw "venv creation did not produce python.exe"
        }
        Write-Host "  Virtual environment created at ./venv/" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: Failed to create virtual environment" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Try running manually: $pythonCmd -m venv venv" -ForegroundColor Gray
        Write-Host "  If 'venv' module is missing, install it:" -ForegroundColor Gray
        Write-Host "    - Windows: Python installer should include it" -ForegroundColor Gray
        Write-Host "    - Or: $pythonCmd -m pip install virtualenv" -ForegroundColor Gray
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "  OK: Virtual environment exists" -ForegroundColor Green
}

# ══════════════════════════════════════════════
# Step 5: Install Python dependencies
# ══════════════════════════════════════════════
Write-Host "[5/7] Installing Python dependencies..." -ForegroundColor Yellow
$requirementsFile = Join-Path $BACKEND "requirements.txt"

# Upgrade pip first to avoid warnings on fresh venv
Write-Host "  Upgrading pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet 2>&1 | Out-Null

if (Test-Path $requirementsFile) {
    # Check which packages are already installed
    $installedRaw = & $venvPip freeze 2>&1
    $installed = @()
    if ($installedRaw -and $installedRaw -is [array]) {
        $installed = $installedRaw
    } elseif ($installedRaw -and $installedRaw -is [string] -and $installedRaw.Trim() -ne "") {
        $installed = @($installedRaw)
    }

    $requirements = Get-Content $requirementsFile | Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*#' }
    $missingPackages = @()

    foreach ($req in $requirements) {
        $pkgName = ($req -split '==|>=|<=|~=|!=|<|>|\[')[0].Trim().ToLower()
        $found = $false
        foreach ($inst in $installed) {
            if ($inst -match "(?i)^$([regex]::Escape($pkgName))==") {
                $found = $true
                break
            }
        }
        if (-Not $found) {
            $missingPackages += $pkgName
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-Host "  Missing packages: $($missingPackages -join ', ')" -ForegroundColor Gray
        Write-Host "  Installing from requirements.txt..." -ForegroundColor Gray
        & $venvPip install -r $requirementsFile 2>&1 | ForEach-Object {
            if ($_ -match "Successfully installed") { Write-Host "  $_" -ForegroundColor Green }
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  WARNING: Some packages may have failed. Retrying with verbose output..." -ForegroundColor Yellow
            & $venvPip install -r $requirementsFile
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  ERROR: Failed to install Python dependencies" -ForegroundColor Red
                Write-Host "  Try manually: .\venv\Scripts\pip.exe install -r backend\requirements.txt" -ForegroundColor Gray
                Read-Host "Press Enter to exit"
                exit 1
            }
        }
        Write-Host "  Python packages installed" -ForegroundColor Green
    } else {
        Write-Host "  OK: All Python packages already installed" -ForegroundColor Green
    }
} else {
    Write-Host "  ERROR: requirements.txt not found at $requirementsFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Also ensure python-docx is installed (needed for report generation)
$docxInstalled = & $venvPip freeze 2>&1 | Select-String -Pattern "(?i)^python-docx=="
if (-Not $docxInstalled) {
    Write-Host "  Installing python-docx (for report generation)..." -ForegroundColor Gray
    & $venvPip install python-docx --quiet 2>&1 | Out-Null
    Write-Host "  python-docx installed" -ForegroundColor Green
}

# ══════════════════════════════════════════════
# Step 6: Install Node.js dependencies
# ══════════════════════════════════════════════
Write-Host "[6/7] Installing Node.js dependencies..." -ForegroundColor Yellow
$nodeModules = Join-Path $FRONTEND "node_modules"
$packageJson = Join-Path $FRONTEND "package.json"

if (-Not (Test-Path $packageJson)) {
    Write-Host "  ERROR: package.json not found at $FRONTEND" -ForegroundColor Red
    Write-Host "  Make sure the frontend/ folder is complete" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

if (-Not (Test-Path $nodeModules)) {
    Write-Host "  No node_modules found. Running npm install..." -ForegroundColor Gray
    Write-Host "  (This may take 1-3 minutes on first run)" -ForegroundColor Gray
    Push-Location $FRONTEND
    npm install 2>&1 | ForEach-Object {
        if ($_ -match "added \d+ packages") { Write-Host "  $_" -ForegroundColor Green }
    }
    $npmExitCode = $LASTEXITCODE
    Pop-Location
    if ($npmExitCode -ne 0) {
        Write-Host "  ERROR: npm install failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Troubleshooting:" -ForegroundColor White
        Write-Host "    1. Delete frontend/node_modules and try again" -ForegroundColor Gray
        Write-Host "    2. Run: cd frontend && npm install" -ForegroundColor Gray
        Write-Host "    3. If behind a proxy, configure npm proxy settings" -ForegroundColor Gray
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "  npm packages installed" -ForegroundColor Green
} else {
    # node_modules exists, but check if it looks healthy (has .package-lock.json)
    $lockFile = Join-Path $FRONTEND "node_modules\.package-lock.json"
    if (-Not (Test-Path $lockFile)) {
        Write-Host "  node_modules may be corrupted. Reinstalling..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $nodeModules -ErrorAction SilentlyContinue
        Push-Location $FRONTEND
        npm install 2>&1 | Out-Null
        Pop-Location
        Write-Host "  npm packages reinstalled" -ForegroundColor Green
    } else {
        Write-Host "  OK: node_modules exists" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════
# Step 7: Start servers
# ══════════════════════════════════════════════
Write-Host "[7/7] Starting servers..." -ForegroundColor Yellow
Write-Host ""

# Kill any existing processes on ports 5000 and 3000
foreach ($port in @(5001, 3000)) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "  Stopping existing process on port $port..." -ForegroundColor Gray
        $conn | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }
}

# Start Backend
Write-Host "  Starting Backend (Flask) on port 5001..." -ForegroundColor Cyan
# Run Flask with the backend folder as the working directory so that 'app.py'
# can import local modules like 'database.py' correctly.
$backendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m", "flask", "--app", "app", "run", "--port", "5001" -WorkingDirectory $BACKEND -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3

# Verify backend started
$backendOK = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001/api/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        Write-Host "  Backend started successfully!" -ForegroundColor Green
        $backendOK = $true
        break
    } catch {
        if ($i -lt 3) {
            Write-Host "  Waiting for backend... (attempt $i/3)" -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    }
}
if (-Not $backendOK) {
    Write-Host "  Backend may still be starting. Check the backend window for errors." -ForegroundColor Yellow
    Write-Host "  If it fails, try: cd backend; ..\venv\Scripts\python.exe -m flask --app app run --port 5001" -ForegroundColor Gray
}

# Start Frontend
Write-Host "  Starting Frontend (React) on port 3000..." -ForegroundColor Cyan
$env:BROWSER = "none"
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "start" -WorkingDirectory $FRONTEND -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Smart Expense Tracker is running!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:5001" -ForegroundColor White
Write-Host ""
Write-Host "  Opening browser in a few seconds..." -ForegroundColor Gray

# Open browser after frontend has time to compile
Start-Sleep -Seconds 8
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "  Press Ctrl+C or close this window to stop both servers." -ForegroundColor Yellow
Write-Host ""

# Keep script alive and gracefully shut down on exit
try {
    while ($true) {
        Start-Sleep -Seconds 60
    }
} finally {
    Write-Host ""
    Write-Host "Shutting down..." -ForegroundColor Yellow
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Backend stopped" -ForegroundColor Gray
    }
    if ($frontendProcess -and !$frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Frontend stopped" -ForegroundColor Gray
    }
    Write-Host "Done." -ForegroundColor Green
}
