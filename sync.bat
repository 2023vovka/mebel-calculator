@echo off
chcp 65001 >nul
echo 🚀 Начинаем синхронизацию с GitHub...
git add .
git commit -m "Автоматическое обновление проекта (Antigravity)"
git push origin main
echo ✅ Синхронизация завершена успешно!
pause
