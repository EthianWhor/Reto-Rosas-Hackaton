"""Predice la etapa de apertura de una rosa y devuelve tips para el trabajador.

La imagen debe estar centrada en una sola rosa (foto de la app o recorte del
detector). Si la confianza es baja, la respuesta lo dice en lugar de inventar.

Ejemplo:
    python -m ml.predict --ckpt runs/rosanet/best.pt foto.jpg --cam mapa.jpg
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ml.data import eval_transform
from ml.model import RosaNet, load_checkpoint
from ml.stages import STAGE_LABELS, STAGE_TIPS

DEFAULT_THRESHOLD = 0.6


class RosePredictor:
    def __init__(self, ckpt: Path, device: str | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.classes = load_checkpoint(ckpt, self.device)
        self.threshold = threshold

    def predict(self, image: Image.Image) -> dict:
        x = eval_transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs = torch.softmax(self.model(x), dim=1)[0].cpu().tolist()
        best = max(range(len(probs)), key=probs.__getitem__)
        stage = self.classes[best]
        return {
            "etapa": stage,
            "nombre": STAGE_LABELS.get(stage, stage),
            "confianza": round(probs[best], 3),
            "seguro": probs[best] >= self.threshold,
            "probabilidades": {c: round(p, 3) for c, p in zip(self.classes, probs)},
            "tips": STAGE_TIPS.get(stage, {}),
        }

    def gradcam(self, image: Image.Image, class_index: int | None = None) -> Image.Image:
        """Superpone en rojo las zonas de la rosa que más pesaron en la decisión."""
        return gradcam_overlay(self.model, image, self.device, class_index)


def gradcam_overlay(model: RosaNet, image: Image.Image, device: str, class_index: int | None = None) -> Image.Image:
    image = image.convert("RGB")
    # Última ReLU del último bloque (antes del MaxPool): mapa de 14x14.
    layer = model.features[-1][-2]
    store = {}

    def hook(_module, _inputs, output):
        store["act"] = output
        output.register_hook(lambda grad: store.__setitem__("grad", grad))

    handle = layer.register_forward_hook(hook)
    try:
        x = eval_transform(image).unsqueeze(0).to(device)
        logits = model(x)
        idx = int(logits.argmax(1)) if class_index is None else class_index
        model.zero_grad(set_to_none=True)
        logits[0, idx].backward()
    finally:
        handle.remove()

    weights = store["grad"].mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((weights * store["act"]).sum(dim=1))[0].detach().cpu().numpy()
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    heat = np.array(Image.fromarray(np.uint8(cam * 255)).resize(image.size, Image.BILINEAR), dtype=np.float32) / 255
    base = np.asarray(image, dtype=np.float32)
    red = np.zeros_like(base)
    red[..., 0] = 255
    alpha = (heat * 0.55)[..., None]
    return Image.fromarray(np.uint8(base * (1 - alpha) + red * alpha))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path)
    p.add_argument("--ckpt", type=Path, default=Path("runs/rosanet/best.pt"))
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Confianza mínima para 'seguro'")
    p.add_argument("--cam", type=Path, help="Guardar imagen con el mapa de calor Grad-CAM")
    args = p.parse_args()

    predictor = RosePredictor(args.ckpt, threshold=args.threshold)
    with Image.open(args.image) as im:
        result = predictor.predict(im)
        if args.cam:
            predictor.gradcam(im).save(args.cam)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["seguro"]:
        print("\nNo estoy seguro: toma otra foto (más cerca, con mejor luz) o consulta a alguien con experiencia.")


if __name__ == "__main__":
    main()
