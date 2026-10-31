# Torrent Manager's uninstall maintenance. No qBittorrent APIs or files are changed.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Prepare','Remove')][string]$Mode,
    [Parameter(Mandatory=$true)][string]$AppDirectory,
    [string]$TestRoot = '',
    [Parameter(Mandatory=$true)][string]$ReportPath
)
$ErrorActionPreference = 'Stop'
$script:Problems = [System.Collections.Generic.List[string]]::new()
$script:ProtectedPaths = [System.Collections.Generic.List[string]]::new()
$script:OwnedId = '4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F'

function FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}
function IsWithin([string]$Path, [string]$Root) {
    $p = FullPath $Path
    $r = FullPath $Root
    return $p.Equals($r, [StringComparison]::OrdinalIgnoreCase) -or $p.StartsWith($r + '\', [StringComparison]::OrdinalIgnoreCase)
}
function HasReparseAncestor([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $true }
        $item = $item.Parent
    }
    return $false
}
function RememberDownload([string]$Directory) {
    $settings = Join-Path $Directory 'beallitasok.json'
    if (Test-Path -LiteralPath $settings -PathType Leaf) {
        try {
            $data = Get-Content -LiteralPath $settings -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($data.qb_save_path -and [IO.Path]::IsPathRooted([string]$data.qb_save_path)) {
                $script:ProtectedPaths.Add((FullPath ([string]$data.qb_save_path)))
            }
        } catch { $script:Problems.Add("Cannot read download location in $settings; preserving this directory."); $script:ProtectedPaths.Add((FullPath $Directory)) }
    }
}
function RemoveOwnedTree([string]$Path, [string]$Boundary) {
    if (-not (IsWithin $Path $Boundary)) { throw 'Cleanup escaped its owned directory.' }
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $full = FullPath $Path
    foreach ($protected in $script:ProtectedPaths) {
        if (IsWithin $full $protected) { $script:Problems.Add("Preserved download directory: $full"); return }
    }
    try {
        $item = Get-Item -LiteralPath $full -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            # Remove only the link, never enumerate its target.
            if ($item.PSIsContainer) { [IO.Directory]::Delete($full) } else { [IO.File]::Delete($full) }
            return
        }
        if ($item.PSIsContainer) {
            foreach ($child in @(Get-ChildItem -LiteralPath $full -Force)) {
                RemoveOwnedTree $child.FullName $Boundary
            }
            if (@(Get-ChildItem -LiteralPath $full -Force).Count -eq 0) { [IO.Directory]::Delete($full) }
        } else {
            # Explicit torrent metadata placed here by a user is not application data.
            if ($item.Extension -ieq '.torrent') { $script:Problems.Add("Preserved torrent file: $full"); return }
            $item.Attributes = [IO.FileAttributes]::Normal
            [IO.File]::Delete($full)
        }
    } catch { $script:Problems.Add("Could not remove $full : $($_.Exception.Message)") }
}
function RemoveOwnShortcut([string]$Path) {
    if (-not $Path -or [IO.Path]::GetFileName($Path) -ine 'Torrent Manager.lnk') { return }
    if ($TestRoot -and -not (IsWithin $Path $TestRoot)) { throw 'Test shortcut escaped the test root.' }
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        try {
            # Exact name alone is not sufficient: a user may have replaced this link.
            $shell = New-Object -ComObject WScript.Shell
            $link = $shell.CreateShortcut($Path)
            if ([IO.Path]::GetFileName($link.TargetPath) -ieq 'TorrentManager.exe') {
                Remove-Item -LiteralPath $Path -Force
            }
        } catch { $script:Problems.Add("Could not remove shortcut $Path : $($_.Exception.Message)") }
    }
}
function ExpandProfilePath([string]$Value, [string]$Profile, [string]$Local, [string]$Roaming) {
    $expanded = $Value.Replace('%USERPROFILE%', $Profile).Replace('%userprofile%', $Profile)
    if ($Local) { $expanded = $expanded.Replace('%LOCALAPPDATA%', $Local) }
    if ($Roaming) { $expanded = $expanded.Replace('%APPDATA%', $Roaming) }
    $expanded = [Environment]::ExpandEnvironmentVariables($expanded)
    if ($expanded.Contains('%') -or -not [IO.Path]::IsPathRooted($expanded)) { throw "Unresolved profile path: $Value" }
    return FullPath $expanded
}
function ProfilePlan([string]$Profile, $Hive) {
    $local = Join-Path $Profile 'AppData\Local'
    $roaming = Join-Path $Profile 'AppData\Roaming'
    $desktop = Join-Path $Profile 'Desktop'
    $startup = Join-Path $roaming 'Microsoft\Windows\Start Menu\Programs\Startup'
    if ($null -ne $Hive) {
        $key = $Hive.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')
        if ($null -ne $key) {
            try {
                $option = [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
                $local = ExpandProfilePath ([string]$key.GetValue('Local AppData',$local,$option)) $Profile '' ''
                $roaming = ExpandProfilePath ([string]$key.GetValue('AppData',$roaming,$option)) $Profile $local ''
                $desktop = ExpandProfilePath ([string]$key.GetValue('Desktop',$desktop,$option)) $Profile $local $roaming
                $startup = ExpandProfilePath ([string]$key.GetValue('Startup',$startup,$option)) $Profile $local $roaming
            } finally { $key.Close() }
        }
    }
    $roots = @((Join-Path $local 'TorrentManager'), (Join-Path $roaming 'TorrentManager'),
        (Join-Path $Profile 'AppData\Local\TorrentManager'), (Join-Path $Profile 'AppData\Roaming\TorrentManager')) | Select-Object -Unique
    foreach ($root in $roots) { RememberDownload $root }
    return @{ Roots=$roots; Desktop=$desktop; Startup=$startup }
}
function CleanProfile($Plan, $Hive) {
    foreach ($root in $Plan.Roots) {
        if ($TestRoot -and -not (IsWithin $root $TestRoot)) { throw 'Test profile escaped the test root.' }
        if (HasReparseAncestor (Split-Path -Parent $root)) { $script:Problems.Add("Skipped linked profile parent: $root"); continue }
        $record = Join-Path $root 'windows.ini'
        if (Test-Path -LiteralPath $record -PathType Leaf) {
            foreach ($line in Get-Content -LiteralPath $record -Encoding UTF8) {
                if ($line -match '^\s*(DesktopShortcut|StartupShortcut)\s*=\s*(.+?)\s*$') { RemoveOwnShortcut $Matches[2] }
            }
        }
        RemoveOwnedTree $root $root
    }
    RemoveOwnShortcut (Join-Path $Plan.Desktop 'Torrent Manager.lnk')
    RemoveOwnShortcut (Join-Path $Plan.Startup 'Torrent Manager.lnk')
    if ($null -ne $Hive) {
        try {
            $Hive.DeleteSubKeyTree('Software\TorrentManager', $false)
            $run = $Hive.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Run', $true)
            if ($null -ne $run) { try { $run.DeleteValue('TorrentManager', $false) } finally { $run.Close() } }
        } catch { $script:Problems.Add("Could not remove Torrent Manager registry settings: $($_.Exception.Message)") }
    }
}

try {
    $AppDirectory = FullPath $AppDirectory
    if ([IO.Path]::GetFileName($AppDirectory) -ine 'Torrent Manager') { throw 'Refusing cleanup outside a dedicated Torrent Manager folder.' }
    if (HasReparseAncestor $AppDirectory) { throw 'Refusing cleanup through a linked installation folder.' }
    if ($TestRoot) {
        $TestRoot = FullPath $TestRoot
        if (-not (IsWithin $AppDirectory $TestRoot)) { throw 'Test installation escaped its root.' }
        $fixture = Join-Path $TestRoot '.torrentmanager-test'
        if (-not (Test-Path -LiteralPath $fixture) -or (Get-Content -LiteralPath $fixture -Raw).Trim() -ne $script:OwnedId) {
            throw 'Missing isolated-test authorization marker.'
        }
    }
    $marker = Join-Path $AppDirectory '.torrentmanager-install'
    if (-not (Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne $script:OwnedId) {
        throw 'Missing application ownership marker; cleanup refused.'
    }
    if ($Mode -eq 'Prepare') {
        # Match actual executable paths, not process names from another installation.
        foreach ($process in Get-Process -ErrorAction SilentlyContinue) {
            try {
                if ($process.Id -eq $PID -or -not $process.Path -or -not (IsWithin $process.Path $AppDirectory)) { continue }
                if ($process.ProcessName -notin @('TorrentManager','TorrentMotor','TorrentLogin','TorrentUpdater','chrome','chrome_crashpad_handler','headless_shell')) { continue }
                $null = $process.CloseMainWindow()
                if (-not $process.WaitForExit(1500)) { $process.Kill(); $process.WaitForExit(5000) | Out-Null }
            } catch { $script:Problems.Add("Could not close app process $($process.Id): $($_.Exception.Message)") }
        }
    } else {
        RememberDownload $AppDirectory
        if ($TestRoot) {
            foreach ($profile in @(Get-ChildItem -LiteralPath (Join-Path $TestRoot 'profiles') -Directory -ErrorAction SilentlyContinue)) {
                if (HasReparseAncestor $profile.FullName) { throw 'Test profile is linked.' }
                $plan = ProfilePlan $profile.FullName $null
                CleanProfile $plan $null
            }
        } else {
            $machine = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryView]::Registry64)
            $users = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::Users,[Microsoft.Win32.RegistryView]::Registry64)
            $profiles = $machine.OpenSubKey('SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
            try {
                foreach ($sid in $profiles.GetSubKeyNames()) {
                    if ($sid -notmatch '^S-1-5-21-[0-9-]+$' -and $sid -notmatch '^S-1-12-1-[0-9-]+$') { continue }
                    $entry = $profiles.OpenSubKey($sid)
                    try { $profile = [Environment]::ExpandEnvironmentVariables([string]$entry.GetValue('ProfileImagePath')) } finally { $entry.Close() }
                    if (-not $profile -or -not (Test-Path -LiteralPath $profile -PathType Container)) { continue }
                    if (HasReparseAncestor $profile) { $script:Problems.Add("Skipped linked profile: $profile"); continue }
                    $hive = $null; $mount = ''
                    try {
                        $hive = $users.OpenSubKey($sid, $true)
                        if ($null -eq $hive -and (Test-Path -LiteralPath (Join-Path $profile 'NTUSER.DAT'))) {
                            $mount = 'TorrentManagerUninstall_' + $PID + '_' + $sid
                            & "$env:SystemRoot\System32\reg.exe" load "HKU\$mount" (Join-Path $profile 'NTUSER.DAT') 2>&1 | Out-Null
                            if ($LASTEXITCODE -ne 0) { throw "Cannot load registry profile $sid" }
                            $hive = $users.OpenSubKey($mount, $true)
                        }
                        $plan = ProfilePlan $profile $hive
                        CleanProfile $plan $hive
                    } catch { $script:Problems.Add("Profile cleanup failed for $sid : $($_.Exception.Message)") }
                    finally {
                        if ($null -ne $hive) { $hive.Close() }
                        if ($mount) {
                            [GC]::Collect(); [GC]::WaitForPendingFinalizers()
                            & "$env:SystemRoot\System32\reg.exe" unload "HKU\$mount" 2>&1 | Out-Null
                            if ($LASTEXITCODE -ne 0) { $script:Problems.Add("Could not unload temporary registry mount $mount") }
                        }
                    }
                }
            } finally { if ($profiles) { $profiles.Close() }; $machine.Close(); $users.Close() }
        }
        RemoveOwnedTree $AppDirectory $AppDirectory
    }
} catch { $script:Problems.Add($_.Exception.Message) }
if ($script:Problems.Count) {
    [IO.File]::WriteAllLines($ReportPath, $script:Problems, [Text.Encoding]::UTF8)
    exit 1
}
exit 0
