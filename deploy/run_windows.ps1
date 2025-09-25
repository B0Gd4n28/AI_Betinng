param([string]$RepoPath = "C:\Users\Bogdan\Downloads\free-soccer-telegram-bot")
$ErrorActionPreference = "Stop"
Set-Location $RepoPath

# alege 'py' sau 'python'
$python = (Get-Command py -ErrorAction SilentlyContinue) ? "py" : "python"

if (-not (Test-Path ".venv")) { & $python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
& pip install -r requirements.txt

New-Item -ItemType Directory -Path logs -ErrorAction SilentlyContinue | Out-Null

while ($true) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts] Starting PariuSmart AI bot..."
  try {
    & $python -m bot.bot 2>&1 | Tee-Object -FilePath "logs\bot.log" -Append
  } catch {
    Write-Host "[$ts] Bot crashed: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 5
}