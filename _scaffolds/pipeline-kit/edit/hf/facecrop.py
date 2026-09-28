"""facecrop.py — crop dinamico que SEGUE O ROSTO (YuNet), robusto e SUAVE.
Normaliza posicao e tamanho da face -> enquadramento consistente o video todo.
Saida 1080x960 (metade superior do split), preenchido (sem barras).

Robustez: rejeita deteccoes implausiveis/outliers, interpola frames sem face,
filtro de mediana + media movel larga (anti-jitter), e margem grande (o rosto
nao encosta nas bordas, entao erro de rastreio nao joga ele pra fora).

Uso: facecrop.py <in.mp4> <model.onnx> <out.mp4>
"""
import sys
import os
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yunet_ort import YuNetORT

IN, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
OUT_W, OUT_H = 1080, 960
AR = OUT_W / OUT_H
TARGET_FACE_FRAC = 0.26            # face = 26% da saida (mais margem = mais seguro)
FACE_CY_FRAC = 0.42               # centro da face a 42% do topo do crop
MED = 9                            # filtro de mediana (mata spikes)
SMOOTH_POS = 41                    # media movel da posicao (anti-jitter)
SMOOTH_ZOOM = 71                   # media movel do zoom (extra suave; evita "respirar")
MIN_CROPH, MAX_CROPH = 900, 1920

cap = cv2.VideoCapture(IN)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
FPS = cap.get(cv2.CAP_PROP_FPS) or 30.0
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

det = YuNetORT(MODEL, conf=0.6, nms=0.3)

# pass 1: deteccao crua + validacao
CXv = np.full(N, np.nan); CYv = np.full(N, np.nan); FHv = np.full(N, np.nan)
i = 0
while True:
    ok, fr = cap.read()
    if not ok or i >= N:
        break
    faces = det.detect(fr)
    if faces is not None and len(faces) > 0:
        f = max(faces, key=lambda a: a[2] * a[3])
        x, y, w, h, sc = float(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[-1])
        ccx, ccy = x + w / 2.0, y + h / 2.0
        # plausibilidade: tamanho e posicao razoaveis pra um talking head
        if sc >= 0.6 and 0.04 * H <= h <= 0.62 * H and 0.10 * W <= ccx <= 0.90 * W and 0.04 * H <= ccy <= 0.75 * H:
            CXv[i], CYv[i], FHv[i] = ccx, ccy, h
    i += 1
cap.release()
n = i

def interp_nan(a):
    a = a[:n].copy()
    idx = np.arange(n)
    good = ~np.isnan(a)
    if good.sum() == 0:
        a[:] = [W / 2.0]
        return a
    a[~good] = np.interp(idx[~good], idx[good], a[good])
    return a

def medfilt(a, k):
    k |= 1; pad = k // 2
    ap = np.pad(a, (pad, pad), mode='edge')
    return np.array([np.median(ap[j:j + k]) for j in range(len(a))])

def movavg(a, k):
    k |= 1; pad = k // 2
    ap = np.pad(a, (pad, pad), mode='edge')
    return np.convolve(ap, np.ones(k) / k, mode='valid')

cx = movavg(medfilt(interp_nan(CXv), MED), SMOOTH_POS)
cy = movavg(medfilt(interp_nan(CYv), MED), SMOOTH_POS)
fh = movavg(medfilt(interp_nan(FHv), MED), SMOOTH_ZOOM)

# pass 2: recorte
vw = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (OUT_W, OUT_H))
cap = cv2.VideoCapture(IN)
i = 0
while True:
    ok, fr = cap.read()
    if not ok or i >= n:
        break
    cropH = max(MIN_CROPH, min(MAX_CROPH, fh[i] / TARGET_FACE_FRAC))
    cropW = cropH * AR
    if cropW > W:
        cropW = float(W); cropH = cropW / AR
    top = cy[i] - FACE_CY_FRAC * cropH
    left = cx[i] - cropW / 2.0
    left = max(0.0, min(left, W - cropW))
    top = max(0.0, min(top, H - cropH))
    x0, y0 = int(round(left)), int(round(top))
    x1, y1 = min(x0 + int(round(cropW)), W), min(y0 + int(round(cropH)), H)
    out = cv2.resize(fr[y0:y1, x0:x1], (OUT_W, OUT_H), interpolation=cv2.INTER_CUBIC)
    vw.write(out)
    i += 1
cap.release(); vw.release()
valid = int(np.sum(~np.isnan(CXv[:n])))
print(f"ok: {n} frames ({valid} com face detectada) -> {OUT}")
