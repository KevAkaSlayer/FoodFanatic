# Start FoodFanatic locally. Creates the virtualenv, installs dependencies,
# copies .env, and applies migrations only when those steps are still missing.
#
#   .\run.ps1              start the development server
#   .\run.ps1 test         run the test suite
#   .\run.ps1 check        run system checks
#   .\run.ps1 seed         load the demo menu
#   .\run.ps1 admin        create a superuser
#   .\run.ps1 <anything>   passed straight through to manage.py

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Command = @("runserver")
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

# requirements.txt is newer than the install marker, or there is no marker yet.
$marker = Join-Path $PSScriptRoot ".venv\.requirements-installed"
$requirements = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path $marker) -or
    (Get-Item $requirements).LastWriteTimeUtc -gt (Get-Item $marker).LastWriteTimeUtc) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    & $python -m pip install --quiet --upgrade pip
    & $python -m pip install --quiet -r requirements.txt
    if (-not (Test-Path $marker)) { New-Item -ItemType File $marker | Out-Null }
    (Get-Item $marker).LastWriteTimeUtc = (Get-Date).ToUniversalTime()
}

if (-not (Test-Path (Join-Path $PSScriptRoot ".env"))) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Cyan
    Copy-Item .env.example .env
}

# Translate the friendly aliases into their manage.py equivalents. Rebuilding
# the array by index would break for a bare alias, so only replace element 0.
$aliases = @{ "seed" = "seed_menu"; "admin" = "createsuperuser" }
if ($aliases.ContainsKey($Command[0])) {
    $Command[0] = $aliases[$Command[0]]
}

if ($Command[0] -eq "runserver") {
    & $python manage.py migrate --noinput
    Write-Host "`nFoodFanatic is starting on http://127.0.0.1:8000/`n" -ForegroundColor Green
}

& $python manage.py @Command
exit $LASTEXITCODE
