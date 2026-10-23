"""Entrena RosaNet desde cero sobre el dataset de etapas.

Espera la estructura que genera ml.prepare_data:
    <data>/train/<etapa>/*.jpg, <data>/val/<etapa>/*.jpg, <data>/test/<etapa>/*.jpg

Guarda en <out>/:
    best.pt          mejor modelo según Macro-F1 en validación
    history.csv      pérdida y métricas por época
    test_metrics.json métricas finales en test (con el mejor modelo)

Ejemplo:
    python -m ml.train --data data/stages --out runs/rosanet --epochs 40
"""

import argparse
import csv
import json
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from ml.data import StageFolder, eval_transform, present_classes, train_transform
from ml.evaluate import evaluate, format_report
from ml.model import RosaNet, count_parameters, load_checkpoint, save_checkpoint


def class_weights(counts: list[int]) -> torch.Tensor:
    """Peso inverso a la frecuencia, para que las etapas con pocas fotos cuenten igual."""
    total = sum(counts)
    return torch.tensor([total / (len(counts) * c) for c in counts], dtype=torch.float32)


def train_one_epoch(model, loader, criterion, optimizer, scheduler, scaler, device) -> float:
    model.train()
    running, seen = 0.0, 0
    for images, labels in loader:
        images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type=device, enabled=scaler.is_enabled()):
            loss = criterion(model(images), labels)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        scheduler.step()
        running += loss.item() * images.size(0)
        seen += images.size(0)
    return running / seen


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, default=Path("data/stages"))
    p.add_argument("--out", type=Path, default=Path("runs/rosanet"))
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-3, help="Tasa de aprendizaje máxima (OneCycle)")
    p.add_argument("--weight-decay", type=float, default=5e-4)
    p.add_argument("--patience", type=int, default=10, help="Épocas sin mejorar antes de parar")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    torch.manual_seed(args.seed)
    torch.backends.cudnn.benchmark = True  # entradas de tamaño fijo: cuDNN elige el algoritmo más rápido
    device = "cuda" if torch.cuda.is_available() else "cpu"
    args.out.mkdir(parents=True, exist_ok=True)

    classes = present_classes(args.data / "train")
    if len(classes) < 2:
        raise SystemExit(f"Se necesitan al menos 2 etapas con imágenes en {args.data / 'train'}")
    train_ds = StageFolder(args.data / "train", classes, train_transform)
    val_ds = StageFolder(args.data / "val", classes, eval_transform)
    test_ds = StageFolder(args.data / "test", classes, eval_transform)
    counts = train_ds.class_counts()
    print(f"Dispositivo: {device} | etapas: {classes}")
    print(f"Imágenes -> train {len(train_ds)} {counts} | val {len(val_ds)} | test {len(test_ds)}")

    loader_kw = dict(batch_size=args.batch_size, num_workers=args.workers, pin_memory=device == "cuda")
    train_loader = DataLoader(train_ds, shuffle=True, drop_last=len(train_ds) > args.batch_size, **loader_kw)
    val_loader = DataLoader(val_ds, **loader_kw)

    model = RosaNet(num_classes=len(classes)).to(device)
    print(f"RosaNet: {count_parameters(model):,} parámetros")
    criterion = nn.CrossEntropyLoss(weight=class_weights(counts).to(device), label_smoothing=0.1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=args.lr, epochs=args.epochs, steps_per_epoch=len(train_loader)
    )
    scaler = torch.amp.GradScaler(enabled=device == "cuda")

    best_f1, best_epoch = -1.0, 0
    with open(args.out / "history.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_accuracy", "val_macro_f1", "seconds"])
        for epoch in range(1, args.epochs + 1):
            start = time.time()
            loss = train_one_epoch(model, train_loader, criterion, optimizer, scheduler, scaler, device)
            val = evaluate(model, val_loader, classes, device)
            elapsed = time.time() - start
            writer.writerow([epoch, f"{loss:.4f}", f"{val['accuracy']:.4f}", f"{val['macro_f1']:.4f}", f"{elapsed:.1f}"])
            f.flush()

            mark = ""
            if val["macro_f1"] > best_f1:
                best_f1, best_epoch = val["macro_f1"], epoch
                save_checkpoint(args.out / "best.pt", model, classes, {"epoch": epoch, "val_macro_f1": best_f1})
                mark = "  <- mejor"
            print(f"Época {epoch:3d} | pérdida {loss:.4f} | val exactitud {val['accuracy']:.3f}"
                  f" macro-F1 {val['macro_f1']:.3f} | {elapsed:.0f}s{mark}")
            if epoch - best_epoch >= args.patience:
                print(f"Sin mejora en {args.patience} épocas, se detiene el entrenamiento.")
                break

    print(f"\nMejor época: {best_epoch} (val macro-F1 {best_f1:.3f})")
    if len(test_ds):
        model, _ = load_checkpoint(args.out / "best.pt", device)
        test = evaluate(model, DataLoader(test_ds, **loader_kw), classes, device)
        print("\n=== Test (imágenes nunca vistas en entrenamiento) ===")
        print(format_report(test))
        (args.out / "test_metrics.json").write_text(json.dumps(test, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
