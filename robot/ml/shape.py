"""Rasgos de forma y color de una rosa recortada (enfoque tipo "plantilla").

La finca define el punto de corte con forma y color (variedad Freedom):
  - inmaduro (punto 2): cabeza pequeña, rojo más oscuro, sépalos pegados a los pétalos;
  - óptimo (punto 3): caracol definido mostrando centro, rojo vivo e intenso, patrón de copa.

Aquí se separa la cabeza de la rosa por su color rojo y se miden esos rasgos con
números que no dependen del tamaño del recorte. Un clasificador pequeño
(regresión logística) aprende los cortes con pocas rosas, y su resultado se
puede explicar ("copa abierta", "rojo vivo"), a diferencia de una CNN.
"""

import numpy as np
from PIL import Image
from scipy import ndimage

SIZE = 160  # el recorte se lleva a este lado antes de medir
FEATURES = [
    "alto_ancho",      # silueta alargada (botón) vs redonda
    "copa_arriba",     # ancho arriba / ancho en el medio: >1 = la punta se abre en copa
    "punta",           # ancho arriba / ancho máximo: botón puntiagudo = bajo
    "relleno",         # área roja / caja de la silueta: pétalos sueltos dejan huecos
    "rugosidad",       # perímetro² / área: bordes de pétalos abiertos = más irregular
    "rojo_brillo",     # V medio de los píxeles rojos: rojo vivo vs oscuro
    "rojo_saturacion", # S medio de los píxeles rojos
    "rojo_tono",       # tono medio (rojo puro vs morado oscuro)
    "rojo_area",       # fracción del recorte que es rosa
    "sepalos_verde",   # verde pegado a los lados de la mitad baja de la cabeza
]


def red_mask(hsv: np.ndarray) -> np.ndarray:
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red_hue = (h <= 14) | (h >= 210)  # escala 0-255 de PIL; incluye rojos amoratados (Freedom a contraluz)
    return red_hue & (s >= 0.16) & (v >= 0.08)


def green_mask(hsv: np.ndarray) -> np.ndarray:
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return (h >= 35) & (h <= 120) & (s >= 0.20) & (v >= 0.10)


def rose_region(mask: np.ndarray) -> np.ndarray:
    """Componente roja más grande cerca del centro (la cabeza de la rosa del recorte)."""
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_closing(mask, iterations=4)
    labels, n = ndimage.label(mask)
    if n == 0:
        return mask
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w]
    best, best_score = 0, -1.0
    for i in range(1, n + 1):
        comp = labels == i
        area = comp.sum()
        cy, cx = yy[comp].mean() / h, xx[comp].mean() / w
        score = area * (1.2 - np.hypot(cy - 0.5, cx - 0.5))  # grande y centrada
        if score > best_score:
            best, best_score = i, score
    return ndimage.binary_fill_holes(labels == best)


def shape_features(image: Image.Image) -> np.ndarray:
    im = image.convert("RGB").resize((SIZE, SIZE))
    hsv = np.asarray(im.convert("HSV"), dtype=np.float32) / np.array([1, 255, 255], dtype=np.float32)
    raw_red = red_mask(hsv)
    region = rose_region(raw_red)
    area = region.sum()
    if area < 30:  # no se encontró rosa roja
        return np.full(len(FEATURES), np.nan, dtype=np.float32)

    rows = np.where(region.any(axis=1))[0]
    cols = np.where(region.any(axis=0))[0]
    top, bottom, left, right = rows[0], rows[-1], cols[0], cols[-1]
    height, width = bottom - top + 1, right - left + 1
    widths = region[top:bottom + 1].sum(axis=1).astype(np.float32)

    def width_at(frac: float) -> float:
        i = int(round(frac * (len(widths) - 1)))
        lo, hi = max(0, i - 2), min(len(widths), i + 3)
        return float(widths[lo:hi].mean())

    eroded = ndimage.binary_erosion(region)
    perimeter = float((region & ~eroded).sum())
    red_px = region & raw_red
    v_red = hsv[..., 2][red_px] if red_px.any() else hsv[..., 2][region]
    s_red = hsv[..., 1][red_px] if red_px.any() else hsv[..., 1][region]
    h_red = hsv[..., 0][red_px] if red_px.any() else hsv[..., 0][region]
    hue_centered = np.where(h_red > 128, h_red - 256, h_red)  # el rojo da la vuelta en 0/255

    # Sépalos: verde en franjas a los lados de la mitad baja de la cabeza.
    band = max(3, int(0.15 * width))
    y0, y1 = top + height // 2, bottom + 1
    sides = np.zeros_like(region)
    sides[y0:y1, max(0, left - band):left + band] = True
    sides[y0:y1, max(0, right - band):right + band] = True
    sides &= ~region
    green = green_mask(hsv)
    sepals = green[sides].mean() if sides.any() else 0.0

    max_w = float(widths.max())
    return np.array([
        height / width,
        width_at(0.15) / max(width_at(0.6), 1),
        width_at(0.2) / max_w,
        area / float(height * width),
        perimeter ** 2 / area,
        float(v_red.mean()),
        float(s_red.mean()),
        float(hue_centered.mean()),
        area / float(SIZE * SIZE),
        float(sepals),
    ], dtype=np.float32)


def mask_preview(image: Image.Image) -> Image.Image:
    """Recorte con la silueta detectada en blanco (para revisar la segmentación)."""
    im = image.convert("RGB").resize((SIZE, SIZE))
    hsv = np.asarray(im.convert("HSV"), dtype=np.float32) / np.array([1, 255, 255], dtype=np.float32)
    region = rose_region(red_mask(hsv))
    arr = np.asarray(im).copy()
    edge = region & ~ndimage.binary_erosion(region, iterations=2)
    arr[edge] = (255, 255, 255)
    return Image.fromarray(arr)


# --- Clasificador de forma (se combina con RosaNet en ml.predict) ---

DEFAULT_SHAPE_MODEL = "forma.joblib"  # se busca junto al checkpoint de RosaNet


def train_shape_model(samples: list[tuple], classes: list[str]):
    """Entrena la regresión logística de forma. samples = [(ruta, índice_de_clase)]."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X = np.array([shape_features(Image.open(p)) for p, _ in samples])
    y = np.array([label for _, label in samples])
    median = np.nanmedian(X, axis=0)
    X = np.where(np.isnan(X), median, X)
    clf = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", C=0.5, max_iter=2000))
    clf.fit(X, y)
    return {"clf": clf, "median": median, "classes": classes, "features": FEATURES}


def shape_probs(bundle: dict, image: Image.Image) -> tuple[np.ndarray | None, dict]:
    """Probabilidades por clase según la forma, y los rasgos medidos.

    Devuelve (None, rasgos) si no se encontró una rosa roja en el recorte: entonces
    decide solo RosaNet.
    """
    feats = shape_features(image)
    rasgos = {name: (None if np.isnan(v) else round(float(v), 3)) for name, v in zip(FEATURES, feats)}
    if np.isnan(feats).all():
        return None, rasgos
    x = np.where(np.isnan(feats), bundle["median"], feats)[None]
    probs = np.zeros(len(bundle["classes"]))
    probs[bundle["clf"].classes_] = bundle["clf"].predict_proba(x)[0]
    return probs, rasgos


def main() -> None:
    import argparse
    import joblib

    from ml.calibrate import public_pasado
    from ml.data import list_samples
    from ml.stages import STAGES

    p = argparse.ArgumentParser(description="Entrena el clasificador de forma con todas las rosas de la finca.")
    p.add_argument("--finca", default="data/finca_stages")
    p.add_argument("--publico", default="data/pre", help="Recortes públicos (para completar 'pasado')")
    p.add_argument("--extra-pasado", type=int, default=40)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=f"modelos/{DEFAULT_SHAPE_MODEL}")
    args = p.parse_args()

    from pathlib import Path
    finca = Path(args.finca)
    # Igual que el RosaNet de operación: train+val de la finca (los casos difíciles quedan fuera).
    samples = list_samples(finca / "train", STAGES) + list_samples(finca / "val", STAGES)
    samples += public_pasado(Path(args.publico), args.extra_pasado, args.seed)
    bundle = train_shape_model(samples, STAGES)
    joblib.dump(bundle, args.out)
    print(f"Clasificador de forma con {len(samples)} rosas -> {args.out}")


if __name__ == "__main__":
    main()
