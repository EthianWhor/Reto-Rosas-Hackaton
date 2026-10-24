"""Une varios datasets YOLO en uno solo de una clase ("rosa") para el detector.

El detector solo tiene que encontrar dónde hay una rosa en la escena; decidir
si está inmadura, en punto óptimo o pasada es trabajo de RosaNet. Por eso todas
las cajas con mapeo en stages.py se convierten a la clase 0 y el resto se descarta.

Se respeta el split de cada dataset (train/valid/test). Los nombres de archivo
llevan el nombre del dataset como prefijo para que no choquen.

Escenas del invernadero (--finca): export de Roboflow con TODAS las rosas
marcadas (ver ml.preanotar). Son pocas, así que su train se repite --repetir
veces para que pesen frente a los públicos, y su valid/test son los únicos que
se usan para validar y medir (es donde el detector tiene que funcionar). De los
públicos (--yolo) solo se usa el train, opcionalmente limitado con --max-publico.

OJO: no usar data/finca_yolo para el detector. Ahí solo están marcadas algunas
rosas de cada escena; las demás quedarían como "fondo" y el detector aprendería
a ignorar rosas reales.

Ejemplos:
    python -m ml.prepare_detector --yolo descargas/rose --yolo descargas/floracion --out data/detector
    python -m ml.prepare_detector --finca descargas/rosas_finca --repetir 8         --yolo descargas/rose --yolo descargas/floracion --max-publico 1000 --out data/detector_finca
"""

import argparse
import random
import shutil
from pathlib import Path

from PIL import Image

from ml.data import night_scene
from ml.prepare_data import IMAGE_EXTS, SPLIT_DIRS, read_class_names
from ml.stages import map_class_name

OUT_SPLITS = {"train": "train", "val": "valid", "test": "test"}


def convert_labels(lines: list[str], names: list[str]) -> list[str]:
    out = []
    for line in lines:
        parts = line.split()
        name = names[int(parts[0])] if parts else ""
        if not parts or (name.lower() not in ("rosa", "rose") and map_class_name(name) is None):
            continue
        values = [float(v) for v in parts[1:]]
        if len(values) > 4:  # polígono -> caja
            xs, ys = values[0::2], values[1::2]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            values = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
        out.append("0 " + " ".join(f"{v:.6f}" for v in values))
    return out


def merge(root: Path, out: Path, counts: dict, splits=("train", "val", "test"), repeat: int = 1,
          max_train: int | None = None, seed: int = 0, night: int = 0, pattern: str | None = None) -> None:
    """Copia un dataset YOLO a una sola clase.

    night > 0: además agrega copias "de noche" (data.night_scene): `night` copias variadas por
    imagen de train y una copia fija por imagen de valid/test, para medir de día y de noche.
    pattern: solo usa las imágenes cuyo nombre contiene ese texto.
    """
    rng = random.Random(seed)
    names = read_class_names(root / "data.yaml")
    for split_dir in sorted(root.iterdir()):
        split = SPLIT_DIRS.get(split_dir.name)
        if split not in splits or not (split_dir / "images").is_dir():
            continue
        dest = out / OUT_SPLITS[split]
        (dest / "images").mkdir(parents=True, exist_ok=True)
        (dest / "labels").mkdir(parents=True, exist_ok=True)
        images = sorted(i for i in (split_dir / "images").iterdir()
                        if i.suffix.lower() in IMAGE_EXTS and (pattern is None or pattern in i.name))
        if split == "train" and max_train and len(images) > max_train:
            images = random.Random(seed).sample(images, max_train)
        copies = repeat if split == "train" else 1
        for img in images:
            label = split_dir / "labels" / f"{img.stem}.txt"
            lines = convert_labels(label.read_text().splitlines(), names) if label.exists() else []
            for k in range(copies):
                name = f"{root.name}_{img.stem}" + (f"_r{k}" if copies > 1 else "")
                shutil.copy(img, dest / "images" / f"{name}{img.suffix.lower()}")
                # Una imagen sin cajas también sirve: le enseña al detector qué NO es una rosa.
                (dest / "labels" / f"{name}.txt").write_text("\n".join(lines))
                counts[OUT_SPLITS[split]][0] += 1
                counts[OUT_SPLITS[split]][1] += len(lines)
            n_night = night if split == "train" else (1 if night else 0)
            for k in range(n_night):
                name = f"{root.name}_{img.stem}_noche{k}"
                with Image.open(img) as im:
                    night_scene(im.convert("RGB"), rng if split == "train" else None).save(
                        dest / "images" / f"{name}.jpg", quality=92)
                (dest / "labels" / f"{name}.txt").write_text("\n".join(lines))
                counts[OUT_SPLITS[split]][0] += 1
                counts[OUT_SPLITS[split]][1] += len(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--yolo", type=Path, action="append", default=[], help="Dataset YOLO público (repetible)")
    p.add_argument("--finca", type=Path, help="Escenas del invernadero con todas las rosas marcadas")
    p.add_argument("--repetir", type=int, default=8, help="Veces que se repite el train de --finca")
    p.add_argument("--max-publico", type=int, help="Máximo de imágenes de train por dataset público")
    p.add_argument("--noche", type=int, default=0,
                   help="Copias 'de noche' por escena de train de --finca (y una fija en valid/test para medir)")
    p.add_argument("--out", type=Path, default=Path("data/detector"))
    args = p.parse_args()

    if args.out.exists():
        shutil.rmtree(args.out)
    counts = {s: [0, 0] for s in OUT_SPLITS.values()}
    if args.finca:
        print(f"Uniendo {args.finca} (train x{args.repetir}, valid y test para medir) ...")
        merge(args.finca, args.out, counts, repeat=args.repetir, night=args.noche)
    for spec in args.yolo:
        # "ruta::texto" usa solo las imágenes cuyo nombre contiene ese texto.
        root, _, pattern = str(spec).partition("::")
        print(f"Uniendo {root}" + (f" (solo '{pattern}')" if pattern else "") + " ...")
        # Con escenas de la finca, los públicos solo aportan train: se valida en el invernadero.
        merge(Path(root), args.out, counts, splits=("train",) if args.finca else ("train", "val", "test"),
              max_train=args.max_publico, pattern=pattern or None)
    (args.out / "data.yaml").write_text(
        f"path: {args.out.resolve().as_posix()}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n"
        "names: ['rosa']\nnc: 1\n", encoding="utf-8")
    for split, (n_img, n_box) in counts.items():
        print(f"  {split:5s} imágenes={n_img}  rosas={n_box}")


if __name__ == "__main__":
    main()
