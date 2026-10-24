import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Image } from 'expo-image';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { Aparecer, BarraProgreso, LluviaDePetalos } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { CATEGORIAS } from '@/data/categorias';
import type { Reporte } from '@/data/reporte';
import { ROSAS } from '@/data/rosas';
import type { CategoriaId } from '@/data/tipos';
import { etiquetarDudosa, leerRevisadas } from '@/logica/dudosas';
import { useOperario } from '@/logica/operario';
import { cargarReporte, type Origen } from '@/logica/reporte';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

type Dudosa = NonNullable<Reporte['dudosas']>[number];

// Foto de la rosa dudosa. Cuando el robot suba sus fotos, `foto` traerá una dirección web; mientras
// tanto (o con el reporte de ejemplo) se usa una foto real de la finca como muestra.
function fotoDe(d: Dudosa) {
  if (d.foto?.startsWith('http')) return { uri: d.foto };
  let h = 0;
  for (const ch of d.rosa_id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return ROSAS[h % ROSAS.length].imagen;
}

const cama = (cuadranteId?: string) => {
  const m = cuadranteId?.match(/C(\d+)-T(\d+)/);
  return m ? `Cama ${Number(m[1])} · metros ${(Number(m[2]) - 1) * 5}–${Number(m[2]) * 5}` : 'Ubicación sin dato';
};

// El robot pregunta, el experto responde: cada respuesta se guarda para reentrenar a RosaNet.
export default function Revisar() {
  const { token } = useOperario();
  const { width } = useWindowDimensions();
  const [datos, setDatos] = useState<{ reporte: Reporte; origen: Origen; pendientes: Dudosa[]; total: number } | null>(null);
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [gracias, setGracias] = useState(0);

  const cargar = useCallback(async () => {
    try {
      const { reporte, origen } = await cargarReporte();
      const todas = reporte.dudosas ?? [];
      const revisadas = await leerRevisadas(reporte.id_ronda);
      setDatos({ reporte, origen, pendientes: todas.filter((d) => !revisadas.has(d.rosa_id)), total: todas.length });
      setError('');
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      cargar();
    }, [cargar]),
  );

  if (!datos) {
    return (
      <View style={styles.centro}>
        {error ? <Text style={styles.error}>{error}</Text> : <ActivityIndicator size="large" color={colores.primario} />}
      </View>
    );
  }

  const actual = datos.pendientes[0];
  const hechas = datos.total - datos.pendientes.length;

  async function responder(categoria: CategoriaId) {
    if (!actual || !token || guardando) return;
    setGuardando(true);
    try {
      await etiquetarDudosa(token, datos!.reporte.id_ronda, actual.rosa_id, actual.cuadrante_id, categoria);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      setGracias((g) => g + 1);
      setDatos({ ...datos!, pendientes: datos!.pendientes.slice(1) });
      setError('');
    } catch (e) {
      setError((e as Error).message);
    }
    setGuardando(false);
  }

  if (!actual) {
    return (
      <View style={styles.centro}>
        <Aparecer estilo={styles.centrado}>
          <View style={styles.listo}>
            <Ionicons name="checkmark-done" size={60} color="#fff" />
          </View>
          <Text style={styles.titulo}>Todo revisado</Text>
          <Text style={[styles.cuerpo, { textAlign: 'center' }]}>Gracias: tus respuestas entrenan al robot.</Text>
          <BotonGrande titulo="Volver" claro color={colores.primario} onPress={() => router.back()} />
        </Aparecer>
        <LluviaDePetalos disparo={gracias} cantidad={30} />
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.contenido}>
        <View style={styles.encabezado}>
          <Text style={styles.contador}>
            {hechas + 1} de {datos.total}
          </Text>
          <View style={{ flex: 1 }}>
            <BarraProgreso valor={hechas / Math.max(datos.total, 1)} color={colores.oro} />
          </View>
        </View>

        <Aparecer key={actual.rosa_id} estilo={styles.tarjeta}>
          <Image source={fotoDe(actual)} style={{ width: '100%', height: Math.min(width - 48, 420) }} contentFit="cover" transition={200} />
          <View style={styles.info}>
            <View style={styles.pregunta}>
              <Ionicons name="hardware-chip" size={22} color="#7E57C2" />
              <Text style={styles.preguntaTexto}>El robot no está seguro. ¿Cómo está esta rosa?</Text>
            </View>
            <Text style={styles.cuerpo}>
              {cama(actual.cuadrante_id)}
              {actual.confianza != null ? ` · seguro al ${Math.round(actual.confianza * 100)} %` : ''}
            </Text>
            {datos.origen === 'ejemplo' && <Text style={styles.nota}>Foto de muestra (datos de ejemplo)</Text>}
          </View>
        </Aparecer>

        {!!error && <Text style={styles.error}>{error}</Text>}
        <View style={styles.opciones}>
          {CATEGORIAS.map((c) => (
            <BotonGrande
              key={c.id}
              titulo={c.boton}
              icono={c.icono}
              color={c.color}
              deshabilitado={guardando}
              onPress={() => responder(c.id)}
            />
          ))}
        </View>
      </ScrollView>
      <LluviaDePetalos disparo={gracias} cantidad={10} />
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  centrado: { alignItems: 'center', gap: espacio.m, maxWidth: 400 },
  listo: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colores.acierto,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 6,
    borderBottomColor: colores.aciertoOscuro,
  },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 640, width: '100%', alignSelf: 'center' },
  encabezado: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  contador: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.textoSuave },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 24, overflow: 'hidden', ...sombra },
  info: { padding: espacio.m, gap: espacio.xs },
  pregunta: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  preguntaTexto: { flex: 1, fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  nota: { fontSize: 13, fontFamily: fuente.normal, color: colores.gris },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error, textAlign: 'center' },
  opciones: { gap: espacio.m },
});
