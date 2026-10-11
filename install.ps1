$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "NOTHOS v6 — Windows Installer"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher not found. Install Python 3.11+."
}

py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }

$Python = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
$Nothos = Join-Path $PSScriptRoot ".venv\\Scripts\\nothos.exe"

& $Python -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Package installation failed" }

& $Nothos doctor

Write-Host "NOTHOS installed successfully."
Write-Host "Run: .\\.venv\\Scripts\\nothos.exe --help"
Write-Host "Banner: .\\.venv\\Scripts\\nothos.exe banner --style ascii"
