$hf='C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1'
$proj='C:\Users\betat\Desktop\VIDEOS\projects'
foreach ($k in 'PERP_CPRO_I_1','PERP_CPRO_I_2','PERP_CPRO_R_1','PERP_CPRO_R_2') {
  Set-Location (Join-Path $proj "$k\edit\hf\subs-animated")
  Write-Host "=== RENDER $k ===" (Get-Date -Format HH:mm:ss)
  & $hf render --format webm -o ..\subs-animated.webm 2>&1 | Select-String -Pattern 'Render complete|Error' | ForEach-Object { $_.Line }
}
Write-Host "ALL CPRO CAPTION RENDERS DONE" (Get-Date -Format HH:mm:ss)
