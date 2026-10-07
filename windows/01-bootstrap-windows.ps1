$ErrorActionPreference = 'Stop'
function Ensure-WingetPackage([string]$Id) {
    $found = winget list --id $Id --exact --accept-source-agreements 2>$null
    if ($LASTEXITCODE -ne 0) { winget install --id $Id --exact --accept-source-agreements --accept-package-agreements }
}
function Ensure-VSCodeExtension([string]$Id) {
    if (-not (Get-Command code -ErrorAction SilentlyContinue)) { return }
    $installed = code --list-extensions
    if ($installed -notcontains $Id) { code --install-extension $Id --force }
}
Ensure-WingetPackage 'Git.Git'
Ensure-WingetPackage 'Microsoft.VisualStudioCode'
Ensure-VSCodeExtension 'ms-vscode-remote.remote-wsl'
Write-Host 'Model-specific VS Code extensions are installed later by setup.sh after the harness is selected.'
Write-Host 'If WSL is missing, run: wsl --install -d Ubuntu'
$wslConfig = Join-Path $env:USERPROFILE '.wslconfig'
if (-not (Test-Path $wslConfig)) {
@"
[wsl2]
dnsTunneling=true
autoProxy=true
"@ | Set-Content -Path $wslConfig -Encoding ASCII
    Write-Host "Created $wslConfig"
}
Write-Host 'Windows bootstrap complete.'
