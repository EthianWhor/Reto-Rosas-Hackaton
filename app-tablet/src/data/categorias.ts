import type { CategoriaId } from './tipos';

export type Categoria = {
  id: CategoriaId;
  /** Nombre corto que ve el operario en los botones del juego. */
  boton: string;
  /** Nombre de la categoría en el proceso estándar de la finca. */
  nombreFinca: string;
  color: string;
  /** Rasgos a observar (de la "Información técnica" de la finca, variedad Freedom). */
  mirar: string[];
  /** Cómo distinguirla de la categoría vecina. */
  diferencia: string;
};

// Los tips son los mismos de robot/ml/stages.py (STAGE_TIPS). Si cambian allá, cambiarlos aquí.
export const CATEGORIAS: Categoria[] = [
  {
    id: '1_inmaduro',
    boton: 'Muy pronto',
    nombreFinca: 'Inmaduro – no cortar',
    color: '#5B7F3A',
    mirar: [
      'La cabeza (botón floral) se ve más pequeña.',
      'El rojo es más oscuro.',
      'Los sépalos están pegados a los pétalos.',
    ],
    diferencia:
      'Cortarla aquí (punto 2, cerrado) es la falla más común. Espera a que el caracol se defina ' +
      'mostrando el centro y el rojo se vuelva vivo e intenso.',
  },
  {
    id: '2_optimo',
    boton: 'Punto óptimo',
    nombreFinca: 'Punto óptimo de corte (punto 3)',
    color: '#C0392B',
    mirar: [
      'El caracol está definido y se ve el centro.',
      'El color de los pétalos es vivo e intenso.',
      'La flor presenta un patrón de copa.',
    ],
    diferencia:
      'Es el punto 3, el punto de corte. Si la cabeza se ve pequeña, el rojo oscuro y los sépalos ' +
      'pegados, todavía está inmadura.',
  },
  {
    id: '3_pasado',
    boton: 'Muy tarde',
    nombreFinca: 'Pasado / sobreabierto',
    color: '#8E5A2B',
    mirar: ['La flor ya está sobreabierta: pasó del punto de corte.'],
    diferencia: 'Ya no está en punto óptimo; se debió cortar antes.',
  },
];

export function categoria(id: CategoriaId): Categoria {
  return CATEGORIAS.find((c) => c.id === id)!;
}
