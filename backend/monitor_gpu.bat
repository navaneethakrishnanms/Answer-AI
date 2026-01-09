@echo off
echo ================================================================================
echo GPU MONITORING FOR AI EXAM EVALUATOR
echo ================================================================================
echo.

:menu
echo Choose an option:
echo.
echo [1] Check GPU Status
echo [2] Monitor GPU in Real-time
echo [3] Check Ollama Models
echo [4] Run Full GPU Check
echo [5] Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto check_status
if "%choice%"=="2" goto monitor
if "%choice%"=="3" goto check_models
if "%choice%"=="4" goto full_check
if "%choice%"=="5" goto end

:check_status
echo.
echo Checking GPU status...
nvidia-smi
echo.
pause
goto menu

:monitor
echo.
echo Starting real-time GPU monitoring (Press Ctrl+C to stop)...
echo.
nvidia-smi -l 1
goto menu

:check_models
echo.
echo Checking Ollama models...
curl http://localhost:11434/api/tags
echo.
pause
goto menu

:full_check
echo.
echo Running comprehensive GPU check...
python check_gpu.py
echo.
pause
goto menu

:end
echo.
echo Exiting...
exit
