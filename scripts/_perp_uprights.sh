#!/bin/bash
IN="C:/Users/betat/Desktop/VIDEOS/input/PERPETUOS"; PROJ="C:/Users/betat/Desktop/VIDEOS/projects"
for k in PERP_CPA_2 PERP_CPRO_I_1 PERP_CPRO_I_2 PERP_CPRO_R_1 PERP_CPRO_R_2 PERP_CFP_1 PERP_CFP_2; do
  echo "=== UPRIGHT $k ==="; date +%T
  ffmpeg -y -i "$IN/$k.MP4" -vf "transpose=1,fps=30,scale=1080:1920:flags=lanczos" \
    -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
    -c:a pcm_s16le "$PROJ/$k/edit/upright.mp4" 2>&1 | tail -1
done
echo "ALL UPRIGHTS DONE"; date +%T
