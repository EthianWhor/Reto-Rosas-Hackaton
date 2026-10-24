// Proceso de corte y sanación, tomado de contenido/corte-y-sanacion.md (manuales de rosa de corte).
// Es la versión de trabajo mientras la finca confirma su propio protocolo: cuando lo envíe, se
// cambian los textos aquí y la pantalla no cambia.

export type Paso = { titulo: string; detalle: string };

export const PASOS: Paso[] = [
  { titulo: 'Alistarse', detalle: 'Guantes y tijera afilada y desinfectada.' },
  { titulo: 'Elegir la rosa', detalle: 'Solo la que está en punto 3.' },
  { titulo: 'Elegir dónde cortar', detalle: 'Sobre la segunda hoja de cinco foliolos.' },
  { titulo: 'Elegir la yema', detalle: 'La más hinchada, mirando hacia afuera de la planta.' },
  { titulo: 'Cortar', detalle: 'En bisel, pegado a la yema, sin dejar tocón.' },
  { titulo: 'Sacar el tallo', detalle: 'Por arriba, sin rozar otras flores. Nunca al suelo.' },
  { titulo: 'Hidratar', detalle: 'Al balde antes de 20 minutos.' },
  { titulo: 'Sanar la planta', detalle: 'Revisar el corte, quitar hojas secas, residuos y tallos débiles.' },
  { titulo: 'Desinfectar otra vez', detalle: 'Al cambiar de cama y después de una planta enferma.' },
];

export type Pregunta = { texto: string; opciones: string[]; correcta: number; porque: string };

export const PREGUNTAS: Pregunta[] = [
  {
    texto: '¿Sobre qué hoja se corta?',
    opciones: ['Sobre una hoja de tres foliolos', 'Sobre la segunda hoja de cinco foliolos', 'Lo más abajo posible'],
    correcta: 1,
    porque: 'La yema de una hoja de cinco foliolos da un tallo largo y fuerte.',
  },
  {
    texto: '¿Hacia dónde debe mirar la yema que queda?',
    opciones: ['Hacia el centro de la planta', 'Hacia afuera de la planta', 'No importa'],
    correcta: 1,
    porque: 'Así el tallo nuevo crece hacia afuera y el centro queda aireado, con menos hongos.',
  },
  {
    texto: 'Si siempre cortas hacia el mismo lado…',
    opciones: ['La planta se carga y se puede caer', 'La planta crece más derecha', 'No pasa nada'],
    correcta: 0,
    porque: 'Hay que repartir los cortes entre los lados para que la planta quede pareja.',
  },
  {
    texto: '¿Cómo es un buen corte?',
    opciones: ['Recto y lejos de la yema', 'En bisel, pegado a la yema', 'Desgarrado, de un tirón'],
    correcta: 1,
    porque: 'El bisel deja escurrir el agua y sin tocón no se seca un pedazo de tallo.',
  },
  {
    texto: '¿Qué está mal? Quedó un pedazo largo de tallo sobre la yema.',
    opciones: ['Nada, así protege la yema', 'Es un tocón: se seca y entran hongos', 'Hay que pintarlo'],
    correcta: 1,
    porque: 'Se corta unos 5 mm arriba de la yema, sin tocón.',
  },
  {
    texto: 'Cortaste la rosa y tienes las manos ocupadas. ¿Dónde la dejas?',
    opciones: ['En el suelo un momento', 'Directo al balde o al carro', 'Sobre la planta'],
    correcta: 1,
    porque: 'En el suelo se contamina y se maltrata.',
  },
  {
    texto: '¿En cuánto tiempo debe llegar al agua?',
    opciones: ['Antes de 20 minutos', 'Al final del turno', 'Antes de 2 horas'],
    correcta: 0,
    porque: 'Después de 20 minutos el tallo se tapona y la flor dura menos.',
  },
  {
    texto: '¿Cuándo se desinfecta la tijera?',
    opciones: ['Una vez al día', 'Al cambiar de cama y después de una planta enferma', 'Solo si se ve sucia'],
    correcta: 1,
    porque: 'Una tijera sucia lleva Botrytis y bacterias de planta en planta.',
  },
  {
    texto: 'Verdadero o falso: conviene trabajar con dos tijeras y alternarlas.',
    opciones: ['Verdadero', 'Falso'],
    correcta: 0,
    porque: 'Mientras una está en el desinfectante, usas la otra.',
  },
  {
    texto: '¿Qué es sanar la planta después del corte?',
    opciones: [
      'Revisar el corte y quitar hojas secas, residuos y tallos débiles',
      'Regarla más',
      'Cortarle todas las hojas',
    ],
    correcta: 0,
    porque: 'Los residuos y las heridas mal hechas son donde crecen los hongos.',
  },
  {
    texto: 'Verdadero o falso: hay que dejar 2 o 3 yemas con hojas completas en el tallo.',
    opciones: ['Verdadero', 'Falso'],
    correcta: 0,
    porque: 'Esas hojas siguen alimentando la planta para el próximo tallo.',
  },
];
