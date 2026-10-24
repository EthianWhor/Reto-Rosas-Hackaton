import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { useOperario } from '@/logica/operario';
import { fechaLarga } from '@/logica/reporte';
import { duracion } from '@/logica/turno';
import { useTurno } from '@/logica/useTurno';
import { colores, espacio, texto } from '@/tema';

// Los cuadrantes que le tocan al trabajador con la sesión abierta, en orden. Cada uno se marca
// con un toque cuando termina de cortarlo.

export default function MiTurno() {
  const { usuario } = useOperario();
  const { datos, reparto, error, cambiarHecho } = useTurno();

  if (!usuario) return <Text style={styles.vacio}>Entra con tu nombre para ver tu turno.</Text>;
  if (!datos && error) return <Text style={styles.vacio}>{error}</Text>;
  if (!datos || !reparto) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  const mio = reparto.porTrabajador[usuario.id];
  if (!datos.presentes.includes(usuario.id) || !mio) {
    return (
      <Text style={styles.vacio}>
        Hoy no apareces en el turno. Si viniste, pídele a la coordinadora que te marque como presente.
      </Text>
    );
  }

  const hechas = mio.tareas.filter((t) => datos.hechos[t.cuadrante.cuadrante_id]).length;
  const rosas = mio.tareas.reduce((s, t) => s + t.cuadrante.optimo, 0);

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>{usuario.nombre}, tu turno · {fechaLarga(datos.reporte.fecha)}</Text>
      {!!error && <Text style={styles.error}>{error}</Text>}
      {mio.tareas.length === 0 ? (
        <Text style={styles.cuerpo}>
          Hoy no te tocó ningún cuadrante para cortar. Pregúntale a la coordinadora en qué apoyar.
        </Text>
      ) : (
        <>
          <Text style={styles.cuerpo}>
            {mio.tareas.length} cuadrantes · {rosas} rosas en punto 3 · unas {duracion(mio.minutos)}
          </Text>
          <View style={styles.barra}>
            <View style={[styles.relleno, { flex: hechas }]} />
            <View style={{ flex: mio.tareas.length - hechas }} />
          </View>
          <Text style={styles.cuerpo}>
            Llevas {hechas} de {mio.tareas.length}
            {hechas === mio.tareas.length ? ' · ¡Terminaste! Avísale a la coordinadora.' : ''}
          </Text>

          {mio.tareas.map(({ cuadrante: c, minutos }, i) => {
            const hecho = !!datos.hechos[c.cuadrante_id];
            return (
              <Pressable
                key={c.cuadrante_id}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: hecho }}
                onPress={() => cambiarHecho(c.cuadrante_id, usuario.id, !hecho)}
                style={({ pressed }) => [styles.fila, hecho && styles.filaHecha, pressed && { opacity: 0.7 }]}
              >
                <View style={[styles.check, hecho && styles.checkHecho]}>
                  <Text style={styles.checkTexto}>{hecho ? '✓' : i + 1}</Text>
                </View>
                <View style={styles.filaTexto}>
                  <Text style={[styles.filaTitulo, hecho && styles.tachado]}>
                    Cama {c.cama} · metros {c.desde_m}–{c.hasta_m}
                  </Text>
                  <Text style={styles.cuerpo}>
                    {c.optimo} rosas en punto 3 · ~{duracion(minutos)}
                  </Text>
                </View>
                <Text style={styles.accion}>{hecho ? 'Hecho' : 'Marcar'}</Text>
              </Pressable>
            );
          })}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 900, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  vacio: { fontSize: texto.subtitulo, color: colores.texto, padding: espacio.xl, textAlign: 'center' },
  error: { fontSize: texto.cuerpo, color: colores.error },
  barra: { flexDirection: 'row', height: 16, borderRadius: 8, backgroundColor: colores.borde, overflow: 'hidden' },
  relleno: { backgroundColor: colores.acierto },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  filaHecha: { borderColor: colores.acierto, backgroundColor: '#EEF6EE' },
  check: {
    width: 56,
    height: 56,
    borderRadius: 12,
    borderWidth: 3,
    borderColor: colores.textoSuave,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkHecho: { backgroundColor: colores.acierto, borderColor: colores.acierto },
  checkTexto: { fontSize: texto.subtitulo, fontWeight: '800', color: colores.texto },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  tachado: { textDecorationLine: 'line-through', color: colores.textoSuave },
  accion: { fontSize: 16, fontWeight: '700', color: colores.textoSuave },
});
