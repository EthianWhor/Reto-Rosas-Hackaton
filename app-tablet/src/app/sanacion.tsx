import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useMemo, useState } from 'react';
import { Animated, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import { Aparecer, BarraProgreso, LluviaDePetalos, Rebote, useSacudir } from '@/componentes/animaciones';
import { PASOS, PREGUNTAS } from '@/data/sanacion';
import { colores, espacio, fuente, texto } from '@/tema';

const VERDE = '#26A69A';

type Modo = 'inicio' | 'ordenar' | 'preguntas' | 'fin';

function barajar<T>(lista: T[]): T[] {
  const copia = [...lista];
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

// Proceso de corte y sanación (versión de trabajo, ver src/data/sanacion.ts): repasar los pasos,
// ordenarlos y responder preguntas, con el mismo estilo del juego de clasificar.
export default function Sanacion() {
  const [modo, setModo] = useState<Modo>('inicio');
  const [resultado, setResultado] = useState({ aciertos: 0, total: 0 });

  if (modo === 'ordenar')
    return <Ordenar onFin={(r) => (setResultado(r), setModo('fin'))} />;
  if (modo === 'preguntas')
    return <Preguntas onFin={(r) => (setResultado(r), setModo('fin'))} />;
  if (modo === 'fin') return <Fin {...resultado} onVolver={() => setModo('inicio')} />;

  return (
    <ScrollView contentContainerStyle={styles.pagina}>
      <Aparecer estilo={styles.cabeza}>
        <View style={styles.icono}>
          <Ionicons name="medkit" size={40} color="#fff" />
        </View>
        <Text style={styles.titulo}>Corte y sanación</Text>
        <Text style={[styles.suave, { textAlign: 'center' }]}>Los 9 pasos, de alistarse a dejar la planta sana.</Text>
      </Aparecer>

      {PASOS.map((p, i) => (
        <Aparecer key={p.titulo} retraso={40 * i} estilo={styles.paso}>
          <View style={styles.numero}>
            <Text style={styles.numeroTexto}>{i + 1}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.pasoTitulo}>{p.titulo}</Text>
            <Text style={styles.suave}>{p.detalle}</Text>
          </View>
        </Aparecer>
      ))}

      <View style={styles.botones}>
        <BotonGrande titulo="Ordenar los pasos" icono="list" color={VERDE} onPress={() => setModo('ordenar')} />
        <BotonGrande titulo="Preguntas" icono="help-circle" onPress={() => setModo('preguntas')} />
      </View>
      <Text style={styles.nota}>Versión de trabajo, basada en manuales de rosa de corte. Falta confirmarla con la finca.</Text>
    </ScrollView>
  );
}

function Ordenar({ onFin }: { onFin: (r: { aciertos: number; total: number }) => void }) {
  const tarjetas = useMemo(() => barajar(PASOS.map((p, i) => ({ ...p, i }))), []);
  const [siguiente, setSiguiente] = useState(0);
  const [errores, setErrores] = useState(0);
  const [fallo, setFallo] = useState<number | null>(null);
  const [petalos, setPetalos] = useState(0);
  const { x, sacudir } = useSacudir();

  const tocar = (i: number) => {
    if (i < siguiente) return;
    if (i === siguiente) {
      Haptics.selectionAsync();
      setFallo(null);
      const nuevo = siguiente + 1;
      setSiguiente(nuevo);
      if (nuevo === PASOS.length) {
        setPetalos((n) => n + 1);
        setTimeout(() => onFin({ aciertos: PASOS.length, total: PASOS.length + errores }), 900);
      }
    } else {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      setErrores((n) => n + 1);
      setFallo(i);
      sacudir();
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.pagina}>
        <BarraProgreso valor={siguiente / PASOS.length} color={VERDE} />
        <Text style={styles.pregunta}>¿Cuál es el paso {Math.min(siguiente + 1, PASOS.length)}?</Text>
        <Animated.View style={{ gap: espacio.s, transform: [{ translateX: x }] }}>
          {tarjetas.map((t) => {
            const hecho = t.i < siguiente;
            const malo = t.i === fallo;
            return (
              <Pressable
                key={t.titulo}
                accessibilityRole="button"
                onPress={() => tocar(t.i)}
                style={[styles.opcion, hecho && styles.opcionBien, malo && styles.opcionMal]}
              >
                {hecho ? (
                  <View style={[styles.numero, { backgroundColor: colores.acierto }]}>
                    <Text style={styles.numeroTexto}>{t.i + 1}</Text>
                  </View>
                ) : (
                  <Ionicons name="ellipse-outline" size={28} color={colores.gris} />
                )}
                <Text style={[styles.opcionTexto, hecho && { color: colores.aciertoOscuro }]}>{t.titulo}</Text>
              </Pressable>
            );
          })}
        </Animated.View>
      </ScrollView>
      <LluviaDePetalos disparo={petalos} />
    </View>
  );
}

function Preguntas({ onFin }: { onFin: (r: { aciertos: number; total: number }) => void }) {
  const lista = useMemo(() => barajar(PREGUNTAS), []);
  const [n, setN] = useState(0);
  const [elegida, setElegida] = useState<number | null>(null);
  const [aciertos, setAciertos] = useState(0);
  const [petalos, setPetalos] = useState(0);
  const { x, sacudir } = useSacudir();
  const p = lista[n];
  const bien = elegida === p.correcta;

  const elegir = (i: number) => {
    if (elegida !== null) return;
    setElegida(i);
    if (i === p.correcta) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setAciertos((a) => a + 1);
      setPetalos((v) => v + 1);
    } else {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      sacudir();
    }
  };

  const seguir = () => {
    if (n + 1 === lista.length) return onFin({ aciertos, total: lista.length });
    setN(n + 1);
    setElegida(null);
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.pagina}>
        <BarraProgreso valor={n / lista.length} />
        <Rebote clave={n}>
          <Text style={styles.pregunta}>{p.texto}</Text>
        </Rebote>
        <Animated.View style={{ gap: espacio.s, transform: [{ translateX: x }] }}>
          {p.opciones.map((o, i) => {
            const marcarBien = elegida !== null && i === p.correcta;
            const marcarMal = elegida === i && !bien;
            return (
              <Pressable
                key={o}
                accessibilityRole="button"
                onPress={() => elegir(i)}
                style={[styles.opcion, marcarBien && styles.opcionBien, marcarMal && styles.opcionMal]}
              >
                <Text style={styles.opcionTexto}>{o}</Text>
              </Pressable>
            );
          })}
        </Animated.View>
      </ScrollView>

      {elegida !== null && (
        <Aparecer estilo={[styles.hoja, { backgroundColor: bien ? colores.aciertoSuave : colores.errorSuave }]}>
          <Text style={[styles.pasoTitulo, { color: bien ? colores.aciertoOscuro : colores.errorOscuro }]}>
            {bien ? '¡Bien!' : 'Casi'}
          </Text>
          <Text style={styles.cuerpo}>{p.porque}</Text>
          <BotonGrande titulo="Seguir" color={bien ? colores.acierto : colores.error} onPress={seguir} />
        </Aparecer>
      )}
      <LluviaDePetalos disparo={petalos} />
    </View>
  );
}

function Fin({ aciertos, total, onVolver }: { aciertos: number; total: number; onVolver: () => void }) {
  const ratio = total ? aciertos / total : 0;
  return (
    <View style={styles.centro}>
      <Aparecer estilo={styles.cabeza}>
        <Ionicons name={ratio >= 0.8 ? 'trophy' : 'leaf'} size={72} color={ratio >= 0.8 ? colores.oro : VERDE} />
        <Text style={styles.titulo}>
          {aciertos} de {total}
        </Text>
        <Text style={styles.suave}>{ratio >= 0.8 ? '¡Muy bien! Ya lo tienes.' : 'Repásalo otra vez y vuelve a intentarlo.'}</Text>
        <BotonGrande titulo="Volver" onPress={onVolver} estilo={{ alignSelf: 'stretch' }} />
      </Aparecer>
    </View>
  );
}

const styles = StyleSheet.create({
  pagina: { padding: espacio.l, gap: espacio.m, paddingBottom: 220 },
  centro: { flex: 1, justifyContent: 'center', padding: espacio.xl },
  cabeza: { alignItems: 'center', gap: espacio.s },
  icono: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: VERDE,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 5,
    borderBottomColor: '#1B7C73',
  },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  suave: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.texto },
  paso: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    backgroundColor: colores.tarjeta,
    borderRadius: 18,
    borderWidth: 2,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  numero: { width: 36, height: 36, borderRadius: 18, backgroundColor: VERDE, justifyContent: 'center', alignItems: 'center' },
  numeroTexto: { color: '#fff', fontFamily: fuente.titulo, fontSize: texto.cuerpo },
  pasoTitulo: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto },
  botones: { gap: espacio.m, marginTop: espacio.s },
  nota: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.gris, textAlign: 'center' },
  pregunta: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  opcion: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    minHeight: 60,
    backgroundColor: colores.tarjeta,
    borderRadius: 18,
    borderWidth: 2,
    borderBottomWidth: 4,
    borderColor: colores.borde,
    paddingHorizontal: espacio.m,
    paddingVertical: espacio.s,
  },
  opcionBien: { borderColor: colores.acierto, backgroundColor: colores.aciertoSuave },
  opcionMal: { borderColor: colores.error, backgroundColor: colores.errorSuave },
  opcionTexto: { flex: 1, fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.texto },
  hoja: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    padding: espacio.l,
    gap: espacio.s,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
});
