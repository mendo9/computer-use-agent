# on_startup.ps1
# PowerShell script to install and run CUA computer-server on Windows VM
# Usage: .\on_startup.ps1

$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "CUA Computer Server - Windows VM Setup" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

# Get the directory where the script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Current directory: $PWD" -ForegroundColor Yellow

# Check if Python is available
try {
    $PythonVersion = python --version 2>&1
    Write-Host "Found Python: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Update pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip --quiet
    Write-Host "Pip upgraded successfully" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Failed to upgrade pip, continuing anyway..." -ForegroundColor Yellow
}

# Install/upgrade cua-computer-server
Write-Host "`nInstalling/upgrading cua-computer-server..." -ForegroundColor Yellow
try {
    pip install --upgrade --no-input cua-computer-server
    Write-Host "cua-computer-server installed/upgraded successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install cua-computer-server" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    exit 1
}

# Start the computer server
Write-Host "`nStarting computer server..." -ForegroundColor Yellow
& ".\run_computer_server.ps1"