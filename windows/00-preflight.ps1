$ErrorActionPreference = "Stop"

Write-Host "=== Codex/SGLang Windows 11 preflight ===" -ForegroundColor Cyan

function Show-Command($Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host ("[OK] {0}: {1}" -f $Name, $cmd.Source) -ForegroundColor Green
    } else {
        Write-Host ("[MISSING] {0}" -f $Name) -ForegroundColor Yellow
    }
}

Show-Command winget
Show-Command wsl
Show-Command git
Show-Command code

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    Write-Host "`n=== VS Code extensions ===" -ForegroundColor Cyan
    $extensions = & $codeCmd.Source --list-extensions 2>$null
    foreach ($ext in @("ms-vscode-remote.remote-wsl", "OpenAI.chatgpt")) {
        if ($extensions -match "(?i)^$([regex]::Escape($ext))$") {
            Write-Host ("[OK] {0}" -f $ext) -ForegroundColor Green
        } else {
            Write-Host ("[MISSING] {0}" -f $ext) -ForegroundColor Yellow
        }
    }
}

Write-Host "`n=== WSL status ===" -ForegroundColor Cyan
$wslFeatureEnabled = $false
$vmPlatformEnabled = $false
try {
    $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    $vmFeature = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
    $wslFeatureEnabled = ($wslFeature.State -eq "Enabled")
    $vmPlatformEnabled = ($vmFeature.State -eq "Enabled")
    Write-Host ("WSL feature: {0}" -f $wslFeature.State)
    Write-Host ("VirtualMachinePlatform: {0}" -f $vmFeature.State)
} catch {
    Write-Host "Could not query Windows optional features (run as Administrator for full preflight)." -ForegroundColor Yellow
}

if ($wslFeatureEnabled -and $vmPlatformEnabled) {
    try {
        wsl --status
        wsl -l -v
    } catch {
        Write-Host "WSL features are enabled but WSL is not fully configured yet." -ForegroundColor Yellow
    }
} else {
    Write-Host "WSL is not fully enabled yet; bootstrap will install or enable it." -ForegroundColor Yellow
}

Write-Host "`n=== Virtualization hint ===" -ForegroundColor Cyan
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Write-Host ("VirtualizationFirmwareEnabled: {0}" -f $cpu.VirtualizationFirmwareEnabled)
} catch {
    Write-Host "Could not query virtualization state (non-fatal)." -ForegroundColor Yellow
}

Write-Host "`nNext: run .\windows\01-bootstrap-windows.ps1 as Administrator." -ForegroundColor Cyan
