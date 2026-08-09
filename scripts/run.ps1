param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8787,
    [string]$DataDir = "work/data"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
$env:PYTHONPATH = Join-Path $Root "src"
python app.py --host $HostName --port $Port --data-dir $DataDir --static-dir web
