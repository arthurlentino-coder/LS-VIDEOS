# hf.ps1 — wrapper PATH-safe para o HyperFrames CLI.
# O Node existe em "C:\Program Files\nodejs" mas nem sempre está no PATH da sessão.
# Este wrapper prepende o Node ao PATH e repassa TODOS os argumentos pro `npx hyperframes`.
#
# Uso (de dentro da pasta da composição, ex.: projects/<nome>/edit/hf/intro/):
#   & 'C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1' lint
#   & 'C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1' render -o out.mp4
#   & 'C:\Users\betat\Desktop\claude\video use\helpers\hf.ps1' render --format webm -o overlay.webm
#
# Regra do processo (2026-07-21): liberado sempre que a edição precisar de motion/overlay (README §8).

# NÃO usar 'Stop': o hyperframes escreve status (◆ ◇) no stderr, e em modo estrito
# o PowerShell trataria isso como erro fatal. O que importa é o exit code, repassado abaixo.
$ErrorActionPreference = 'Continue'

$nodeDir = 'C:\Program Files\nodejs'
if (-not (Test-Path (Join-Path $nodeDir 'node.exe'))) {
    Write-Error "Node não encontrado em $nodeDir. Ajuste o caminho em hf.ps1."
    exit 1
}
if ($env:Path -notlike "*$nodeDir*") {
    $env:Path = "$nodeDir;" + $env:Path
}

# Repassa os argumentos crus pro hyperframes via npx.
& "$nodeDir\npx.cmd" --yes hyperframes @args
exit $LASTEXITCODE
