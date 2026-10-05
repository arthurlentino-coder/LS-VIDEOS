#!/usr/bin/env bash
# build_item.sh — build canônico de 1 item (da base_zoom até entregue+vestido).
# ÁUDIO POR COPY É PADRÃO: todo build termina no dress_item (bed por mood + SFX por copy).
#
# Pré: projects/<proj>/edit/base_zoom.mp4 pronto + as comps autoradas
#      (subs-animated, split/public, hybrid/public, faceless). A subs-divider é gerada aqui.
#
# Uso:
#   bash build_item.sh <projdir> <outbase> <lote> "<item>" [BDR]
#   ex: bash build_item.sh projects/CFP_7 output/CFP/CFP_7 CFP "CFP 7"
# Flags por env:
#   RECONCILE=0  -> NÃO alinhar duração à base (use p/ itens com CTA esticado)
#   DRESS=0      -> pular o passo de áudio (raro)
#   MOOD=auto|calmo|serio|energico
set +e
PROJ="$1"; OUT="$2"; LOTE="$3"; ITEM="$4"; BDR="$5"
ROOT="C:/Users/betat/Desktop/VIDEOS"; cd "$ROOT"
KIT="$ROOT/_scaffolds/pipeline-kit"
HF="$PROJ/edit/hf"; BASE="$PROJ/edit/base_zoom.mp4"
VP9="-c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 30 -deadline good -cpu-used 4 -an"
[ -z "$BDR" ] && BDR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$BASE")
MOOD="${MOOD:-auto}"
echo "### build_item $ITEM  base=${BDR}s"

# 0) robustez: gerar divisória + alinhar durações
[ -d "$HF/subs-animated" ] && PYTHONIOENCODING=utf-8 py "$KIT/edit/hf/make_divider.py" --edit "$PROJ/edit" 2>&1 | tail -1
if [ "${RECONCILE:-1}" = "1" ]; then PYTHONIOENCODING=utf-8 py "$KIT/edit/hf/reconcile_durations.py" --edit "$PROJ/edit" 2>&1 | tail -1; fi

# 1) áudio base + top + input do hybrid
ffmpeg -y -hide_banner -loglevel error -i "$BASE" -vn -c:a aac -b:a 192k -ar 48000 "$HF/faceless/assets/audio.m4a"
cp "$BASE" "$HF/hybrid/public/input-video.mp4"
( cd "$HF" && PYTHONIOENCODING=utf-8 py facecrop.py ../base_zoom.mp4 yunet.onnx split/public/top.mp4 >/dev/null 2>&1 )

# 2) NORMAL
( cd "$HF" && npx hyperframes render subs-animated -o sa.mov --format mov --fps 30 --workers 1 --sdr >/dev/null 2>&1 && ffmpeg -y -hide_banner -loglevel error -i sa.mov $VP9 sa.webm && ffmpeg -y -hide_banner -loglevel error -i sa.webm -t $BDR -c copy subs-animated.webm && rm -f sa.mov sa.webm )
PYTHONIOENCODING=utf-8 py "$HF/compose_hfsubs.py" --base "$BASE" --overlay "$HF/subs-animated.webm" --out "$OUT.mp4" >/dev/null 2>&1
echo "### normal ok"
# 3) DIVISÓRIA + SPLIT
( cd "$HF" && npx hyperframes render subs-divider -o sd.mov --format mov --fps 30 --workers 1 --sdr >/dev/null 2>&1 && ffmpeg -y -hide_banner -loglevel error -i sd.mov $VP9 sd.webm && ffmpeg -y -hide_banner -loglevel error -i sd.webm -t $BDR -c copy subs-divider.webm && rm -f sd.mov sd.webm )
( cd "$HF" && npx hyperframes render split/public -o split_motion.mp4 --fps 30 --workers 1 --sdr >/dev/null 2>&1 )
PYTHONIOENCODING=utf-8 py apps/mesa-de-corte/finish_split.py --edit "$PROJ/edit" --out "${OUT}_split.mp4" --base "$BASE" 2>&1 | grep -iE "check_cert|OK ->"
# 4) HYBRID
( cd "$HF" && npx hyperframes render hybrid/public -o hybrid_motion.mp4 --fps 30 --workers 1 --sdr >/dev/null 2>&1 )
PYTHONIOENCODING=utf-8 py apps/mesa-de-corte/finish_hybrid.py --edit "$PROJ/edit" --out "${OUT}_hybrid.mp4" --base "$BASE" 2>&1 | grep -iE "check_cert|OK ->"
# 5) FACELESS
( cd "$HF" && npx hyperframes render faceless -o faceless_prenorm.mp4 --fps 30 --workers 1 --sdr >/dev/null 2>&1 )
PYTHONIOENCODING=utf-8 py apps/mesa-de-corte/finish_faceless.py --edit "$PROJ/edit" --out "${OUT}_faceless.mp4" 2>&1 | grep -iE "check_cert|OK ->"
rm -f "$HF/split_motion.mp4" "$HF/hybrid_motion.mp4" "$HF/faceless_prenorm.mp4"

# 6) ÁUDIO PADRÃO — bed por mood + SFX por copy (split = bed-only)
if [ "${DRESS:-1}" = "1" ]; then
  echo "### dress (audio por copy, mood=$MOOD)"
  PYTHONIOENCODING=utf-8 py "$KIT/audio/dress_item.py" --edit "$PROJ/edit" --outbase "$OUT" --mood "$MOOD" 2>&1 | grep -iE "mood|vestido|dress_item OK"
fi

PYTHONIOENCODING=utf-8 py apps/mesa-de-corte/set_status.py "$LOTE" "$ITEM" revisar "$OUT.mp4"
echo "### QA:"; PYTHONIOENCODING=utf-8 py apps/mesa-de-corte/qa_lote.py "$LOTE" 2>&1 | grep -iE "vídeos|ok|aviso"
echo "### $ITEM FIM"
