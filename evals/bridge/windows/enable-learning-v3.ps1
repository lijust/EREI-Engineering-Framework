# One-time owner-authorized upgrade of the existing PRIVATE Gemini bridge.
# No API calls to Gemini, no token reentry, no new task, no daily cap change.
# Requires two clean SHA-pinned worktrees: this bridge + reviewed V3 adapter.
param(
    [string]$v3_root = "$env:USERPROFILE\Desktop\erei-core13-learning-v3"
)
$ErrorActionPreference = "Stop"
$taskName = "EREI - Gemini Private Bridge"
$state = Join-Path $env:LOCALAPPDATA "EREI\GeminiBridge"
$configPath = Join-Path $state "config.json"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$start = Join-Path $PSScriptRoot "start-gemini-bridge.ps1"
$expectedV3 = "bfe43153a137db15e93d8f6e81d145e4bf9ab024"
$tempFile = Join-Path $state ("config-v3-pending-" + $PID + ".json")
$oldJson = $null
$oldAction = $null
$taskUpdated = $false
$configUpdated = $false
$wasRunning = $false
$completed = $false

function assert-clean-source([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        throw "V3_WORKTREE_MISSING"
    }
    $commit = (& git -C $path rev-parse HEAD 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $commit -cne $expectedV3) {
        throw "V3_WORKTREE_REVISION_MISMATCH"
    }
    $changes = (& git -C $path status --porcelain --untracked-files=all 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $changes.Length -gt 0) {
        throw "V3_WORKTREE_NOT_CLEAN"
    }
}

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "BRIDGE_CONFIG_NOT_INSTALLED"
}
assert-clean-source $v3_root
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
$oldAction = $task.Actions
$wasRunning = ($task.State -eq "Running")
$oldJson = [System.IO.File]::ReadAllText($configPath)
$cfg = $oldJson | ConvertFrom-Json
if ($cfg.version -ne 1 -or $cfg.queue_repo -cne "lijust/EREI-Gemini-Control" -or
    $cfg.enabled -ne $true -or $cfg.daily_limit -lt 1 -or $cfg.daily_limit -gt 10) {
    throw "UNEXPECTED_EXISTING_BRIDGE_CONFIG"
}
$beforeLimit = [int]$cfg.daily_limit
if ($null -ne $cfg.PSObject.Properties["adapter_v3_root"]) {
    $cfg.adapter_v3_root = $v3_root
} else {
    $cfg | Add-Member -NotePropertyName "adapter_v3_root" -NotePropertyValue $v3_root
}

try {
    if ($wasRunning) {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $stopped = $false
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            if ((Get-ScheduledTask -TaskName $taskName).State -ne "Running") {
                $stopped = $true
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if (-not $stopped) {
            throw "OLD_BRIDGE_STOP_UNCONFIRMED"
        }
    }
    $newJson = $cfg | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText(
        $tempFile, $newJson, (New-Object System.Text.UTF8Encoding($false))
    )
    Move-Item -LiteralPath $tempFile -Destination $configPath -Force
    $configUpdated = $true

    # A read-only check of both pinned adapter revisions and the private repo.
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $start -healthcheck
    if ($LASTEXITCODE -ne 0) {
        throw "V3_PRIVATE_HEALTHCHECK_FAILED"
    }
    $scriptArgs = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $start + '"'
    $newAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $scriptArgs
    Set-ScheduledTask -TaskName $taskName -Action $newAction -ErrorAction Stop | Out-Null
    $taskUpdated = $true
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $running = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ((Get-ScheduledTask -TaskName $taskName).State -eq "Running") {
            $running = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $running) {
        throw "V3_BRIDGE_TASK_NOT_RUNNING"
    }
    $completed = $true
    Write-Host "PRIVATE_V3_BRIDGE_UPGRADE_SUCCESS"
    Write-Host "V3_SOURCE_AND_QUEUE_HEALTHCHECK_PASS"
    Write-Host ("DAILY_LIMIT_UNCHANGED_" + $beforeLimit)
    Write-Host "NO_GEMINI_MODEL_CALLS_DURING_UPGRADE"
} finally {
    if (Test-Path -LiteralPath $tempFile -PathType Leaf) {
        Remove-Item -LiteralPath $tempFile -Force
    }
    if (-not $completed) {
        if ($taskUpdated) {
            Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            Set-ScheduledTask -TaskName $taskName -Action $oldAction -ErrorAction SilentlyContinue | Out-Null
        }
        if ($configUpdated) {
            [System.IO.File]::WriteAllText(
                $configPath, $oldJson,
                (New-Object System.Text.UTF8Encoding($false))
            )
        }
        if ($wasRunning) {
            Start-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        }
        Write-Host "V3_UPGRADE_NOT_ACCEPTED_OLD_CONFIG_RESTORED"
    }
}
