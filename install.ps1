param(
  [Alias("Host")]
  [ValidateSet("codex", "gemini")]
  [string]$HostName = $env:WSR_HOST,
  [ValidateSet("user", "workspace")]
  [string]$Scope = $env:WSR_SCOPE,
  [ValidateSet("native", "agents")]
  [string]$Layout = $env:WSR_LAYOUT,
  [string]$Dest = $env:WSR_DEST,
  [string]$WorkspaceRoot = $env:WSR_WORKSPACE_ROOT
)

if (-not $HostName) {
  $HostName = "codex"
}
if (-not $Scope) {
  $Scope = "user"
}
if (-not $Layout) {
  $Layout = "native"
}

$scriptPath = $MyInvocation.MyCommand.Path
$repoRoot = if ($scriptPath) { Split-Path -Parent $scriptPath } else { $null }
$localAudit = if ($repoRoot) { Join-Path $repoRoot "scripts\audit.ps1" } else { $null }

if ($localAudit -and (Test-Path $localAudit)) {
  $argsList = @("install", "--host", $HostName, "--scope", $Scope)
  if ($HostName -eq "gemini") {
    $argsList += @("--layout", $Layout)
  }
  if ($Dest) {
    $argsList += @("--dest", $Dest)
  }
  if ($WorkspaceRoot) {
    $argsList += @("--workspace-root", $WorkspaceRoot)
  }
  & $localAudit @argsList
  exit $LASTEXITCODE
}

$skillUrl = "https://github.com/adams216/web-security-review-skill/releases/latest/download/web-security-review.skill"
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("web-security-review-" + [System.Guid]::NewGuid().ToString("N"))
$artifact = Join-Path $tempRoot "web-security-review.skill"
$extractRoot = Join-Path $tempRoot "extract"

New-Item -ItemType Directory -Force -Path $tempRoot, $extractRoot | Out-Null

try {
  Invoke-WebRequest -UseBasicParsing -Uri $skillUrl -OutFile $artifact

  if ($Dest) {
    $destItem = New-Item -ItemType Directory -Force -Path $Dest
    $skillsDir = [System.IO.Path]::GetFullPath($destItem.FullName)
  } elseif ($HostName -eq "codex" -and $Scope -eq "user") {
    $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    $skillsDir = Join-Path $codexHome "skills"
  } elseif ($HostName -eq "codex") {
    $root = if ($WorkspaceRoot) { $WorkspaceRoot } else { (Get-Location).Path }
    $skillsDir = Join-Path (Join-Path $root ".agents") "skills"
  } else {
    $container = if ($Layout -eq "agents") { ".agents" } else { ".gemini" }
    if ($Scope -eq "workspace") {
      $root = if ($WorkspaceRoot) { $WorkspaceRoot } else { (Get-Location).Path }
      $skillsDir = Join-Path (Join-Path $root $container) "skills"
    } else {
      $skillsDir = Join-Path (Join-Path $HOME $container) "skills"
    }
  }

  New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
  Expand-Archive -LiteralPath $artifact -DestinationPath $extractRoot -Force

  $source = Join-Path $extractRoot "web-security-review"
  $target = Join-Path $skillsDir "web-security-review"
  if (Test-Path $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
  }
  Move-Item -LiteralPath $source -Destination $target

  Write-Output "Installed web-security-review to: $target"
  if ($HostName -eq "codex") {
    if ($Scope -eq "workspace") {
      Write-Output "Restart the Codex session or refresh skills if it is already open."
    } else {
      Write-Output "Restart the Codex app/session if the skill is not listed."
    }
    Write-Output "Try: Use `$web-security-review for a quick security review of this repo."
  } else {
    Write-Output "Try in Gemini CLI: /skills reload"
    Write-Output "Then ask: Use the web-security-review skill to review this repo."
  }
} finally {
  if (Test-Path $tempRoot) {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force
  }
}
