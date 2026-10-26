# One-time owner-run setup. Secrets never leave Windows except as auth headers
# to intended GitHub/Gemini services. Current-user interactive task works
# while desktop is LOCKED (not after logoff or sleep). No admin required.
param(
    [Parameter(Mandatory=$true)][string]$queue_repo,
    [int]$daily_limit = 3,
    [switch]$no_task
)
$ErrorActionPreference = "Stop"
if ($queue_repo -cnotmatch '^lijust/[A-Za-z0-9_.-]+$') {
    throw "queue_repo must be a private lijust GitHub repository"
}
if ($daily_limit -lt 1 -or $daily_limit -gt 10) {
    throw "daily_limit must be 1 to 10"
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$state = Join-Path $env:LOCALAPPDATA "EREI\GeminiBridge"
$stateDb = Join-Path $state "state"
$evidence = Join-Path $env:USERPROFILE "Desktop\erei-core13-evidence\github-bridge"
$adapter = Join-Path $env:USERPROFILE "Desktop\erei-core13-schema-compact-v2"
$target = Join-Path $env:USERPROFILE "Desktop\erei-core13-target"
$configFile = Join-Path $state "config.json"
$githubPath = Join-Path $state "github-token.dpapi"
$geminiPath = Join-Path $state "gemini-key.dpapi"

if (-not (Test-Path -LiteralPath (Join-Path $adapter ".git"))) {
    throw "pinned schema-compact-v2 worktree does not exist"
}
if (-not (Test-Path -LiteralPath (Join-Path $target ".git"))) {
    throw "frozen target worktree does not exist"
}
[System.IO.Directory]::CreateDirectory($state) | Out-Null
[System.IO.Directory]::CreateDirectory($stateDb) | Out-Null
[System.IO.Directory]::CreateDirectory($evidence) | Out-Null

if (-not (Test-Path -LiteralPath $githubPath)) {
    $g = Read-Host "Fine-grained GitHub token (PRIVATE queue repo Issues R/W only)" -AsSecureString
    try {
        [System.IO.File]::WriteAllText($githubPath, (ConvertFrom-SecureString $g))
    } finally {
        $g.Dispose()
    }
}
if (-not (Test-Path -LiteralPath $geminiPath)) {
    $k = Read-Host "Gemini Free-tier API key (local DPAPI; never GitHub)" -AsSecureString
    try {
        [System.IO.File]::WriteAllText($geminiPath, (ConvertFrom-SecureString $k))
    } finally {
        $k.Dispose()
    }
}
$config = [ordered]@{
    version = 1
    queue_repo = $queue_repo
    queue_owner = "lijust"
    adapter_root = $adapter
    target_root = $target
    evidence_root = $evidence
    state_root = $stateDb
    daily_limit = $daily_limit
    poll_seconds = 60
    enabled = $true
}
[System.IO.File]::WriteAllText(
    $configFile, ($config | ConvertTo-Json -Depth 5),
    (New-Object System.Text.UTF8Encoding($false))
)

# Read-only healthcheck verifies PRIVATE queue and pinned source SHA identities.
$start = Join-Path $PSScriptRoot "start-gemini-bridge.ps1"
& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $start -healthcheck
if ($LASTEXITCODE -ne 0) {
    throw "healthcheck failed; no scheduled task installed"
}

if (-not $no_task) {
    $taskName = "EREI - Gemini Private Bridge"
    $who = "$env:USERDOMAIN\$env:USERNAME"
    $arg = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $start + '"'
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $who
    $principal = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([timespan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-Host "PRIVATE_BRIDGE_TASK_INSTALLED_AND_STARTED"
} else {
    Write-Host "PRIVATE_BRIDGE_INSTALLED_MANUAL_MODE"
}
Write-Host "GEMINI_CREDENTIALS_ENCRYPTED_FOR_CURRENT_WINDOWS_USER"
Write-Host "BASELINE_RETESTS_NOT_STARTED"
