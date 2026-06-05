param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 3001
)

$ErrorActionPreference = "Continue"

function Write-Check {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail = ""
    )
    $status = if ($Ok) { "PASS" } else { "FAIL" }
    $color = if ($Ok) { "Green" } else { "Red" }
    if ($Detail) {
        Write-Host "[$status] $Name - $Detail" -ForegroundColor $color
    } else {
        Write-Host "[$status] $Name" -ForegroundColor $color
    }
}

function Test-Endpoint {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 8
        return @{
            Ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
            Detail = "HTTP $($response.StatusCode)"
            Content = $response.Content
        }
    } catch {
        return @{
            Ok = $false
            Detail = $_.Exception.Message
            Content = ""
        }
    }
}

$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"

Write-Host "996 Studio local environment check"
Write-Host "Default backend health URL: http://127.0.0.1:8001/health"
Write-Host "Default frontend URL: http://127.0.0.1:3001/studio"
Write-Host "Default STYLE_CODE URL: http://127.0.0.1:8001/production-studio/style-codes"
Write-Host "Default provider health URL: http://127.0.0.1:8001/ai_providers/health"
Write-Host ""

$keyDetail = if ($env:OFOX_API_KEY) { "set; key is not printed" } else { "not set; run scripts/start_local_studio.ps1" }
Write-Check "OFOX_API_KEY" ([bool]$env:OFOX_API_KEY) $keyDetail

$backend = Test-Endpoint "$backendUrl/health"
Write-Check "backend 8001" $backend.Ok $backend.Detail

$frontend = Test-Endpoint "$frontendUrl/studio"
Write-Check "frontend 3001 /studio" $frontend.Ok $frontend.Detail

$styleCodes = Test-Endpoint "$backendUrl/production-studio/style-codes"
Write-Check "/production-studio/style-codes" $styleCodes.Ok $styleCodes.Detail

$providerHealth = Test-Endpoint "$backendUrl/ai_providers/health"
$providerOk = $false
if ($providerHealth.Ok) {
    try {
        $body = $providerHealth.Content | ConvertFrom-Json
        $providerOk = @($body.items | Where-Object { $_.type -eq "ofox" -and $_.status -eq "healthy" }).Count -gt 0
        $detail = if ($providerOk) { "at least one Ofox provider is healthy" } else { "no healthy Ofox provider" }
    } catch {
        $detail = "provider health JSON parse failed"
    }
} else {
    $detail = $providerHealth.Detail
}
Write-Check "provider health" $providerOk $detail

Write-Host ""
Write-Host "If any check FAILs, rerun scripts/start_local_studio.ps1 first."
