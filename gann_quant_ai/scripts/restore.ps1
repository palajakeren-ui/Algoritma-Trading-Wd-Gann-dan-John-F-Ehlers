# =====================================================
# Gann Quant AI - Restore Script (Windows PowerShell)
# Restore from backup
# =====================================================
# Usage: .\restore.ps1 -BackupFile "path\to\backup.zip"
# =====================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$TempDir = Join-Path $env:TEMP "gann_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "         GANN QUANT AI - RESTORE SCRIPT              " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Validate backup file
if (!(Test-Path $BackupFile)) {
    Write-Host "ERROR: Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "Backup: $BackupFile" -ForegroundColor Yellow

# Confirm restore
if (!$Force) {
    $Confirm = Read-Host "This will overwrite existing data. Continue? (y/N)"
    if ($Confirm -ne "y" -and $Confirm -ne "Y") {
        Write-Host "Restore cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Extract backup
Write-Host "[1/3] Extracting backup..." -ForegroundColor Yellow
Expand-Archive -Path $BackupFile -DestinationPath $TempDir -Force
$BackupContent = Get-ChildItem $TempDir | Select-Object -First 1

# Restore directories
Write-Host "[2/3] Restoring data..." -ForegroundColor Yellow
$Dirs = @("configs", "outputs", "data", "vault", "logs")
foreach ($Dir in $Dirs) {
    $SourceDir = Join-Path $BackupContent.FullName $Dir
    $DestDir = Join-Path $ProjectDir $Dir
    if (Test-Path $SourceDir) {
        if (Test-Path $DestDir) { Remove-Item $DestDir -Recurse -Force }
        Copy-Item -Path $SourceDir -Destination $DestDir -Recurse -Force
        Write-Host "  OK: $Dir" -ForegroundColor Green
    }
}

# Cleanup
Write-Host "[3/3] Cleaning up..." -ForegroundColor Yellow
Remove-Item $TempDir -Recurse -Force

# Show backup info
$InfoFile = Join-Path $BackupContent.FullName "backup_info.json"
if (Test-Path $InfoFile) {
    $Info = Get-Content $InfoFile | ConvertFrom-Json
    Write-Host ""
    Write-Host "Restored from backup:" -ForegroundColor Cyan
    Write-Host "  Timestamp: $($Info.timestamp)"
    Write-Host "  Hostname:  $($Info.hostname)"
}

Write-Host ""
Write-Host "Restore completed successfully!" -ForegroundColor Green
