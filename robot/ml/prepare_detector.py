"""Une varios datasets YOLO en uno solo de una clase ("rosa") para el detector.

El detector solo tiene que encontrar dónde hay una rosa en la escena; decidir
si está inmadura, en punto óptimo o pasada es trabajo de RosaNet. Por eso todas
las cajas con mapeo en stages.py se convierten a la clase 0 y el resto se descarta.

Se respeta el split de cada dataset (train/valid/test). Los nombres de archivo
llevan el nombre del dataset como prefijo para que no choquen.

OJO: no usar data/finca_yolo para el detector. En las fotos de la finca solo
están marcadas algunas rosas de cada escena; las demás quedarían como "fondo"
y el detector aprendería a ignorar rosas reales. Las fotos de la finca sirven
para RosaNet (recortes) y para revisar el detector a ojo.

Ejemplo:
    python -m ml.prepare_detector --yolo descargas/rose --yolo descargas/floracion --out data/detector
"""

import argparse
import shutil
from pathlib import Path

from ml.prepare_data import IMAGE_EXTS, SPLIT_DIRS, read_class_names
from ml.stages import map_class_name

OUT_SPLITS = {"train": "train", "val": "valid", "test": "test"}


def convert_labels(lines: list[str], names: list[str]) -> list[str]:
    out = []
    for line in lines:
        parts = line.split()
        if not parts or map_class_name(names[int(parts[0])]) is None:
            continue
        values = [float(v) for v in parts[1:]]
        if len(values) > 4:  # polígono -> caja
            xs, ys = values[0::2], values[1::2]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            values = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
        out.append("0 " + " ".join(f"{v:.6f}" for v in values))
    return out


def merge(root: Path, out: Path, counts: dict) -> None:
    names = read_class_names(root / "data.yaml")
    for split_dir in root.iterdir():
        split = SPLIT_DIRS.get(split_dir.name)
        if split is None or not (split_dir / "images").is_dir():
            continue
        dest = out / OUT_SPLITS[split]
        (dest / "images").mkdir(parents=True, exist_ok=True)
        (dest / "labels").mkdir(parents=True, exist_ok=True)
        for img in (split_dir / "images").iterdir():
            if img.suffix.lower() not in IMAGE_EXTS:
                continue
            label = split_dir / "labels" / f"{img.stem}.txt"
            lines = convert_labels(label.read_text().splitlines(), names) if label.exists() else []
            name = f"{root.name}_{img.stem}"
            shutil.copy(img, dest / "images" / f"{name}{img.suffix.lower()}")
            # Una imagen sin cajas también sirve: le enseña al detector qué NO es una rosa.
            (dest / "labels" / f"{name}.txt").write_text("\n".join(lines))
            counts[OUT_SPLITS[split]][0] += 1
            counts[OUT_SPLITS[split]][1] += len(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--yolo", type=Path, action="append", required=True, help="Dataset YOLO (repetible)")
    p.add_argument("--out", type=Path, default=Path("data/detector"))
    args = p.parse_args()

    if args.out.exists():
        shutil.rmtree(args.out)
    counts = {s: [0, 0] for s in OUT_SPLITS.values()}
    for root in args.yolo:
        print(f"Uniendo {root} ...")
        merge(root, args.out, counts)
    (args.out / "data.yaml").write_text(
        f"path: {args.out.resolve().as_posix()}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n"
        "names: ['rosa']\nnc: 1\n", encoding="utf-8")
    for split, (n_img, n_box) in counts.items():
        print(f"  {split:5s} imágenes={n_img}  rosas={n_box}")


if __name__ == "__main__":
    main()
