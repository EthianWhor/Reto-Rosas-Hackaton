import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import type { Cuadrante, Prioridad, Reporte } from '@/data/reporte';
import { cargarReporte, fechaLarga, hora, type Origen } from '@/logica/reporte';
import { useOperario } from '@/logica/operario';
import { colores, espacio, texto } from '@/tema';

// Turnero del día: con el reporte de la ronda nocturna del robot, dice a qué cuadrantes ir primero.
// Va en una tablet o pantalla fija a la entrada del invernadero.

const PRIORIDAD: Record<Prioridad, { color: string; nombre: string }> = {
  alta: { color: '#C0392B', nombre: 'Cortar hoy' },
  media: { color: '#E08E2B', nombre: 'Pocas listas' },
  baja: { color: '#8D8378', nombre: 'Nada para cortar' },
};

// Cuántos cuadrantes se listan por sección; el reparto completo está en "Mi turno" y en "Turno".
const MAXIMO = 10;

const ORIGEN: Record<Origen, string> = {
  robot: 'Reporte recibido del robot',
  guardado: 'Sin conexión: se muestra el último reporte recibido',
  ejemplo: 'Reporte de ejemplo (el robot todavía no ha enviado uno)',
};

export default function Hoy() {
  const { nombre } = useOperario();
  const [datos, setDatos] = useState<{ reporte: Reporte; origen: Origen } | null>(null);
  const [cargando, setCargando] = useState(false);

  const actualizar = useCallback(async () => {
    setCargando(true);
    setDatos(await cargarReporte());
    setCargando(false);
  }, []);

  useEffect(() => {
    actualizar();
  }, [actualizar]);

  if (!datos) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  const { reporte, origen } = datos;
  const enOrden = [...reporte.cuadrantes].sort((a, b) => a.orden - b.orden);
  const paraHoy = enOrden.filter((c) => c.optimo > 0);
  const paraManana = [...reporte.cuadrantes].filter((c) => c.lista_manana > 0).sort((a, b) => b.lista_manana - a.lista_manana);
  const primero = paraHoy[0];
  const totalHoy = reporte.cuadrantes.reduce((s, c) => s + c.optimo, 0);
  const totalManana = reporte.cuadrantes.reduce((s, c) => s + c.lista_manana, 0);
  const dudosas = reporte.dudosas?.length ?? reporte.cuadrantes.reduce((s, c) => s + c.dudosa, 0);

  return (
    <ScrollView
      contentContainerStyle={styles.contenido}
      refreshControl={<RefreshControl refreshing={cargando} onRefresh={actualizar} />}
    >
      <Text style={styles.titulo}>{nombre ? `${nombre}, hoy` : 'Hoy'} · {fechaLarga(reporte.fecha)}</Text>
      <Text style={styles.cuerpo}>
        Invernadero {reporte.invernadero} · ronda del robot de {hora(reporte.inicio)} a {hora(reporte.fin)}
      </Text>

      {primero ? (
        <View style={[styles.destacado, { borderColor: PRIORIDAD[primero.prioridad].color }]}>
          <Text style={styles.etiqueta}>Ve primero a</Text>
          <Text style={styles.grande}>Cama {primero.cama}</Text>
          <Text style={styles.subtitulo}>
            metros {primero.desde_m} a {primero.hasta_m} · {primero.optimo} rosas en punto 3
          </Text>
          <Text style={styles.codigo}>{primero.cuadrante_id}</Text>
        </View>
      ) : (
        <View style={[styles.destacado, { borderColor: PRIORIDAD.baja.color }]}>
          <Text style={styles.subtitulo}>Hoy el robot no encontró rosas en punto 3.</Text>
        </View>
      )}

      <View style={styles.resumen}>
        <Dato valor={totalHoy} texto="listas hoy" color={PRIORIDAD.alta.color} />
        <Dato valor={totalManana} texto="listas mañana" color={PRIORIDAD.media.color} />
        <Dato valor={dudosas} texto="para revisar" color={colores.textoSuave} />
      </View>

      <Text style={styles.seccion}>Orden de corte de hoy</Text>
      {paraHoy.slice(0, MAXIMO).map((c) => (
        <FilaCuadrante key={c.cuadrante_id} c={c} detalle={`${c.optimo} en punto 3 · ${c.lista_manana} para mañana`} />
      ))}
      {paraHoy.length > MAXIMO && <Text style={styles.cuerpo}>y {paraHoy.length - MAXIMO} cuadrantes más con rosas para hoy</Text>}

      {paraManana.length > 0 && (
        <>
          <Text style={styles.seccion}>Mañana</Text>
          {paraManana.slice(0, MAXIMO).map((c) => (
            <FilaCuadrante key={c.cuadrante_id} c={c} manana detalle={`${c.lista_manana} rosas llegan al punto 3 mañana`} />
          ))}
          {paraManana.length > MAXIMO && <Text style={styles.cuerpo}>y {paraManana.length - MAXIMO} cuadrantes más</Text>}
        </>
      )}

      {reporte.obstaculos.length > 0 && (
        <Text style={styles.aviso}>
          ⚠ El robot encontró obstáculos en {reporte.obstaculos.join(', ')}. Revisar el paso.
        </Text>
      )}

      <Text style={styles.origen}>{ORIGEN[origen]}</Text>
      <BotonGrande titulo="Actualizar" color="#455A64" onPress={actualizar} deshabilitado={cargando} />
    </ScrollView>
  );
}

function Dato({ valor, texto: etiqueta, color }: { valor: number; texto: string; color: string }) {
  return (
    <View style={styles.dato}>
      <Text style={[styles.numero, { color }]}>{valor}</Text>
      <Text style={styles.cuerpo}>{etiqueta}</Text>
    </View>
  );
}

// En "Mañana" no se muestra el turno ni la prioridad de hoy, para no confundir.
function FilaCuadrante({ c, detalle, manana }: { c: Cuadrante; detalle: string; manana?: boolean }) {
  const p = manana ? { color: PRIORIDAD.media.color, nombre: 'Mañana' } : PRIORIDAD[c.prioridad];
  return (
    <View style={styles.fila}>
      <View style={[styles.turno, { backgroundColor: p.color }]}>
        <Text style={styles.turnoTexto}>{manana ? c.lista_manana : c.orden}</Text>
      </View>
      <View style={styles.filaTexto}>
        <Text style={styles.filaTitulo}>
          Cama {c.cama} · metros {c.desde_m}–{c.hasta_m}
        </Text>
        <Text style={styles.cuerpo}>{detalle}</Text>
      </View>
      <Text style={[styles.prioridad, { color: p.color }]}>{p.nombre}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 900, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  subtitulo: { fontSize: texto.subtitulo, color: colores.texto, textAlign: 'center' },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  destacado: {
    backgroundColor: colores.tarjeta,
    borderWidth: 4,
    borderRadius: 20,
    padding: espacio.l,
    alignItems: 'center',
    gap: espacio.s,
  },
  etiqueta: { fontSize: texto.cuerpo, color: colores.textoSuave, textTransform: 'uppercase', letterSpacing: 1 },
  grande: { fontSize: 56, fontWeight: '900', color: colores.texto },
  codigo: { fontSize: 15, color: colores.textoSuave },
  resumen: { flexDirection: 'row', gap: espacio.m },
  dato: {
    flex: 1,
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colores.borde,
    padding: espacio.m,
    alignItems: 'center',
  },
  numero: { fontSize: 40, fontWeight: '800' },
  seccion: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto, marginTop: espacio.m },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  turno: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
  turnoTexto: { color: '#fff', fontSize: texto.subtitulo, fontWeight: '800' },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  prioridad: { fontSize: 16, fontWeight: '700' },
  aviso: { fontSize: texto.cuerpo, color: colores.error, marginTop: espacio.m },
  origen: { fontSize: 15, color: colores.textoSuave, textAlign: 'center', marginTop: espacio.l },
});
