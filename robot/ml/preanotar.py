"""Prepara fotos del invernadero preanotadas por el detector, para corregirlas en Roboflow.

Anotar desde cero es lento; corregir es rápido. Este script propone una caja
"rosa" por cada rosa que ve el detector (con umbral bajo, para no perder rosas)
y suma las rosas que marcó la finca. En Roboflow solo hay que borrar las cajas
malas, ajustar y agregar las que falten. Luego se exporta en YOLOv8 y se usa
para reentrenar el detector con fotos del invernadero de verdad.

Fuentes:
  --finca   export YOLO de ml.finca_labels (fotos de escena + rosas marcadas)
  --video   videos del invernadero; se toma un fotograma cada --cada segundos

Salida (formato YOLO que Roboflow acepta al subir una carpeta):
    <out>/images/*.jpg   <out>/labels/*.txt   <out>/data.yaml   <out>/preview/*.jpg

Ejemplo:
    python -m ml.preanotar --finca data/finca_yolo \
        --video "descargas/General/Videos de apoyo/Video 1 vista a un lado.mp4" \
        --video "descargas/General/Videos de apoyo/Video 2 vista al camino.mp4" \
        --video "descargas/General/Videos de apoyo/Corte con carro.mp4" --out data/preanotadas
"""

import argparse
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

from ml.detect import RoseDetector


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    area = lambda r: (r[2] - r[0]) * (r[3] - r[1])
    return inter / (area(a) + area(b) - inter) if inter else 0.0


def finca_boxes(label: Path, w: int, h: int) -> list:
    boxes = []
    for line in label.read_text().splitlines() if label.exists() else []:
        _, cx, cy, bw, bh = map(float, line.split())
        boxes.append([(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h])
    return boxes


def merge(detected: list, marked: list) -> list:
    """Cajas del detector + las marcadas por la finca que el detector no encontró."""
    out = list(detected)
    for m in marked:
        if not any(iou(m, d) > 0.2 for d in detected):
            out.append(m)
    return out


def video_frames(path: Path, every_s: float):
    import cv2

    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step, i = max(1, round(fps * every_s)), 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            yield i, Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        i += 1
    cap.release()


def save(name: str, image: Image.Image, boxes: list, out: Path, marked: int = 0) -> None:
    image.save(out / "images" / f"{name}.jpg", quality=95)
    w, h = image.size
    lines = [f"0 {(b[0] + b[2]) / 2 / w:.6f} {(b[1] + b[3]) / 2 / h:.6f} {(b[2] - b[0]) / w:.6f} {(b[3] - b[1]) / h:.6f}"
             for b in boxes]
    (out / "labels" / f"{name}.txt").write_text("\n".join(lines))
    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    for j, b in enumerate(boxes):
        draw.rectangle(b, outline="orange" if j >= len(boxes) - marked else "lime", width=max(2, w // 300))
    preview.save(out / "preview" / f"{name}.jpg", quality=80)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--finca", type=Path, help="Export YOLO de ml.finca_labels")
    p.add_argument("--video", type=Path, action="append", default=[])
    p.add_argument("--cada", type=float, default=1.0, help="Segundos entre fotogramas de video")
    p.add_argument("--detector", type=Path, default=Path("modelos/detector_rosas.pt"))
    p.add_argument("--out", type=Path, default=Path("data/preanotadas"))
    args = p.parse_args()

    if args.out.exists():
        shutil.rmtree(args.out)
    for sub in ("images", "labels", "preview"):
        (args.out / sub).mkdir(parents=True)
    det = RoseDetector(args.detector)
    n_img = n_det = n_marked = 0

    if args.finca:
        for img_path in sorted(args.finca.glob("*/images/*")):
            with Image.open(img_path) as im:
                im = im.convert("RGB")
                detected = [d["bbox"] for d in det.detect(im)]
                marked = finca_boxes(img_path.parent.parent / "labels" / f"{img_path.stem}.txt", *im.size)
                boxes = merge(detected, marked)
                extra = len(boxes) - len(detected)
                save(f"finca_{img_path.stem}", im, boxes, args.out, marked=extra)
            n_img, n_det, n_marked = n_img + 1, n_det + len(detected), n_marked + extra

    for video in args.video:
        slug = re.sub(r"[^a-z0-9]+", "_", video.stem.lower()).strip("_")
        for i, frame in video_frames(video, args.cada):
            detected = [d["bbox"] for d in det.detect(frame)]
            save(f"video_{slug}_{i:05d}", frame, detected, args.out)
            n_img, n_det = n_img + 1, n_det + len(detected)

    (args.out / "data.yaml").write_text("names: ['rosa']\nnc: 1\ntrain: images\nval: images\n", encoding="utf-8")
    print(f"{n_img} imágenes | {n_det} cajas del detector | {n_marked} cajas de la finca que el detector no vio")
    print(f"Revisar en {args.out / 'preview'} (verde = detector, naranja = marcada por la finca) y subir a Roboflow")


if __name__ == "__main__":
    main()
