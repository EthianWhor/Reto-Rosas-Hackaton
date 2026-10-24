"""Entrena RosaNet sobre un dataset de recortes por clase.

Espera la estructura que genera ml.prepare_data:
    <data>/train/<clase>/*.jpg, <data>/val/<clase>/*.jpg, <data>/test/<clase>/*.jpg

Dos usos:
  1. Preentrenar desde cero con los datasets públicos (escala "publica").
  2. Calibrar con la finca partiendo del preentrenado: --init carga todas las
     capas menos la última (que cambia de clases) y --freeze congela los
     primeros bloques para no olvidar lo aprendido con pocas fotos.

Guarda en <out>/:
    best.pt           mejor modelo según Macro-F1 en validación
    history.csv       pérdida y métricas por época
    test_metrics.json métricas finales en test (con el mejor modelo)

Ejemplos:
    python -m ml.train --data data/pre --out runs/rosanet_pre --epochs 40
    python -m ml.train --data data/finca_stages --out runs/rosanet --init runs/rosanet_pre/best.pt --freeze 2
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
    """Peso inverso a la frecuencia, para que las clases con pocas fotos cuenten igual."""
    total = sum(counts)
    return torch.tensor([total / (len(counts) * max(c, 1)) for c in counts], dtype=torch.float32)


def build_model(num_classes: int, init: Path | None = None, freeze: int = 0) -> RosaNet:
    """RosaNet nueva, opcionalmente con los pesos de un preentrenamiento.

    freeze = cuántos bloques convolucionales congelar (el stem se congela si freeze > 0).
    """
    model = RosaNet(num_classes=num_classes)
    if init is not None:
        state = torch.load(init, map_location="cpu", weights_only=False)["state_dict"]
        state = {k: v for k, v in state.items() if not k.startswith("classifier.")}
        missing, _ = model.load_state_dict(state, strict=False)
        assert all(k.startswith("classifier.") for k in missing), missing
    model.frozen = []
    if freeze > 0:
        model.frozen = [model.stem, *model.features[:freeze]]
        for module in model.frozen:
            for param in module.parameters():
                param.requires_grad = False
    return model


def train_one_epoch(model, loader, criterion, optimizer, scheduler, scaler, device) -> float:
    model.train()
    for module in model.frozen:  # BatchNorm congelado: no actualizar sus estadísticas
        module.eval()
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


def fit(model, train_ds, val_ds, classes, out: Path, epochs=40, batch_size=32, lr=3e-3, weight_decay=5e-4,
        patience=10, workers=2, device="cpu", verbose=True, select="best") -> dict:
    """Entrena y guarda <out>/best.pt. Devuelve un resumen.

    select="best": guarda la época con mejor Macro-F1 en validación (y para si no mejora).
    select="last": entrena todas las épocas y guarda el modelo final. Se usa en la
    validación cruzada, donde elegir la época mirando el fold de prueba inflaría el resultado.
    """
    out.mkdir(parents=True, exist_ok=True)
    loader_kw = dict(batch_size=batch_size, num_workers=workers, pin_memory=device == "cuda",
                     persistent_workers=workers > 0)
    train_loader = DataLoader(train_ds, shuffle=True, drop_last=len(train_ds) > batch_size, **loader_kw)
    val_loader = DataLoader(val_ds, **loader_kw)

    model = model.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights(train_ds.class_counts()).to(device), label_smoothing=0.1)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=lr, epochs=epochs,
                                                    steps_per_epoch=len(train_loader))
    scaler = torch.amp.GradScaler(enabled=device == "cuda")

    best_f1, best_epoch = -1.0, 0
    with open(out / "history.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_accuracy", "val_macro_f1", "seconds"])
        for epoch in range(1, epochs + 1):
            start = time.time()
            loss = train_one_epoch(model, train_loader, criterion, optimizer, scheduler, scaler, device)
            val = evaluate(model, val_loader, classes, device)
            elapsed = time.time() - start
            writer.writerow([epoch, f"{loss:.4f}", f"{val['accuracy']:.4f}", f"{val['macro_f1']:.4f}", f"{elapsed:.1f}"])
            f.flush()

            mark = ""
            if val["macro_f1"] > best_f1:
                best_f1, best_epoch = val["macro_f1"], epoch
                if select == "best":
                    save_checkpoint(out / "best.pt", model, classes, {"epoch": epoch, "val_macro_f1": best_f1})
                    mark = "  <- mejor"
            if verbose:
                print(f"Época {epoch:3d} | pérdida {loss:.4f} | val exactitud {val['accuracy']:.3f}"
                      f" macro-F1 {val['macro_f1']:.3f} | {elapsed:.0f}s{mark}", flush=True)
            if select == "best" and epoch - best_epoch >= patience:
                if verbose:
                    print(f"Sin mejora en {patience} épocas, se detiene el entrenamiento.")
                break
    if select == "last":
        save_checkpoint(out / "best.pt", model, classes, {"epoch": epoch, "val_macro_f1": val["macro_f1"]})
        return {"best_epoch": epoch, "val_macro_f1": val["macro_f1"]}
    return {"best_epoch": best_epoch, "val_macro_f1": best_f1}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, default=Path("data/stages"))
    p.add_argument("--out", type=Path, default=Path("runs/rosanet"))
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-3, help="Tasa de aprendizaje máxima (OneCycle)")
    p.add_argument("--weight-decay", type=float, default=5e-4)
    p.add_argument("--patience", type=int, default=10, help="Épocas sin mejorar antes de parar")
    p.add_argument("--init", type=Path, help="Checkpoint preentrenado (se cargan todas las capas menos la última)")
    p.add_argument("--freeze", type=int, default=0, help="Bloques convolucionales a congelar (0-4)")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    torch.manual_seed(args.seed)
    torch.backends.cudnn.benchmark = True  # entradas de tamaño fijo: cuDNN elige el algoritmo más rápido
    device = "cuda" if torch.cuda.is_available() else "cpu"

    classes = present_classes(args.data / "train")
    if len(classes) < 2:
        raise SystemExit(f"Se necesitan al menos 2 clases con imágenes en {args.data / 'train'}")
    train_ds = StageFolder(args.data / "train", classes, train_transform)
    val_ds = StageFolder(args.data / "val", classes, eval_transform)
    test_ds = StageFolder(args.data / "test", classes, eval_transform)
    print(f"Dispositivo: {device} | clases: {classes}")
    print(f"Imágenes -> train {len(train_ds)} {train_ds.class_counts()} | val {len(val_ds)} | test {len(test_ds)}")

    model = build_model(len(classes), args.init, args.freeze)
    print(f"RosaNet: {count_parameters(model):,} parámetros entrenables"
          + (f" (desde {args.init}, {args.freeze} bloques congelados)" if args.init else ""))
    summary = fit(model, train_ds, val_ds, classes, args.out, args.epochs, args.batch_size, args.lr,
                  args.weight_decay, args.patience, args.workers, device)

    print(f"\nMejor época: {summary['best_epoch']} (val macro-F1 {summary['val_macro_f1']:.3f})")
    if len(test_ds):
        model, _ = load_checkpoint(args.out / "best.pt", device)
        test = evaluate(model, DataLoader(test_ds, batch_size=args.batch_size), classes, device)
        print("\n=== Test (imágenes nunca vistas en entrenamiento) ===")
        print(format_report(test))
        (args.out / "test_metrics.json").write_text(json.dumps(test, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
