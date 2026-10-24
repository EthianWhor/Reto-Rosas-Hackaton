"""Convierte los datasets descargados en un dataset de clasificación por etapas.

Salida (formato ImageFolder):
    <out>/train/<etapa>/*.jpg
    <out>/val/<etapa>/*.jpg
    <out>/test/<etapa>/*.jpg

Fuentes soportadas:
  --yolo    Export de Roboflow en formato YOLO (carpeta con data.yaml y
            train/valid/test con images/ y labels/). Cada caja se recorta como
            una imagen independiente. Se respeta el split de Roboflow.
  --folder  Dataset de clasificación con una subcarpeta por clase (p. ej.
            Mendeley). Se reparte en train/val/test con semilla fija.

Ejemplo:
    python -m ml.prepare_data --yolo descargas/rose-v1 --yolo descargas/floracion \
        --folder descargas/mendeley --out data/stages
"""

import argparse
import random
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from ml.stages import SCALES, map_class_name

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLIT_DIRS = {"train": "train", "valid": "val", "val": "val", "test": "test"}


def read_class_names(data_yaml: Path) -> list[str]:
    names = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))["names"]
    if isinstance(names, dict):  # {0: "bud", 1: "flower"}
        names = [names[k] for k in sorted(names)]
    return names


def label_to_box(values: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    """Línea YOLO (sin la clase) -> caja en píxeles. Acepta caja o polígono."""
    if len(values) == 4:
        cx, cy, w, h = values
        x0, x1 = cx - w / 2, cx + w / 2
        y0, y1 = cy - h / 2, cy + h / 2
    else:  # polígono de segmentación: x1 y1 x2 y2 ...
        xs, ys = values[0::2], values[1::2]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)


def pad_box(box, width, height, pad: float):
    x0, y0, x1, y1 = box
    dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
    return (
        max(0, int(x0 - dx)),
        max(0, int(y0 - dy)),
        min(width, int(x1 + dx)),
        min(height, int(y1 + dy)),
    )


def is_grayscale(im: Image.Image, tol: int = 4) -> bool:
    """True si la imagen no tiene color (algunos exports de Roboflow traen copias en gris)."""
    small = np.asarray(im.convert("RGB").resize((64, 64)), dtype=np.int16)
    return int((small.max(axis=2) - small.min(axis=2)).max()) <= tol


def crop_yolo_dataset(root: Path, out: Path, pad: float, min_size: int, counts: dict, scale: str = "finca") -> None:
    names = read_class_names(root / "data.yaml")
    prefix = root.name
    for split_dir in root.iterdir():
        split = SPLIT_DIRS.get(split_dir.name)
        if split is None or not (split_dir / "images").is_dir():
            continue
        for img_path in (split_dir / "images").iterdir():
            if img_path.suffix.lower() not in IMAGE_EXTS:
                continue
            label_path = split_dir / "labels" / f"{img_path.stem}.txt"
            if not label_path.exists():
                continue
            lines = [l.split() for l in label_path.read_text().splitlines() if l.strip()]
            if not lines:
                continue
            with Image.open(img_path) as im:
                im = im.convert("RGB")
                # El color es un criterio de la finca: una copia en gris enseñaría lo contrario.
                if is_grayscale(im):
                    counts["grayscale"] += 1
                    continue
                for i, parts in enumerate(lines):
                    stage = map_class_name(names[int(parts[0])], scale)
                    if stage is None:
                        counts["ignored"] += 1
                        continue
                    box = label_to_box([float(v) for v in parts[1:]], *im.size)
                    box = pad_box(box, *im.size, pad)
                    if min(box[2] - box[0], box[3] - box[1]) < min_size:
                        counts["too_small"] += 1
                        continue
                    dest = out / split / stage / f"{prefix}_{img_path.stem}_{i}.jpg"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    im.crop(box).save(dest, quality=95)
                    counts[split] += 1


def split_folder_dataset(root: Path, out: Path, seed: int, val: float, test: float, counts: dict,
                         scale: str = "finca") -> None:
    rng = random.Random(seed)
    prefix = root.name
    for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        stage = map_class_name(class_dir.name, scale)
        if stage is None:
            print(f"  [aviso] carpeta '{class_dir.name}' sin mapeo en stages.py, se ignora")
            continue
        images = sorted(p for p in class_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
        rng.shuffle(images)
        n_test, n_val = int(len(images) * test), int(len(images) * val)
        for idx, img_path in enumerate(images):
            split = "test" if idx < n_test else "val" if idx < n_test + n_val else "train"
            dest = out / split / stage / f"{prefix}_{img_path.stem}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(img_path) as im:
                im.convert("RGB").save(dest, quality=95)
            counts[split] += 1


def print_summary(out: Path) -> None:
    print("\nImágenes por split y etapa:")
    for split in ("train", "val", "test"):
        classes = sorted({d.name for d in out.glob("*/*") if d.is_dir()})
        row = {s: len(list((out / split / s).glob("*.jpg"))) for s in classes}
        print(f"  {split:5s} " + "  ".join(f"{s}={n}" for s, n in row.items()))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--yolo", type=Path, action="append", default=[], help="Export YOLO de Roboflow")
    p.add_argument("--folder", type=Path, action="append", default=[], help="Dataset con carpeta por clase")
    p.add_argument("--out", type=Path, default=Path("data/stages"))
    p.add_argument("--pad", type=float, default=0.10, help="Margen alrededor de cada caja (fracción)")
    p.add_argument("--min-size", type=int, default=32, help="Descarta recortes más pequeños (px)")
    p.add_argument("--val", type=float, default=0.15)
    p.add_argument("--test", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--escala", choices=sorted(SCALES), default="finca",
                   help="finca = 3 categorías de la finca; publica = escala propia de los datasets públicos (preentrenamiento)")
    args = p.parse_args()

    counts = {"train": 0, "val": 0, "test": 0, "ignored": 0, "too_small": 0, "grayscale": 0}
    for root in args.yolo:
        print(f"Recortando {root} ...")
        crop_yolo_dataset(root, args.out, args.pad, args.min_size, counts, args.escala)
    for root in args.folder:
        print(f"Repartiendo {root} ...")
        split_folder_dataset(root, args.out, args.seed, args.val, args.test, counts, args.escala)

    print(f"\nGuardadas: train={counts['train']} val={counts['val']} test={counts['test']}"
          f" | ignoradas (sin mapeo)={counts['ignored']} | muy pequeñas={counts['too_small']}"
          f" | fotos en gris descartadas={counts['grayscale']}")
    print_summary(args.out)


if __name__ == "__main__":
    main()
