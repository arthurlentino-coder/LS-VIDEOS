$hf = 'C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1'
$proj = 'C:\Users\betat\Desktop\VIDEOS\projects'
$keys = 'PERP_CPA_1','PERP_CPA_2','PERP_CPRO_I_1','PERP_CPRO_I_2','PERP_CPRO_R_1','PERP_CPRO_R_2','PERP_CFP_1'
foreach ($k in $keys) {
  Set-Location (Join-Path $proj "$k\edit\hf\subs-animated")
  Write-Host "=== RENDER $k ===" (Get-Date -Format HH:mm:ss)
  & $hf render --format webm -o ..\subs-animated.webm 2>&1 | Select-String -Pattern 'Render complete|error|Error' | ForEach-Object { $_.Line }
}
Write-Host "STAGE B DONE" (Get-Date -Format HH:mm:ss)
