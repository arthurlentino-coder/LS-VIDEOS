# queue_notify.ps1 — Mesa de Corte
# Roda pela Tarefa Agendada "MesaDeCorte-QueueNotify" a cada ~5 min.
# Varre orders/*.json; se houver item em_edicao SEM saida (pedido/aprovacao novos
# ainda nao produzidos) e ainda nao avisado, dispara uma notificacao do Windows.
# Notifica UMA vez por item (dedupe via orders/_notify_state.txt) pra nao encher.

$ErrorActionPreference = 'SilentlyContinue'
$ordersDir = Join-Path $PSScriptRoot 'orders'
$state = Join-Path $ordersDir '_notify_state.txt'

$pending = $null
Get-ChildItem $ordersDir -Filter *.json -File | ForEach-Object {
  if ($pending) { return }
  try { $o = Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return }
  if (-not $o.fila) { return }
  foreach ($it in $o.fila) {
    if ($it.status -eq 'em_edicao' -and [string]::IsNullOrWhiteSpace([string]$it.saida)) {
      $pending = "$($o.lote)|$($it.id)"
      break
    }
  }
}

$last = ''
if (Test-Path $state) { $last = (Get-Content $state -Raw -Encoding UTF8).Trim() }

if ($pending) {
  if ($pending -ne $last) {
    $parts = $pending -split '\|', 2
    try {
      Add-Type -AssemblyName System.Windows.Forms
      Add-Type -AssemblyName System.Drawing
      $ni = New-Object System.Windows.Forms.NotifyIcon
      $ni.Icon = [System.Drawing.SystemIcons]::Information
      $ni.Visible = $true
      $ni.BalloonTipTitle = 'Mesa de Corte'
      $ni.BalloonTipText = "$($parts[0]) - '$($parts[1])' aguardando edicao. Abra o Claude para produzir."
      $ni.ShowBalloonTip(15000)
      Start-Sleep -Seconds 16
      $ni.Dispose()
    } catch {}
    Set-Content -Path $state -Value $pending -Encoding UTF8
  }
} else {
  if ($last) { Remove-Item $state -Force -ErrorAction SilentlyContinue }
}
