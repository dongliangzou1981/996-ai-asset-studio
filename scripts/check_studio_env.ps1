param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 3001
)

$ErrorActionPreference = "Continue"

function Get-Cn {
    param([string]$Base64Text)
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Base64Text))
}

function Write-Cn {
    param([string]$Base64Text)
    Write-Host (Get-Cn $Base64Text)
}

function Test-Endpoint {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 8
        return @{
            Ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
            Content = $response.Content
        }
    } catch {
        return @{
            Ok = $false
            Content = ""
        }
    }
}

$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"

Write-Cn "OTk2IOe+juacr+i1hOS6p+eUn+aIkCAtIOeOr+Wig+ajgOafpQ=="
Write-Host "http://127.0.0.1:8001/health"
Write-Host "http://127.0.0.1:3001/studio"
Write-Host "http://127.0.0.1:8001/production-studio/style-codes"
Write-Host "http://127.0.0.1:8001/ai_providers/health"
Write-Host ""

if ($env:OFOX_API_KEY) {
    Write-Cn "44CQ5q2j5bi444CRT0ZPWF9BUElfS0VZIOW3suiuvue9ru+8jOacquaJk+WNsCBLZXk="
} else {
    Write-Cn "44CQ5byC5bi444CR5pyq5qOA5rWL5YiwIE9GT1hfQVBJX0tFWe+8jOivt+i/kOihjCDlkK/liqjlt6XkvZzlj7AucHMx"
}

$backend = Test-Endpoint "$backendUrl/health"
if ($backend.Ok) {
    Write-Cn "44CQ5q2j5bi444CR5ZCO56uv6L+Q6KGM5q2j5bi4"
} else {
    Write-Cn "44CQ5byC5bi444CR5ZCO56uv5pyq6L+Q6KGM77yM6K+36L+Q6KGMIOWQr+WKqOW3peS9nOWPsC5wczE="
}

$frontend = Test-Endpoint "$frontendUrl/studio"
if ($frontend.Ok) {
    Write-Cn "44CQ5q2j5bi444CR5YmN56uv6L+Q6KGM5q2j5bi4"
} else {
    Write-Cn "44CQ5byC5bi444CR5YmN56uv5pyq6L+Q6KGM77yM6K+36L+Q6KGMIOWQr+WKqOW3peS9nOWPsC5wczE="
}

$styleCodes = Test-Endpoint "$backendUrl/production-studio/style-codes"
if ($styleCodes.Ok) {
    Write-Cn "44CQ5q2j5bi444CR6aOO5qC85YiX6KGo5o6l5Y+j5q2j5bi4"
} else {
    Write-Cn "44CQ5byC5bi444CR6aOO5qC85YiX6KGo5o6l5Y+j5LiN5Y+v6K6/6Zeu"
}

$providerHealth = Test-Endpoint "$backendUrl/ai_providers/health"
$providerOk = $false
if ($providerHealth.Ok) {
    try {
        $body = $providerHealth.Content | ConvertFrom-Json
        $providerOk = @($body.items | Where-Object { $_.type -eq "ofox" -and $_.status -eq "healthy" }).Count -gt 0
    } catch {
        $providerOk = $false
    }
}
if ($providerOk) {
    Write-Cn "44CQ5q2j5bi444CR5qih5Z6L5pyN5Yqh6YWN572u5q2j5bi4"
} else {
    Write-Cn "44CQ5byC5bi444CR5qih5Z6L5pyN5Yqh5pyq5YeG5aSH5aW977yM6K+36L+Q6KGMIOWQr+WKqOW3peS9nOWPsC5wczE="
}

Write-Host ""
Write-Cn "5aaC5p6c5pyJ5byC5bi477yM6K+35YWI6L+Q6KGMIOWQr+WKqOW3peS9nOWPsC5wczHvvIzkuI3pnIDopoHmiYvliqjliIfmjaLnu4jnq6/miJbmn6XnnIvml6Xlv5fjgII="
