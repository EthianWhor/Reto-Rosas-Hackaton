"""Convierte el material de la finca (PDF con círculos + fotos) en un dataset YOLO.

La finca envió fotos de escena y, por cada categoría, un PDF donde un círculo
naranja marca la rosa de esa categoría. Los círculos son figuras vectoriales:
aquí se leen sus coordenadas, se pasan al sistema de la foto original y se
escriben como cajas YOLO. Una misma foto puede tener cajas de varias clases.

Entrada (carpeta descomprimida de General.zip):
    01_Inmaduro_No_Cortar.pdf   + 01_Inmaduro_No_Cortar/<n>.jpeg
    02_Punto_Optimo_Corte.pdf   + 02_Punto_Optimo_Corte/<n>.jpeg
    03_Pasado_Sobreabierto.pdf  + 03_Pasado_Sobreabierto/<n>.jpeg
    04_Casos_Dificiles_Ruido.pdf + 04_Casos_Dificiles_Ruido/<n>.jpeg

Salida (mismo formato que un export YOLO de Roboflow, lo lee ml.prepare_data):
    <out>/data.yaml
    <out>/{train,valid,test}/images/<n>.jpeg
    <out>/{train,valid,test}/labels/<n>.txt
    <out>/dificiles.json   cajas de los casos difíciles (sin categoría)
    <out>/preview/<n>.jpg  fotos con las cajas dibujadas, para revisar

Las fotos que aparecen en "Casos difíciles" van completas a test: sirven para
medir robustez y no se entrenan con ellas.

Ejemplo:
    python -m ml.finca_labels --src descargas/General --out data/finca_yolo
"""

import argparse
import json
import random
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader
from pypdf.generic import ContentStream

# Carpeta/PDF de la finca -> nombre de clase (debe existir en stages.DATASET_CLASS_MAP).
CATEGORIES = {
    "01_Inmaduro_No_Cortar": "inmaduro",
    "02_Punto_Optimo_Corte": "optimo",
    "03_Pasado_Sobreabierto": "pasado",
}
DIFFICULT = "04_Casos_Dificiles_Ruido"
CLASS_NAMES = list(CATEGORIES.values())
CIRCLE_RGB = (0.914, 0.443, 0.196)  # naranja de los círculos
PREVIEW_COLORS = {"inmaduro": "deepskyblue", "optimo": "lime", "pasado": "red", "dificil": "yellow"}


def mat_mul(a, b):
    """Producto de matrices PDF [a b c d e f] (a se aplica primero)."""
    return [
        a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
        a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
        a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5],
    ]


def apply(m, x, y):
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


def invert(m):
    det = m[0] * m[3] - m[1] * m[2]
    a, b, c, d = m[3] / det, -m[1] / det, -m[2] / det, m[0] / det
    return [a, b, c, d, -(m[4] * a + m[5] * c), -(m[4] * b + m[5] * d)]


def is_circle_color(rgb, tol=0.05) -> bool:
    return len(rgb) == 3 and all(abs(float(v) - t) < tol for v, t in zip(rgb, CIRCLE_RGB))


def page_circles(page, reader) -> tuple[list[tuple[float, float, float, float]], tuple[int, int]]:
    """Devuelve las cajas de los círculos normalizadas a la foto (x0, y0, x1, y1 en 0..1)."""
    ops = ContentStream(page.get_contents(), reader).operations
    ctm, stack = [1, 0, 0, 1, 0, 0], []
    stroke_rgb, path, has_curve = (0, 0, 0), [], False
    image_matrix, image_size, shapes = None, None, []
    xobjects = page["/Resources"].get("/XObject", {})

    for operands, op in ops:
        op = op.decode() if isinstance(op, bytes) else op
        if op == "q":
            stack.append((ctm, stroke_rgb))
        elif op == "Q":
            ctm, stroke_rgb = stack.pop()
        elif op == "cm":
            ctm = mat_mul([float(v) for v in operands], ctm)
        elif op == "RG":
            stroke_rgb = tuple(float(v) for v in operands)
        elif op == "Do":
            xobj = xobjects[operands[0]].get_object()
            if xobj.get("/Subtype") == "/Image":
                image_matrix, image_size = ctm, (int(xobj["/Width"]), int(xobj["/Height"]))
        elif op in ("m", "l"):
            path.append(apply(ctm, float(operands[0]), float(operands[1])))
        elif op == "c":
            has_curve = True
            nums = [float(v) for v in operands]
            path.extend(apply(ctm, nums[i], nums[i + 1]) for i in range(0, 6, 2))
        elif op in ("S", "s", "f", "F", "f*", "B", "b", "n"):
            if op in ("S", "s") and has_curve and is_circle_color(stroke_rgb):
                shapes.append(path)
            path, has_curve = [], False

    if image_matrix is None:
        return [], (0, 0)
    inv = invert(image_matrix)
    boxes = []
    for pts in shapes:
        uv = [apply(inv, x, y) for x, y in pts]  # espacio de la imagen: (0,0) abajo-izquierda
        us, vs = [u for u, _ in uv], [1 - v for _, v in uv]  # v hacia abajo, como en la foto
        box = (max(0.0, min(us)), max(0.0, min(vs)), min(1.0, max(us)), min(1.0, max(vs)))
        if box[2] > box[0] and box[3] > box[1]:
            boxes.append(box)
    return boxes, image_size


def shrink(box, factor):
    """Reduce la caja hacia su centro: el círculo queda más grande que la rosa."""
    x0, y0, x1, y1 = box
    dx, dy = (x1 - x0) * factor / 2, (y1 - y0) * factor / 2
    return x0 + dx, y0 + dy, x1 - dx, y1 - dy


def read_pdf_boxes(pdf: Path) -> dict[str, list]:
    """{número de foto: [cajas]} a partir del número impreso en cada página."""
    reader, result = PdfReader(pdf), {}
    for page in reader.pages:
        match = re.search(r"\d+", page.extract_text() or "")
        if not match:
            print(f"  [aviso] {pdf.name}: página sin número, se ignora")
            continue
        boxes, _ = page_circles(page, reader)
        if not boxes:
            print(f"  [aviso] {pdf.name}: la foto {match.group()} no tiene círculo")
        result.setdefault(match.group(), []).extend(boxes)
    return result


def find_image(src: Path, number: str) -> Path | None:
    for folder in (*CATEGORIES, DIFFICULT):
        for ext in (".jpeg", ".jpg", ".png"):
            p = src / folder / f"{number}{ext}"
            if p.exists():
                return p
    return None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", type=Path, required=True, help="Carpeta General descomprimida")
    p.add_argument("--out", type=Path, default=Path("data/finca_yolo"))
    p.add_argument("--shrink", type=float, default=0.25, help="Fracción a recortar del círculo (0 = caja del círculo)")
    p.add_argument("--val", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    labels: dict[str, list[tuple[int, tuple]]] = {}
    for folder, cls in CATEGORIES.items():
        pdf = args.src / f"{folder}.pdf"
        for number, boxes in read_pdf_boxes(pdf).items():
            labels.setdefault(number, []).extend((CLASS_NAMES.index(cls), shrink(b, args.shrink)) for b in boxes)
    difficult = {n: [shrink(b, args.shrink) for b in boxes]
                 for n, boxes in read_pdf_boxes(args.src / f"{DIFFICULT}.pdf").items()}

    # Las fotos de casos difíciles van a test; el resto se reparte en train/valid.
    numbers = sorted(set(labels) | set(difficult), key=int)
    rest = [n for n in numbers if n not in difficult]
    random.Random(args.seed).shuffle(rest)
    n_val = max(1, int(len(rest) * args.val))
    split_of = {n: "test" for n in difficult} | {n: "valid" for n in rest[:n_val]} | {n: "train" for n in rest[n_val:]}

    if args.out.exists():
        shutil.rmtree(args.out)
    (args.out / "preview").mkdir(parents=True)
    counts = {s: [0] * len(CLASS_NAMES) for s in ("train", "valid", "test")}
    for number in numbers:
        img_path = find_image(args.src, number)
        if img_path is None:
            print(f"  [aviso] no se encontró la foto {number}")
            continue
        split = split_of[number]
        (args.out / split / "images").mkdir(parents=True, exist_ok=True)
        (args.out / split / "labels").mkdir(parents=True, exist_ok=True)
        shutil.copy(img_path, args.out / split / "images" / img_path.name)
        lines = []
        for cls, (x0, y0, x1, y1) in labels.get(number, []):
            lines.append(f"{cls} {(x0 + x1) / 2:.6f} {(y0 + y1) / 2:.6f} {x1 - x0:.6f} {y1 - y0:.6f}")
            counts[split][cls] += 1
        (args.out / split / "labels" / f"{img_path.stem}.txt").write_text("\n".join(lines))

        with Image.open(img_path) as im:
            im = im.convert("RGB")
            draw, (w, h) = ImageDraw.Draw(im), im.size
            tagged = [(CLASS_NAMES[c], b) for c, b in labels.get(number, [])] + [("dificil", b) for b in difficult.get(number, [])]
            for name, (x0, y0, x1, y1) in tagged:
                draw.rectangle((x0 * w, y0 * h, x1 * w, y1 * h), outline=PREVIEW_COLORS[name], width=max(3, w // 200))
                draw.text((x0 * w + 6, y0 * h + 4), name, fill=PREVIEW_COLORS[name])
            im.save(args.out / "preview" / f"{number}.jpg", quality=85)

    (args.out / "data.yaml").write_text(
        f"names: {CLASS_NAMES}\nnc: {len(CLASS_NAMES)}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n", encoding="utf-8")
    (args.out / "dificiles.json").write_text(json.dumps(difficult, indent=2), encoding="utf-8")

    print(f"Fotos: {len(numbers)} (test = casos difíciles: {len(difficult)})")
    for split, row in counts.items():
        print(f"  {split:5s} cajas " + "  ".join(f"{c}={n}" for c, n in zip(CLASS_NAMES, row)))
    print(f"Revisa las cajas en {args.out / 'preview'}")


if __name__ == "__main__":
    main()
