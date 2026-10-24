// Estilo de RoseApp: rosa, rojo y blanco. Botones y textos grandes, porque la usan operarios en una
// tablet compartida, a veces con guantes.
export const colores = {
  fondo: '#FFF6F8',
  tarjeta: '#FFFFFF',
  texto: '#3B1820',
  textoSuave: '#8C6B74',
  borde: '#F4D9E1',

  primario: '#D7263D',
  primarioOscuro: '#A51C2F',
  rosa: '#F06292',
  rosaOscuro: '#C2185B',
  rosaSuave: '#FDE4EC',

  acierto: '#2E9E5B',
  aciertoOscuro: '#21774A',
  aciertoSuave: '#E3F5EA',
  error: '#D93A3A',
  errorOscuro: '#A82B2B',
  errorSuave: '#FDE6E6',
  oro: '#F2A93B',
  gris: '#9E8C91',
  grisOscuro: '#76666B',
};

export const espacio = { xs: 4, s: 8, m: 16, l: 24, xl: 32 };

export const texto = {
  titulo: 30,
  subtitulo: 21,
  cuerpo: 17,
  boton: 20,
  pequeno: 14,
};

// Nunito (redondeada y amable); se carga en src/app/_layout.tsx.
export const fuente = {
  normal: 'Nunito_600SemiBold',
  negrita: 'Nunito_800ExtraBold',
  titulo: 'Nunito_900Black',
};

export const sombra = {
  shadowColor: '#A51C2F',
  shadowOpacity: 0.08,
  shadowRadius: 12,
  shadowOffset: { width: 0, height: 4 },
  elevation: 2,
};

/** Versión más oscura de un color, para el borde inferior de los botones 3D. */
export function oscurecer(hex: string, cantidad = 0.22): string {
  const n = parseInt(hex.slice(1), 16);
  const canal = (c: number) => Math.round(c * (1 - cantidad));
  const r = canal((n >> 16) & 255);
  const g = canal((n >> 8) & 255);
  const b = canal(n & 255);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}
