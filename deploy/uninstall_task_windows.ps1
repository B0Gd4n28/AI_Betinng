param([string]$TaskName = "PariuSmartAIBot")
$ErrorActionPreference = "Stop"
try {
  Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Task '$TaskName' removed."
} catch {
  Write-Host "Failed to remove task: $($_.Exception.Message)"
}