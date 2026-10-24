import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Animated, Easing, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Aparecer, BarraProgreso, LluviaDePetalos, Rebote, useSacudir } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { categoria, CATEGORIAS } from '@/data/categorias';
import type { CategoriaId } from '@/data/tipos';
import { useOperario } from '@/logica/operario';
import { guardarRonda, type Respuesta } from '@/logica/progreso';
import { armarRonda } from '@/logica/ronda';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const PUNTOS_POR_ACIERTO = 10;
const FELICITACIONES = ['¡Muy bien!', '¡Excelente!', '¡Buen ojo!', '¡Así es!', '¡Perfecto!'];

// Práctica tipo Duolingo: una rosa real de la finca, tres opciones y respuesta inmediata.
export default function Practicar() {
  const { nombre, token } = useOperario();
  const { width, height } = useWindowDimensions();
  const arriba = useSafeAreaInsets().top;
  const horizontal = width > height && width > 700;

  const [ronda, setRonda] = useState(() => armarRonda());
  const [indice, setIndice] = useState(0);
  const [respuestas, setRespuestas] = useState<Respuesta[]>([]);
  const [elegida, setElegida] = useState<CategoriaId | null>(null);
  const [racha, setRacha] = useState(0);
  const [mejorRacha, setMejorRacha] = useState(0);
  const [petalos, setPetalos] = useState(0);
  const [felicitacion, setFelicitacion] = useState(FELICITACIONES[0]);
  const inicioPregunta = useRef(Date.now());
  const { x: sacudida, sacudir } = useSacudir();
  const hoja = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(hoja, {
      toValue: elegida ? 1 : 0,
      duration: elegida ? 320 : 0,
      easing: Easing.out(Easing.back(1.2)),
      useNativeDriver: true,
    }).start();
  }, [elegida, hoja]);

  if (ronda.length === 0) {
    return (
      <View style={[styles.centro, { paddingTop: arriba }]}>
        <Text style={styles.titulo}>No hay fotos cargadas</Text>
      </View>
    );
  }

  const aciertos = respuestas.filter((r) => r.correcta === r.elegida).length;

  if (indice >= ronda.length) {
    return (
      <Final
        aciertos={aciertos}
        total={ronda.length}
        mejorRacha={mejorRacha}
        arriba={arriba}
        otraRonda={reiniciar}
      />
    );
  }

  const rosa = ronda[indice];
  const correcta = categoria(rosa.categoria);
  const acerto = elegida === rosa.categoria;

  function responder(id: CategoriaId) {
    if (elegida) return;
    const bien = id === rosa.categoria;
    setElegida(id);
    setRespuestas((prev) => [
      ...prev,
      { rosaId: rosa.id, correcta: rosa.categoria, elegida: id, ms: Date.now() - inicioPregunta.current },
    ]);
    if (bien) {
      const nueva = racha + 1;
      setRacha(nueva);
      setMejorRacha((m) => Math.max(m, nueva));
      setFelicitacion(nueva >= 3 ? `¡${nueva} seguidas!` : FELICITACIONES[Math.floor(Math.random() * FELICITACIONES.length)]);
      setPetalos((p) => p + 1);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } else {
      setRacha(0);
      sacudir();
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
    }
  }

  function siguiente() {
    const nuevoIndice = indice + 1;
    if (nuevoIndice >= ronda.length) {
      guardarRonda(token, { fecha: new Date().toISOString(), operario: nombre, respuestas }).catch(() => {});
    }
    setElegida(null);
    setIndice(nuevoIndice);
    inicioPregunta.current = Date.now();
  }

  function reiniciar() {
    setRonda(armarRonda());
    setIndice(0);
    setRespuestas([]);
    setElegida(null);
    setRacha(0);
    setMejorRacha(0);
    inicioPregunta.current = Date.now();
  }

  const colorHoja = acerto ? colores.acierto : colores.error;

  return (
    <View style={[styles.pantalla, { paddingTop: arriba + espacio.s }]}>
      {/* Barra superior: salir, avance y racha */}
      <View style={styles.barraSuperior}>
        <Pressable accessibilityRole="button" accessibilityLabel="Salir de la práctica" onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))} hitSlop={12}>
          <Ionicons name="close" size={32} color={colores.gris} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <BarraProgreso valor={(indice + (elegida ? 1 : 0)) / ronda.length} color={colores.rosa} />
        </View>
        <Rebote clave={racha} estilo={styles.racha}>
          <Ionicons name="rose" size={24} color={racha > 0 ? colores.primario : colores.borde} />
          <Text style={[styles.rachaTexto, { color: racha > 0 ? colores.primario : colores.gris }]}>{racha}</Text>
        </Rebote>
      </View>

      <ScrollView contentContainerStyle={[styles.contenido, horizontal && styles.fila]}>
        <View style={horizontal ? styles.mitad : undefined}>
          <Text style={styles.pregunta}>¿Cómo está esta rosa?</Text>
          <Animated.View style={[styles.marcoFoto, { transform: [{ translateX: sacudida }] }]}>
            <Image
              source={rosa.imagen}
              style={{ width: '100%', height: horizontal ? height * 0.55 : Math.min(width - 48, 420) }}
              contentFit="cover"
              transition={200}
            />
          </Animated.View>
        </View>

        <View style={[styles.opciones, horizontal && styles.mitad]}>
          {CATEGORIAS.map((c) => {
            const atenuada = elegida && c.id !== rosa.categoria && c.id !== elegida;
            return (
              <View key={c.id} style={{ opacity: atenuada ? 0.35 : 1 }}>
                <BotonGrande titulo={c.boton} icono={c.icono} color={c.color} onPress={() => responder(c.id)} />
              </View>
            );
          })}
        </View>
      </ScrollView>

      {/* Hoja de respuesta que sube desde abajo */}
      {elegida && (
        <Animated.View
          style={[
            styles.hoja,
            { backgroundColor: acerto ? colores.aciertoSuave : colores.errorSuave },
            { transform: [{ translateY: hoja.interpolate({ inputRange: [0, 1], outputRange: [260, 0] }) }] },
          ]}
        >
          <View style={styles.hojaCabeza}>
            <Rebote clave={indice} estilo={[styles.hojaIcono, { backgroundColor: colorHoja }]}>
              <Ionicons name={acerto ? 'checkmark' : 'close'} size={30} color="#fff" />
            </Rebote>
            <View style={{ flex: 1 }}>
              <Text style={[styles.hojaTitulo, { color: colorHoja }]}>{acerto ? felicitacion : `Era: ${correcta.boton}`}</Text>
              <Text style={styles.hojaTexto}>{acerto ? correcta.mirar.join(' · ') : correcta.pista}</Text>
            </View>
            {acerto && (
              <Rebote clave={indice} estilo={styles.puntos}>
                <Text style={styles.puntosTexto}>+{PUNTOS_POR_ACIERTO}</Text>
              </Rebote>
            )}
          </View>
          {!acerto && (
            <View style={styles.chips}>
              {correcta.mirar.map((m) => (
                <View key={m} style={[styles.chip, { borderColor: colorHoja }]}>
                  <Text style={[styles.chipTexto, { color: colorHoja }]}>{m}</Text>
                </View>
              ))}
            </View>
          )}
          <BotonGrande titulo="Continuar" color={colorHoja} onPress={siguiente} />
        </Animated.View>
      )}

      <LluviaDePetalos disparo={petalos} cantidad={racha >= 3 ? 30 : 16} />
    </View>
  );
}

function Final({
  aciertos,
  total,
  mejorRacha,
  arriba,
  otraRonda,
}: {
  aciertos: number;
  total: number;
  mejorRacha: number;
  arriba: number;
  otraRonda: () => void;
}) {
  const proporcion = aciertos / total;
  const escala = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.spring(escala, { toValue: 1, friction: 4, tension: 80, useNativeDriver: true }).start();
  }, [escala]);

  const titulo = proporcion >= 0.9 ? '¡Ojo de experto!' : proporcion >= 0.6 ? '¡Bien hecho!' : '¡Sigue practicando!';

  return (
    <View style={[styles.final, { paddingTop: arriba + espacio.xl }]}>
      <Animated.View style={[styles.trofeo, { transform: [{ scale: escala }] }]}>
        <Ionicons name={proporcion >= 0.6 ? 'rose' : 'leaf'} size={72} color="#fff" />
      </Animated.View>
      <Aparecer retraso={150}>
        <Text style={styles.finalTitulo}>{titulo}</Text>
      </Aparecer>
      <Aparecer retraso={300} estilo={styles.datos}>
        <Dato icono="checkmark-circle" color={colores.acierto} valor={`${aciertos}/${total}`} etiqueta="Correctas" />
        <Dato icono="star" color={colores.oro} valor={`${aciertos * PUNTOS_POR_ACIERTO}`} etiqueta="Puntos" />
        <Dato icono="rose" color={colores.primario} valor={`${mejorRacha}`} etiqueta="Mejor racha" />
      </Aparecer>
      <Aparecer retraso={450} estilo={styles.acciones}>
        <BotonGrande titulo="Otra ronda" icono="refresh" onPress={otraRonda} />
        <BotonGrande titulo="Mi progreso" claro color={colores.primario} onPress={() => router.replace('/progreso')} />
      </Aparecer>
      <LluviaDePetalos disparo={proporcion >= 0.6 ? 1 : 0} cantidad={40} />
    </View>
  );
}

function Dato({ icono, color, valor, etiqueta }: { icono: 'star' | 'rose' | 'checkmark-circle'; color: string; valor: string; etiqueta: string }) {
  return (
    <View style={[styles.dato, { borderColor: color }]}>
      <Ionicons name={icono} size={26} color={color} />
      <Text style={[styles.datoValor, { color }]}>{valor}</Text>
      <Text style={styles.datoEtiqueta}>{etiqueta}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: colores.fondo },
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  barraSuperior: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, paddingHorizontal: espacio.l, paddingBottom: espacio.s },
  racha: { flexDirection: 'row', alignItems: 'center', gap: 4, minWidth: 48 },
  rachaTexto: { fontSize: texto.subtitulo, fontFamily: fuente.titulo },
  contenido: { padding: espacio.l, paddingBottom: 280, gap: espacio.l, maxWidth: 1100, width: '100%', alignSelf: 'center' },
  fila: { flexDirection: 'row', alignItems: 'flex-start' },
  mitad: { flex: 1 },
  pregunta: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto, marginBottom: espacio.m },
  marcoFoto: { borderRadius: 24, overflow: 'hidden', borderWidth: 4, borderColor: colores.tarjeta, ...sombra },
  opciones: { gap: espacio.m, justifyContent: 'center' },
  hoja: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    padding: espacio.l,
    paddingBottom: espacio.xl,
    gap: espacio.m,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
  },
  hojaCabeza: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  hojaIcono: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
  hojaTitulo: { fontSize: 24, fontFamily: fuente.titulo },
  hojaTexto: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.texto, marginTop: 2 },
  puntos: { backgroundColor: colores.oro, borderRadius: 14, paddingHorizontal: 12, paddingVertical: 6 },
  puntosTexto: { color: '#fff', fontFamily: fuente.titulo, fontSize: 18 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.s },
  chip: { borderWidth: 2, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 4, backgroundColor: colores.tarjeta },
  chipTexto: { fontFamily: fuente.negrita, fontSize: 15 },
  final: { flex: 1, alignItems: 'center', padding: espacio.l, gap: espacio.l, backgroundColor: colores.fondo },
  trofeo: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: colores.primario,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 8,
    borderBottomColor: colores.primarioOscuro,
  },
  finalTitulo: { fontSize: 34, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  datos: { flexDirection: 'row', gap: espacio.m, flexWrap: 'wrap', justifyContent: 'center' },
  dato: {
    width: 110,
    paddingVertical: espacio.m,
    borderRadius: 18,
    borderWidth: 2,
    backgroundColor: colores.tarjeta,
    alignItems: 'center',
    gap: 2,
  },
  datoValor: { fontSize: 24, fontFamily: fuente.titulo },
  datoEtiqueta: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.textoSuave },
  acciones: { gap: espacio.m, width: '100%', maxWidth: 420, marginTop: espacio.m },
});
