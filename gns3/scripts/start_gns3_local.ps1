$ErrorActionPreference = "Stop"

$gns3Server = "C:\Program Files\GNS3\gns3server.EXE"
$dynamipsDir = "C:\Program Files\GNS3\dynamips"
$vpcsDir = "C:\Program Files\GNS3\vpcs"
$configFile = Join-Path $env:APPDATA "GNS3\2.2\gns3_server.ini"
$port = 3082

if (-not (Test-Path $gns3Server)) {
    throw "gns3server.EXE not found at $gns3Server"
}

if (-not (Test-Path (Join-Path $dynamipsDir "dynamips.exe"))) {
    throw "dynamips.exe not found at $dynamipsDir"
}

if (-not (Test-Path (Join-Path $vpcsDir "vpcs.exe"))) {
    throw "vpcs.exe not found at $vpcsDir"
}

if (-not (Test-Path $configFile)) {
    throw "GNS3 config file not found at $configFile"
}

$env:PATH = "$dynamipsDir;$vpcsDir;$env:PATH"

Write-Host "Starting GNS3 server on http://localhost:$port"
Write-Host "Using config: $configFile"
Write-Host "Using Dynamips dir in PATH: $dynamipsDir"
Write-Host "Using VPCS dir in PATH: $vpcsDir"

& $gns3Server --host localhost --port $port --config $configFile -L
