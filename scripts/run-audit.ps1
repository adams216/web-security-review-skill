param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @()

if ($env:PYTHON_BIN) {
  $candidates += $env:PYTHON_BIN
}

$candidates += @("python", "py")

$pythonCmd = $null
foreach ($candidate in $candidates) {
  $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
  if ($resolved) {
    $pythonCmd = $resolved.Source
    break
  }
}

if (-not $pythonCmd) {
  Write-Error "python or py must be available on PATH"
  exit 1
}

& $pythonCmd (Join-Path $scriptDir "run_audit.py") @RemainingArgs
exit $LASTEXITCODE
