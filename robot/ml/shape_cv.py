"""Compara con validación cruzada: rasgos de forma solos, RosaNet sola y las dos combinadas.

Usa los mismos folds (por foto) y las mismas semillas que ml.calibrate, y los
modelos RosaNet que calibrate ya guardó por fold (<runs>/<prefijo><semilla>/foldN/best.pt),
así cada método se mide con exactamente las mismas rosas de la finca. Mide de
día (recorte original) y "de noche" (data.night_like).

Ejemplo:
    python -m ml.shape_cv --runs runs/sweep_oscuro --prefijo o0.5- --semillas 1 2 3
"""

import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.calibrate import make_folds, public_pasado
from ml.data import eval_transform, list_samples, night_like
from ml.evaluate import metrics_from_confusion
from ml.model import load_checkpoint
from ml.shape import shape_features
from ml.stages import STAGES

CONDITIONS = {"dia": lambda im: im, "noche": night_like}
METHODS = ("forma", "rosanet", "promedio", "producto")


def features(paths, transform) -> np.ndarray:
    return np.array([shape_features(transform(Image.open(p).convert("RGB"))) for p in paths])


def impute(train: np.ndarray, test: np.ndarray):
    med = np.nanmedian(train, axis=0)
    fix = lambda x: np.where(np.isnan(x), med, x)
    return fix(train), fix(test)


@torch.no_grad()
def rosanet_probs(model, paths, transform, device) -> np.ndarray:
    x = torch.stack([eval_transform(transform(Image.open(p).convert("RGB"))) for p in paths]).to(device)
    return torch.softmax(model(x), dim=1).cpu().numpy()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--finca", type=Path, default=Path("data/finca_stages"))
    p.add_argument("--publico", type=Path, default=Path("data/pre"))
    p.add_argument("--runs", type=Path, default=Path("runs/sweep_oscuro"))
    p.add_argument("--prefijo", default="o0.5-")
    p.add_argument("--semillas", type=int, nargs="+", default=[1, 2, 3])
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--peso-forma", type=float, default=0.5, help="Peso de la forma en el promedio")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pool = list_samples(args.finca / "train", STAGES) + list_samples(args.finca / "val", STAGES)
    optimo = STAGES.index("2_optimo")
    summary = {(m, c): [] for m in METHODS for c in CONDITIONS}

    for seed in args.semillas:
        extra = public_pasado(args.publico, 40, seed)
        folds = make_folds(pool, args.k, seed)
        conf = {(m, c): np.zeros((3, 3), dtype=int) for m in METHODS for c in CONDITIONS}
        for i, fold in enumerate(folds):
            train = [s for j, f in enumerate(folds) if j != i for s in f] + extra
            y_train = np.array([l for _, l in train])
            y_test = np.array([l for _, l in fold])
            clf = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", C=0.5, max_iter=2000))
            f_train = features([p for p, _ in train], CONDITIONS["dia"])
            model, _ = load_checkpoint(args.runs / f"{args.prefijo}{seed}" / f"fold{i + 1}" / "best.pt", device)
            for cond, transform in CONDITIONS.items():
                f_tr, f_te = impute(f_train, features([p for p, _ in fold], transform))
                clf.fit(f_tr, y_train)
                p_shape = np.zeros((len(fold), 3))
                p_shape[:, clf.classes_] = clf.predict_proba(f_te)
                p_net = rosanet_probs(model, [p for p, _ in fold], transform, device)
                w = args.peso_forma
                preds = {
                    "forma": p_shape.argmax(1),
                    "rosanet": p_net.argmax(1),
                    "promedio": (w * p_shape + (1 - w) * p_net).argmax(1),
                    "producto": (np.log(p_shape + 1e-6) * w + np.log(p_net + 1e-6) * (1 - w)).argmax(1),
                }
                for m, pr in preds.items():
                    for t, q in zip(y_test, pr):
                        conf[(m, cond)][t, q] += 1
        for key, c in conf.items():
            met = metrics_from_confusion(c.tolist(), STAGES)
            summary[key].append((met["accuracy"], met["per_class"]["2_optimo"]["recall"], c[0, optimo], c[0].sum()))

    print(f"Semillas {args.semillas} (promedio) | inmaduras->óptimo sobre {summary[(METHODS[0], 'dia')][0][3]}")
    for cond in CONDITIONS:
        for m in METHODS:
            vals = np.array([v[:3] for v in summary[(m, cond)]], dtype=float)
            acc, rec, err = vals.mean(0)
            print(f"{cond:5s} {m:9s}: exactitud {acc:.3f} | recall óptimo {rec:.3f} | inmaduras->óptimo {err:.1f}")


if __name__ == "__main__":
    main()
