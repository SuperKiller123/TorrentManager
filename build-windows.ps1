# Torrent Manager v0.4 – egyetlen PowerShell-parancsból készül el a Windows-verzió.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = '1'

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    if ($pythonLauncher) {
        & py -3.13 -m venv .venv
    } else {
        & python -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw "Python virtuális környezet létrehozása sikertelen. Python 3.13 szükséges." }
}
$py = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $py -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "A Python-függőségek telepítése sikertelen." }

# Tartós könyvtárban lévő Chromium. Ismételt fordításkor nem szükséges újraletölteni.
$browserCache = Join-Path $PSScriptRoot '.browser-cache'
$env:PLAYWRIGHT_BROWSERS_PATH = $browserCache
& $py -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw "A Chromium telepítése sikertelen." }

# A GUI és a motor külön folyamat, de egymás melletti exe-ként kerül kiadásra.
& $py -m PyInstaller --noconfirm --onedir --windowed --name TorrentManager `
    --paths $PSScriptRoot TorrentManager.py
if ($LASTEXITCODE -ne 0) { throw "A GUI build sikertelen." }

& $py -m PyInstaller --noconfirm --onefile --console --name TorrentMotor `
    --paths $PSScriptRoot --collect-all playwright TorrentMotor.py
if ($LASTEXITCODE -ne 0) { throw "A motor build sikertelen." }

$bundle = Join-Path $PSScriptRoot 'dist\TorrentManager'
if (-not (Test-Path $bundle)) { throw "Nem található a GUI kimeneti mappája." }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'dist\TorrentMotor.exe') `
    -Destination (Join-Path $bundle 'TorrentMotor.exe') -Force
$bundledBrowser = Join-Path $bundle 'browsers'
if (Test-Path $bundledBrowser) { Remove-Item $bundledBrowser -Recurse -Force }
Copy-Item -LiteralPath $browserCache -Destination $bundledBrowser -Recurse -Force
if (-not (Get-ChildItem $bundledBrowser -Directory -Filter 'chromium-*' -ErrorAction SilentlyContinue)) {
    throw "Hiányzik a Chromium a hordozható alkalmazásból."
}

# Külön ZIP a GitHub Releases oldalon közzétehető, hordozható verzióhoz.
$portable = Join-Path $PSScriptRoot 'dist\TorrentManager-v0.4-Windows-portable.zip'
if (Test-Path $portable) { Remove-Item $portable -Force }
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $portable -CompressionLevel Optimal
Write-Host "Hordozható program: $bundle\TorrentManager.exe"
Write-Host "Hordozható ZIP: $portable"

# Inno Setup 6, ha telepítve van. GitHub Actions alatt automatikusan telepítjük.
$iscc = $null
foreach ($candidate in @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)) {
    if ($candidate -and (Test-Path $candidate)) { $iscc = $candidate; break }
}
if ($iscc) {
    & $iscc 'installer.iss'
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup build sikertelen." }
    Write-Host "Telepítő: dist\installer\TorrentManager-Setup-v0.4.0.exe"
} else {
    Write-Host "Inno Setup 6 nem található. Hordozható ZIP készült telepítő helyett."
}

# A frissítő automatikusan kizárólag a megfelelő SHA-256 értékű telepítőt fogadja el.
$hashes = @()
$setup = Join-Path $PSScriptRoot 'dist\installer\TorrentManager-Setup-v0.4.0.exe'
foreach ($file in @($portable, $setup)) {
    if (Test-Path $file) {
        $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant()
        $hashes += "$digest  $(Split-Path -Leaf $file)"
    }
}
[System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'dist\SHA256SUMS.txt'),
    [string[]]$hashes, (New-Object System.Text.UTF8Encoding($false)))
