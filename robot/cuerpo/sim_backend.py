"""Cuerpo del robot en MuJoCo.

Camina como en referencias/jardin_10_plantas.py: un punto guía (mocap) sostiene
la pelvis y las piernas se animan. No tiene equilibrio real; eso lo hará el
controlador oficial de AgiBot en el robot real. Los motores siguen una pose
objetivo con un control PD.
"""

import time

import mujoco
import numpy as np

from cuerpo.interfaz import Captura, Cuerpo
from cuerpo.posturas import NEUTRA
from sim.escena_invernadero import ALTURA_PELVIS, CAMARA, Escena, resolucion

KP, KD = 150.0, 5.0       # control PD de los motores
PERIODO_PASO = 1.0        # segundos por ciclo de pasos (izq + der)
ESPERA_POSTURA_S = 1.5    # tiempo para que cintura y cabeza lleguen
CODO_DOBLADO = -0.5       # brazos pegados al cuerpo para caber en el camino de 80 cm


class CuerpoSim(Cuerpo):
    def __init__(self, escena: Escena, cfg: dict, visor=None):
        self.m, self.d, self.visor = escena.m, escena.d, visor
        self.cfg = cfg
        m = self.m
        j = m.actuator_trnid[:, 0]
        self.qadr, self.vadr = m.jnt_qposadr[j], m.jnt_dofadr[j]
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
        self.id = {m.actuator(i).name.replace("motor_", "").replace("_joint", ""): i for i in range(m.nu)}
        self.obj = np.zeros(m.nu)
        self.guia = m.body("guia").mocapid[0]
        self.cam = m.camera(CAMARA).id
        ancho, alto = resolucion(cfg)
        self.render = mujoco.Renderer(m, alto, ancho)
        self.velocidad = cfg["recorrido"]["velocidad_m_s"]

    # ---------- motores ----------
    def _poner(self, **angulos):
        for nombre, valor in angulos.items():
            self.obj[self.id[nombre]] = valor

    def _paso(self):
        tau = KP * (self.obj - self.d.qpos[self.qadr]) - KD * self.d.qvel[self.vadr]
        self.d.ctrl[:] = np.clip(tau, self.lo, self.hi)
        mujoco.mj_step(self.m, self.d)
        if self.visor is not None and self.d.time % 0.02 < self.m.opt.timestep:  # dibuja 50 veces por segundo
            if not self.visor.is_running():
                raise KeyboardInterrupt("se cerró el visor")
            self.visor.sync()
            time.sleep(0.015)

    def _esperar(self, seg: float):
        for _ in range(int(seg / self.m.opt.timestep)):
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
        p = self.d.mocap_pos[self.guia]
        return float(p[0]), float(p[1])

    def caminar_hasta(self, x: float) -> None:
        if any(self.obj[self.id[k]] != v for k, v in NEUTRA.items()):
            self.posar(NEUTRA)  # nunca camina girado ni inclinado
        x0 = self.d.mocap_pos[self.guia][0]
        dist = x - x0
        if abs(dist) < 1e-3:
            return
        t_total = abs(dist) / self.velocidad
        dt = self.m.opt.timestep
        for k in range(int(t_total / dt)):
            t = k * dt
            self.d.mocap_pos[self.guia][0] = x0 + dist * t / t_total
            self.d.mocap_pos[self.guia][2] = ALTURA_PELVIS + 0.01 * abs(np.sin(2 * np.pi * t / PERIODO_PASO))
            amp = 0.35 * min(1.0, t / 0.5, (t_total - t) / 0.5)   # arranca y frena suave
            self._piernas(2 * np.pi * t / PERIODO_PASO, amp)
            self._paso()
        self.d.mocap_pos[self.guia][0] = x
        self.d.mocap_pos[self.guia][2] = ALTURA_PELVIS
        self._piernas(0, 0)
        self._esperar(0.3)

    def posar(self, angulos: dict) -> dict:
        self._poner(**angulos)
        self._esperar(ESPERA_POSTURA_S)
        return {k: round(float(self.d.qpos[self.qadr[self.id[k]]]), 3) for k in angulos}

    def foto(self) -> Captura:
        self.render.update_scene(self.d, camera=CAMARA)
        rgb = self.render.render()
        self.render.enable_depth_rendering()
        self.render.update_scene(self.d, camera=CAMARA)
        prof = self.render.render().astype(np.float32)
        self.render.disable_depth_rendering()
        return Captura(
            rgb=rgb, profundidad=prof,
            cam_pos=self.d.cam_xpos[self.cam].copy(),
            cam_mat=self.d.cam_xmat[self.cam].reshape(3, 3).copy(),
            fovy_grados=float(self.m.cam_fovy[self.cam]),
            robot_xy=self.posicion(),
            angulos={k: round(float(self.d.qpos[self.qadr[self.id[k]]]), 3) for k in NEUTRA},
        )

    def cerrar(self) -> None:
        self.render.close()
