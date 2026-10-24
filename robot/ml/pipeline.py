"""Pipeline de operación del robot: foto de escena -> rosas -> categoría -> reporte.

1. El detector (YOLO ajustado) encuentra cada rosa en la foto.
2. Cada rosa se recorta y RosaNet decide: inmaduro, óptimo o pasado.
3. Se arma un reporte por sector para el dashboard (coordinadores y pantalla
   a la entrada del campo).

Ejemplo (todas las fotos de un sector):
    python -m ml.pipeline --sector B3 fotos/b3/*.jpg --out reportes/b3.json --anotadas reportes/b3
"""

import argparse
import glob
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from ml.detect import DET_IMGSZ, RoseDetector
from ml.predict import DEFAULT_THRESHOLD, RosePredictor
from ml.prepare_data import pad_box
from ml.stages import STAGE_LABELS

COLORS = {"1_inmaduro": "deepskyblue", "2_optimo": "lime", "3_pasado": "red", "incierta": "yellow"}


class RoseInspector:
    """Detector + RosaNet: una entrada por rosa encontrada en la foto."""

    def __init__(self, detector_weights: Path, classifier_ckpt: Path, det_conf: float | None = None,
                 threshold: float = DEFAULT_THRESHOLD, pad: float = 0.15, device: str | None = None,
                 imgsz: int = DET_IMGSZ):
        self.detector = RoseDetector(detector_weights, conf=det_conf, imgsz=imgsz, device=device)
        self.classifier = RosePredictor(classifier_ckpt, device=device, threshold=threshold)
        self.pad = pad

    def inspect(self, image: Image.Image) -> list[dict]:
        image = image.convert("RGB")
        roses = []
        for det in self.detector.detect(image):
            box = det["bbox"]
            crop_box = pad_box([int(v) for v in box], *image.size, self.pad)
            pred = self.classifier.predict(image.crop(crop_box))
            roses.append({
                "caja": [round(v) for v in box],
                "confianza_deteccion": det["confianza"],
                "categoria": pred["etapa"] if pred["seguro"] else "incierta",
                "categoria_red": pred["etapa"],
                "confianza": pred["confianza"],
                "probabilidades": pred["probabilidades"],
            })
        return roses


def summarize(sector: str, photos: list[dict]) -> dict:
    counts = {"1_inmaduro": 0, "2_optimo": 0, "3_pasado": 0, "incierta": 0}
    for photo in photos:
        for rose in photo["rosas"]:
            counts[rose["categoria"]] += 1
    total = sum(counts.values())
    if counts["2_optimo"] > 0:
        prioridad = "alta"      # hay rosas para cortar hoy
    elif counts["incierta"] > 0:
        prioridad = "revisar"   # la red no está segura: que pase alguien con experiencia
    else:
        prioridad = "baja"
    return {
        "sector": sector,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "fotos": len(photos),
        "rosas_detectadas": total,
        "conteo": counts,
        "listas_para_cortar": counts["2_optimo"],
        "prioridad": prioridad,
        "detalle": photos,
    }


def draw_annotations(image: Image.Image, roses: list[dict]) -> Image.Image:
    image = image.convert("RGB")
    draw, width = ImageDraw.Draw(image), max(3, image.width // 250)
    for rose in roses:
        cat = rose["categoria"]
        label = f"{STAGE_LABELS.get(cat, 'Incierta')} {rose['confianza']:.0%}"
        draw.rectangle(rose["caja"], outline=COLORS[cat], width=width)
        draw.text((rose["caja"][0] + 4, rose["caja"][1] + 4), label, fill=COLORS[cat])
    return image


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("images", nargs="+", help="Fotos del sector (acepta comodines)")
    p.add_argument("--sector", required=True)
    p.add_argument("--detector", type=Path, default=Path("modelos/detector_rosas.pt"))
    p.add_argument("--ckpt", type=Path, default=Path("modelos/rosanet.pt"))
    p.add_argument("--det-conf", type=float, help="Confianza mínima del detector (por defecto, la medida para ese modelo)")
    p.add_argument("--imgsz", type=int, default=DET_IMGSZ, help="Resolución a la que se procesa la foto en el detector")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Confianza mínima de RosaNet")
    p.add_argument("--out", type=Path, help="Guardar el reporte JSON")
    p.add_argument("--anotadas", type=Path, help="Carpeta para guardar las fotos con las cajas dibujadas")
    args = p.parse_args()

    paths = [Path(f) for pattern in args.images for f in (glob.glob(pattern) or [pattern])]
    inspector = RoseInspector(args.detector, args.ckpt, args.det_conf, args.threshold, imgsz=args.imgsz)
    photos = []
    for path in paths:
        with Image.open(path) as im:
            roses = inspector.inspect(im)
            if args.anotadas:
                args.anotadas.mkdir(parents=True, exist_ok=True)
                draw_annotations(im, roses).save(args.anotadas / f"{path.stem}.jpg", quality=90)
        photos.append({"foto": path.name, "rosas": roses})
        print(f"{path.name}: {len(roses)} rosas")

    report = summarize(args.sector, photos)
    c = report["conteo"]
    print(f"\nSector {args.sector}: {report['rosas_detectadas']} rosas | óptimas {c['2_optimo']}"
          f" | inmaduras {c['1_inmaduro']} | pasadas {c['3_pasado']} | inciertas {c['incierta']}"
          f" | prioridad {report['prioridad']}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
