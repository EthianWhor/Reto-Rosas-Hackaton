"""Prueba de humo de todo el pipeline con imágenes sintéticas (sin datasets reales)."""

import random

import pytest
import torch
import yaml
from PIL import Image, ImageDraw

from ml import finca_labels, prepare_data
from ml.data import StageFolder, present_classes
from ml.model import IMAGE_SIZE, RosaNet, load_checkpoint, save_checkpoint
from ml.predict import RosePredictor
from ml.stages import STAGES, map_class_name


def make_yolo_dataset(root, names, per_split=4):
    """Export estilo Roboflow: data.yaml + {train,valid,test}/{images,labels}."""
    (root).mkdir(parents=True)
    (root / "data.yaml").write_text(yaml.safe_dump({"names": names, "nc": len(names)}))
    rng = random.Random(0)
    for split in ("train", "valid", "test"):
        (root / split / "images").mkdir(parents=True)
        (root / split / "labels").mkdir(parents=True)
        for i in range(per_split):
            im = Image.new("RGB", (320, 240), (40, 90, 40))
            ImageDraw.Draw(im).ellipse((100, 60, 220, 180), fill=(200, 30, 60))
            im.save(root / split / "images" / f"img{i}.jpg")
            cls = rng.randrange(len(names))
            lines = [f"{cls} 0.5 0.5 0.4 0.5", "0 0.01 0.01 0.01 0.01"]  # la 2ª caja es diminuta
            (root / split / "labels" / f"img{i}.txt").write_text("\n".join(lines))


def test_map_class_name_is_case_insensitive():
    assert map_class_name("Optimo") == "2_optimo"
    assert map_class_name("Mid-Bud") == "2_optimo"
    assert map_class_name("4_Senescence") == "3_pasado"
    assert map_class_name("desconocida") is None


def test_public_scale_keeps_its_own_classes():
    assert map_class_name("Mid-Bud", "publica") == "b_abriendo"
    assert map_class_name("optimo", "publica") is None  # la finca no entra al preentrenamiento


def test_calibration_folds_keep_each_photo_together():
    from pathlib import Path

    from ml import calibrate

    samples = [(Path(f"finca_yolo_{photo}_{i}.jpg"), label)
               for photo, label, n in [(26, 0, 3), (8, 1, 2), (13, 2, 1), (5, 0, 1), (9, 1, 1)] for i in range(n)]
    folds = calibrate.make_folds(samples, k=3, seed=0)
    assert sorted(s for f in folds for s in f) == sorted(samples)
    for fold in folds:
        photos = {calibrate.photo_of(p) for p, _ in fold}
        for other in folds:
            if other is not fold:
                assert photos.isdisjoint({calibrate.photo_of(p) for p, _ in other})


def test_build_model_loads_pretrained_and_freezes(tmp_path):
    from ml.train import build_model

    pre = RosaNet(num_classes=4)
    save_checkpoint(tmp_path / "pre.pt", pre, ["a", "b", "c", "d"])
    model = build_model(3, tmp_path / "pre.pt", freeze=2)
    assert torch.equal(model.features[3][0].weight, pre.features[3][0].weight)
    assert model.classifier[-1].out_features == 3
    assert not any(p.requires_grad for p in model.features[1].parameters())
    assert all(p.requires_grad for p in model.features[2].parameters())


def test_finca_matrix_math_maps_pdf_points_to_photo():
    # Foto dibujada en la página con escala 200x300 y origen en (50, 100).
    image_matrix = [200, 0, 0, 300, 50, 100]
    inv = finca_labels.invert(image_matrix)
    u, v = finca_labels.apply(inv, 150, 250)  # centro de la foto en la página
    assert abs(u - 0.5) < 1e-9 and abs(v - 0.5) < 1e-9
    scaled = finca_labels.mat_mul([2, 0, 0, 2, 0, 0], [1, 0, 0, 1, 10, 20])  # escala y luego traslada
    assert finca_labels.apply(scaled, 1, 1) == (12, 22)
    assert finca_labels.shrink((0.2, 0.2, 0.6, 0.6), 0.5) == pytest.approx((0.3, 0.3, 0.5, 0.5))


def test_label_to_box_accepts_box_and_polygon():
    assert prepare_data.label_to_box([0.5, 0.5, 0.2, 0.4], 100, 100) == (40, 30, 60, 70)
    assert prepare_data.label_to_box([0.1, 0.2, 0.3, 0.2, 0.3, 0.6], 100, 100) == (10, 20, 30, 60)


def test_is_grayscale():
    assert prepare_data.is_grayscale(Image.new("RGB", (100, 100), (90, 90, 90)))
    assert not prepare_data.is_grayscale(Image.new("RGB", (100, 100), (200, 30, 60)))


def test_crop_yolo_dataset(tmp_path):
    make_yolo_dataset(tmp_path / "rose", ["bud", "mid-bud", "flower", "leaf"])
    counts = {"train": 0, "val": 0, "test": 0, "ignored": 0, "too_small": 0, "grayscale": 0}
    prepare_data.crop_yolo_dataset(tmp_path / "rose", tmp_path / "out", 0.1, 32, counts)
    assert counts["too_small"] == 12  # una caja diminuta por imagen
    assert counts["train"] + counts["val"] + counts["test"] + counts["ignored"] == 12
    for split in ("train", "val", "test"):
        assert (tmp_path / "out" / split).is_dir()
    crops = list((tmp_path / "out").rglob("*.jpg"))
    assert crops and all(c.parent.name in STAGES for c in crops)


def test_prepare_detector_merges_into_single_class(tmp_path):
    from ml import prepare_detector

    assert prepare_detector.convert_labels(["2 0.5 0.5 0.2 0.2", "3 0.1 0.1 0.1 0.1"],
                                           ["bud", "mid-bud", "flower", "leaf"]) == ["0 0.500000 0.500000 0.200000 0.200000"]
    make_yolo_dataset(tmp_path / "rose", ["bud", "mid-bud", "flower"])
    counts = {s: [0, 0] for s in ("train", "valid", "test")}
    prepare_detector.merge(tmp_path / "rose", tmp_path / "det", counts)
    assert counts["train"][0] == 4 and counts["train"][1] == 8  # 2 cajas por imagen
    labels = (tmp_path / "det" / "train" / "labels").glob("*.txt")
    assert all(line.startswith("0 ") for f in labels for line in f.read_text().splitlines())


def test_bundled_models_follow_the_robot_contract():
    """Los modelos de modelos/ cargan y devuelven lo que espera el código del robot."""
    import numpy as np
    from pathlib import Path

    from ml.detect import RoseDetector

    if not Path("modelos/detector_rosas.pt").exists():
        pytest.skip("faltan los modelos en robot/modelos")
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    image[200:260, 300:350] = (150, 20, 40)
    detections = RoseDetector("modelos/detector_rosas.pt", device="cpu").detect(image)
    assert isinstance(detections, list)
    assert all(set(d) == {"bbox", "confianza"} and len(d["bbox"]) == 4 for d in detections)
    pred = RosePredictor("modelos/rosanet.pt", device="cpu").predict(Image.fromarray(image[180:280, 280:370]))
    assert pred["etapa"] in STAGES and set(pred["probabilidades"]) == set(STAGES)


def test_model_output_shape():
    model = RosaNet(num_classes=4)
    out = model(torch.randn(2, 3, IMAGE_SIZE, IMAGE_SIZE))
    assert out.shape == (2, 4)


def test_checkpoint_roundtrip_and_predict(tmp_path):
    classes = STAGES[:3]
    model = RosaNet(num_classes=len(classes))
    save_checkpoint(tmp_path / "m.pt", model, classes)
    loaded, loaded_classes = load_checkpoint(tmp_path / "m.pt")
    assert loaded_classes == classes

    predictor = RosePredictor(tmp_path / "m.pt", device="cpu")
    image = Image.new("RGB", (300, 300), (200, 30, 60))
    result = predictor.predict(image)
    assert result["etapa"] in classes
    assert abs(sum(result["probabilidades"].values()) - 1) < 0.01
    assert "mirar" in result["tips"]
    cam = predictor.gradcam(image)
    assert cam.size == image.size


def test_stage_folder_keeps_training_indices(tmp_path):
    for stage in (STAGES[0], STAGES[2]):
        (tmp_path / stage).mkdir()
        Image.new("RGB", (50, 50)).save(tmp_path / stage / "a.jpg")
    assert present_classes(tmp_path) == [STAGES[0], STAGES[2]]
    ds = StageFolder(tmp_path, STAGES[:3])
    assert sorted(label for _, label in ds.samples) == [0, 2]
    assert ds.class_counts() == [1, 0, 1]


@pytest.mark.slow
def test_train_cli_end_to_end(tmp_path, monkeypatch):
    from ml import train

    make_yolo_dataset(tmp_path / "rose", ["bud", "mid-bud", "flower"], per_split=12)
    counts = {"train": 0, "val": 0, "test": 0, "ignored": 0, "too_small": 0, "grayscale": 0}
    prepare_data.crop_yolo_dataset(tmp_path / "rose", tmp_path / "stages", 0.1, 32, counts)
    out = tmp_path / "run"
    monkeypatch.setattr("sys.argv", ["train", "--data", str(tmp_path / "stages"), "--out", str(out),
                                     "--epochs", "2", "--batch-size", "4", "--workers", "0"])
    train.main()
    assert (out / "best.pt").exists()
    assert (out / "history.csv").read_text().count("\n") >= 2
