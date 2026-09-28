#!/bin/bash
# _fincap2_finish.sh <PROJECT_EDIT_DIR> <OUTPUT_MP4>
# base_zoom_seam.mp4 + degrade + lockup + subs-animated.webm -> transicao loop rapida + click -> loudnorm
set -e
E="$1"; OUT="$2"
IN="/c/Users/betat/Desktop/VIDEOS/input/FinCapital"
GRAD="/c/Users/betat/Desktop/VIDEOS/projects/FINCAP_4/edit/hf/footer_grad.png"
G="format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='min(255,0.95*(0.299*r(X,Y)+0.587*g(X,Y)+0.114*b(X,Y)))'"

# 1) prenorm = base + degrade + lockup + caption
ffmpeg -y -i "$E/base_zoom_seam.mp4" -i "$GRAD" -i "$IN/lockup_white.png" -c:v libvpx-vp9 -i "$E/hf/subs-animated.webm" \
 -filter_complex "[0:v][1:v]overlay=0:0[g];[2:v]scale=380:-1[lk];[g][lk]overlay=(W-w)/2:1778[gl];[gl][3:v]overlay=0:0:format=auto[v]" \
 -map "[v]" -map "0:a" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 25 -c:a aac -b:a 256k "$E/hf/prenorm.mp4"

# durations / offsets (folga 0.28 cada, sweep 1.6x -> burn 0.672s)
PD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$E/hf/prenorm.mp4")
TOT=$(awk "BEGIN{printf \"%.3f\", $PD+0.56}")
ROFF=$(awk "BEGIN{printf \"%.3f\", $TOT-0.672}")
REN=$(awk "BEGIN{printf \"%.3f\", $ROFF-0.03}")
CKMS=$(awk "BEGIN{printf \"%d\", ($TOT-0.05)*1000}")

# 2) transicao loop + click
ffmpeg -y -i "$E/hf/prenorm.mp4" -ss 17.42 -t 0.42 -i "$IN/film-burn-transitions.mp4" -i "$IN/click_proc.wav" \
 -filter_complex "\
[0:v]tpad=start_duration=0.28:start_mode=clone:stop_duration=0.28:stop_mode=clone,setpts=PTS-STARTPTS[base];\
[1:v]scale=1080:1920,setsar=1,$G,setpts=PTS-STARTPTS,setpts=1.6*PTS,split=2[bx][by];\
[by]reverse,setpts=PTS+${ROFF}/TB[b2];\
[base][bx]overlay=0:0:enable='lt(t,0.78)'[s1];\
[s1][b2]overlay=0:0:enable='gte(t,${REN})':eof_action=pass[v];\
[0:a]adelay=280|280,apad[sp];\
[2:a]volume=0.8,aformat=channel_layouts=stereo,adelay=${CKMS}|${CKMS}[ck];\
[sp][ck]amix=inputs=2:duration=first:normalize=0[a]" \
 -map "[v]" -map "[a]" -t "$TOT" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 25 -c:a aac -b:a 256k "$E/hf/transition.mp4"

# 3) loudnorm two-pass
J=$(ffmpeg -i "$E/hf/transition.mp4" -af "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | tr '\n' ' ')
ii=$(echo "$J"|grep -o '"input_i" : "[^"]*"'|grep -o '\-\?[0-9.]*"'|tr -d '"')
it=$(echo "$J"|grep -o '"input_tp" : "[^"]*"'|grep -o '\-\?[0-9.]*"'|tr -d '"')
il=$(echo "$J"|grep -o '"input_lra" : "[^"]*"'|grep -o '\-\?[0-9.]*"'|tr -d '"')
ih=$(echo "$J"|grep -o '"input_thresh" : "[^"]*"'|grep -o '\-\?[0-9.]*"'|tr -d '"')
io=$(echo "$J"|grep -o '"target_offset" : "[^"]*"'|grep -o '\-\?[0-9.]*"'|tr -d '"')
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -i "$E/hf/transition.mp4" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$ii:measured_TP=$it:measured_LRA=$il:measured_thresh=$ih:offset=$io:linear=true" -c:a aac -b:a 256k "$OUT"
echo "DONE: $OUT (total=$TOT)"
