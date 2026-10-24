"""Evalúa un modelo entrenado sobre una carpeta de imágenes por etapa.

Sirve para el test final y, sobre todo, para medir con fotos propias de rosas
comerciales que el modelo nunca vio (evidencia para el pitch).

Ejemplo:
    python -m ml.evaluate --ckpt runs/rosanet/best.pt --data data/propias
"""

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from ml.data import StageFolder
from ml.model import load_checkpoint


def predict_logits(model, images: torch.Tensor, tta: bool = False) -> torch.Tensor:
    """Logits del modelo; con tta promedia la imagen y su espejo horizontal."""
    logits = model(images)
    if tta:
        logits = (logits + model(torch.flip(images, dims=[3]))) / 2
    return logits


@torch.no_grad()
def evaluate(model, loader, classes: list[str], device, tta: bool = False) -> dict:
    model.eval()
    n = len(classes)
    confusion = [[0] * n for _ in range(n)]  # filas = real, columnas = predicha
    for images, labels in loader:
        preds = predict_logits(model, images.to(device), tta).argmax(1).cpu()
        for t, p in zip(labels.tolist(), preds.tolist()):
            confusion[t][p] += 1
    return metrics_from_confusion(confusion, classes)


def metrics_from_confusion(confusion: list[list[int]], classes: list[str]) -> dict:
    n = len(classes)
    per_class, f1s = {}, []
    for i, cls in enumerate(classes):
        tp = confusion[i][i]
        support = sum(confusion[i])
        predicted = sum(row[i] for row in confusion)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
        if support:
            f1s.append(f1)

    total = sum(map(sum, confusion))
    return {
        "accuracy": sum(confusion[i][i] for i in range(n)) / total if total else 0.0,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "per_class": per_class,
        "confusion": confusion,
        "classes": classes,
        "n_images": total,
    }


def format_report(metrics: dict) -> str:
    classes = metrics["classes"]
    lines = [
        f"Imágenes: {metrics['n_images']}  |  Exactitud: {metrics['accuracy']:.3f}  |  Macro-F1: {metrics['macro_f1']:.3f}",
        "",
        f"{'etapa':22s} {'precisión':>9s} {'recall':>7s} {'f1':>6s} {'n':>5s}",
    ]
    for cls, m in metrics["per_class"].items():
        lines.append(f"{cls:22s} {m['precision']:9.3f} {m['recall']:7.3f} {m['f1']:6.3f} {m['support']:5d}")
    lines += ["", "Matriz de confusión (filas = real, columnas = predicha):"]
    width = max(len(c) for c in classes)
    lines.append(" " * (width + 1) + " ".join(f"{i + 1:>5d}" for i in range(len(classes))))
    for cls, row in zip(classes, metrics["confusion"]):
        lines.append(f"{cls:>{width}s} " + " ".join(f"{v:5d}" for v in row))
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ckpt", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True, help="Carpeta con una subcarpeta por etapa")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--out", type=Path, help="Guardar métricas en JSON")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, classes = load_checkpoint(args.ckpt, device)
    dataset = StageFolder(args.data, classes)
    metrics = evaluate(model, DataLoader(dataset, batch_size=args.batch_size), classes, device)
    print(format_report(metrics))
    if args.out:
        args.out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
