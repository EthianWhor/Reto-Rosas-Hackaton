"""Carga de imágenes por etapa y transformaciones compartidas."""

import random
from pathlib import Path

import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from ml.model import IMAGE_SIZE

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)

# Margen del recorte alrededor de la rosa: el pipeline recorta con 15 % de margen por lado,
# así que la rosa ocupa el centro y el margen es 0.15 / 1.3 ≈ 11.5 % del recorte por lado.
CROP_MARGIN = 0.115


def darken_margin(im: Image.Image, margin: float = CROP_MARGIN, level: float = 0.0,
                  vignette: bool = False, fill: tuple | None = None) -> Image.Image:
    """Oscurece lo que queda fuera de la rosa SIN cambiar la escala (no agrega bordes).

    level: brillo que conserva el fondo (0 = negro, 0.3 = gris oscuro).
    vignette: en vez de un rectángulo, una elipse con borde suave, como una linterna.
    fill: pinta el margen de un color fijo (para las pruebas: negro o gris claro).
    """
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    if vignette:
        rx, ry = w * (0.5 - margin) * 1.15, h * (0.5 - margin) * 1.15
        d = np.sqrt(((x - w / 2) / rx) ** 2 + ((y - h / 2) / ry) ** 2)
        keep = np.clip((1.35 - d) / 0.35, 0, 1)   # 1 dentro de la rosa, se apaga hacia los bordes
    else:
        mx, my = w * margin, h * margin
        inside = (x >= mx) & (x < w - mx) & (y >= my) & (y < h - my)
        keep = inside.astype(np.float32)
    keep = keep[..., None]
    if fill is not None:
        out = arr * keep + np.array(fill, dtype=np.float32) * (1 - keep)
    else:
        out = arr * (level + (1 - level) * keep)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def darken_sky(im: Image.Image, level: float = 0.1) -> Image.Image:
    """Oscurece el cielo / plástico del invernadero (claro y casi sin color) en toda la imagen.

    De noche no hay cielo claro detrás de la rosa. La rosa (roja) y las hojas (verdes) tienen
    saturación, así que no se tocan.
    """
    hsv = np.asarray(im.convert("HSV"), dtype=np.float32) / 255
    sat, val = hsv[..., 1], hsv[..., 2]
    sky = np.clip((0.30 - sat) / 0.15, 0, 1) * np.clip((val - 0.45) / 0.2, 0, 1)
    keep = 1 - sky * (1 - level)
    arr = np.asarray(im.convert("RGB"), dtype=np.float32) * keep[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


class RandomDarkBackground:
    """Aumento "de noche": con probabilidad p oscurece al azar el margen alrededor de la rosa.

    De noche la luz del robot ilumina la rosa y el fondo queda oscuro; sin este aumento,
    RosaNet confunde inmaduras con óptimas cuando el fondo es oscuro (medido por el equipo del robot).
    """

    def __init__(self, p: float = 0.5):
        self.p = p

    def __call__(self, im: Image.Image) -> Image.Image:
        if random.random() >= self.p:
            return im
        level = random.uniform(0.0, 0.35)
        if random.random() < 0.5:
            im = darken_sky(im, level)
        return darken_margin(im, margin=random.uniform(0.06, 0.16), level=level, vignette=random.random() < 0.5)


def make_train_transform(dark_p: float = 0.0) -> transforms.Compose:
    """Transformación de entrenamiento. dark_p > 0 activa el aumento de fondo oscuro."""
    # El fondo se oscurece primero, cuando la rosa todavía está en el centro del recorte.
    steps = [RandomDarkBackground(dark_p)] if dark_p > 0 else []
    # Sin jitter de tono (hue): el color de los pétalos y sépalos es una pista de la etapa.
    steps += [
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.6, 1.0), ratio=(0.8, 1.25)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ]
    return transforms.Compose(steps)


train_transform = make_train_transform()

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])

# Pruebas de robustez al fondo (misma escala que el recorte original).
def black_margin(im: Image.Image) -> Image.Image:
    return darken_margin(im, fill=(0, 0, 0))


def grey_margin(im: Image.Image) -> Image.Image:
    return darken_margin(im, fill=(200, 200, 200))


def night_scene(im: Image.Image, rng: random.Random | None = None) -> Image.Image:
    """Escena completa "de noche con linterna": cielo/plástico oscuro y bordes en penumbra.

    Sin rng da la versión fija que se usa para medir; con rng varía la intensidad (aumento).
    """
    if rng is None:
        sky, edge, bright = 0.08, 0.25, 0.8
    else:
        sky, edge, bright = rng.uniform(0.03, 0.2), rng.uniform(0.1, 0.45), rng.uniform(0.6, 1.0)
    im = darken_margin(darken_sky(im, sky), margin=0.05, level=edge, vignette=True)
    arr = np.asarray(im, dtype=np.float32) * bright
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def night_like(im: Image.Image) -> Image.Image:
    """Aproximación de una foto nocturna con linterna: cielo y margen casi negros."""
    return darken_margin(darken_sky(im, 0.05), level=0.05, vignette=True)


dark_margin_eval_transform = transforms.Compose([black_margin, eval_transform])
grey_margin_eval_transform = transforms.Compose([grey_margin, eval_transform])
night_eval_transform = transforms.Compose([night_like, eval_transform])
BACKGROUND_TESTS = {
    "original": eval_transform,
    "margen_negro": dark_margin_eval_transform,
    "margen_gris": grey_margin_eval_transform,
    "noche": night_eval_transform,
}


def present_classes(root: Path) -> list[str]:
    """Clases (subcarpetas con al menos una imagen) en orden alfabético.

    Las categorías de la finca empiezan por 1_, 2_, 3_, así que quedan en el orden de STAGES.
    """
    return sorted(d.name for d in Path(root).iterdir() if d.is_dir() and any(d.iterdir()))


def list_samples(root: Path, classes: list[str]) -> list[tuple[Path, int]]:
    return [
        (p, idx)
        for idx, cls in enumerate(classes)
        if (Path(root) / cls).is_dir()
        for p in sorted((Path(root) / cls).iterdir())
        if p.suffix.lower() in IMAGE_EXTS
    ]


class StageFolder(Dataset):
    """Como ImageFolder, pero con la lista de clases fija (la del entrenamiento).

    Así val/test/fotos propias usan los mismos índices aunque les falte alguna etapa.
    """

    def __init__(self, root: Path | None, classes: list[str], transform=eval_transform, samples=None):
        self.classes, self.transform = classes, transform
        self.samples = samples if samples is not None else list_samples(root, classes)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, i):
        path, label = self.samples[i]
        with Image.open(path) as im:
            return self.transform(im.convert("RGB")), label

    def class_counts(self) -> list[int]:
        counts = [0] * len(self.classes)
        for _, label in self.samples:
            counts[label] += 1
        return counts
