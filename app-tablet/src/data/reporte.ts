// Formato del reporte JSON que deja el robot después de cada ronda
// (robot/PLAN_robot_rosas_X2.md, sección 10.4, y robot/reporte/archivos.py en la rama A).
// Los nombres de los campos son los del robot: no cambiarlos aquí sin cambiarlos allá.

export type Prioridad = 'alta' | 'media' | 'baja';
export type EstadoRosa = 'optimo' | 'lista_manana' | 'inmaduro' | 'pasado' | 'dudosa';

export type Cuadrante = {
  cuadrante_id: string;
  cama: number;
  tramo: number;
  desde_m: number;
  hasta_m: number;
  optimo: number;
  lista_manana: number;
  inmaduro: number;
  pasado: number;
  dudosa: number;
  total: number;
  prioridad: Prioridad;
  /** 1 = el cuadrante al que hay que ir primero. */
  orden: number;
};

export type RosaLista = {
  rosa_id: string;
  estado: 'optimo' | 'lista_manana';
  cuadrante_id?: string;
  cama: number;
  lado: string;
  metro_en_cama: number;
  altura_m: number;
  diametro_cm?: number;
  confianza: number;
  foto?: string;
  fecha_hora?: string;
};

export type Reporte = {
  id_ronda: string;
  invernadero: string;
  fecha: string;
  inicio: string;
  fin: string;
  cuadrantes: Cuadrante[];
  rosas_listas: RosaLista[];
  dudosas?: { rosa_id: string; cuadrante_id?: string; foto?: string; confianza?: number }[];
  obstaculos: string[];
  ronda?: Record<string, string | number>;
};

// Invernadero de ejemplo como el de la simulación del robot (robot/config/config.yaml en la rama A):
// 20 camas de 30 m, cuadrantes ("tramos") de 5 m. Números al azar, pero siempre los mismos.
function cuadrantesDeEjemplo(): Cuadrante[] {
  let semilla = 7;
  const azar = (max: number) => {
    semilla = (semilla * 1103515245 + 12345) % 2147483648;
    return Math.floor((semilla / 2147483648) * (max + 1));
  };
  const lista: Cuadrante[] = [];
  for (let cama = 1; cama <= 20; cama++) {
    for (let tramo = 1; tramo <= 6; tramo++) {
      // Unas 8 a 12 rosas por metro de cama (como en la simulación): 40 a 60 por tramo de 5 m.
      const optimo = Math.max(0, azar(18) - 4);
      const lista_manana = azar(10);
      const inmaduro = 25 + azar(25);
      const pasado = azar(3) === 0 ? 1 : 0;
      const dudosa = azar(4) === 0 ? 1 : 0;
      lista.push({
        cuadrante_id: `INV1-C${String(cama).padStart(2, '0')}-T${tramo}`,
        cama,
        tramo,
        desde_m: (tramo - 1) * 5,
        hasta_m: tramo * 5,
        optimo,
        lista_manana,
        inmaduro,
        pasado,
        dudosa,
        total: optimo + lista_manana + inmaduro + pasado + dudosa,
        prioridad: optimo >= 3 ? 'alta' : optimo + lista_manana > 0 ? 'media' : 'baja',
        orden: 0,
      });
    }
  }
  // Mismo orden que el robot: puntaje = óptimo + 0,5 · lista mañana.
  const puntaje = (c: Cuadrante) => c.optimo + 0.5 * c.lista_manana;
  [...lista].sort((a, b) => puntaje(b) - puntaje(a)).forEach((c, i) => (c.orden = i + 1));
  return lista;
}

// Una rosa dudosa por cada cuadrante del ejemplo que tiene alguna, con una confianza baja.
function dudosasDeEjemplo(cuadrantes: Cuadrante[]): NonNullable<Reporte['dudosas']> {
  return cuadrantes
    .filter((c) => c.dudosa > 0)
    .map((c, i) => ({
      rosa_id: `${c.cuadrante_id}-${(c.desde_m + 2.5).toFixed(2)}-1.70`,
      cuadrante_id: c.cuadrante_id,
      confianza: 0.4 + ((i * 7) % 20) / 100,
    }));
}

const CUADRANTES_EJEMPLO = cuadrantesDeEjemplo();

// Reporte de ejemplo con el mismo formato, para mostrar la pantalla sin el robot conectado.
export const REPORTE_EJEMPLO: Reporte = {
  id_ronda: 'INV1_2026-10-24_220000',
  invernadero: 'INV1',
  fecha: '2026-10-24',
  inicio: '2026-10-24 22:00:00',
  fin: '2026-10-24 23:41:00',
  cuadrantes: CUADRANTES_EJEMPLO,
  rosas_listas: [
    { rosa_id: 'INV1-C07-T3-12.35-1.84', estado: 'optimo', cama: 7, lado: 'izq', metro_en_cama: 12.35, altura_m: 1.84, diametro_cm: 5.1, confianza: 0.87 },
    { rosa_id: 'INV1-C12-T2-6.10-1.62', estado: 'optimo', cama: 12, lado: 'der', metro_en_cama: 6.1, altura_m: 1.62, diametro_cm: 4.9, confianza: 0.81 },
  ],
  dudosas: dudosasDeEjemplo(CUADRANTES_EJEMPLO),
  obstaculos: ['INV1-C04-T2'],
};
