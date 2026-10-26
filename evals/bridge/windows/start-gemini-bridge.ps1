# Windows owner-user DPAPI wrapper for the local Gemini bridge.
# Run only from a pinned/reviewed checkout. Never prints credential values.
param(
    [switch]$once,
    [switch]$healthcheck
)
$ErrorActionPreference = "Stop"
$state = Join-Path $env:LOCALAPPDATA "EREI\GeminiBridge"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$config = Join-Path $state "config.json"
$githubPath = Join-Path $state "github-token.dpapi"
$geminiPath = Join-Path $state "gemini-key.dpapi"

function read-user-dpapi-secret([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "encrypted credential file missing"
    }
    $ciphertext = [System.IO.File]::ReadAllText($path)
    $secure = ConvertTo-SecureString -String $ciphertext
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        $ptr = [IntPtr]::Zero
        $secure.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $config)) {
    throw "bridge config not installed"
}

try {
    $env:EREI_BRIDGE_GITHUB_TOKEN = read-user-dpapi-secret $githubPath
    $env:GEMINI_API_KEY = read-user-dpapi-secret $geminiPath
    Push-Location $root
    try {
        # Never execute untrusted __pycache__ bytecode alongside live tokens.
        # Isolated interpreter ignores PYTHON* environment and user site;
        # a fresh alternate pycache prefix prevents reading stale .pyc files.
        $freshCache = Join-Path $env:TEMP ("erei-bridge-pycache-" + [Guid]::NewGuid().ToString("N"))
        $boot = 'import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module("evals.bridge.github_gemini_worker",run_name="__main__")'
        $argsList = @("-I", "-B", "-X", ("pycache_prefix=" + $freshCache), "-c", $boot, $root, "--config", $config)
        if ($once) { $argsList += "--once" }
        if ($healthcheck) { $argsList += "--healthcheck" }
        & python @argsList
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 2 }
    } finally {
        Pop-Location
    }
} finally {
    Remove-Item Env:\EREI_BRIDGE_GITHUB_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
}
exit $code
