"""Calibra RosaNet con las rosas de la finca y mide con validación cruzada.

Parte del modelo preentrenado con los datasets públicos y lo ajusta a las 3
categorías de la finca. Como la finca dio pocas rosas (~70), un solo split de
validación sería puro ruido; por eso se usa validación cruzada por foto:
las rosas de una misma foto quedan siempre en el mismo fold.

La finca solo dio 2 rosas "pasado". Para completar esa categoría se suman
recortes públicos de rosas abiertas o senescentes (sin duda "pasado" con el
estándar de la finca). Nunca se usan para medir: la medición es solo con la finca.

Pasos:
  1. K folds sobre train+val de la finca -> métricas de validación cruzada.
  2. Modelo final con todas esas rosas -> se mide en test (casos difíciles de la finca).

Ejemplo:
    python -m ml.calibrate --finca data/finca_stages --publico data/pre \
        --init runs/rosanet_pre/best.pt --out runs/rosanet
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from ml.data import StageFolder, eval_transform, list_samples, train_transform
from ml.evaluate import evaluate, format_report, metrics_from_confusion
from ml.stages import PUBLIC_PASADO, STAGES
from ml.train import build_model, fit

PASADO = STAGES.index("3_pasado")


def photo_of(path: Path) -> str:
    """finca_yolo_26_2.jpg -> finca_yolo_26 (todas las rosas de la foto 26)."""
    return path.stem.rsplit("_", 1)[0]


def make_folds(samples, k: int, seed: int) -> list[list]:
    """Reparte las fotos en k folds, empezando por las de clases escasas para equilibrar."""
    groups = defaultdict(list)
    for path, label in samples:
        groups[photo_of(path)].append((path, label))
    counts = defaultdict(int)
    for _, label in samples:
        counts[label] += 1
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    keys.sort(key=lambda g: min(counts[l] for _, l in groups[g]))  # la clase más rara de la foto primero
    folds = [[] for _ in range(k)]
    for i, g in enumerate(keys):
        folds[i % k].extend(groups[g])
    return folds


def public_pasado(publico: Path, n: int, seed: int) -> list:
    pool = [p for cls in PUBLIC_PASADO for p in sorted((publico / "train" / cls).glob("*.jpg"))]
    random.Random(seed).shuffle(pool)
    return [(p, PASADO) for p in pool[:n]]


def merge_confusion(total, conf):
    return [[a + b for a, b in zip(r1, r2)] for r1, r2 in zip(total, conf)] if total else conf


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--finca", type=Path, default=Path("data/finca_stages"))
    p.add_argument("--publico", type=Path, default=Path("data/pre"), help="Recortes en escala pública")
    p.add_argument("--init", type=Path, default=Path("runs/rosanet_pre/best.pt"))
    p.add_argument("--out", type=Path, default=Path("runs/rosanet"))
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--freeze", type=int, default=2, help="Bloques congelados del preentrenado")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--extra-pasado", type=int, default=40, help="Recortes públicos de 'pasado' a sumar")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if str(args.init).lower() == "none":  # para comparar: sin preentrenamiento
        args.init, args.freeze = None, 0

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    classes = STAGES
    pool = list_samples(args.finca / "train", classes) + list_samples(args.finca / "val", classes)
    hard = list_samples(args.finca / "test", classes)
    extra = public_pasado(args.publico, args.extra_pasado, args.seed) if args.extra_pasado else []
    print(f"Finca: {len(pool)} rosas para validación cruzada, {len(hard)} difíciles para test"
          f" | {len(extra)} 'pasado' públicas de apoyo")

    fit_kw = dict(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, workers=args.workers,
                  device=device, verbose=False, select="last")
    total_conf = None
    folds = make_folds(pool, args.k, args.seed)
    for i, fold in enumerate(folds):
        if not fold:
            continue
        train = [s for j, f in enumerate(folds) if j != i for s in f] + extra
        train_ds = StageFolder(None, classes, train_transform, samples=train)
        val_ds = StageFolder(None, classes, eval_transform, samples=fold)
        model = build_model(len(classes), args.init, args.freeze)
        fit(model, train_ds, val_ds, classes, args.out / f"fold{i + 1}", **fit_kw)
        m = evaluate(model.to(device), DataLoader(val_ds, batch_size=64), classes, device)
        total_conf = merge_confusion(total_conf, m["confusion"])
        print(f"Fold {i + 1}/{args.k}: {len(fold)} rosas | exactitud {m['accuracy']:.3f} | macro-F1 {m['macro_f1']:.3f}")

    cv = metrics_from_confusion(total_conf, classes)
    print("\n=== Validación cruzada (cada rosa de la finca medida por un modelo que no la vio) ===")
    print(format_report(cv))

    # Modelo final: todas las rosas del pool (+ apoyo) y medición en los casos difíciles.
    train_ds = StageFolder(None, classes, train_transform, samples=pool + extra)
    hard_ds = StageFolder(None, classes, eval_transform, samples=hard)
    model = build_model(len(classes), args.init, args.freeze)
    fit(model, train_ds, hard_ds, classes, args.out, **fit_kw)
    result = {"validacion_cruzada": cv, "config": {k: str(v) for k, v in vars(args).items()}}
    if hard:
        test = evaluate(model.to(device), DataLoader(hard_ds, batch_size=64), classes, device)
        print("\n=== Casos difíciles de la finca (test) ===")
        print(format_report(test))
        result["test_dificiles"] = test
    (args.out / "calibracion.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nModelo final para operar: {args.out / 'best.pt'}")


if __name__ == "__main__":
    main()
