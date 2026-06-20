# ATELIX ViralClip AI Pipeline — Development Server (Windows PowerShell)
# Run: .\scripts\dev.ps1

$backendJob = Start-Job -Name "backend" -ScriptBlock {
    Set-Location -LiteralPath "D:\laragon\www\ai-cliper\backend"
    & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

$workerJob = Start-Job -Name "worker" -ScriptBlock {
    Set-Location -LiteralPath "D:\laragon\www\ai-cliper\backend"
    & ".\.venv\Scripts\python.exe" -m celery -A app.core.celery_app worker --loglevel=info
}

$frontendJob = Start-Job -Name "frontend" -ScriptBlock {
    Set-Location -LiteralPath "D:\laragon\www\ai-cliper\frontend"
    npm run dev
}

Write-Host "Services started:" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan

Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-Job -Name "backend" -ErrorAction SilentlyContinue
    Stop-Job -Name "worker" -ErrorAction SilentlyContinue
    Stop-Job -Name "frontend" -ErrorAction SilentlyContinue
    Remove-Job -Name "backend","worker","frontend" -ErrorAction SilentlyContinue
    Write-Host "All services stopped." -ForegroundColor Red
}
