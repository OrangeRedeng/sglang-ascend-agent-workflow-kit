#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"


function Set-Wsl2ConfigOption {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Key,
        [string]$Value
    )

    $sectionStart = -1
    $sectionEnd = $Lines.Count
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^\s*\[wsl2\]\s*$') {
            $sectionStart = $i
            continue
        }
        if ($sectionStart -ge 0 -and $i -gt $sectionStart -and $Lines[$i] -match '^\s*\[.+\]\s*$') {
            $sectionEnd = $i
            break
        }
    }

    if ($sectionStart -lt 0) {
        if ($Lines.Count -gt 0 -and $Lines[$Lines.Count - 1] -ne '') { $Lines.Add('') }
        $Lines.Add('[wsl2]')
        $sectionStart = $Lines.Count - 1
        $sectionEnd = $Lines.Count
    }

    for ($i = $sectionStart + 1; $i -lt $sectionEnd; $i++) {
        if ($Lines[$i] -match ('^\s*' + [regex]::Escape($Key) + '\s*=')) {
            $Lines[$i] = "$Key=$Value"
            return
        }
    }

    $Lines.Insert($sectionEnd, "$Key=$Value")
}

function Ensure-WingetPackage {
    param([string]$Id, [string]$Name)
    Write-Host "\n==> $Name" -ForegroundColor Cyan
    winget install --id $Id --exact --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "winget returned $LASTEXITCODE for $Name. It may already be installed; verify manually." -ForegroundColor Yellow
    }
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget not found. Install/update Microsoft App Installer first."
}

Ensure-WingetPackage -Id "Git.Git" -Name "Git for Windows"
Ensure-WingetPackage -Id "Microsoft.VisualStudioCode" -Name "Visual Studio Code"

# Locate VS Code CLI after install.
$code = Get-Command code -ErrorAction SilentlyContinue
if (-not $code) {
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
    if (Test-Path $candidate) { $code = $candidate }
}

if ($code) {
    Write-Host "\n==> VS Code extensions" -ForegroundColor Cyan
    & $code --install-extension ms-vscode-remote.remote-wsl --force
    & $code --install-extension OpenAI.chatgpt --force
} else {
    Write-Host "VS Code installed, but 'code' CLI was not found in this PowerShell session." -ForegroundColor Yellow
    Write-Host "Open VS Code once, then install extensions: ms-vscode-remote.remote-wsl and OpenAI.chatgpt." -ForegroundColor Yellow
}

Write-Host "\n==> WSL2 networking" -ForegroundColor Cyan
$wslConfigPath = Join-Path $env:USERPROFILE ".wslconfig"
$configLines = [System.Collections.Generic.List[string]]::new()
if (Test-Path $wslConfigPath) {
    foreach ($line in Get-Content $wslConfigPath) { $configLines.Add($line) }
}
Set-Wsl2ConfigOption -Lines $configLines -Key "networkingMode" -Value "mirrored"
Set-Wsl2ConfigOption -Lines $configLines -Key "dnsTunneling" -Value "true"
Set-Wsl2ConfigOption -Lines $configLines -Key "autoProxy" -Value "true"
Set-Content -Path $wslConfigPath -Value $configLines -Encoding ascii
Write-Host "Configured $wslConfigPath with mirrored networking, DNS tunneling, and Windows proxy inheritance." -ForegroundColor Green
Write-Host "These settings take effect after 'wsl --shutdown' or a Windows reboot." -ForegroundColor Yellow

Write-Host "\n==> WSL2 / Ubuntu" -ForegroundColor Cyan
$hasUbuntu = $false
try {
    $distros = (wsl -l -q 2>$null) -join "`n"
    if ($distros -match "Ubuntu") { $hasUbuntu = $true }
} catch {}

if (-not $hasUbuntu) {
    Write-Host "Ubuntu WSL not detected. Starting installation..." -ForegroundColor Yellow
    wsl --install -d Ubuntu
    Write-Host "\nIf Windows requests a reboot, reboot now." -ForegroundColor Yellow
    Write-Host "After reboot, run: wsl -l -v" -ForegroundColor Cyan
    Write-Host "If no distribution is installed, run: wsl --install -d Ubuntu" -ForegroundColor Cyan
    Write-Host "Then run: wsl --shutdown; wsl -d Ubuntu" -ForegroundColor Cyan
    Write-Host "Create your Linux user and continue with wsl/02-bootstrap-wsl.sh." -ForegroundColor Cyan
    exit 0
}

wsl --set-default-version 2
Write-Host "Ubuntu already exists. Current WSL distributions:" -ForegroundColor Green
wsl -l -v

Write-Host "\nHost bootstrap complete." -ForegroundColor Green
Write-Host "Next, in Ubuntu WSL run the kit's wsl/02-bootstrap-wsl.sh." -ForegroundColor Cyan
