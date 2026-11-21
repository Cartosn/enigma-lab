# Instala el entorno de Enigma Lab en Windows (PowerShell 5.1 o 7).
#
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1
#
# Instala con winget, solo para tu usuario, lo que falte: uv (gestor de entornos de
# Python) y GNU Make. Después uv descarga Python 3.12 y las dependencias de uv.lock.

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Update-SessionPath {
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $env:Path = "$user;$machine"
}

if (-not (Test-Command 'uv')) {
    Write-Host 'Instalando uv con winget...'
    winget install --id astral-sh.uv -e --source winget
    Update-SessionPath
}

if (-not (Test-Command 'make')) {
    Write-Host 'Instalando GNU Make con winget...'
    winget install --id ezwinports.make -e --source winget
    Update-SessionPath
}

uv python install 3.12
uv sync

Write-Host ''
Write-Host 'Listo. Abre la app con:  make app'
Write-Host '(Si esta terminal no encuentra uv o make, abre una nueva.)'
