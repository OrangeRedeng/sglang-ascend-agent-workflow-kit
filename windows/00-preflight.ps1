$ErrorActionPreference = 'Stop'
Write-Host '=== Windows / WSL preflight ==='
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber
Write-Host "`nWSL status:"
wsl --status
Write-Host "`nWSL distributions:"
wsl --list --verbose
Write-Host "`nGit:"
if (Get-Command git -ErrorAction SilentlyContinue) { git --version } else { Write-Warning 'Git is not installed yet.' }
Write-Host "`nVS Code:"
if (Get-Command code -ErrorAction SilentlyContinue) { code --version | Select-Object -First 1 } else { Write-Warning 'VS Code is not installed yet.' }
Write-Host "`nPreflight complete."
