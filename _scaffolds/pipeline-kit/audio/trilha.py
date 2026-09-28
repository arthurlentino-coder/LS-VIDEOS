#!/usr/bin/env python3
"""Trilha (audio bed) reusável — receita README §7.7. Moods: calmo / serio / energico.

Dois modos:
  build-bed  --out bed_master.wav --dur 130
      Sintetiza pad (Am7·Fmaj7·Cadd9·G6, voicings 7a/9a) + topline plucks celeste.
  apply      --video final.mp4 --bed bed_master.wav --out final_trilha.mp4 --whoosh T1,T2
      Mixa bed (vol 0.60) com ducking sidechain sob a fala + 2 whooshes nas junções,
      afade out, alimiter, e loudnorm two-pass -14. Não toca no vídeo, só no áudio.
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

WHOOSH = Path(os.environ.get("HF_SFX_DIR") or Path.home() / ".claude" / "skills" / "hyperframes-media" / "assets" / "sfx") / "whoosh-short.mp3"
_here = Path(__file__).resolve()
_videos = next((q for q in _here.parents if (q / "input").is_dir()), _here.parents[3])
HELPERS = Path(os.environ.get("VIDEO_USE_HELPERS") or _videos.parent / "claude" / "video use" / "helpers")
SR = 48000

XF = 0.9

# ---- MOODS de trilha (bed) — cada um com ASSINATURA distinta (não é só EQ/tempo) ----
MOODS = {
  # calmo/corporativo — pad quente 7a/9a + celeste fluido (reverb). Sem ritmo.
  "calmo": dict(
    chords=[[110.00,261.63,329.63,392.00,440.00],   # Am7
            [ 87.31,220.00,261.63,329.63,349.23],   # Fmaj7
            [130.81,329.63,392.00,523.25,587.33],   # Cadd9
            [ 98.00,246.94,293.66,392.00,440.00]],  # G6
    gains=[0.14,0.12,0.11,0.11,0.09], chord_dur=4.6, motif=14.0,
    plucks=[(0.2,659.25),(3.6,523.25),(7.1,587.33),(10.6,493.88)],
    pluck_decay=2.4, pluck_vol=0.28, top_vol=0.40, top_echo="aecho=0.8:0.9:150:0.35",
    lowpass=2400, chorus="chorus=0.5:0.9:50:0.4:0.25:2"),
  # sério/institucional — menor, LENTO, DRONE grave sustentado + sinos profundos esparsos (decay longo). Muito espaço.
  "serio": dict(
    chords=[[ 55.00,220.00,261.63,329.63,392.00],   # Am (grave)
            [ 73.42,220.00,293.66,349.23,440.00],   # Dm7
            [ 82.41,246.94,293.66,392.00,493.88],   # Em7
            [ 65.41,196.00,261.63,311.13,392.00]],  # Cm-ish
    gains=[0.17,0.10,0.09,0.08,0.06], chord_dur=6.4, motif=19.2,
    plucks=[(0.6,329.63),(7.5,246.94),(14.0,392.00)],  # sinos: poucos, graves, longos
    pluck_decay=0.9, pluck_vol=0.22, top_vol=0.34, top_echo="aecho=0.9:0.95:280:0.45",
    lowpass=1650, chorus="chorus=0.4:0.7:70:0.3:0.15:1.2",
    drone=[55.00, 82.41], drone_vol=0.12),
  # enérgico/direto — pad claro + KICK pulsante (~92 BPM) + arp brilhante staccato. Movimento.
  "energico": dict(
    chords=[[130.81,329.63,392.00,523.25,659.25],   # C
            [ 98.00,293.66,392.00,493.88,587.33],   # G
            [110.00,329.63,440.00,523.25,659.25],   # Am
            [ 87.31,349.23,440.00,523.25,698.46]],  # F
    gains=[0.12,0.10,0.10,0.09,0.08], chord_dur=3.2, motif=13.04,  # 13.04 = 20 beats @92bpm
    plucks=[(0.0,659.25),(0.652,987.77),(1.304,783.99),(1.957,659.25),
            (2.609,987.77),(3.261,880.00),(3.913,659.25),(4.565,783.99),
            (5.217,987.77),(5.870,659.25),(6.522,880.00),(7.174,987.77)],  # arp em colcheias
    pluck_decay=6.0, pluck_vol=0.16, top_vol=0.30, top_echo="aecho=0.7:0.7:90:0.2",
    lowpass=3600, chorus="chorus=0.6:1.0:40:0.45:0.3:2.5",
    pulse=dict(bpm=92, vol=0.42)),
}

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def chord_expr(freqs, gains):
    return "+".join(f"{g}*sin(2*PI*{f}*t)" for f, g in zip(freqs, gains))

def build_bed(out: Path, dur: float, mood: str = "calmo"):
    M = MOODS.get(mood, MOODS["calmo"])
    CHORDS, GAINS, CHORD_DUR = M["chords"], M["gains"], M["chord_dur"]
    PLUCKS, MOTIF = M["plucks"], M["motif"]
    tmp = Path(tempfile.mkdtemp())
    # 1) cada acorde -> wav
    chord_wavs = []
    for i, fr in enumerate(CHORDS):
        w = tmp/f"chord{i}.wav"
        run(["ffmpeg","-y","-f","lavfi","-i",
             f"aevalsrc={chord_expr(fr, GAINS)}:d={CHORD_DUR}:s={SR}",
             "-af","afade=t=in:st=0:d=0.6,afade=t=out:st=%.2f:d=0.6"%(CHORD_DUR-0.6),
             str(w)])
        chord_wavs.append(w)
    # 2) acrossfade sequencial -> progressão
    prog = tmp/"prog.wav"
    cur = chord_wavs[0]
    for i in range(1, len(chord_wavs)):
        nxt = tmp/f"prog{i}.wav"
        run(["ffmpeg","-y","-i",str(cur),"-i",str(chord_wavs[i]),
             "-filter_complex",f"[0][1]acrossfade=d={XF}:c1=tri:c2=tri",str(nxt)])
        cur = nxt
    run(["ffmpeg","-y","-i",str(cur),"-c","copy",str(prog)])
    # 3) plucks/sinos/arp -> motivo (decay+vol por mood)
    dec, pv = M.get("pluck_decay",2.2), M.get("pluck_vol",0.30)
    pluck_wavs=[]
    for j,(t,f) in enumerate(PLUCKS):
        w=tmp/f"pk{j}.wav"
        run(["ffmpeg","-y","-f","lavfi","-i",
             f"aevalsrc={pv}*sin(2*PI*{f}*t)*exp(-{dec}*t):d=1.8:s={SR}",str(w)])
        pluck_wavs.append((w,t))
    inputs=[]; filt=[]
    for j,(w,t) in enumerate(pluck_wavs):
        inputs += ["-i",str(w)]
        filt.append(f"[{j}]adelay={int(t*1000)}|{int(t*1000)}[p{j}]")
    mixp="".join(f"[p{j}]" for j in range(len(pluck_wavs)))
    filt.append(f"{mixp}amix=inputs={len(pluck_wavs)}:normalize=0,apad=whole_dur={MOTIF},atrim=0:{MOTIF}[m]")
    motif=tmp/"motif.wav"
    run(["ffmpeg","-y",*inputs,"-filter_complex",";".join(filt),"-map","[m]",str(motif)])
    # 3b) camada extra por mood: pulse (kick) ou drone
    extra=None
    if M.get("pulse"):
        B=60.0/M["pulse"]["bpm"]; kv=M["pulse"]["vol"]
        # kick com pitch-drop: repete a cada B s ao longo do motif
        kick=f"{kv}*sin(2*PI*(45+75*exp(-38*mod(t\\,{B:.4f})))*t)*exp(-9*mod(t\\,{B:.4f}))"
        extra=tmp/"pulse.wav"
        run(["ffmpeg","-y","-f","lavfi","-i",f"aevalsrc={kick}:d={MOTIF}:s={SR}","-af","lowpass=f=180",str(extra)])
    elif M.get("drone"):
        dv=M["drone_vol"]; dr="+".join(f"{dv}*sin(2*PI*{f}*t)" for f in M["drone"])
        extra=tmp/"drone.wav"
        run(["ffmpeg","-y","-f","lavfi","-i",f"aevalsrc={dr}:d={MOTIF}:s={SR}",
             "-af",f"afade=t=in:st=0:d=1.5,afade=t=out:st={MOTIF-1.5:.1f}:d=1.5,lowpass=f=140",str(extra)])
    # 4) loop pad + motif (+ extra) -> mix final
    ins=["-stream_loop","-1","-i",str(prog),"-stream_loop","-1","-i",str(motif)]
    fc=[f"[0]atrim=0:{dur},highpass=f=60,lowpass=f={M['lowpass']},{M['chorus']}[pad]",
        f"[1]atrim=0:{dur},{M.get('top_echo','aecho=0.8:0.9:120:0.3')},volume={M['top_vol']}[top]"]
    mix="[pad][top]"
    if extra:
        ins+=["-stream_loop","-1","-i",str(extra)]
        fc.append(f"[2]atrim=0:{dur},volume=1.0[ex]"); mix+="[ex]"
    fc.append(f"{mix}amix=inputs={3 if extra else 2}:normalize=0[bed]")
    run(["ffmpeg","-y",*ins,"-filter_complex",";".join(fc),"-map","[bed]","-t",f"{dur}",str(out)])
    print(f"bed ({mood}) ->", out)

def apply(video: Path, bed: Path, out: Path, whoosh_ts):
    # duração do vídeo
    dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(video)]).decode().strip())
    prenorm = out.parent/(out.stem+"_prenorm.mp4")
    inputs=["-i",str(video),"-i",str(bed)]
    wfilt=[]; wlabels=[]
    for k,t in enumerate(whoosh_ts):
        inputs+=["-i",str(WHOOSH)]
        idx=2+k
        wfilt.append(f"[{idx}:a]adelay={int(t*1000)}|{int(t*1000)},volume=0.26[w{k}]")
        wlabels.append(f"[w{k}]")
    fc=[
        f"[1:a]atrim=0:{dur},volume=0.60[bg]",
        "[0:a]asplit=2[v1][v2]",
        # fade SÓ no bed (não na voz) — senão o afade no mix final corta o fim da fala
        f"[bg][v2]sidechaincompress=threshold=0.06:ratio=3:attack=25:release=420,"
        f"afade=t=out:st={max(0,dur-2.6):.2f}:d=2.6[bgd]",
        *wfilt,
        f"[v1][bgd]{''.join(wlabels)}amix=inputs={2+len(whoosh_ts)}:normalize=0:duration=first,"
        f"alimiter=limit=0.95[aout]",
    ]
    run(["ffmpeg","-y",*inputs,"-filter_complex",";".join(fc),
         "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-ar",str(SR),
         "-movflags","+faststart",str(prenorm)])
    sys.path.insert(0,str(HELPERS)); import render
    render.apply_loudnorm_two_pass(prenorm, out, preview=False)
    prenorm.unlink(missing_ok=True)
    print("trilha ->", out)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("build-bed"); b.add_argument("--out",required=True); b.add_argument("--dur",type=float,default=130)
    b.add_argument("--mood",default="calmo",choices=list(MOODS.keys()))
    ba=sub.add_parser("build-all"); ba.add_argument("--dir",required=True); ba.add_argument("--dur",type=float,default=130)
    a=sub.add_parser("apply"); a.add_argument("--video",required=True); a.add_argument("--bed",required=True)
    a.add_argument("--out",required=True); a.add_argument("--whoosh",default="")
    args=ap.parse_args()
    if args.cmd=="build-bed":
        build_bed(Path(args.out),args.dur,args.mood)
    elif args.cmd=="build-all":
        d=Path(args.dir); d.mkdir(parents=True,exist_ok=True)
        for m in MOODS: build_bed(d/f"bed_{m}.wav",args.dur,m)
    else:
        ts=[float(x) for x in args.whoosh.split(",") if x.strip()]
        apply(Path(args.video),Path(args.bed),Path(args.out),ts)
