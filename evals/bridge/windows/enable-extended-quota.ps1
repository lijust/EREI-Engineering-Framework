# Upgrade the owner-local private Gemini bridge from reviewed V4 to the
# reviewed extended-budget worker, keeping SAME DPAPI secrets and SQLite journal.
# No live Gemini requests during upgrade. Never changes any other Scheduled Task.
param([ValidateRange(1,500)][int]$DailyLimit = 450)

$ErrorActionPreference = "Stop"
$taskName = "EREI - Gemini Private Bridge"
$state = Join-Path $env:LOCALAPPDATA "EREI\GeminiBridge"
$configPath = Join-Path $state "config.json"
$start = Join-Path $PSScriptRoot "start-gemini-bridge.ps1"
$pending = Join-Path $state ("config-quota-pending-" + $PID + ".json")
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
$originalActions = $task.Actions
$wasRunning = ($task.State -eq "Running")
$oldJson = [System.IO.File]::ReadAllText($configPath)
$cfg = $oldJson | ConvertFrom-Json
if ($cfg.queue_repo -cne "lijust/EREI-Gemini-Control" -or
    $cfg.version -ne 1 -or $cfg.enabled -ne $true -or
    $null -eq $cfg.PSObject.Properties["adapter_v3_root"] -or
    $null -eq $cfg.PSObject.Properties["adapter_v4_root"]) {
    throw "EXPECTED_PRIVATE_V4_LOCAL_CONFIGURATION_NOT_PRESENT"
}
$configChanged = $false
$taskChanged = $false
$complete = $false
try {
    if ($wasRunning) {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $stopped = $false
        for ($i = 0; $i -lt 30; $i++) {
            if ((Get-ScheduledTask -TaskName $taskName).State -ne "Running") {
                $stopped = $true
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if (-not $stopped) { throw "PREVIOUS_BRIDGE_NOT_CONFIRMED_STOPPED" }
    }

    $cfg.daily_limit = $DailyLimit
    [System.IO.File]::WriteAllText(
        $pending, ($cfg | ConvertTo-Json -Depth 10),
        (New-Object System.Text.UTF8Encoding($false))
    )
    Move-Item -LiteralPath $pending -Destination $configPath -Force
    $configChanged = $true

    # Readonly; fails closed if pinned V2/V3/V4 sources or queue no longer match.
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $start -healthcheck
    if ($LASTEXITCODE -ne 0) { throw "QUOTA_BRIDGE_HEALTHCHECK_FAILED" }
    $arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $start + '"'
    $newAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    Set-ScheduledTask -TaskName $taskName -Action $newAction -ErrorAction Stop | Out-Null
    $taskChanged = $true
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop

    $running = $false
    for ($i = 0; $i -lt 30; $i++) {
        if ((Get-ScheduledTask -TaskName $taskName).State -eq "Running") {
            $running = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $running) { throw "UPGRADED_BRIDGE_NOT_RUNNING" }
    $complete = $true
    Write-Host "PRIVATE_BRIDGE_EXTENDED_QUOTA_UPGRADE_SUCCESS"
    Write-Host ("LOCAL_DAILY_LIMIT_" + $DailyLimit + "_MAX_500")
    Write-Host "PROVIDER_429_CIRCUIT_BREAKER_ENABLED"
    Write-Host "MODEL_CALLS_DURING_UPGRADE_0"
} finally {
    if (Test-Path -LiteralPath $pending) {
        Remove-Item -LiteralPath $pending -Force -ErrorAction SilentlyContinue
    }
    if (-not $complete) {
        if ($taskChanged) {
            Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            Set-ScheduledTask -TaskName $taskName -Action $originalActions -ErrorAction SilentlyContinue | Out-Null
        }
        if ($configChanged) {
            [System.IO.File]::WriteAllText(
                $configPath, $oldJson,
                (New-Object System.Text.UTF8Encoding($false))
            )
        }
        if ($wasRunning) {
            Start-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        }
        Write-Host "QUOTA_UPGRADE_ROLLBACK_ATTEMPTED"
    }
}
