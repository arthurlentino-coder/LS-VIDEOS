#!/bin/bash
export PYTHONUTF8=1
PY="/c/Users/betat/AppData/Local/Programs/Python/Python312/python.exe"
PROJ="C:/Users/betat/Desktop/VIDEOS/projects"; OUT="C:/Users/betat/Desktop/VIDEOS/output/PERPETUOS"
for k in PERP_CPA_1 PERP_CPA_2 PERP_CPRO_I_1 PERP_CPRO_I_2 PERP_CPRO_R_1 PERP_CPRO_R_2 PERP_CFP_1 PERP_CFP_2; do
  P="$PROJ/$k/edit"
  echo "=== COMPOSE $k ==="; date +%T
  "$PY" "$P/hf/compose_hfsubs.py" --base "$P/base_tight.mp4" --overlay "$P/hf/subs-animated.webm" --out "$OUT/$k.mp4" 2>&1 | tail -2
done
rm -f "$OUT/PERP_CFP_2_tight.mp4"
echo "STAGE C DONE"; date +%T
