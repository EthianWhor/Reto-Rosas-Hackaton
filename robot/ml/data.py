"""Carga de imágenes por etapa y transformaciones compartidas."""

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from ml.model import IMAGE_SIZE
from ml.stages import STAGES

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)

# Sin jitter de tono (hue): el color de los pétalos y sépalos es una pista de la etapa.
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.6, 1.0), ratio=(0.8, 1.25)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.15),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])


def present_classes(root: Path) -> list[str]:
    """Etapas (en el orden de STAGES) que tienen al menos una imagen en root."""
    return [s for s in STAGES if (root / s).is_dir() and any((root / s).iterdir())]


class StageFolder(Dataset):
    """Como ImageFolder, pero con la lista de clases fija (la del entrenamiento).

    Así val/test/fotos propias usan los mismos índices aunque les falte alguna etapa.
    """

    def __init__(self, root: Path, classes: list[str], transform=eval_transform):
        self.classes, self.transform = classes, transform
        self.samples = [
            (p, idx)
            for idx, cls in enumerate(classes)
            if (Path(root) / cls).is_dir()
            for p in sorted((Path(root) / cls).iterdir())
            if p.suffix.lower() in IMAGE_EXTS
        ]

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
