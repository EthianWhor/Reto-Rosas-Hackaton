"""Ajusta un YOLO preentrenado para encontrar rosas en las fotos de escena.

Parte de pesos preentrenados (YOLO11n por defecto, el más liviano) y solo
aprende una clase: "rosa". La categoría de cada rosa la decide RosaNet.

Ejemplo:
    python -m ml.train_detector --data data/detector/data.yaml --epochs 60
El mejor modelo queda en runs/detector/weights/best.pt
"""

import argparse
from pathlib import Path


def main() -> None:
    from ultralytics import YOLO
    import torch

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, default=Path("data/detector/data.yaml"))
    p.add_argument("--weights", default="yolo11n.pt",
                   help="Pesos de partida (yolo11n.pt, o modelos/detector_rosas.pt para un ajuste fino)")
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16, help="Bajar a 8 si se queda sin memoria (GPU de 4 GB)")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--project", type=Path, default=Path("runs"))
    p.add_argument("--name", default="detector")
    p.add_argument("--patience", type=int, default=15, help="Épocas sin mejorar antes de parar")
    args = p.parse_args()

    model = YOLO(args.weights)
    model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=0 if torch.cuda.is_available() else "cpu",
        project=str(args.project.resolve()),
        name=args.name,
        exist_ok=True,
        patience=args.patience,
        # Sin cambio de tono: el rojo de la rosa importa (aunque aquí solo se detecta).
        hsv_h=0.0,
        fliplr=0.5,
        plots=True,
    )
    metrics = model.val(split="test")
    print(f"\nTest -> mAP50: {metrics.box.map50:.3f}  mAP50-95: {metrics.box.map:.3f}"
          f"  precisión: {metrics.box.mp:.3f}  recall: {metrics.box.mr:.3f}")


if __name__ == "__main__":
    main()
