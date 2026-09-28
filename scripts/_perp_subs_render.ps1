$hf = 'C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1'
$proj = 'C:\Users\betat\Desktop\VIDEOS\projects'
$keys = 'PERP_CPA_2','PERP_CPRO_I_1','PERP_CPRO_I_2','PERP_CPRO_R_1','PERP_CPRO_R_2','PERP_CFP_1','PERP_CFP_2'
foreach ($k in $keys) {
  $dir = Join-Path $proj "$k\edit\hf\subs-animated"
  Write-Host "=== SUBS RENDER $k ===" (Get-Date -Format HH:mm:ss)
  Set-Location $dir
  & $hf render --format webm -o ..\subs-animated.webm 2>&1 | Select-String -Pattern 'Render complete|\.webm|error' | ForEach-Object { $_.Line }
}
Write-Host "ALL SUBS RENDERED" (Get-Date -Format HH:mm:ss)
