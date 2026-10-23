"""RosaNet: CNN propia para clasificar la etapa de apertura de una rosa.

Arquitectura (entrada 3x224x224):
    Stem: conv3x3 con stride 2 (224 -> 112), 32 canales
    4 bloques convolucionales [conv3x3-BN-ReLU] x2 + MaxPool
        canales 32 -> 64 -> 128 -> 256, resolución 112 -> 56 -> 28 -> 14 -> 7
    Global Average Pooling -> Dropout -> capa lineal (una salida por etapa)

Unos 1,2 M de parámetros y ~1,5 GFLOPs por imagen: suficientemente pequeña
para entrenar desde cero con pocos miles de imágenes en una GPU de 4 GB, y
para correr en una Raspberry Pi. El último bloque convolucional
(`features[-1]`) es el que usa Grad-CAM para mostrar en qué parte de la rosa
se fijó la red.
"""

import torch
from torch import nn

IMAGE_SIZE = 224


def conv_block(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


class RosaNet(nn.Module):
    def __init__(self, num_classes: int, channels=(32, 64, 128, 256), dropout: float = 0.3):
        super().__init__()
        # El stem reduce la resolución a la mitad antes de los bloques: las
        # convoluciones a 224x224 completos eran casi la mitad del cómputo.
        self.stem = nn.Sequential(
            nn.Conv2d(3, channels[0], kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(channels[0]),
            nn.ReLU(inplace=True),
        )
        blocks, in_ch = [], channels[0]
        for out_ch in channels:
            blocks.append(conv_block(in_ch, out_ch))
            in_ch = out_ch
        self.features = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(dropout), nn.Linear(in_ch, num_classes))
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.pool(self.features(self.stem(x))))


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def save_checkpoint(path, model: RosaNet, classes: list[str], extra: dict | None = None) -> None:
    torch.save({"state_dict": model.state_dict(), "classes": classes, "image_size": IMAGE_SIZE, **(extra or {})}, path)


def load_checkpoint(path, device="cpu") -> tuple[RosaNet, list[str]]:
    ckpt = torch.load(path, map_location=device, weights_only=False)
    model = RosaNet(num_classes=len(ckpt["classes"]))
    model.load_state_dict(ckpt["state_dict"])
    return model.to(device).eval(), ckpt["classes"]
