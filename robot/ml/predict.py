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
from ml.shape import DEFAULT_SHAPE_MODEL, shape_probs
from ml.stages import STAGE_LABELS, STAGE_TIPS

DEFAULT_THRESHOLD = 0.6
SHAPE_WEIGHT = 0.5  # peso de la forma al combinar con RosaNet (ml.shape_cv)


class RosePredictor:
    """RosaNet + clasificador de forma (si existe forma.joblib junto al checkpoint).

    Las dos opiniones se promedian (peso SHAPE_WEIGHT para la forma). Medido con validación
    cruzada en rosas de la finca: de día 72 % -> 77 % de exactitud y 43 % -> 61 % de óptimas
    reconocidas sin más inmaduras llamadas óptimas; de noche 76 % -> 77 %. Si en el recorte no
    se encuentra una rosa roja, decide solo RosaNet.
    """

    def __init__(self, ckpt: Path, device: str | None = None, threshold: float = DEFAULT_THRESHOLD,
                 shape_model: Path | str | None = "auto"):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.classes = load_checkpoint(ckpt, self.device)
        self.threshold = threshold
        if shape_model == "auto":
            shape_model = Path(ckpt).parent / DEFAULT_SHAPE_MODEL
        self.shape = None
        if shape_model is not None and Path(shape_model).exists():
            import joblib

            self.shape = joblib.load(shape_model)
            if list(self.shape["classes"]) != list(self.classes):
                raise ValueError(f"{shape_model} tiene clases {self.shape['classes']}, RosaNet tiene {self.classes}")

    def predict(self, image: Image.Image) -> dict:
        image = image.convert("RGB")
        x = eval_transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            net = torch.softmax(self.model(x), dim=1)[0].cpu().numpy()
        shape, rasgos = shape_probs(self.shape, image) if self.shape else (None, None)
        probs = net if shape is None else (1 - SHAPE_WEIGHT) * net + SHAPE_WEIGHT * shape
        best = int(probs.argmax())
        stage = self.classes[best]
        rounded = lambda v: {c: round(float(q), 3) for c, q in zip(self.classes, v)}
        return {
            "etapa": stage,
            "nombre": STAGE_LABELS.get(stage, stage),
            "confianza": round(float(probs[best]), 3),
            "seguro": bool(probs[best] >= self.threshold),
            "probabilidades": rounded(probs),
            "tips": STAGE_TIPS.get(stage, {}),
            # Detalle de cada opinión y los rasgos medidos (para explicar la decisión).
            "fuentes": {"rosanet": rounded(net), "forma": None if shape is None else rounded(shape)},
            "rasgos": rasgos,
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
    p.add_argument("--ckpt", type=Path, default=Path("modelos/rosanet.pt"))
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
