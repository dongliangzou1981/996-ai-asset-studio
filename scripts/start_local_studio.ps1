param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 3001
)

$ErrorActionPreference = "Stop"

function Test-ProjectRoot {
    return (Test-Path "backend\app\main.py") -and
        (Test-Path "frontend\package.json") -and
        (Test-Path "scripts\setup_ofox_provider.py")
}

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
    } catch {
        return $false
    }
}

if (-not (Test-ProjectRoot)) {
    Write-Host "Please cd to the project root before running scripts/start_local_studio.ps1" -ForegroundColor Red
    exit 1
}

$projectRoot = (Get-Location).Path
$pythonExe = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Missing backend\.venv\Scripts\python.exe. Please create the backend virtual environment first." -ForegroundColor Red
    exit 1
}

if (-not $env:OFOX_API_KEY) {
    $secureKey = Read-Host "Enter OFOX_API_KEY (input is hidden)" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try {
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    if (-not $plainKey) {
        Write-Host "OFOX_API_KEY is empty. Startup stopped." -ForegroundColor Red
        exit 1
    }
    $env:OFOX_API_KEY = $plainKey
}

$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"
$studioUrl = "$frontendUrl/studio"

if (-not (Test-HttpOk "$backendUrl/health")) {
    Write-Host "Starting backend FastAPI at $backendUrl"
    Start-Job -Name "996-studio-backend" -ArgumentList $projectRoot, $pythonExe, $BackendPort, $env:OFOX_API_KEY -ScriptBlock {
        param($Root, $Python, $Port, $OfoxKey)
        Set-Location $Root
        $env:OFOX_API_KEY = $OfoxKey
        & $Python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $Port
    } | Out-Null
}

$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk "$backendUrl/health") {
        break
    }
    Start-Sleep -Seconds 1
}

if (-not (Test-HttpOk "$backendUrl/health")) {
    Write-Host "Backend startup failed. Run scripts/check_studio_env.ps1 for diagnostics." -ForegroundColor Red
    exit 1
}

Write-Host "Ensuring default Ofox provider..."
& $pythonExe "scripts\setup_ofox_provider.py" --api-base $backendUrl | Out-Host

if (-not (Test-HttpOk $studioUrl)) {
    Write-Host "Starting frontend Next.js at $frontendUrl"
    Start-Job -Name "996-studio-frontend" -ArgumentList $projectRoot, $FrontendPort, $backendUrl -ScriptBlock {
        param($Root, $Port, $ApiBase)
        Set-Location (Join-Path $Root "frontend")
        $env:NEXT_PUBLIC_API_BASE_URL = $ApiBase
        npm run dev -- --hostname 127.0.0.1 --port $Port
    } | Out-Null
}

Write-Host ""
Write-Host "Local studio is starting:" -ForegroundColor Green
Write-Host $studioUrl -ForegroundColor Cyan
Write-Host "Default frontend URL: http://127.0.0.1:3001/studio"
Write-Host ""
Write-Host "If generation fails, run scripts/check_studio_env.ps1 in this PowerShell session."
Write-Host "After this PowerShell window closes, the OFOX_API_KEY entered here expires."
