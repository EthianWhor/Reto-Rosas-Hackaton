import type { ImageSource } from 'expo-image';

// Mismas claves que robot/ml/stages.py (STAGES), para que la app, el robot y la AR
// hablen el mismo idioma que el proceso estándar de la finca.
export type CategoriaId = '1_inmaduro' | '2_optimo' | '3_pasado';

export type Rosa = {
  id: string;
  categoria: CategoriaId;
  imagen: ImageSource | number;
  /** Fotos del robot: quién confirmó la categoría. Sin valor, es una foto de la finca. */
  fuente?: 'experto' | 'robot';
};
