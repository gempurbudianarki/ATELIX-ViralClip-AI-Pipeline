# ATELIX ViralClip AI Pipeline — Development Setup (Windows PowerShell)
# Run: .\scripts\setup.ps1

Write-Host "ATELIX ViralClip AI Pipeline - Setup" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta

if (-not (Test-Path -Path ".env")) {
    Copy-Item -Path ".env.example" -Destination ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
}
else {
    Write-Host "[SKIP] .env already exists" -ForegroundColor Yellow
}

Set-Location -LiteralPath "backend"
Write-Host "[...] Installing Python dependencies..." -ForegroundColor Cyan
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
Set-Location ..

Set-Location -LiteralPath "frontend"
Write-Host "[...] Installing frontend dependencies..." -ForegroundColor Cyan
npm install
Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green
Set-Location ..

New-Item -ItemType File -Force -Path "data\temp\.gitkeep", "data\output\.gitkeep", "data\models\.gitkeep" | Out-Null
Write-Host "[OK] Created .gitkeep files" -ForegroundColor Green

Write-Host ""
Write-Host "Setup complete! Start the services:" -ForegroundColor Green
Write-Host "  Backend: cd backend; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "  Worker:  cd backend; .venv\Scripts\Activate.ps1; celery -A app.core.celery_app worker -l info"
Write-Host "  Frontend: cd frontend; npm run dev"
Write-Host "  Or use Docker: docker compose up -d"
