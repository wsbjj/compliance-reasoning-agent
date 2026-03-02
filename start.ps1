$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Starting Compliance Reasoning Agent..." -ForegroundColor Cyan

if (-Not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found." -ForegroundColor Yellow
}

Write-Host "Starting FastAPI Backend (Opening new window)..." -ForegroundColor Green
Start-Process -FilePath "uv" -ArgumentList "run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Starting Streamlit Frontend (Opening new window)..." -ForegroundColor Green
Start-Process -FilePath "uv" -ArgumentList "run streamlit run frontend/app.py --server.port 8501" -WindowStyle Normal

Write-Host "=========================================="
Write-Host "Backend API: http://localhost:8000/docs"
Write-Host "Frontend UI: http://localhost:8501"
Write-Host "=========================================="
Write-Host "To stop the services, please close the two new console windows." -ForegroundColor Yellow
