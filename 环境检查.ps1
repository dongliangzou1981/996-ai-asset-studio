param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 3001
)

& ".\scripts\check_studio_env.ps1" -BackendPort $BackendPort -FrontendPort $FrontendPort
