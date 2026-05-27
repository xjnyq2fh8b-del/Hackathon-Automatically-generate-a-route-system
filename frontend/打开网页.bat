@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "NODE_EXE=C:\Users\11147\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"

echo 正在启动西湖即时路线 Agent...
echo 浏览器会自动打开：http://localhost:4173

start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1; Start-Process 'http://localhost:4173'"

if exist "%NODE_EXE%" (
  "%NODE_EXE%" server.mjs
) else (
  node server.mjs
)

pause
