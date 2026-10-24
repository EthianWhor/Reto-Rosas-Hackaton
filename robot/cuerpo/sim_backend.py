"""Cuerpo del robot en MuJoCo.

Camina como en referencias/jardin_10_plantas.py: un punto guía (mocap) sostiene
la pelvis y las piernas se animan. Para girar se rota el punto guía. No tiene equilibrio real; eso lo hará el
controlador oficial de AgiBot en el robot real. Los motores siguen una pose
objetivo con un control PD.
"""

import math
import time

import mujoco
import numpy as np

from cuerpo.interfaz import Captura, Cuerpo
from cuerpo.posturas import CINTURA_YAW, NEUTRA, limites_inclinacion, repartir_inclinacion
from sim.escena_invernadero import ALTURA_PELVIS, CAMARA, PUNTERO, Escena, resolucion
from sim.rosas import ids_carteles, mirar_a_la_camara

KP, KD = 150.0, 5.0       # control PD de los motores
PERIODO_PASO = 1.0        # segundos por ciclo de pasos (izq + der)
ESPERA_POSTURA_S = 1.5    # tiempo para que cintura y cabeza lleguen
CODO_DOBLADO = -0.5       # brazos pegados al cuerpo para caber en el camino de 80 cm
VELOCIDAD_GIRO = 0.6      # rad/s al girar en el lugar
# Sensor de obstáculos: rayos a estas alturas (m). Los altos ven lo que obliga a frenar; los bajos,
# mangueras y desniveles. Solo ven la escena (grupos 0 y 1), no el propio robot (grupos 2 y 3).
ALTURAS_RAYO_ALTO = (0.08, 0.25, 0.5, 1.0)
ALTURAS_RAYO_BAJO = (0.015,)
INICIO_RAYO_M = 0.25      # los rayos salen un poco delante del cuerpo
GRUPOS_SENSOR = np.array([1, 1, 0, 0, 0, 0], dtype=np.uint8)   # el robot también dibuja en el 1: _rayo lo salta


GRUPO_OCULTO = 5          # grupo que el renderer no dibuja
MARGEN_FOTO_M = 2.5       # se dibuja hasta camara.distancia_max_m + esto (más lejos no se analiza)

ITERACIONES_APUNTAR = 6
ERROR_APUNTAR_RAD = 0.03     # ~1,7°: a 1 m de la rosa, menos de 2 cm del centro
GANANCIA_INCLINACION = 0.6
ESPERA_CORRECCION_S = 1.0


def _limitar(valor: float, limites: tuple[float, float]) -> float:
    return min(max(valor, limites[0]), limites[1])


class CuerpoSim(Cuerpo):
    """Camina con el modelo liviano (`mf`, `df`: robot, piso y camas) y usa el completo (`m`, `d`)
    para la cámara, el sensor y el visor, copiándole antes la pose del robot (`_al_completo`)."""

    def __init__(self, escena: Escena, cfg: dict, visor=None):
        self.m, self.d, self.visor = escena.m, escena.d, visor
        self.mf = escena.m_fisica if escena.m_fisica is not None else escena.m
        self.df = escena.d_fisica if escena.d_fisica is not None else escena.d
        self.cfg = cfg
        m = self.mf
        j = m.actuator_trnid[:, 0]
        self.qadr, self.vadr = m.jnt_qposadr[j], m.jnt_dofadr[j]
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
        self.id = {m.actuator(i).name.replace("motor_", "").replace("_joint", ""): i for i in range(m.nu)}
        self.obj = np.zeros(m.nu)
        self.guia = m.body("guia").mocapid[0]
        self.cam = m.camera(CAMARA).id
        completo = self.m
        self.del_robot = completo.body_rootid == completo.body("pelvis").id   # el sensor no ve al robot
        self.puntero = completo.light(PUNTERO).id
        ancho, alto = resolucion(cfg)
        # el renderer dibuja hasta max_geom piezas: con el invernadero completo faltaban rosas en la foto
        self.render = mujoco.Renderer(completo, alto, ancho, max_geom=max(10000, completo.ngeom + 1000))
        self.velocidad = cfg["recorrido"]["velocidad_m_s"]
        self.carteles = ids_carteles(completo)   # rosas con foto real (vacío si son figuras)
        self.alto_obstaculo = cfg["recorrido"]["alto_obstaculo_m"]
        self.obstaculos = [(o, completo.geom(o.nombre).id) for o in escena.obstaculos]
        # piezas de plantas y estructura: en cada foto se dibujan solo las cercanas (con el invernadero
        # completo, dibujar las ~52.000 tardaba 1,2 s por foto)
        fijos = [completo.body(n).id for n in ("rosales", "estructura")]
        self.piezas_fijas = np.flatnonzero(np.isin(completo.geom_bodyid, fijos))
        self.radio_foto = cfg["camara"]["distancia_max_m"] + MARGEN_FOTO_M
        self.espera_frente_obstaculo = 0.0

    def _al_completo(self) -> None:
        """Copia la pose del robot del modelo de la física al completo (antes de una foto o un rayo)."""
        if self.df is self.d:
            return
        self.d.qpos[:], self.d.qvel[:] = self.df.qpos, self.df.qvel
        self.d.mocap_pos[:], self.d.mocap_quat[:] = self.df.mocap_pos, self.df.mocap_quat
        self.d.time = self.df.time
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_camlight(self.m, self.d)

    # ---------- motores ----------
    def _poner(self, **angulos):
        for nombre, valor in angulos.items():
            self.obj[self.id[nombre]] = valor

    def _paso(self):
        tau = KP * (self.obj - self.df.qpos[self.qadr]) - KD * self.df.qvel[self.vadr]
        self.df.ctrl[:] = np.clip(tau, self.lo, self.hi)
        mujoco.mj_step(self.mf, self.df)
        if self.visor is not None and self.df.time % 0.02 < self.mf.opt.timestep:  # dibuja 50 veces por segundo
            if not self.visor.is_running():
                raise KeyboardInterrupt("se cerró el visor")
            self._al_completo()
            self.visor.sync()
            time.sleep(0.015)

    def _esperar(self, seg: float):
        for _ in range(int(seg / self.mf.opt.timestep)):
            self._paso()

    def _piernas(self, fase: float, amp: float):
        for lado, desfase in (("left", 0), ("right", np.pi)):
            s = np.sin(fase + desfase)
            cadera = -amp * s                        # pierna adelante / atrás
            rodilla = 2.2 * amp * max(0.0, s)        # dobla la rodilla al levantar
            self._poner(**{f"{lado}_hip_pitch": cadera - 0.25 * rodilla,
                           f"{lado}_knee": rodilla,
                           f"{lado}_ankle_pitch": -(cadera + rodilla) * 0.5})
        # brazos casi quietos: el camino es angosto
        self._poner(left_shoulder_pitch=0.1 * amp * np.sin(fase + np.pi),
                    right_shoulder_pitch=0.1 * amp * np.sin(fase))

    # ---------- interfaz ----------
    def pararse(self) -> None:
        self.obj[:] = 0
        self._poner(left_elbow=CODO_DOBLADO, right_elbow=CODO_DOBLADO)
        self._esperar(1.0)

    def posicion(self) -> tuple[float, float]:
        p = self.df.mocap_pos[self.guia]
        return float(p[0]), float(p[1])

    def rumbo(self) -> float:
        w, _, _, z = self.df.mocap_quat[self.guia]
        yaw = 2 * np.arctan2(z, w)
        return float((yaw + np.pi) % (2 * np.pi) - np.pi)   # entre −π y π

    def _poner_rumbo(self, yaw: float) -> None:
        self.df.mocap_quat[self.guia] = [np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]

    def orientar(self, yaw: float) -> None:
        """Gira en el lugar (dando pasitos) hasta mirar hacia `yaw`, por el lado más corto."""
        inicio = self.rumbo()
        delta = (yaw - inicio + np.pi) % (2 * np.pi) - np.pi
        if abs(delta) < 1e-3:
            return
        t_total = abs(delta) / VELOCIDAD_GIRO
        dt = self.mf.opt.timestep
        for k in range(int(t_total / dt)):
            t = k * dt
            self._poner_rumbo(inicio + delta * t / t_total)
            self._piernas(2 * np.pi * t / PERIODO_PASO, 0.15 * min(1.0, t / 0.3, (t_total - t) / 0.3))
            self._paso()
        self._poner_rumbo(inicio + delta)
        self._piernas(0, 0)
        self._esperar(0.2)

    def ir_a(self, x: float, y: float, velocidad: float | None = None) -> None:
        if any(self.obj[self.id[k]] != v for k, v in NEUTRA.items()):
            self.posar(NEUTRA)  # nunca camina girado ni inclinado
        x0, y0 = self.posicion()
        dx, dy = x - x0, y - y0
        dist = float(np.hypot(dx, dy))
        if dist < 1e-3:
            return
        self.orientar(float(np.arctan2(dy, dx)))   # siempre camina de frente
        t_total = dist / (velocidad or self.velocidad)
        dt = self.mf.opt.timestep
        self.espera_frente_obstaculo = 0.0   # se movió: empieza otra espera
        for k in range(int(t_total / dt)):
            t = k * dt
            f = t / t_total
            self.df.mocap_pos[self.guia][:2] = [x0 + dx * f, y0 + dy * f]
            self.df.mocap_pos[self.guia][2] = ALTURA_PELVIS + 0.01 * abs(np.sin(2 * np.pi * t / PERIODO_PASO))
            amp = 0.35 * min(1.0, t / 0.5, (t_total - t) / 0.5)   # arranca y frena suave
            self._piernas(2 * np.pi * t / PERIODO_PASO, amp)
            self._paso()
        self.df.mocap_pos[self.guia][:] = [x, y, ALTURA_PELVIS]
        self._piernas(0, 0)
        self._esperar(0.3)

    def obstaculos_adelante(self, distancia_max: float) -> tuple[float | None, float | None]:
        """Rayos hacia adelante (como un LiDAR) en el centro del camino y a 25 cm de cada lado."""
        self._al_completo()
        x, y = self.posicion()
        rumbo = self.rumbo()
        adelante = np.array([np.cos(rumbo), np.sin(rumbo), 0.0])
        lado = np.array([-np.sin(rumbo), np.cos(rumbo), 0.0])
        geomid = np.array([-1], dtype=np.int32)
        cerca = {}
        for tipo, alturas in (("alto", ALTURAS_RAYO_ALTO), ("bajo", ALTURAS_RAYO_BAJO)):
            for h in alturas:
                for desvio in (-0.25, 0.0, 0.25):
                    inicio = np.array([x, y, h]) + desvio * lado + INICIO_RAYO_M * adelante
                    d = self._rayo(inicio, adelante, geomid)
                    if 0 <= d <= distancia_max - INICIO_RAYO_M:
                        cerca[tipo] = min(cerca.get(tipo, np.inf), float(d + INICIO_RAYO_M))
        return cerca.get("alto"), cerca.get("bajo")

    def _rayo(self, inicio, direccion, geomid) -> float:
        """Distancia a lo primero que no es el robot (un hombro o un brazo pueden quedar delante
        del rayo si la cintura está girada). −1 si no hay nada."""
        recorrido = 0.0
        for _ in range(10):
            d = mujoco.mj_ray(self.m, self.d, inicio, direccion, GRUPOS_SENSOR, 1, -1, geomid)
            if d < 0 or not self.del_robot[self.m.geom_bodyid[geomid[0]]]:
                return d if d < 0 else recorrido + d
            paso = d + 0.02                   # sigue el rayo 2 cm más allá, hasta salir de esa pieza
            inicio, recorrido = inicio + paso * direccion, recorrido + paso
        return -1.0

    def esperar(self, segundos: float) -> None:
        """Quieto. En la simulación, un obstáculo con `se_quita_s` desaparece cuando el robot
        lleva ese tiempo esperando frente a él (como si alguien lo quitara)."""
        self._esperar(segundos)
        self.espera_frente_obstaculo += segundos
        x, y = self.posicion()
        for o, g in self.obstaculos:
            if (o.se_quita_s is not None and self.espera_frente_obstaculo >= o.se_quita_s
                    and np.hypot(o.x - x, self.m.geom_pos[g][1] - y) < 1.5):
                self.m.geom_pos[g][2] = -5.0   # lo quitaron
                mujoco.mj_kinematics(self.m, self.d)

    def posar(self, angulos: dict) -> dict:
        self._poner(**angulos)
        self._esperar(ESPERA_POSTURA_S)
        return {k: round(float(self.df.qpos[self.qadr[self.id[k]]]), 3) for k in angulos}

    def senalar(self, punto, segundos: float) -> bool:
        """Gira la cintura y sube o baja la cabeza hasta que la rosa quede en el centro de la foto
        (corrige con la pose real de la cámara, unas pocas veces) y prende el puntero."""
        punto = np.asarray(punto, dtype=float)
        x, y = self.posicion()
        giro = (math.atan2(punto[1] - y, punto[0] - x) - self.rumbo() + math.pi) % (2 * math.pi) - math.pi
        angulos, inclinacion = dict(NEUTRA, waist_yaw=_limitar(giro, CINTURA_YAW)), 0.0
        for k in range(ITERACIONES_APUNTAR):
            angulos["head_pitch"], angulos["waist_pitch"] = repartir_inclinacion(inclinacion)
            self._poner(**angulos)
            # corregir es un movimiento chico, pero hay que medir con la cámara quieta (si no, se pasa)
            self._esperar(ESPERA_POSTURA_S if k == 0 else ESPERA_CORRECCION_S)
            p = self.df.cam_xmat[self.cam].reshape(3, 3).T @ (punto - self.df.cam_xpos[self.cam])
            error_x, error_y = math.atan2(p[0], -p[2]), math.atan2(p[1], -p[2])   # la cámara mira hacia −z
            if max(abs(error_x), abs(error_y)) < ERROR_APUNTAR_RAD:
                break
            angulos["waist_yaw"] = _limitar(angulos["waist_yaw"] - error_x, CINTURA_YAW)
            # negativo = más arriba. Solo una parte: la cintura también mueve la cámara y con una rosa
            # cerca la corrección completa se pasa (oscila).
            inclinacion = _limitar(inclinacion - GANANCIA_INCLINACION * error_y, limites_inclinacion())
        self.m.light_active[self.puntero] = True     # la luz está en el modelo completo (el que se ve)
        self._esperar(segundos)
        self.m.light_active[self.puntero] = False
        return max(abs(error_x), abs(error_y)) < ERROR_APUNTAR_RAD

    def foto(self) -> Captura:
        self._al_completo()
        mirar_a_la_camara(self.m, self.d, self.carteles, self.d.cam_xpos[self.cam].copy())
        piezas = self.piezas_fijas
        lejos = piezas[np.linalg.norm(self.d.geom_xpos[piezas] - self.d.cam_xpos[self.cam], axis=1)
                       - self.m.geom_rbound[piezas] > self.radio_foto]
        grupos = self.m.geom_group[lejos].copy()
        self.m.geom_group[lejos] = GRUPO_OCULTO      # no se dibujan (ni cuentan para la profundidad)
        try:
            self.render.update_scene(self.d, camera=CAMARA)
            rgb = self.render.render()
            self.render.enable_depth_rendering()
            self.render.update_scene(self.d, camera=CAMARA)
            prof = self.render.render().astype(np.float32)
            self.render.disable_depth_rendering()
        finally:
            self.m.geom_group[lejos] = grupos
        return Captura(
            rgb=rgb, profundidad=prof,
            cam_pos=self.d.cam_xpos[self.cam].copy(),
            cam_mat=self.d.cam_xmat[self.cam].reshape(3, 3).copy(),
            fovy_grados=float(self.m.cam_fovy[self.cam]),
            robot_xy=self.posicion(),
            angulos={k: round(float(self.df.qpos[self.qadr[self.id[k]]]), 3) for k in NEUTRA},
            rumbo=self.rumbo(),
        )

    def nivel_bateria(self) -> float:
        """Batería simulada: baja con el tiempo del robot (`sim.bateria`). Del X2: ~500 Wh, ~2 h de
        uso → ~0,8 % por minuto. Al seguir una ronda (`--continuar`) vuelve a salir cargada."""
        b = self.cfg["sim"]["bateria"]
        return max(0.0, b["inicial_pct"] - b["consumo_pct_min"] * self.df.time / 60)

    def cerrar(self) -> None:
        self.render.close()
