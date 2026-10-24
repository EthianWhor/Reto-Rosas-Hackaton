"""Cuerpo del robot real: AgiBot X2 Ultra con el SDK AimDK_X2 (ROS 2 Humble). Sección 14 del plan.

ESQUELETO. Cumple la misma interfaz que `sim_backend.py` (`cuerpo/interfaz.py`), así la ronda, la
percepción y el reporte no cambian al pasar al robot. Hay dos partes:

- **Ya hecho y probado sin robot** (funciones sueltas de abajo): pasar la nube del LiDAR a
  "obstáculo alto / bajo", la profundidad de milímetros a metros, la cámara de ROS a la convención
  de la percepción, la velocidad para ir a un punto y la lectura de la batería.
- **Falta probar en el robot** (métodos de `CuerpoReal`): cada uno dice qué tópico o servicio del
  SDK usa, con qué mensaje y en qué modo, y levanta NotImplementedError hasta que alguien lo pruebe
  con el robot delante. `python main.py --revisar` con `modo: real` muestra la lista.

Nombres de tópicos y servicios sacados de la documentación oficial AimDK_X2 1.1.0
(https://x2-aimdk.agibot.com/en/latest/). Pueden cambiar con la versión del firmware: confirmar
con la que trae nuestro robot.

Lo que la documentación dice que cambia el plan (detalle en la sección 14):
- La cámara RGB-D de la cabeza da **1280 × 720** (no 1920 × 1080 como en la simulación).
- En el X2 Ultra original **la cabeza solo gira (yaw)**: la inclinación la hace toda la cintura
  (±0,31 rad). En el "X2 Ultra (nueva versión)" la cabeza también inclina.
- La cabeza se manda en el modo HEAD_ONLY, que no camina. La cintura solo tiene el control de bajo
  nivel (sin protección por tiempo). Hay que preguntarle a AgiBot cómo mover la cintura con el
  robot de pie y en equilibrio.
- El robot no trae un foco en la cabeza: para la acción física hay que montar uno (las luces del SDK
  son la tira LED del pecho).
- La posición del robot sale del módulo de SLAM / navegación, que es opcional (se pide a soporte).
"""

import math

import numpy as np

from cuerpo.interfaz import Captura, Cuerpo

# --- Tópicos y servicios del SDK (AimDK_X2 1.1.0) -------------------------------------------------
SRV_FUENTE = "/aimdk_5Fmsgs/srv/SetMcInputSource"      # registrar nuestra fuente de comandos
SRV_MODO = "/aimdk_5Fmsgs/srv/SetMcAction"             # cambiar de modo (STAND_DEFAULT, HEAD_ONLY, ...)
TOPICO_CAMINAR = "/aima/mc/locomotion/velocity"        # McLocomotionVelocity, 50 Hz, se frena a los 200 ms
TOPICO_CABEZA = "/mc/upper_body_command"               # UpperBodyCommandArray.head_pos [yaw, pitch], modo HEAD_ONLY
TOPICO_CINTURA = "/aima/hal/joint/waist/command"       # JointCommandArray (bajo nivel, sin protección)
TOPICO_ARTICULACIONES = "/aima/hal/joint/{grupo}/state"   # JointStateArray, grupo = head | waist | arm | leg
TOPICO_RGB = "/aima/hal/sensor/rgbd_head_front/rgb_image"           # Image 1280 × 720 RGB8, 30 Hz
TOPICO_PROFUNDIDAD = "/aima/hal/sensor/rgbd_head_front/depth_image"  # Image 1280 × 720 16UC1 (mm)
TOPICO_INFO_CAMARA = "/aima/hal/sensor/rgbd_head_front/rgb_camera_info"
TOPICO_LIDAR = "/aima/hal/sensor/lidar_chest_front/lidar_pointcloud"  # PointCloud2, 10 Hz
TOPICO_BATERIA = "/aima/hal/pmu/state"                 # PmuState, 1 Hz
SRV_LED = "/aimdk_5Fmsgs/srv/SetPmuLed"                # tira LED del pecho (tarda ~5 s en responder)

FUENTE = "sdk_rosas"           # nombre de nuestra fuente de comandos (el SDK pide el prefijo sdk_)
PRIORIDAD_FUENTE = 40          # 40–100 le gana a la app del celular (60 no); el control remoto (80) siempre gana
FRECUENCIA_CAMINAR_HZ = 50
VELOCIDAD_MIN_ARRANQUE = 0.1   # m/s: con menos el robot no arranca (dato aproximado del SDK)
GIRO_MAX = 0.6                 # rad/s, igual que en la simulación
ANCHO_SENSOR_M = 0.25          # mitad del ancho que se revisa adelante (los rayos de la simulación van a ±0,25 m)
INICIO_SENSOR_M = 0.25         # lo que está más cerca que esto es el propio robot
ALTO_MAX_SENSOR_M = 1.05       # más arriba no estorba (ramas, alambres a 1,2 m)
PISO_M = 0.01                  # menos que esto es el piso (ruido del LiDAR)


# --- Funciones ya hechas (no necesitan el robot) -------------------------------------------------

def obstaculos_en_nube(puntos: np.ndarray, distancia_max: float, alto_obstaculo_m: float
                       ) -> tuple[float | None, float | None]:
    """(alto, bajo) más cercanos adelante, igual que `obstaculos_adelante` de la simulación.

    `puntos`: N × 3 en el marco del robot (x adelante, y a la izquierda, z hacia arriba desde el piso),
    ya transformados desde el marco del LiDAR del pecho. Se mira un pasillo de ±ANCHO_SENSOR_M.
    """
    if puntos is None or not len(puntos):
        return None, None
    x, y, z = puntos[:, 0], puntos[:, 1], puntos[:, 2]
    adelante = (x >= INICIO_SENSOR_M) & (x <= distancia_max) & (np.abs(y) <= ANCHO_SENSOR_M)
    alto = adelante & (z > alto_obstaculo_m) & (z <= ALTO_MAX_SENSOR_M)
    bajo = adelante & (z > PISO_M) & (z <= alto_obstaculo_m)
    return (float(x[alto].min()) if alto.any() else None,
            float(x[bajo].min()) if bajo.any() else None)


def profundidad_a_metros(imagen_mm: np.ndarray) -> np.ndarray:
    """La profundidad del X2 viene en milímetros (uint16). La percepción usa metros; 0 = sin dato."""
    return imagen_mm.astype(np.float32) / 1000.0


def optica_a_percepcion(rotacion_optica: np.ndarray) -> np.ndarray:
    """Ejes de la cámara en el mundo, de la convención de ROS a la de la percepción.

    ROS (marco óptico): mira hacia +z, x a la derecha, y hacia abajo.
    Percepción (como MuJoCo): mira hacia −z, x a la derecha, y hacia arriba. Se dan vuelta y y z.
    """
    return np.asarray(rotacion_optica, dtype=float) @ np.diag([1.0, -1.0, -1.0])


def fovy_desde_info(alto_px: int, fy: float) -> float:
    """Campo de visión vertical (grados) desde camera_info (K[4] = fy). Mejor que el del config."""
    return math.degrees(2 * math.atan(alto_px / (2 * fy)))


def velocidad_hacia(pose: tuple[float, float, float], meta: tuple[float, float], velocidad: float
                    ) -> tuple[float, float]:
    """(adelante m/s, giro rad/s) para ir de `pose` (x, y, rumbo) a `meta`, como en la simulación:
    primero gira mirando hacia donde va y después avanza derecho, corrigiendo el rumbo de a poco.
    El SDK es de lazo abierto: esto se llama en cada vuelta (50 Hz) con la pose medida."""
    x, y, rumbo = pose
    dx, dy = meta[0] - x, meta[1] - y
    distancia = math.hypot(dx, dy)
    if distancia < 0.02:
        return 0.0, 0.0
    error = (math.atan2(dy, dx) - rumbo + math.pi) % (2 * math.pi) - math.pi
    giro = max(-GIRO_MAX, min(GIRO_MAX, 1.5 * error))
    if abs(error) > 0.3:                       # muy torcido: gira en el lugar
        return 0.0, giro
    adelante = max(VELOCIDAD_MIN_ARRANQUE, min(velocidad, 0.8 * distancia))
    return adelante, giro


def bateria_pct(estado_pmu) -> float:
    """Porcentaje de batería del mensaje PmuState."""
    return float(estado_pmu.battery_remaining_capacity_percentage)


def cargando(estado_pmu) -> bool:
    """Bit 0 de bms_status_bits = cargando (útil para saber que llegó bien a la base)."""
    return bool(int(estado_pmu.bms_status_bits) & 1)


# --- El cuerpo real (falta probar en el robot) ----------------------------------------------------

PENDIENTES = [
    ("pararse", "registrar la fuente sdk_rosas (SetMcInputSource) y pasar a STAND_DEFAULT (SetMcAction)"),
    ("posicion / rumbo", "pose del robot: módulo SLAM/navegación de AgiBot (opcional, pedir a soporte) "
                         "o odometría + marcas AprilTag en las camas"),
    ("ir_a / orientar", "publicar McLocomotionVelocity a 50 Hz con velocidad_hacia() y la pose medida"),
    ("obstaculos_adelante", "leer el PointCloud2 del LiDAR del pecho, pasarlo al marco del robot (TF) "
                            "y usar obstaculos_en_nube()"),
    ("posar", "cabeza por /mc/upper_body_command (modo HEAD_ONLY); cintura: preguntar a AgiBot "
              "(solo hay control de bajo nivel)"),
    ("foto", "RGB + profundidad de la cámara RGB-D de la cabeza y su pose en el mundo (TF + pose del robot)"),
    ("senalar", "montar un foco en la cabeza (el SDK solo prende la tira LED del pecho)"),
    ("nivel_bateria", "suscribirse a /aima/hal/pmu/state y usar bateria_pct()"),
]


def pendientes() -> list[tuple[str, str]]:
    return list(PENDIENTES)


class CuerpoReal(Cuerpo):
    """El X2 Ultra de verdad. Necesita ROS 2 Humble y el paquete `aimdk_msgs` del SDK (en el robot)."""

    def __init__(self, cfg: dict):
        try:
            import rclpy                       # noqa: F401  (solo existe en el robot o con ROS 2 instalado)
            import aimdk_msgs                  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "El modo real necesita ROS 2 Humble y el paquete aimdk_msgs del SDK AimDK_X2 "
                "(se corre en el robot). Ver la sección 14 del plan.") from e
        self.cfg = cfg
        # Aquí: rclpy.init(), un nodo, los clientes de SRV_FUENTE / SRV_MODO / SRV_LED, los
        # publicadores de TOPICO_CAMINAR / TOPICO_CABEZA y las suscripciones a cámara, LiDAR,
        # articulaciones y batería (QoS BEST_EFFORT, como pide el SDK), girando en otro hilo.

    @staticmethod
    def _falta(que: str):
        raise NotImplementedError(f"real_backend: falta probar en el robot: {que} (sección 14 del plan)")

    def pararse(self) -> None:
        """1. SetMcInputSource: action ADD (1001), name FUENTE, priority PRIORIDAD_FUENTE, timeout 1000 ms.
        2. SetMcAction: action_desc "STAND_DEFAULT" (de pie con equilibrio; camina con el mismo modo).
        Revisar response.header.code == 0 en los dos."""
        self._falta("pararse")

    def posicion(self) -> tuple[float, float]:
        """x, y en el plano del invernadero (el mismo de `navegacion/plano.py`). El SDK de caminar es
        de lazo abierto: la pose sale de la localización de SLAM o de odometría + marcas AprilTag."""
        self._falta("posicion")

    def rumbo(self) -> float:
        self._falta("rumbo")

    def ir_a(self, x: float, y: float, velocidad: float | None = None) -> None:
        """Bucle a FRECUENCIA_CAMINAR_HZ: pose medida → velocidad_hacia() → McLocomotionVelocity
        (source = FUENTE, forward_velocity, angular_velocity; lateral 0). Al llegar, publicar ceros.
        Si se dejan de mandar comandos 200 ms, el robot se frena solo."""
        self._falta("ir_a")

    def orientar(self, rumbo: float) -> None:
        """Igual que ir_a pero solo angular_velocity hasta que el error de rumbo sea < 0,03 rad."""
        self._falta("orientar")

    def obstaculos_adelante(self, distancia_max: float) -> tuple[float | None, float | None]:
        """Última nube de TOPICO_LIDAR → puntos (sensor_msgs_py.point_cloud2.read_points_numpy) →
        marco del robot con la TF del LiDAR del pecho → obstaculos_en_nube(puntos, distancia_max,
        cfg["recorrido"]["alto_obstaculo_m"])."""
        self._falta("obstaculos_adelante")

    def esperar(self, segundos: float) -> None:
        """Quieto: dejar de mandar velocidad (o mandar ceros) y dormir `segundos`."""
        self._falta("esperar")

    def posar(self, angulos: dict) -> dict:
        """Cabeza: SetMcAction "HEAD_ONLY" y publicar head_pos = [head_yaw, head_pitch] a 50 Hz hasta
        llegar (en el X2 Ultra original head_pitch no se mueve). Cintura: TOPICO_CINTURA con
        waist_yaw y waist_pitch (bajo nivel, sin protección: confirmar con AgiBot que se puede con el
        robot de pie). Devolver los ángulos leídos de TOPICO_ARTICULACIONES. Antes de caminar,
        volver a "STAND_DEFAULT"."""
        self._falta("posar")

    def foto(self) -> Captura:
        """RGB (TOPICO_RGB) y profundidad (TOPICO_PROFUNDIDAD → profundidad_a_metros) del mismo
        instante; fovy_desde_info() con camera_info; cam_pos y cam_mat desde la TF de la cámara y la
        pose del robot, con optica_a_percepcion(). Confirmar si la profundidad viene alineada al RGB."""
        self._falta("foto")

    def senalar(self, punto: tuple[float, float, float], segundos: float) -> bool:
        """Apuntar como en la simulación (posar + corregir con la pose de la cámara) y prender un foco
        montado en la cabeza. Mientras no haya foco, se puede usar la tira LED del pecho (SRV_LED,
        led_strip_mode 2 = parpadeo) para avisar que hay una rosa para cortar."""
        self._falta("senalar")

    def nivel_bateria(self) -> float | None:
        """bateria_pct() del último PmuState de TOPICO_BATERIA."""
        self._falta("nivel_bateria")

    def cerrar(self) -> None:
        """Publicar velocidad cero, borrar la fuente (SetMcInputSource DELETE) y rclpy.shutdown()."""
