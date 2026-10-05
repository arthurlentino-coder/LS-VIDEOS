# run.ps1 — sobe o console Mesa de Corte lendo a senha-mestra de um arquivo local.
#
# Senha-mestra (admin): coloque em orders/_token.txt (fica FORA do git, pois orders/ é ignorado).
#   Set-Content -Encoding utf8 apps\mesa-de-corte\orders\_token.txt "minha-senha-forte"
# Sem esse arquivo E sem contas (useradd.py) = modo aberto (uso local, sem login).
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File apps\mesa-de-corte\run.ps1            # local (127.0.0.1)
#   powershell -ExecutionPolicy Bypass -File apps\mesa-de-corte\run.ps1 -Expose    # 0.0.0.0 (p/ o túnel)
param([switch]$Expose, [int]$Port = 8756)

$env:PYTHONIOENCODING = "utf-8"                             # evita cp1252 nos prints (Windows)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path     # apps/mesa-de-corte
$root = Resolve-Path (Join-Path $here "..\..")              # VIDEOS
Set-Location $root

$tokenFile = Join-Path $here "orders\_token.txt"
if (Test-Path $tokenFile) {
    $env:MESA_TOKEN = (Get-Content -Raw $tokenFile).Trim()
    Write-Host "senha-mestra: carregada de orders/_token.txt"
} else {
    Write-Host "sem orders/_token.txt — rodando sem senha-mestra (ok p/ uso local)"
}
$env:MESA_PORT = "$Port"
if ($Expose) {
    $env:MESA_HOST = "0.0.0.0"
    if (-not $env:MESA_TOKEN) { Write-Host "AVISO: -Expose sem _token.txt e sem contas = ABERTO na rede. Crie conta (useradd.py) ou _token.txt antes." -ForegroundColor Yellow }
} else {
    $env:MESA_HOST = "127.0.0.1"
}
Write-Host "subindo console em $($env:MESA_HOST):$($env:MESA_PORT) ..."
py apps\mesa-de-corte\server.py
