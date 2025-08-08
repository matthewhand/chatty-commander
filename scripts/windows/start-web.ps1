#Requires -Version 5.1
param(
    [int]$Port = 8100,
    [switch]$NoAuth = $true
)

$ErrorActionPreference = 'Stop'

# Move to repo root (script is in scripts/windows)
Set-Location (Join-Path $PSScriptRoot '..' | Join-Path -ChildPath '..')

Write-Host "Starting ChattyCommander web server on port $Port..."

$argsList = @('main.py', '--web')
if ($NoAuth) { $argsList += '--no-auth' }
if ($Port)   { $argsList += @('--port', "$Port") }

function Start-With-UvOrPython {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv run python @argsList
        return
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @argsList
        return
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @argsList
        return
    }
    throw 'Neither uv, python, nor py was found in PATH.'
}

Start-With-UvOrPython

Write-Host "Server should be reachable at http://localhost:$Port/docs"

