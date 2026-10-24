import type { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';

import type { CategoriaId } from './tipos';

export type Categoria = {
  id: CategoriaId;
  /** Nombre corto que ve el operario en los botones del juego. */
  boton: string;
  /** Nombre de la categoría en el proceso estándar de la finca. */
  nombreFinca: string;
  color: string;
  icono: ComponentProps<typeof Ionicons>['name'];
  /** Rasgos a observar (de la "Información técnica" de la finca, variedad Freedom). */
  mirar: string[];
  /** Pista corta para no confundirla con la vecina. */
  pista: string;
};

// Mismos criterios que robot/ml/stages.py (STAGE_TIPS), en versión corta para la tablet.
export const CATEGORIAS: Categoria[] = [
  {
    id: '1_inmaduro',
    boton: 'Muy pronto',
    nombreFinca: 'Inmaduro · no cortar',
    color: '#5E9C4B',
    icono: 'hourglass-outline',
    mirar: ['Cabeza pequeña', 'Rojo oscuro', 'Sépalos pegados'],
    pista: 'Cortarla aquí es el error más común. Espera a ver el centro.',
  },
  {
    id: '2_optimo',
    boton: 'Punto óptimo',
    nombreFinca: 'Punto 3 · cortar',
    color: '#D7263D',
    icono: 'cut',
    mirar: ['Se ve el centro', 'Rojo vivo', 'Forma de copa'],
    pista: 'Este es el punto 3: córtala.',
  },
  {
    id: '3_pasado',
    boton: 'Muy tarde',
    nombreFinca: 'Pasada · sobreabierta',
    color: '#A0693A',
    icono: 'alert-circle-outline',
    mirar: ['Flor ancha y plana', 'Pétalos hacia afuera', 'Perdió la forma de copa'],
    pista: 'Se pasó del punto. Había que cortarla antes.',
  },
];

export function categoria(id: CategoriaId): Categoria {
  return CATEGORIAS.find((c) => c.id === id)!;
}
