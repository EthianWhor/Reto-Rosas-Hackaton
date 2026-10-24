import { Ionicons } from '@expo/vector-icons';
import { useCallback, useEffect, useState, type ComponentProps } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import type { Cuadrante, Prioridad, Reporte } from '@/data/reporte';
import { cargarReporte, fechaLarga, hora, type Origen } from '@/logica/reporte';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Turnero del día: con el reporte de la ronda nocturna del robot, dice a qué cuadrantes ir primero.
// Va en una tablet o pantalla fija a la entrada del invernadero.

const PRIORIDAD: Record<Prioridad, { color: string; nombre: string }> = {
  alta: { color: colores.primario, nombre: 'Cortar hoy' },
  media: { color: colores.oro, nombre: 'Pocas' },
  baja: { color: colores.gris, nombre: 'Nada' },
};

// Cuántos cuadrantes se listan por sección; el reparto completo está en "Mi turno" y en "Turno".
const MAXIMO = 10;

const ORIGEN: Record<Exclude<Origen, 'robot'>, string> = {
  guardado: 'Sin conexión · último reporte recibido',
  ejemplo: 'Datos de ejemplo',
};

export default function Hoy() {
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
  const paraHoy = [...reporte.cuadrantes].sort((a, b) => a.orden - b.orden).filter((c) => c.optimo > 0);
  const paraManana = reporte.cuadrantes.filter((c) => c.lista_manana > 0).sort((a, b) => b.lista_manana - a.lista_manana);
  const primero = paraHoy[0];
  const totalHoy = reporte.cuadrantes.reduce((s, c) => s + c.optimo, 0);
  const totalManana = reporte.cuadrantes.reduce((s, c) => s + c.lista_manana, 0);
  const dudosas = reporte.dudosas?.length ?? reporte.cuadrantes.reduce((s, c) => s + c.dudosa, 0);

  return (
    <ScrollView
      contentContainerStyle={styles.contenido}
      refreshControl={<RefreshControl refreshing={cargando} onRefresh={actualizar} colors={[colores.primario]} />}
    >
      <Aparecer>
        <Text style={styles.titulo}>{fechaLarga(reporte.fecha)}</Text>
        <Text style={styles.cuerpo}>
          Invernadero {reporte.invernadero} · ronda de {hora(reporte.inicio)} a {hora(reporte.fin)}
        </Text>
        {origen !== 'robot' && (
          <View style={styles.chip}>
            <Text style={styles.chipTexto}>{ORIGEN[origen]}</Text>
          </View>
        )}
      </Aparecer>

      <Aparecer retraso={100}>
        {primero ? (
          <View style={styles.destacado}>
            <Text style={styles.etiqueta}>Ve primero a</Text>
            <Text style={styles.grande}>Cama {primero.cama}</Text>
            <Text style={styles.destacadoTexto}>
              metros {primero.desde_m}–{primero.hasta_m} · {primero.optimo} rosas listas
            </Text>
          </View>
        ) : (
          <View style={[styles.destacado, { backgroundColor: colores.gris, borderBottomColor: colores.grisOscuro }]}>
            <Text style={styles.destacadoTexto}>Hoy no hay rosas en punto 3.</Text>
          </View>
        )}
      </Aparecer>

      <Aparecer retraso={200} estilo={styles.resumen}>
        <Dato icono="cut" valor={totalHoy} texto="Hoy" color={colores.primario} />
        <Dato icono="sunny" valor={totalManana} texto="Mañana" color={colores.oro} />
        <Dato icono="help-circle" valor={dudosas} texto="Dudosas" color={colores.gris} />
      </Aparecer>

      <Text style={styles.seccion}>Orden de corte</Text>
      {paraHoy.slice(0, MAXIMO).map((c, i) => (
        <Aparecer key={c.cuadrante_id} retraso={250 + i * 40}>
          <Fila c={c} numero={c.orden} color={PRIORIDAD[c.prioridad].color} detalle={`${c.optimo} listas`} />
        </Aparecer>
      ))}
      {paraHoy.length > MAXIMO && <Text style={styles.mas}>+{paraHoy.length - MAXIMO} cuadrantes más</Text>}

      {paraManana.length > 0 && (
        <>
          <Text style={styles.seccion}>Mañana</Text>
          {paraManana.slice(0, MAXIMO).map((c) => (
            <Fila key={c.cuadrante_id} c={c} numero={c.lista_manana} color={colores.oro} detalle={`${c.lista_manana} listas mañana`} />
          ))}
          {paraManana.length > MAXIMO && <Text style={styles.mas}>+{paraManana.length - MAXIMO} cuadrantes más</Text>}
        </>
      )}

      {reporte.obstaculos.length > 0 && (
        <View style={styles.aviso}>
          <Ionicons name="warning" size={22} color={colores.error} />
          <Text style={styles.avisoTexto}>Obstáculo en {reporte.obstaculos.join(', ')}</Text>
        </View>
      )}

      <BotonGrande titulo="Actualizar" icono="refresh" claro color={colores.primario} onPress={actualizar} deshabilitado={cargando} />
    </ScrollView>
  );
}

function Dato({ icono, valor, texto: etiqueta, color }: { icono: ComponentProps<typeof Ionicons>['name']; valor: number; texto: string; color: string }) {
  return (
    <View style={[styles.dato, { borderColor: color }]}>
      <Ionicons name={icono} size={24} color={color} />
      <Text style={[styles.numero, { color }]}>{valor}</Text>
      <Text style={styles.datoEtiqueta}>{etiqueta}</Text>
    </View>
  );
}

function Fila({ c, numero, color, detalle }: { c: Cuadrante; numero: number; color: string; detalle: string }) {
  return (
    <View style={styles.fila}>
      <View style={[styles.turno, { backgroundColor: color }]}>
        <Text style={styles.turnoTexto}>{numero}</Text>
      </View>
      <View style={styles.filaTexto}>
        <Text style={styles.filaTitulo}>Cama {c.cama}</Text>
        <Text style={styles.cuerpo}>
          metros {c.desde_m}–{c.hasta_m} · {detalle}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 820, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  chip: { alignSelf: 'flex-start', backgroundColor: colores.rosaSuave, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3, marginTop: espacio.s },
  chipTexto: { fontSize: 13, fontFamily: fuente.negrita, color: colores.rosaOscuro },
  destacado: {
    backgroundColor: colores.primario,
    borderRadius: 26,
    borderBottomWidth: 6,
    borderBottomColor: colores.primarioOscuro,
    padding: espacio.l,
    alignItems: 'center',
    gap: 2,
  },
  etiqueta: { fontSize: texto.pequeno, fontFamily: fuente.negrita, color: 'rgba(255,255,255,0.85)', textTransform: 'uppercase', letterSpacing: 1.5 },
  grande: { fontSize: 58, fontFamily: fuente.titulo, color: '#fff' },
  destacadoTexto: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: '#fff', textAlign: 'center' },
  resumen: { flexDirection: 'row', gap: espacio.m },
  dato: { flex: 1, backgroundColor: colores.tarjeta, borderRadius: 18, borderWidth: 2, padding: espacio.m, alignItems: 'center' },
  numero: { fontSize: 32, fontFamily: fuente.titulo },
  datoEtiqueta: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.textoSuave },
  seccion: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, marginTop: espacio.m },
  fila: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, backgroundColor: colores.tarjeta, borderRadius: 18, padding: espacio.m, ...sombra },
  turno: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  turnoTexto: { color: '#fff', fontSize: texto.subtitulo, fontFamily: fuente.titulo },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto },
  mas: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.textoSuave, textAlign: 'center' },
  aviso: { flexDirection: 'row', alignItems: 'center', gap: espacio.s, backgroundColor: colores.errorSuave, borderRadius: 16, padding: espacio.m },
  avisoTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error, flex: 1 },
});
