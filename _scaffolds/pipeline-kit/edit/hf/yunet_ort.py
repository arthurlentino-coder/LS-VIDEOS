"""yunet_ort.py — YuNet (2023) via onnxruntime, contornando o cv2.FaceDetectorYN
que quebrou no OpenCV 5.0.0 (new graph engine nao roda o modelo).

Modelo de entrada FIXA 640x640, saidas multi-escala (strides 8/16/32).
Decoder padrao YuNet: score=sqrt(cls*obj), cx=(col+dx)*s, cy=(row+dy)*s,
w=exp(dw)*s, h=exp(dh)*s. Reescala as caixas pra resolucao original.

API: YuNetORT(model, conf, nms).detect(bgr_frame) -> [[x,y,w,h,score], ...]
"""
import numpy as np
import cv2
import onnxruntime as ort


class YuNetORT:
    def __init__(self, model, conf=0.6, nms=0.3):
        self.sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
        self.inp = self.sess.get_inputs()[0].name
        self.onames = [o.name for o in self.sess.get_outputs()]
        self.isize = 640
        self.strides = [8, 16, 32]
        self.conf = conf
        self.nms = nms

    def detect(self, img):
        h0, w0 = img.shape[:2]
        blob = cv2.resize(img, (self.isize, self.isize)).astype(np.float32)
        blob = blob.transpose(2, 0, 1)[None]  # 1,3,640,640 BGR cru (0-255)
        outs = self.sess.run(None, {self.inp: blob})
        d = dict(zip(self.onames, outs))
        dets = []
        for s in self.strides:
            cls = d[f"cls_{s}"][0][:, 0]
            obj = d[f"obj_{s}"][0][:, 0]
            bbox = d[f"bbox_{s}"][0]
            fw = self.isize // s
            fh = self.isize // s
            idx = np.arange(fh * fw)
            r = idx // fw
            c = idx % fw
            score = np.sqrt(np.clip(cls, 0, 1) * np.clip(obj, 0, 1))
            cx = (c + bbox[:, 0]) * s
            cy = (r + bbox[:, 1]) * s
            w = np.exp(bbox[:, 2]) * s
            hh = np.exp(bbox[:, 3]) * s
            x1 = cx - w / 2.0
            y1 = cy - hh / 2.0
            keep = score >= self.conf
            for i in np.where(keep)[0]:
                dets.append([x1[i], y1[i], w[i], hh[i], float(score[i])])
        if not dets:
            return []
        dets = np.array(dets, dtype=np.float32)
        sx = w0 / self.isize
        sy = h0 / self.isize
        dets[:, 0] *= sx; dets[:, 2] *= sx
        dets[:, 1] *= sy; dets[:, 3] *= sy
        boxes = dets[:, :4].tolist()
        scores = dets[:, 4].tolist()
        keep = cv2.dnn.NMSBoxes(boxes, scores, self.conf, self.nms)
        if len(keep) == 0:
            return []
        keep = np.array(keep).flatten()
        return dets[keep].tolist()


if __name__ == "__main__":
    import sys
    det = YuNetORT(sys.argv[2] if len(sys.argv) > 2 else "hf/yunet.onnx", conf=0.6)
    cap = cv2.VideoCapture(sys.argv[1])
    fno = int(sys.argv[3]) if len(sys.argv) > 3 else 600
    cap.set(cv2.CAP_PROP_POS_FRAMES, fno)
    ok, fr = cap.read()
    print("frame", ok, fr.shape if ok else None)
    faces = det.detect(fr)
    print(f"faces: {len(faces)}")
    for f in sorted(faces, key=lambda a: -a[2] * a[3])[:5]:
        print("  box", [round(x, 1) for x in f[:4]], "score", round(f[4], 3))
