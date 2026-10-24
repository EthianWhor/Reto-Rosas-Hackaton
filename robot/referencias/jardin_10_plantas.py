"""
AgiBot X2 Ultra en MuJoCo: ronda nocturna por 10 plantas aleatorias.
El robot camina por la fila, para en cada planta, gira, toma foto,
analiza el color y agrega el resultado a reporte_jardin.csv.

Cómo correrlo (desde la carpeta X2_URDF-v1.4.0):
    py jardin_10_plantas.py                 -> con ventana
    py jardin_10_plantas.py --sin-ventana   -> solo fotos y csv
    py jardin_10_plantas.py --semilla 7     -> repite las mismas plantas
"""
import sys, os, csv, time, random, colorsys, datetime
import numpy as np
import mujoco
from PIL import Image

# ---------------- CONFIGURACIÓN ----------------
ESCENA = "scene_jardin.xml"
CSV_SALIDA = "reporte_jardin.csv"
CARPETA_FOTOS = "fotos"
N_PLANTAS = 10
SEPARACION = 0.5          # metros entre plantas
X_PRIMERA = 0.6           # dónde queda la primera planta
Y_MESA = 0.75             # la mesa queda a la izquierda del robot
VELOCIDAD = 0.25          # m/s caminando
PERIODO_PASO = 1.0        # segundos por ciclo de pasos (izq + der)
PROB_ESTADOS = {"SANA": 0.5, "AMARILLA": 0.3, "SECA": 0.2}  # qué tan seguido sale cada estado
KP, KD = 150.0, 5.0       # control PD de los motores
ANCHO, ALTO = 640, 480
SIMULAR_NOCHE = True
HORA_INICIO, HORA_FIN = 19, 6


# ---------------- PLANTAS ALEATORIAS ----------------
def color_hoja(tipo):
    if tipo == "verde":
        h, s, v = random.uniform(95, 140), random.uniform(0.6, 0.85), random.uniform(0.45, 0.7)  # verde
    elif tipo == "amarilla":
        h, s, v = random.uniform(50, 62), random.uniform(0.7, 0.9), random.uniform(0.75, 0.9)    # amarillo
    else:
        h, s, v = random.uniform(28, 38), random.uniform(0.65, 0.85), random.uniform(0.45, 0.6)  # café seco
    r, g, b = colorsys.hsv_to_rgb(h / 360, s, v)
    return [r, g, b, 1]


def hojas_de(estado):
    if estado == "SANA":
        return ["verde"] * 5                                        # todas verdes
    if estado == "AMARILLA":
        n = random.randint(3, 5)                                    # 3 a 5 hojas amarillas
        return ["amarilla"] * n + ["verde"] * (5 - n)
    n = random.randint(3, 5)                                        # 3 a 5 hojas secas
    return ["seca"] * n + ["amarilla"] * (5 - n)


def agregar_mesa_y_plantas(spec):
    mundo = spec.worldbody
    largo = N_PLANTAS * SEPARACION / 2 + 0.3
    xc = X_PRIMERA + (N_PLANTAS - 1) * SEPARACION / 2
    mesa = mundo.add_body(name="mesa", pos=[xc, Y_MESA, 0])
    mesa.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[largo, 0.2, 0.02], pos=[0, 0, 0.6], rgba=[0.8, 0.8, 0.78, 1])
    for sx in (-1, 1):
        for sy in (-1, 1):
            mesa.add_geom(type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.02, 0.3, 0],
                          pos=[sx * (largo - 0.05), sy * 0.15, 0.3], rgba=[0.8, 0.8, 0.78, 1])

    verdad = []
    for i in range(N_PLANTAS):
        estado = random.choices(list(PROB_ESTADOS), weights=list(PROB_ESTADOS.values()))[0]  # estado al azar
        tipos = hojas_de(estado)
        random.shuffle(tipos)
        x = X_PRIMERA + i * SEPARACION
        p = mundo.add_body(name=f"planta_{i+1:02d}", pos=[x, Y_MESA, 0.62],
                           euler=[0, 0, random.uniform(0, 6.28)])  # giro al azar
        p.add_geom(type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.07, 0.07, 0], pos=[0, 0, 0.07], rgba=[0.35, 0.37, 0.42, 1])  # matera
        p.add_geom(type=mujoco.mjtGeom.mjGEOM_CYLINDER, size=[0.065, 0.005, 0], pos=[0, 0, 0.14], rgba=[0.18, 0.11, 0.06, 1])  # tierra
        tallo = [0.15, 0.6, 0.15, 1] if estado != "SECA" else [0.45, 0.3, 0.1, 1]
        p.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0, 0, 0.14, 0, 0, 0.3], size=[0.008, 0, 0], rgba=tallo)  # tallo
        for k, t in enumerate(tipos):
            ang = k * 2 * np.pi / 5
            p.add_geom(type=mujoco.mjtGeom.mjGEOM_ELLIPSOID, size=[0.09, 0.04, 0.012],
                       pos=[0.05 * np.cos(ang), 0.05 * np.sin(ang), random.uniform(0.21, 0.3)],
                       euler=[0, -0.4, ang], rgba=color_hoja(t))  # hoja
        verdad.append({"planta": f"planta_{i+1:02d}", "x": x, "estado_real": estado})
    return verdad


def cargar_modelo():
    spec = mujoco.MjSpec.from_file(ESCENA)
    cabeza = spec.body("head_pitch_link")
    mat = np.array([0, 0, -1, -1, 0, 0, 0, 1, 0], dtype=float)  # cámara mira al frente
    quat = np.zeros(4); mujoco.mju_mat2Quat(quat, mat)
    cabeza.add_camera(name="cam_cabeza", pos=[0.09, -0.014, -0.045], quat=quat, fovy=45)  # cámara de la cabeza
    cabeza.add_light(name="linterna", pos=[0.07, 0, -0.03], dir=[1, 0, -0.4],
                     diffuse=[0.9, 0.9, 0.8], cutoff=40, exponent=5, castshadow=True)  # linterna
    verdad = agregar_mesa_y_plantas(spec)
    m = spec.compile()
    d = mujoco.MjData(m)
    return m, d, verdad


# ---------------- CONTROL DEL ROBOT ----------------
class Robot:
    def __init__(self, m, d, visor=None):
        self.m, self.d, self.visor = m, d, visor
        j = m.actuator_trnid[:, 0]
        self.qadr, self.vadr = m.jnt_qposadr[j], m.jnt_dofadr[j]   # dónde está cada articulación
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]
        self.id = {m.actuator(i).name.replace("motor_", "").replace("_joint", ""): i for i in range(m.nu)}
        self.obj = np.zeros(m.nu)                                  # pose objetivo (de pie)
        self.guia = m.body("guia").mocapid[0]
        self.render = mujoco.Renderer(m, ALTO, ANCHO)

    def poner(self, **angulos):
        for nombre, valor in angulos.items():
            self.obj[self.id[nombre]] = valor                      # cambia el objetivo de una articulación

    def paso_sim(self):
        tau = KP * (self.obj - self.d.qpos[self.qadr]) - KD * self.d.qvel[self.vadr]  # PD
        self.d.ctrl[:] = np.clip(tau, self.lo, self.hi)
        mujoco.mj_step(self.m, self.d)
        if self.visor is not None and self.d.time % 0.02 < self.m.opt.timestep:  # dibuja 50 veces por segundo
            if not self.visor.is_running():
                sys.exit()
            self.visor.sync(); time.sleep(0.015)

    def esperar(self, seg):
        for _ in range(int(seg / self.m.opt.timestep)):
            self.paso_sim()

    def piernas(self, fase, amp):
        for lado, desfase in (("left", 0), ("right", np.pi)):
            s = np.sin(fase + desfase)
            cadera = -amp * s                                       # pierna adelante / atrás
            rodilla = 2.2 * amp * max(0.0, s)                       # dobla la rodilla al levantar
            self.poner(**{f"{lado}_hip_pitch": cadera - 0.5 * rodilla * 0.5,
                          f"{lado}_knee": rodilla,
                          f"{lado}_ankle_pitch": -(cadera + rodilla) * 0.5})  # pie más o menos plano
        self.poner(left_shoulder_pitch=0.3 * amp * np.sin(fase + np.pi),  # brazos se balancean
                   right_shoulder_pitch=0.3 * amp * np.sin(fase))

    def caminar_hasta(self, x_meta):
        x0 = self.d.mocap_pos[self.guia][0]
        dist = x_meta - x0
        if abs(dist) < 1e-3:
            return
        t_total = abs(dist) / VELOCIDAD
        n = int(t_total / self.m.opt.timestep)
        for k in range(n):
            t = k * self.m.opt.timestep
            frac = t / t_total
            self.d.mocap_pos[self.guia][0] = x0 + dist * frac       # mueve la pelvis
            self.d.mocap_pos[self.guia][2] = 0.69 + 0.01 * abs(np.sin(2 * np.pi * t / PERIODO_PASO))  # sube y baja un poco
            amp = 0.35 * min(1.0, t / 0.5, (t_total - t) / 0.5)     # arranca y frena suave
            self.piernas(2 * np.pi * t / PERIODO_PASO, amp)
            self.paso_sim()
        self.d.mocap_pos[self.guia][0] = x_meta
        self.piernas(0, 0)
        self.esperar(0.3)

    def mirar_planta(self):
        self.poner(waist_yaw=1.3, head_yaw=0.27, head_pitch=0.40)  # gira a la izquierda hacia la mesa
        self.esperar(1.5)

    def mirar_al_frente(self):
        self.poner(waist_yaw=0.0, head_yaw=0.0, head_pitch=0.0)
        self.esperar(1.0)

    def foto(self):
        self.render.update_scene(self.d, camera="cam_cabeza")
        return self.render.render()


# ---------------- ANÁLISIS DE LA FOTO ----------------
def analizar_imagen(img):
    w = img.shape[1]
    img = img[:, w // 4: 3 * w // 4]                # solo el centro (la planta que se mira)
    rgb = img.astype(float) / 255.0
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    v = mx                                          # brillo
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0)  # saturación
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360  # tono

    color = (s > 0.35) & (v > 0.06)                 # pixeles con color (no gris)
    verde = color & (h >= 75) & (h < 170)           # hoja sana
    amarillo = color & (h >= 45) & (h < 75)         # hoja amarilla
    cafe = color & (h >= 20) & (h < 45) & (v > 0.25) # hoja seca (la tierra es más oscura)
    hojas = verde.sum() + amarillo.sum() + cafe.sum()
    if hojas < 200:
        return {"verde%": 0, "amarillo%": 0, "seco%": 0, "estado": "NO SE VE"}

    pv, pa, pc = (100 * x.sum() / hojas for x in (verde, amarillo, cafe))
    if pv >= 75:
        estado = "SANA"
    elif pc >= 30:
        estado = "SECA"
    else:
        estado = "AMARILLA"
    return {"verde%": round(pv, 1), "amarillo%": round(pa, 1), "seco%": round(pc, 1), "estado": estado}


def guardar_fila(fila):
    nuevo = not os.path.exists(CSV_SALIDA)
    with open(CSV_SALIDA, "a", newline="", encoding="utf-8") as f:   # "a" = agrega sin borrar lo anterior
        w = csv.DictWriter(f, fieldnames=list(fila.keys()))
        if nuevo:
            w.writeheader()                                           # encabezado solo la primera vez
        w.writerow(fila)


# ---------------- RONDA ----------------
def ronda(m, d, verdad, visor=None):
    os.makedirs(CARPETA_FOTOS, exist_ok=True)
    robot = Robot(m, d, visor)
    id_ronda = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    robot.esperar(0.5)
    aciertos = 0
    for p in verdad:
        robot.caminar_hasta(p["x"])                    # camina hasta quedar frente a la planta
        robot.mirar_planta()
        img = robot.foto()
        robot.mirar_al_frente()
        nombre = os.path.join(CARPETA_FOTOS, f"{id_ronda}_{p['planta']}.png")
        Image.fromarray(img).save(nombre)
        r = analizar_imagen(img)
        acierto = r["estado"] == p["estado_real"]
        aciertos += acierto
        guardar_fila({
            "ronda": id_ronda,
            "fecha_hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "planta": p["planta"],
            "x_m": round(p["x"], 2),
            "estado_detectado": r["estado"],
            "verde%": r["verde%"], "amarillo%": r["amarillo%"], "seco%": r["seco%"],
            "estado_real": p["estado_real"],   # lo que de verdad tiene la planta simulada
            "acierto": int(acierto),
            "foto": nombre,
        })
        print(f"{p['planta']}  detectado: {r['estado']:9s} real: {p['estado_real']:9s} {'OK' if acierto else 'X'}")
    print(f"Aciertos: {aciertos}/{len(verdad)}  -> guardado en {CSV_SALIDA}")
    robot.render.close()


def es_de_noche():
    hora = datetime.datetime.now().hour
    return SIMULAR_NOCHE or hora >= HORA_INICIO or hora < HORA_FIN


def main():
    if "--semilla" in sys.argv:
        random.seed(int(sys.argv[sys.argv.index("--semilla") + 1]))  # mismas plantas cada vez
    if not es_de_noche():
        print("Todavía es de día. La ronda corre de", HORA_INICIO, "a", HORA_FIN, "h.")
        return
    m, d, verdad = cargar_modelo()
    if "--sin-ventana" in sys.argv:
        ronda(m, d, verdad)
        return
    import mujoco.viewer
    with mujoco.viewer.launch_passive(m, d) as visor:
        visor.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING          # la cámara sigue al robot
        visor.cam.trackbodyid = m.body("pelvis").id
        visor.cam.distance, visor.cam.azimuth, visor.cam.elevation = 2.5, 120, -15
        ronda(m, d, verdad, visor)
        print("Ronda terminada. Cierra la ventana para salir.")
        while visor.is_running():
            mujoco.mj_step(m, d)
            visor.sync(); time.sleep(0.01)


if __name__ == "__main__":
    main()
