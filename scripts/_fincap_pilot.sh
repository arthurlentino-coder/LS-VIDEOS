#!/usr/bin/env bash
# _fincap_pilot.sh <KEY>  — replica a receita do piloto FINCAP_4 (aprovado, pilot_v17)
# sobre o base_zoom_seam.mp4 de qualquer reel FinCapital.
# Recursos: film-burn quente ligando as pontas (loop) + split intro (head em cima /
# b-roll assessor embaixo, 0-6s) + degrade rodapé + lockup fincapital|btg pactual +
# legenda karaokê branca (nossa, box 0.3, atrasada 0.45s) + click no pico do fogo do fim.
# Áudio = SÓ a fala do base (sem trilha) + click, loudnorm two-pass -14 (sem fade).
# Offsets do fim derivam do total: END_SETPTS=TOTAL-1.17, END_ENABLE=TOTAL-1.25,
# CLICK=(TOTAL-0.07)s. Batem exatos com o FINCAP_4 (base 61.8 -> total 62.7).
set -euo pipefail

KEY="${1:?uso: _fincap_pilot.sh <3|4|5|6>}"
VID="C:/Users/betat/Desktop/VIDEOS"
PROJ="$VID/projects/FINCAP_$KEY/edit"
BASE="$PROJ/base_zoom_seam.mp4"
SUBS="$PROJ/hf/subs-animated.webm"
FC="$VID/input/FinCapital"
case "$KEY" in
  3) BROLL="$FC/broll/reel3_investapp.mp4";;   # celular app invest (fala: comprou CDB/taxa)
  4) BROLL="$FC/broll/advisor_tablet.mp4";;    # assessor+tablet (fala: conversa c/ assessor)
  5) BROLL="$FC/broll/reel5_laptop.mp4";;      # notebook dashboard (fala: escolhe fundo/acompanha)
  6) BROLL="$FC/broll/reel6_piechart.mp4";;    # pizza de alocação (fala: cada ativo na carteira)
  *) BROLL="$FC/broll/advisor_tablet.mp4";;
esac
FOOTER="$VID/projects/FINCAP_4/edit/hf/footer_grad.png"   # asset compartilhado
LOCKUP="$FC/lockup_white.png"
BURN="$FC/film-burn-transitions.mp4"
CLICK="$FC/click_proc.wav"
OUTDIR="$VID/output/FINCAPITAL"
PRENORM="$PROJ/hf/pilot_prenorm.mp4"
FINAL="$OUTDIR/FINCAP_${KEY}_pilot.mp4"

for f in "$BASE" "$SUBS" "$BROLL" "$FOOTER" "$LOCKUP" "$BURN" "$CLICK"; do
  [ -f "$f" ] || { echo "FALTA asset: $f" >&2; exit 1; }
done
mkdir -p "$OUTDIR"

BASE_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$BASE")
TOTAL=$(awk "BEGIN{printf \"%.3f\", $BASE_DUR+0.90}")
# burn revertido: pico (luma 202) é a ÚLTIMA frame do clip (dur ~1.914s+1frame).
# alinhar o pico com a última frame do vídeo => END_SETPTS = TOTAL - 1.95.
# (o valor 61.53 da memória era de versão anterior e punha o pico depois do fim.)
END_SETPTS=$(awk "BEGIN{printf \"%.3f\", $TOTAL-1.95}")
END_ENABLE=$(awk "BEGIN{printf \"%.3f\", $TOTAL-0.45}")
CLICK_MS=$(awk "BEGIN{printf \"%d\", ($TOTAL-0.07)*1000}")
echo ">> FINCAP_$KEY  base=$BASE_DUR total=$TOTAL end_setpts=$END_SETPTS end_enable=$END_ENABLE click_ms=$CLICK_MS"

GEQ="format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='min(255,0.95*(0.299*r(X,Y)+0.587*g(X,Y)+0.114*b(X,Y)))'"

# ---------- Pass composite -> prenorm (video + fala+click, sem loudnorm) ----------
ffmpeg -y -hide_banner -loglevel error -stats \
  -i "$BASE" \
  -i "$BROLL" \
  -i "$FOOTER" \
  -i "$LOCKUP" \
  -c:v libvpx-vp9 -i "$SUBS" \
  -ss 17.42 -i "$BURN" \
  -ss 17.42 -i "$BURN" \
  -i "$CLICK" \
  -filter_complex "\
[0:v]tpad=start_duration=0.45:start_mode=clone:stop_duration=0.45:stop_mode=clone,setpts=PTS-STARTPTS,fps=25[bp];\
[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setpts=PTS-STARTPTS[br];\
[bp][br]overlay=0:960:enable='between(t,0,6)'[v1];\
[v1][2:v]overlay=0:0[v2];\
[3:v]scale=380:-1[lk];\
[v2][lk]overlay=(W-w)/2:1778[v3];\
[4:v]setpts=PTS+0.45/TB[su];\
[v3][su]overlay=0:0[v4];\
[5:v]setpts=PTS-STARTPTS,setpts=2.7*PTS,scale=1080:1920,${GEQ}[bs];\
[v4][bs]overlay=0:0:enable='lt(t,1.2)':eof_action=pass[v5];\
[6:v]setpts=PTS-STARTPTS,setpts=2.7*PTS,scale=1080:1920,${GEQ},reverse,setpts=PTS+${END_SETPTS}/TB[be];\
[v5][be]overlay=0:0:enable='gte(t,${END_ENABLE})':eof_action=pass[vout];\
[0:a]adelay=450|450,apad[sp];\
[7:a]adelay=${CLICK_MS}|${CLICK_MS},volume=0.8[ck];\
[sp][ck]amix=inputs=2:normalize=0:duration=first[aout]" \
  -map "[vout]" -map "[aout]" -t "$TOTAL" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 25 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a pcm_s16le -ar 48000 \
  "$PRENORM"
echo ">> prenorm ok: $PRENORM"

# ---------- loudnorm two-pass -14 (sem fade) ----------
PY="C:/Users/betat/AppData/Local/Programs/Python/Python312/python.exe"
MEAS=$(ffmpeg -hide_banner -nostats -i "$PRENORM" \
  -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
  | "$PY" -c "import sys,json,re; s=sys.stdin.read(); m=re.search(r'\{[^{}]*\"input_i\"[^{}]*\}',s,re.S); d=json.loads(m.group(0)); print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
read MI MTP MLRA MTHRESH MOFF <<< "$MEAS"
echo ">> loudnorm measured: I=$MI TP=$MTP LRA=$MLRA thr=$MTHRESH off=$MOFF"

ffmpeg -y -hide_banner -loglevel error -stats -i "$PRENORM" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTHRESH:offset=$MOFF:linear=true:print_format=summary" \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  "$FINAL"
echo ">> FINAL: $FINAL"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL"
