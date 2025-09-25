param(
  [string]$RepoPath = "C:\Users\Bogdan\Downloads\free-soccer-telegram-bot",
  [string]$TaskName = "PariuSmartAIBot"
)
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoPath "deploy\run_windows.ps1"

# Rulează PowerShell cu policy bypass
$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
# Trigger la logon + la boot
$trLogon = New-ScheduledTaskTrigger -AtLogOn
$trBoot  = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable

try {
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trLogon,$trBoot -Settings $settings -RunLevel Highest -Force | Out-Null
  Write-Host "Task '$TaskName' installed."
  Write-Host "Start it now with: Start-ScheduledTask -TaskName `"$TaskName`""
} catch {
  Write-Host "Failed to install task: $($_.Exception.Message)"
  exit 1
}