# Replace ONLY local GitHub PAT using Windows current-user DPAPI.
# Never outputs it or puts it in GitHub, process arguments or a repository.
$ErrorActionPreference = "Stop"
$state = Join-Path $env:LOCALAPPDATA "EREI\GeminiBridge"
$tokenPath = Join-Path $state "github-token.dpapi"
$configPath = Join-Path $state "config.json"
$starter = Join-Path $PSScriptRoot "start-gemini-bridge.ps1"
$tempPath = Join-Path $state ("github-token.dpapi.pending." + $PID)
$oldCipher = $null
$updated = $false
$checked = $false

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "bridge configuration missing; run owner-local installer first"
}
if (-not (Test-Path -LiteralPath $starter -PathType Leaf)) {
    throw "bridge healthcheck launcher missing"
}
if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
    $oldCipher = [System.IO.File]::ReadAllText($tokenPath)
}
$secret = Read-Host "Replacement fine-grained GitHub PAT (private queue Issues R/W)" -AsSecureString
try {
    $cipher = ConvertFrom-SecureString -SecureString $secret
    if ([string]::IsNullOrWhiteSpace($cipher)) {
        throw "empty encrypted token not accepted"
    }
    [System.IO.File]::WriteAllText(
        $tempPath, $cipher, (New-Object System.Text.UTF8Encoding($false))
    )
    Move-Item -LiteralPath $tempPath -Destination $tokenPath -Force
    $updated = $true
    $cipher = $null
} finally {
    $secret.Dispose()
    if (Test-Path -LiteralPath $tempPath) {
        Remove-Item -LiteralPath $tempPath -Force
    }
}

try {
    # Read-only verification: no Gemini call or issue claim.
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $starter -healthcheck
    if ($LASTEXITCODE -ne 0) {
        throw "new token failed local healthcheck"
    }
    $checked = $true
    Write-Host "PRIVATE_GITHUB_TOKEN_ROTATED_AND_HEALTHCHECK_PASSED"
    # The persistent broker read its PAT only when first launched. The new
    # healthcheck is a separate process; it cannot update a running broker.
    # Explicitly require a worker restart before revoking the prior PAT.
    Write-Host "EXISTING_WORKER_RESTART_REQUIRED_BEFORE_OLD_PAT_REVOCATION"
    Write-Host "NO_GEMINI_CALLS_NO_SCHEDULED_TASK_CHANGES"
} finally {
    if ($updated -and -not $checked) {
        if ($null -eq $oldCipher) {
            Remove-Item -LiteralPath $tokenPath -Force -ErrorAction SilentlyContinue
        } else {
            [System.IO.File]::WriteAllText(
                $tokenPath, $oldCipher,
                (New-Object System.Text.UTF8Encoding($false))
            )
        }
        Write-Host "PRIVATE_GITHUB_TOKEN_ROTATION_ROLLED_BACK"
        Write-Host "NO_GEMINI_CALLS_NO_SCHEDULED_TASK_CHANGES"
    }
}
