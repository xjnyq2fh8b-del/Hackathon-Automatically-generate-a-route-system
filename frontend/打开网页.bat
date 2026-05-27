@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "NODE_EXE=C:\Users\11147\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
set "PATH=C:\Users\11147\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;%PATH%"

echo 正在启动西湖即时路线 Agent...
echo 如果浏览器没有自动打开，请访问：http://127.0.0.1:3000

start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:3000'"

if exist "%NODE_EXE%" (
  "%NODE_EXE%" node_modules\next\dist\bin\next dev -H 127.0.0.1 -p 3000
) else (
  node node_modules\next\dist\bin\next dev -H 127.0.0.1 -p 3000
)

pause
