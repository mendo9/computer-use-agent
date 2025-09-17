# run_computer_server_simple.ps1
# Simple PowerShell script to run the CUA computer-server using the built-in CLI
# Usage: .\run_computer_server_simple.ps1 [-Host "0.0.0.0"] [-Port 8000] [-LogLevel "info"]

param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000,
    [string]$LogLevel = "info"
)

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "CUA Computer Server - Simple Runner" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $Host" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host "  Log Level: $LogLevel" -ForegroundColor White

Write-Host "`n==> Starting computer-server on ${Host}:${Port}..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "-" * 50 -ForegroundColor Gray

try {
    # Run computer-server directly using its built-in CLI
    python -m computer_server.main --host $Host --port $Port --log-level $LogLevel
} catch {
    Write-Host "`nERROR: Failed to start computer-server" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Ensure Python is installed and in PATH" -ForegroundColor White
    Write-Host "2. Install cua-computer-server: pip install cua-computer-server" -ForegroundColor White
    Write-Host "3. Check if port $Port is available" -ForegroundColor White
    exit 1
}