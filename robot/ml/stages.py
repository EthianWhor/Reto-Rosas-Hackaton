"""Clases de la red (las 3 categorías del proceso estándar de la finca) y mapeo
desde las clases de cada dataset.

Toda la red trabaja con estas 3 categorías. Cada dataset usa sus propios
nombres de clase; aquí se traducen. Si un nombre de clase no aparece en
DATASET_CLASS_MAP, esa caja o imagen se ignora.

Criterio de la finca (variedad Freedom, ver CONTEXTO.md sección 2.0.1):
el punto de corte es el "punto 3"; cortar en "punto 2" (cerrado) es la
falla más común.
"""

# Orden = índice de clase de la red. No reordenar sin reentrenar.
STAGES = [
    "1_inmaduro",
    "2_optimo",
    "3_pasado",
]

STAGE_LABELS = {
    "1_inmaduro": "Inmaduro – no cortar",
    "2_optimo": "Punto óptimo de corte",
    "3_pasado": "Pasado / sobreabierto",
}

# Nombre de clase en el dataset (en minúsculas) -> categoría de la finca.
DATASET_CLASS_MAP = {
    # Finca (ml.finca_labels) — verdad de terreno.
    "inmaduro": "1_inmaduro",
    "optimo": "2_optimo",
    "pasado": "3_pasado",
    # Datasets públicos (rosas de jardín, otras variedades): solo apoyo.
    # Roboflow "Rose" (Sanjay M) — universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv
    "bud": "1_inmaduro",
    "mid-bud": "2_optimo",  # dudoso: verificar contra las fotos de la finca
    "flower": "3_pasado",
    # Roboflow "食用玫瑰花期检测" — universe.roboflow.com/yolo-lmnpo/-zkger
    "1_bud": "1_inmaduro",
    "2_early_bloom": "2_optimo",  # dudoso: verificar contra las fotos de la finca
    "3_full_bloom": "3_pasado",
    "4_senescence": "3_pasado",
    # Mendeley "Rose Growth Stage" (53vyvz5yyk). OJO: el dataset no define sus
    # etapas; este mapeo es provisional hasta revisar las imágenes a mano.
    "early stage": "1_inmaduro",
    "middle stage": "2_optimo",
    "final stage": "3_pasado",
}

# Tips para que el operario aprenda a reconocer la categoría por sí mismo.
# Basados en la "Información técnica" de la finca (variedad Freedom).
# "mirar": rasgos a observar. "diferencia": cómo distinguirla de la categoría vecina.
STAGE_TIPS = {
    "1_inmaduro": {
        "mirar": [
            "La cabeza (botón floral) se ve más pequeña.",
            "El rojo es más oscuro.",
            "Los sépalos están pegados a los pétalos.",
        ],
        "diferencia": "Cortarla aquí (punto 2, cerrado) es la falla más común. Espera a que el caracol "
                      "se defina mostrando el centro y el rojo se vuelva vivo e intenso.",
    },
    "2_optimo": {
        "mirar": [
            "El caracol está definido y se ve el centro.",
            "El color de los pétalos es vivo e intenso.",
            "La flor presenta un patrón de copa.",
        ],
        "diferencia": "Es el punto 3, el punto de corte. Si la cabeza se ve pequeña, el rojo oscuro y los "
                      "sépalos pegados, todavía está inmadura.",
    },
    "3_pasado": {
        "mirar": [
            "La flor ya está sobreabierta: pasó del punto de corte.",
        ],
        "diferencia": "Ya no está en punto óptimo; se debió cortar antes.",
    },
}


def map_class_name(name: str) -> str | None:
    """Traduce un nombre de clase de un dataset a la categoría de la finca (o None)."""
    return DATASET_CLASS_MAP.get(name.strip().lower())
