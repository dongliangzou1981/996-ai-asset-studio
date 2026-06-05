param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 3001
)

$ErrorActionPreference = "Stop"

function Write-Cn {
    param([string]$Base64Text)
    Write-Host ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Base64Text)))
}

Write-Cn "5q2j5Zyo5ZCv5Yqo5pys5Zyw5bel5L2c5Y+wLi4u"
Write-Cn "5aaC5p6c6ISa5pys5o+Q56S66L6T5YWlIEtlee+8jOi+k+WFpeaXtuS4jeS8muaYvuekuu+8jOi/meaYr+ato+W4uOeahOOAgg=="

& ".\scripts\start_local_studio.ps1" -BackendPort $BackendPort -FrontendPort $FrontendPort

if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
    Write-Cn "5pys5Zyw5bel5L2c5Y+w5ZCv5Yqo5a6M5oiQ5ZCO5Lya6Ieq5Yqo5omT5byA77yaaHR0cDovLzEyNy4wLjAuMTozMDAxL3N0dWRpbw=="
    Start-Process "http://127.0.0.1:$FrontendPort/studio"
}
