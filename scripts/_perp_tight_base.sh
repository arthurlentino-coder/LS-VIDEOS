#!/bin/bash
export PYTHONUTF8=1 VIDEO_USE_FPS=30
PY="/c/Users/betat/AppData/Local/Programs/Python/Python312/python.exe"
H="C:/Users/betat/Desktop/claude/video use/helpers"; PROJ="C:/Users/betat/Desktop/VIDEOS/projects"; V="C:/Users/betat/Desktop/VIDEOS"
for k in PERP_CPA_1 PERP_CPA_2 PERP_CPRO_I_1 PERP_CPRO_I_2 PERP_CPRO_R_1 PERP_CPRO_R_2 PERP_CFP_1; do
  P="$PROJ/$k/edit"
  echo "=== TIGHT-BASE $k ==="; date +%T
  "$PY" "$V/tighten_edl.py" "$k" 0.60 0.22 0.09
  "$PY" "$H/render.py" "$P/edl.json" -o "$P/base_tight.mp4" --no-loudnorm --no-subtitles 2>&1 | tail -1
  DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$P/base_tight.mp4")
  echo "  dur=$DUR -> subs"
  "$PY" "$H/hf_subs.py" --edl "$P/edl.json" --out-dir "$P/hf/subs-animated" --duration "$DUR" --preset vertical --box-alpha 0.3 --crossfade 0.09 2>&1 | tail -1
done
echo "STAGE A DONE"; date +%T
