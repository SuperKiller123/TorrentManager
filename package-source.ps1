$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$archive = Join-Path (Split-Path $repo -Parent) 'TorrentManager-v0.8-source.zip'
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $archive) { throw 'Source archive already exists; review before replacing.' }
$zip = [IO.Compression.ZipFile]::Open($archive, [IO.Compression.ZipArchiveMode]::Create)
try {
    $files = @(Get-ChildItem -LiteralPath $repo -File | Where-Object {
        $_.Extension -in @('.py','.ps1','.iss','.md','.txt','.bat','.html') -or $_.Name -eq '.gitignore'
    })
    foreach ($sub in @('tests','assets','.github','evidence')) {
        $files += Get-ChildItem -LiteralPath (Join-Path $repo $sub) -Recurse -File | Where-Object {
            $_.FullName -notmatch '__pycache__' -and $_.Extension -in @('.py','.ico','.png','.yml','.log')
        }
    }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($repo.Length+1).Replace('\','/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$file.FullName,$relative) | Out-Null
    }
} finally { $zip.Dispose() }
Get-FileHash -LiteralPath $archive -Algorithm SHA256
