"""Escala común de etapas de apertura y mapeo desde las clases de cada dataset.

Toda la red trabaja con esta escala. Cada dataset externo usa sus propios
nombres de clase; aquí se traducen a la escala común. Si un nombre de clase
no aparece en DATASET_CLASS_MAP, esa caja o imagen se ignora.
"""

# Orden = índice de clase de la red. No reordenar sin reentrenar.
STAGES = [
    "1_boton_cerrado",
    "2_apertura_inicial",
    "3_abierta",
    "4_senescente",
]

STAGE_LABELS = {
    "1_boton_cerrado": "Botón cerrado",
    "2_apertura_inicial": "Apertura inicial",
    "3_abierta": "Abierta",
    "4_senescente": "Senescente (pasada)",
}

# Nombre de clase en el dataset (en minúsculas) -> etapa común.
DATASET_CLASS_MAP = {
    # Roboflow "Rose" (Sanjay M) — universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv
    "bud": "1_boton_cerrado",
    "mid-bud": "2_apertura_inicial",
    "flower": "3_abierta",
    # Roboflow "食用玫瑰花期检测" — universe.roboflow.com/yolo-lmnpo/-zkger
    "1_bud": "1_boton_cerrado",
    "2_early_bloom": "2_apertura_inicial",
    "3_full_bloom": "3_abierta",
    "4_senescence": "4_senescente",
    # Mendeley "Rose Growth Stage" (53vyvz5yyk). OJO: el dataset no define sus
    # etapas; este mapeo es provisional hasta revisar las imágenes a mano.
    "early stage": "1_boton_cerrado",
    "middle stage": "2_apertura_inicial",
    "final stage": "3_abierta",
}

# Tips para que el trabajador aprenda a reconocer la etapa por sí mismo.
# "mirar": rasgos a observar. "diferencia": cómo distinguirla de la etapa vecina.
# Borrador: validar con alguien que trabaje en una finca.
STAGE_TIPS = {
    "1_boton_cerrado": {
        "mirar": [
            "Los sépalos (hojitas verdes que envuelven el botón) todavía cubren buena parte de los pétalos.",
            "El botón es firme y alargado; los pétalos están apretados entre sí.",
            "Casi no se ve separación entre los pétalos exteriores.",
        ],
        "diferencia": "Pasa a apertura inicial cuando los sépalos bajan y el primer pétalo exterior empieza a separarse del botón.",
    },
    "2_apertura_inicial": {
        "mirar": [
            "Los sépalos ya bajaron y apuntan hacia afuera o hacia el tallo.",
            "Uno o dos pétalos exteriores empiezan a soltarse, pero el centro sigue cerrado.",
            "El botón se ve más redondeado en la punta.",
        ],
        "diferencia": "Si el centro de la flor ya se ve abierto desde arriba, ya está en etapa abierta.",
    },
    "3_abierta": {
        "mirar": [
            "Varias capas de pétalos están separadas y se ve el centro de la flor.",
            "La forma es de copa abierta, ya no de botón.",
        ],
        "diferencia": "Si los pétalos se ven caídos, secos en el borde o pierden color, ya está senescente.",
    },
    "4_senescente": {
        "mirar": [
            "Pétalos caídos, arrugados o con bordes secos o marrones.",
            "Pérdida de color o manchas.",
        ],
        "diferencia": "Ya no sirve para exportación.",
    },
}


def map_class_name(name: str) -> str | None:
    """Traduce un nombre de clase de un dataset a la etapa común (o None)."""
    return DATASET_CLASS_MAP.get(name.strip().lower())
