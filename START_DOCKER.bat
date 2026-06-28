@echo off
echo ============================================
echo   E-Career Platform - Docker Startup
echo ============================================
echo.

REM Check if Docker Desktop is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop first:
    echo 1. Open Docker Desktop from Start Menu
    echo 2. Wait for it to start (whale icon in taskbar)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] Docker Desktop is running
echo.

echo Starting E-Career services...
cd /d "%~dp0"
docker-compose down 2>nul
docker-compose up -d

echo.
echo Waiting for services to be healthy (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo ============================================
echo   Services Status
echo ============================================
docker-compose ps

echo.
echo ============================================
echo   Quick Start Commands
echo ============================================
echo.
echo 1. Create superuser:
echo    docker-compose exec backend python manage.py createsuperuser
echo.
echo 2. Import companies (100 test):
echo    docker-compose exec backend python manage.py import_companies --limit 100
echo.
echo 3. Scrape jobs (10 test):
echo    docker-compose exec backend python manage.py scrape_jobs --source stripe --limit 10
echo.
echo 4. Access admin panel:
echo    http://localhost:8000/admin
echo.
echo 5. View logs:
echo    docker-compose logs -f
echo.
echo ============================================

pause
