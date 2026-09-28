# -*- coding: utf-8 -*-
"""Trilha musical original (aftermovie/recap de evento) — uplifting -> nostalgica.
py music_gen.py <out.wav> [dur=30] [bpm=120]
Progressao I-V-vi-IV (C G Am F): anthemica/nostalgica. Pad + piano FM + arp + kick/clap
que entram no build e recuam no fecho.
"""
import sys, numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
SR = 44100
beat = 60.0 / BPM
bar = beat * 4
N = int(DUR * SR)
t = np.arange(N) / SR

def note(name):
    A4 = 440.0
    names = {'C':-9,'C#':-8,'D':-7,'D#':-6,'E':-5,'F':-4,'F#':-3,'G':-2,'G#':-1,'A':0,'A#':1,'B':2}
    n = name[:-1]; octv = int(name[-1])
    semi = names[n] + (octv - 4) * 12
    return A4 * 2 ** (semi / 12)

def adsr(n, a, d, s, r, sr=SR):
    ai=int(a*sr); di=int(d*sr); ri=int(r*sr)
    if ai+di+ri > n:  # nota curta: encolhe proporcional
        sc = n/max(1,(ai+di+ri)); ai=int(ai*sc); di=int(di*sc); ri=int(ri*sc)
    si = max(0, n - ai - di - ri)
    parts=[]
    if ai: parts.append(np.linspace(0,1,ai))
    if di: parts.append(np.linspace(1,s,di))
    if si: parts.append(np.full(si,s))
    if ri: parts.append(np.linspace(s,0,ri))
    env = np.concatenate(parts) if parts else np.zeros(n)
    if len(env)<n: env=np.concatenate([env,np.full(n-len(env),env[-1] if len(env) else 0.0)])
    return env[:n]

# progressao (1 acorde por compasso)
PROG = [
    ('C', ['C3','E3','G3','C4'], ['C4','E4','G4']),
    ('G', ['G2','B2','D3','G3'], ['B3','D4','G4']),
    ('A', ['A2','C3','E3','A3'], ['C4','E4','A4']),   # Am
    ('F', ['F2','A2','C3','F3'], ['A3','C4','F4']),
]

L = np.zeros(N); R = np.zeros(N)

def add(sig, start, pan=0.0):
    i0 = int(start*SR)
    if i0 >= N or i0 < 0: return
    i1 = min(N, i0+len(sig))
    if i1 <= i0: return
    s = sig[:i1-i0]
    L[i0:i1] += s*(0.5-0.5*pan); R[i0:i1] += s*(0.5+0.5*pan)

def piano(freq, dur, amp):
    n = int(dur*SR); tt = np.arange(n)/SR
    # FM leve + harmonicos p/ timbre de piano/keys
    mod = np.sin(2*np.pi*freq*tt) * np.exp(-3*tt) * 2.5
    y = (np.sin(2*np.pi*freq*tt + mod)
         + 0.5*np.sin(2*np.pi*2*freq*tt)*np.exp(-4*tt)
         + 0.25*np.sin(2*np.pi*3*freq*tt)*np.exp(-6*tt))
    y *= adsr(n, 0.004, 0.15, 0.5, dur*0.5)
    return y*amp

def padvoice(freq, dur, amp):
    n=int(dur*SR); tt=np.arange(n)/SR
    det=0.6
    y=(np.sin(2*np.pi*freq*tt)+np.sin(2*np.pi*(freq+det)*tt)+np.sin(2*np.pi*(freq-det)*tt))/3
    y+=0.3*np.sin(2*np.pi*2*freq*tt)
    y*=adsr(n,0.6,0.2,0.8,0.8)
    return y*amp

def kick(dur=0.28):
    n=int(dur*SR); tt=np.arange(n)/SR
    f=110*np.exp(-tt*22)+45
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*7)
    return y*0.9

def clap():
    n=int(0.18*SR); nz=np.random.randn(n)*np.exp(-np.arange(n)/SR*45)
    return nz*0.35

def hat(dur=0.05):
    n=int(dur*SR); return np.random.randn(n)*np.exp(-np.arange(n)/SR*120)*0.18

nbars = int(np.ceil(DUR/bar))
build_start = 2*bar          # kick entra
peak_start = 4*bar
out_start = DUR - bar*2      # fecho recua

for b in range(nbars):
    t0 = b*bar
    if t0 >= DUR: break
    chord_name, voices, arp = PROG[b % 4]
    # PAD (todo o tempo, mais forte no meio)
    padamp = 0.10 + (0.06 if t0>=build_start else 0)
    for v in voices[:3]:
        add(padvoice(note(v), bar, padamp), t0, pan=np.random.uniform(-0.3,0.3))
    # PIANO acordes (batida 1 e 3)
    for bt in (0,2):
        for v in voices:
            add(piano(note(v), beat*1.8, 0.09), t0+bt*beat, pan=0.0)
    # ARP (build em diante) — colcheias
    if t0 >= build_start:
        for k in range(8):
            nn = arp[k % len(arp)]
            add(piano(note(nn), beat*0.5, 0.06), t0+k*beat*0.5, pan=((k%2)*2-1)*0.35)
    # BATERIA (build em diante, recua no fecho)
    if build_start <= t0 < out_start:
        for bt in range(4):
            add(kick(), t0+bt*beat, 0.0)
            add(hat(), t0+bt*beat+beat*0.5, 0.4)
        add(clap(), t0+beat, 0.0); add(clap(), t0+3*beat, 0.0)
    elif t0 >= out_start:
        # fecho: so kick na 1 + pad
        add(kick(), t0, 0.0)

# swell/impact no inicio do peak
imp = np.random.randn(int(0.7*SR)); imp*=np.linspace(0,1,len(imp))**2;
add(imp*0.15, peak_start-0.7, 0.0)

y = np.stack([L,R])
# lowpass 1-pole suave (vetorizado) + softclip
a=0.28
try:
    from scipy.signal import lfilter
    for ch in range(2):
        y[ch]=lfilter([a],[1,-(1-a)], y[ch])
except Exception:
    for ch in range(2):
        x=y[ch]; yf=np.empty(N); prev=0.0
        for i in range(N):
            prev=prev+a*(x[i]-prev); yf[i]=prev
        y[ch]=yf
y=np.tanh(y*1.3)
# normaliza
y/= (np.max(np.abs(y))+1e-9); y*=0.89
# fade
fi=int(0.05*SR); fo=int(1.2*SR)
y[:, :fi]*=np.linspace(0,1,fi); y[:, -fo:]*=np.linspace(1,0,fo)

import wave, struct
w=wave.open(OUT,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
inter=(y.T.reshape(-1)*32767).astype(np.int16)
w.writeframes(inter.tobytes()); w.close()
print(f"ok {OUT} {DUR}s {BPM}bpm")
