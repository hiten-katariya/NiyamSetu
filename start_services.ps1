# PowerShell script to start both NiyamSetu FastAPI Backend and Background Worker
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Starting NiyamSetu Backend & Worker Services" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

python run_services.py
