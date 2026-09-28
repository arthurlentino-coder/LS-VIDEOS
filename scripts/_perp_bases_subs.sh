#!/bin/bash
export PYTHONUTF8=1
PY="/c/Users/betat/AppData/Local/Programs/Python/Python312/python.exe"
H="C:/Users/betat/Desktop/claude/video use/helpers"
PROJ="C:/Users/betat/Desktop/VIDEOS/projects"
for k in PERP_CPA_2 PERP_CPRO_I_1 PERP_CPRO_I_2 PERP_CPRO_R_1 PERP_CPRO_R_2 PERP_CFP_1 PERP_CFP_2; do
  P="$PROJ/$k/edit"
  echo "=== BASE $k ==="; date +%T
  ( cd "$P" && "$PY" "$P/zoom_concat.py" --mode seam --hold 0.12 --zoom-t 0.14 --start-dir in --out "$P/base_padrao.mp4" 2>&1 | tail -2 )
  DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$P/base_padrao.mp4")
  echo "  base dur=$DUR -> gen subs"
  "$PY" "$H/hf_subs.py" --edl "$P/edl.json" --out-dir "$P/hf/subs-animated" --duration "$DUR" --preset vertical --box-alpha 0.3 --crossfade 0 2>&1 | tail -1
done
echo "ALL BASES+SUBS-GEN DONE"; date +%T
