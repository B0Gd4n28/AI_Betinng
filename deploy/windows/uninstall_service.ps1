# PariuSmart AI Bot - Service Uninstaller
# Rulează ca Administrator în PowerShell

param(
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "PariuSmartBot"
)

Write-Host "🗑️ Uninstalling PariuSmart AI Bot Windows Service..." -ForegroundColor Yellow

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "❌ This script must be run as Administrator!"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

try {
    # Check if service exists
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Host "🛑 Stopping service..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        
        # Wait for service to stop
        $timeout = 30
        $counter = 0
        while ((Get-Service -Name $ServiceName).Status -eq 'Running' -and $counter -lt $timeout) {
            Start-Sleep -Seconds 1
            $counter++
            Write-Host "." -NoNewline
        }
        Write-Host ""
        
        # Remove service using sc.exe
        Write-Host "🗑️ Removing service..." -ForegroundColor Yellow
        & sc.exe delete $ServiceName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Service '$ServiceName' has been successfully removed!" -ForegroundColor Green
        } else {
            Write-Error "❌ Failed to remove service. Exit code: $LASTEXITCODE"
        }
        
    } else {
        Write-Host "ℹ️ Service '$ServiceName' not found or already removed." -ForegroundColor Cyan
    }
    
} catch {
    Write-Error "❌ Error occurred while uninstalling service: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "🔧 If you want to reinstall the service later, run:" -ForegroundColor Cyan
Write-Host "   .\deploy\windows\install_service.ps1" -ForegroundColor Gray

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")