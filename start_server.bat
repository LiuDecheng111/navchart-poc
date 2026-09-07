@echo off
chcp 65001 >nul
echo ============================================
echo   NavChart POC - 矢量航图渲染验证
echo ============================================
echo.
echo 正在启动本地 HTTP 服务器...
echo 服务器地址: http://localhost:8765
echo 页面地址:   http://localhost:8765/web/index.html
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================
echo.

cd /d "%~dp0"
python -m http.server 8765 --bind 127.0.0.1

pause
