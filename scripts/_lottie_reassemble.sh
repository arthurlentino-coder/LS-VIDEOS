#!/bin/bash
export PYTHONUTF8=1
PY="/c/Users/betat/AppData/Local/Programs/Python/Python312/python.exe"
PROJ="C:/Users/betat/Desktop/VIDEOS/projects"; O="C:/Users/betat/Desktop/VIDEOS/output/PERPETUOS"
for k in PERP_CPA_2 PERP_CPRO_I_1 PERP_CPRO_I_2 PERP_CPRO_R_2; do
  P="$PROJ/$k/edit/hf/split"
  echo "=== REASSEMBLE $k ==="
  ffmpeg -y -hide_banner -nostats -i "$P/motion.mp4" -c:v libvpx-vp9 -i "$P/subs-divider.webm" -i "$O/$k.mp4" \
   -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" -map "[v]" -map 2:a \
   -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
   "$P/split_noSFX.mp4" 2>&1 | tail -1
  "$PY" "$P/sfx_mix.py" --video "$P/split_noSFX.mp4" --cues "$P/sfx.json" --out "$O/${k}_split.mp4" 2>&1 | tail -1
  rm -f "$O/${k}_split_prenorm.mp4"
done
echo "ALL REASSEMBLED"
