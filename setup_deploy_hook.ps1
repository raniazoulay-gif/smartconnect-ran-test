# setup_deploy_hook.ps1
# מריצים פעם אחת — מגדיר git hook שמדליק תחזוקה לפני כל push

$hookDir  = Join-Path $PSScriptRoot ".git\hooks"
$hookPath = Join-Path $hookDir "pre-push"

if (-not (Test-Path $hookDir)) {
    Write-Host "ERROR: לא נמצא תיקיית .git — הרץ את הסקריפט מתוך תיקיית הפרויקט" -ForegroundColor Red
    exit 1
}

$hookScript = @'
#!/bin/sh
echo ""
echo "  Enabling maintenance mode before deploy..."
curl -s -X POST "https://unico-production.up.railway.app/api/admin/maintenance/on?token=UNICO_ADMIN_2026" > /dev/null 2>&1
echo "  Maintenance ON. Pushing to Railway..."
echo ""
exit 0
'@

# כתוב עם שורות Unix (LF) — חובה לגיט
[System.IO.File]::WriteAllText($hookPath, $hookScript.Replace("`r`n", "`n"))

Write-Host ""
Write-Host "  Git pre-push hook הוגדר בהצלחה!" -ForegroundColor Green
Write-Host ""
Write-Host "  מעכשיו כל 'git push' ידליק תחזוקה אוטומטית לפני ה-deploy." -ForegroundColor Cyan
Write-Host "  Railway יסיים את ה-deploy — תחזוקה תכבה לבד." -ForegroundColor Cyan
Write-Host ""
