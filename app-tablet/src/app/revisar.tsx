import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Image } from 'expo-image';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { Aparecer, BarraProgreso, LluviaDePetalos } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { CATEGORIAS } from '@/data/categorias';
import type { CategoriaId } from '@/data/tipos';
import { cargarDudosas, etiquetarDudosa, type Dudosa } from '@/logica/dudosas';
import { useOperario } from '@/logica/operario';
import { supabase } from '@/logica/supabase';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const donde = (d: Dudosa) => {
  if (d.enVivo) return `Foto en vivo del robot${d.fecha_hora ? ` · ${d.fecha_hora.slice(11, 16)}` : ''}`;
  const m = d.cuadrante_id?.match(/C(\d+)-T(\d+)/);
  return m ? `Cama ${Number(m[1])} · metros ${(Number(m[2]) - 1) * 5}–${Number(m[2]) * 5}` : 'Ubicación sin dato';
};

// El robot pregunta, el experto responde: cada respuesta se guarda para reentrenar a RosaNet.
// Solo fotos reales que subió el robot; cuando llega un reporte nuevo, la lista se actualiza sola.
export default function Revisar() {
  const { token } = useOperario();
  const { width } = useWindowDimensions();
  const [datos, setDatos] = useState<{ pendientes: Dudosa[]; total: number } | null>(null);
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [gracias, setGracias] = useState(0);

  const cargar = useCallback(async () => {
    try {
      setDatos(await cargarDudosas());
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

  useEffect(() => {
    const canal = supabase
      .channel('dudosas')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'reportes' }, () => cargar())
      .subscribe();
    return () => {
      supabase.removeChannel(canal);
    };
  }, [cargar]);

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
      await etiquetarDudosa(token, actual.id_ronda, actual.rosa_id, actual.cuadrante_id, categoria);
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
          <Text style={[styles.cuerpo, { textAlign: 'center' }]}>
            Gracias: tus respuestas entrenan al robot. Si el robot duda de otra rosa, aparece aquí sola.
          </Text>
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

        <Aparecer key={actual.id_ronda + actual.rosa_id} estilo={styles.tarjeta}>
          {actual.foto?.startsWith('http') ? (
            <Image
              source={{ uri: actual.foto }}
              style={{ width: '100%', height: Math.min(width - 48, 420) }}
              contentFit="cover"
              transition={200}
            />
          ) : (
            <View style={[styles.sinFoto, { height: Math.min(width - 48, 260) }]}>
              <Ionicons name="image-outline" size={48} color={colores.gris} />
              <Text style={styles.nota}>El robot no subió la foto de esta rosa</Text>
            </View>
          )}
          <View style={styles.info}>
            <View style={styles.pregunta}>
              <Ionicons name={actual.enVivo ? 'radio' : 'hardware-chip'} size={22} color="#7E57C2" />
              <Text style={styles.preguntaTexto}>El robot no está seguro. ¿Cómo está esta rosa?</Text>
            </View>
            <Text style={styles.cuerpo}>
              {donde(actual)}
              {actual.confianza != null ? ` · seguro al ${Math.round(actual.confianza * 100)} %` : ''}
            </Text>
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
  sinFoto: { alignItems: 'center', justifyContent: 'center', gap: espacio.s, backgroundColor: colores.rosaSuave },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error, textAlign: 'center' },
  opciones: { gap: espacio.m },
});
