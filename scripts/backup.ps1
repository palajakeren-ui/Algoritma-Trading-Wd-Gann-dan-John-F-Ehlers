# =====================================================
# Gann Quant AI - Backup Script (Windows PowerShell)
# Automated backup for trading data, configs, and vault
# =====================================================
# Usage: .\backup.ps1 [-KeepBackups 10] [-SkipCompress]
# =====================================================

param(
    [string]$BackupDir = "",
    [switch]$SkipCompress = $false,
    [int]$KeepBackups = 10
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupName = "gann_quant_backup_$Timestamp"

if ($BackupDir -eq "") {
    $BackupDir = Join-Path $ProjectDir "backups"
}
$BackupPath = Join-Path $BackupDir $BackupName

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "         GANN QUANT AI - BACKUP SCRIPT               " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
Write-Host "[1/6] Creating backup directory..." -ForegroundColor Yellow
if (!(Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null }
New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

# Backup each directory
$Dirs = @("configs", "outputs", "data", "vault", "logs")
$Step = 2
foreach ($Dir in $Dirs) {
    Write-Host "[$Step/6] Backing up $Dir..." -ForegroundColor Yellow
    $SourceDir = Join-Path $ProjectDir $Dir
    if (Test-Path $SourceDir) {
        Copy-Item -Path $SourceDir -Destination $BackupPath -Recurse -Force
        Write-Host "  OK: $Dir" -ForegroundColor Green
    } else {
        Write-Host "  SKIP: $Dir not found" -ForegroundColor Gray
    }
    $Step++
}

# Create metadata
$BackupInfo = @{
    backup_name = $BackupName; timestamp = (Get-Date -Format "o")
    project = "Gann Quant AI"; version = "2.2.0"
    hostname = $env:COMPUTERNAME; user = $env:USERNAME
}
$BackupInfo | ConvertTo-Json | Set-Content (Join-Path $BackupPath "backup_info.json")

# Compress
if (!$SkipCompress) {
    Write-Host "Compressing..." -ForegroundColor Yellow
    Compress-Archive -Path $BackupPath -DestinationPath "$BackupDir\$BackupName.zip" -Force
    Remove-Item $BackupPath -Recurse -Force
    $Size = "{0:N2} MB" -f ((Get-Item "$BackupDir\$BackupName.zip").Length / 1MB)
    Write-Host "DONE: $BackupName.zip ($Size)" -ForegroundColor Green
}

# Cleanup old backups
Get-ChildItem $BackupDir -Filter "*.zip" | Sort-Object CreationTime -Descending | 
Select-Object -Skip $KeepBackups | Remove-Item -Force

Write-Host "Backup completed!" -ForegroundColor Cyan
