@echo off
echo Syncing with GitHub...
git add .
git commit -m "Auto-update from Antigravity"
git push origin main
echo Sync complete!
pause
