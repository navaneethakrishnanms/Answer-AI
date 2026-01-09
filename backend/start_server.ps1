# AI Exam Evaluator Backend Startup Script
# This script sets up the environment and starts the FastAPI server

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   AI Exam Evaluator - Backend Server Startup    " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Activate conda environment
Write-Host "[1/5] Activating torch_gpu environment..." -ForegroundColor Yellow
& C:\ProgramData\anaconda3\shell\condabin\conda-hook.ps1
conda activate C:\Users\Trc\.conda\envs\torch_gpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate conda environment" -ForegroundColor Red
    exit 1
}
Write-Host "      ✓ Environment activated" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "[2/5] Creating required directories..." -ForegroundColor Yellow
$dirs = @(
    "C:\Projects\Paper_AI\backend\uploads",
    "C:\Projects\Paper_AI\backend\results",
    "C:\Projects\Paper_AI\backend\temp",
    "C:\Projects\Paper_AI\backend\logs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "      ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "      ✓ Exists: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

# Check Python environment
Write-Host "[3/5] Verifying Python environment..." -ForegroundColor Yellow
$pythonPath = "C:\Users\Trc\.conda\envs\torch_gpu\python.exe"
$pythonVersion = & $pythonPath --version 2>&1
Write-Host "      ✓ Python: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check required packages
Write-Host "[4/5] Checking required packages..." -ForegroundColor Yellow
$packages = @("fastapi", "uvicorn", "sqlalchemy", "PyMuPDF", "torch", "requests")
foreach ($pkg in $packages) {
    $installed = & $pythonPath -c "import $pkg; print($pkg.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✓ $pkg : $installed" -ForegroundColor Green
    } else {
        Write-Host "      ✗ $pkg : NOT INSTALLED" -ForegroundColor Red
        Write-Host ""
        Write-Host "Installing $pkg..." -ForegroundColor Yellow
        & $pythonPath -m pip install $pkg -q
    }
}
Write-Host ""

# Check Ollama service
Write-Host "[5/5] Checking Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "      ✓ Ollama is running" -ForegroundColor Green
    Write-Host "      ✓ Available models:" -ForegroundColor Green
    foreach ($model in $response.models) {
        if ($model.name -like "*qwen*" -or $model.name -like "*deepseek*") {
            Write-Host "        - $($model.name)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "      ✗ Ollama is NOT running!" -ForegroundColor Red
    Write-Host "      Please start Ollama before running the server" -ForegroundColor Yellow
}
Write-Host ""

# Set environment and start server
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Starting FastAPI Server...                     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Change to backend directory and start server
Set-Location "C:\Projects\Paper_AI\backend"
$env:PYTHONPATH = "C:\Projects\Paper_AI\backend"

# Start uvicorn with the correct Python interpreter
& $pythonPath -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
