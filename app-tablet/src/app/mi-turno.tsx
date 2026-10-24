import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useState, type ComponentProps } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer, BarraProgreso, LluviaDePetalos, Rebote } from '@/componentes/animaciones';
import { useOperario } from '@/logica/operario';
import { fechaLarga } from '@/logica/reporte';
import { duracion } from '@/logica/turno';
import { useTurno } from '@/logica/useTurno';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Los cuadrantes que le tocan al trabajador con la sesión abierta, en orden. Cada uno se marca
// con un toque cuando termina de cortarlo.

export default function MiTurno() {
  const { usuario } = useOperario();
  const { datos, reparto, error, cambiarHecho } = useTurno();
  const [petalos, setPetalos] = useState(0);

  if (!usuario) return null;
  if (!datos && error) return <Vacio icono="cloud-offline-outline" texto={error} />;
  if (!datos || !reparto) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  const mio = reparto.porTrabajador[usuario.id];
  if (!datos.presentes.includes(usuario.id) || !mio) {
    return <Vacio icono="person-outline" texto="Hoy no estás en el turno. Avísale a la coordinadora." />;
  }
  if (mio.tareas.length === 0) {
    return <Vacio icono="leaf-outline" texto="Hoy no tienes cuadrantes para cortar." />;
  }

  const hechas = mio.tareas.filter((t) => datos.hechos[t.cuadrante.cuadrante_id]).length;
  const rosas = mio.tareas.reduce((s, t) => s + t.cuadrante.optimo, 0);
  const listo = hechas === mio.tareas.length;

  function marcar(cuadranteId: string, hecho: boolean) {
    cambiarHecho(cuadranteId, usuario!.id, hecho);
    if (!hecho) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    if (hechas + 1 === mio.tareas.length) setPetalos((p) => p + 1);
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.contenido}>
        <Aparecer estilo={[styles.resumen, listo && styles.resumenListo]}>
          <Text style={styles.fecha}>{fechaLarga(datos.reporte.fecha)}</Text>
          <View style={styles.filaResumen}>
            <Rebote clave={hechas}>
              <Text style={styles.contador}>
                {hechas}
                <Text style={styles.contadorTotal}>/{mio.tareas.length}</Text>
              </Text>
            </Rebote>
            <Text style={styles.resumenTexto}>{listo ? '¡Terminaste!' : `${rosas} rosas · ~${duracion(mio.minutos)}`}</Text>
          </View>
          <BarraProgreso valor={hechas / mio.tareas.length} color={colores.acierto} />
        </Aparecer>
        {!!error && <Text style={styles.error}>{error}</Text>}

        {mio.tareas.map(({ cuadrante: c, minutos }, i) => {
          const hecho = !!datos.hechos[c.cuadrante_id];
          return (
            <Aparecer key={c.cuadrante_id} retraso={100 + i * 40}>
              <Pressable
                accessibilityRole="checkbox"
                accessibilityState={{ checked: hecho }}
                accessibilityLabel={`Cama ${c.cama}, metros ${c.desde_m} a ${c.hasta_m}`}
                onPress={() => marcar(c.cuadrante_id, !hecho)}
                style={({ pressed }) => [styles.fila, hecho && styles.filaHecha, pressed && { transform: [{ scale: 0.98 }] }]}
              >
                <Rebote clave={hecho ? 1 : 0} estilo={[styles.check, hecho && styles.checkHecho]}>
                  {hecho ? <Ionicons name="checkmark" size={32} color="#fff" /> : <Text style={styles.checkTexto}>{i + 1}</Text>}
                </Rebote>
                <View style={styles.filaTexto}>
                  <Text style={[styles.filaTitulo, hecho && styles.tachado]}>Cama {c.cama}</Text>
                  <Text style={styles.cuerpo}>
                    metros {c.desde_m}–{c.hasta_m} · {c.optimo} rosas · ~{duracion(minutos)}
                  </Text>
                </View>
              </Pressable>
            </Aparecer>
          );
        })}
      </ScrollView>
      <LluviaDePetalos disparo={petalos} cantidad={36} />
    </View>
  );
}

function Vacio({ icono, texto: mensaje }: { icono: ComponentProps<typeof Ionicons>['name']; texto: string }) {
  return (
    <View style={styles.centro}>
      <Aparecer estilo={styles.centrado}>
        <Ionicons name={icono} size={64} color={colores.rosa} />
        <Text style={styles.vacio}>{mensaje}</Text>
      </Aparecer>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  centrado: { alignItems: 'center', gap: espacio.m, maxWidth: 380 },
  vacio: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto, textAlign: 'center' },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 820, width: '100%', alignSelf: 'center' },
  resumen: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, ...sombra },
  resumenListo: { backgroundColor: colores.aciertoSuave },
  fecha: { fontSize: texto.pequeno, fontFamily: fuente.negrita, color: colores.textoSuave, textTransform: 'uppercase', letterSpacing: 1 },
  filaResumen: { flexDirection: 'row', alignItems: 'baseline', gap: espacio.m, flexWrap: 'wrap' },
  contador: { fontSize: 48, fontFamily: fuente.titulo, color: colores.acierto },
  contadorTotal: { fontSize: 28, color: colores.textoSuave },
  resumenTexto: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    backgroundColor: colores.tarjeta,
    borderRadius: 20,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  filaHecha: { borderColor: colores.acierto, backgroundColor: colores.aciertoSuave },
  check: {
    width: 56,
    height: 56,
    borderRadius: 16,
    borderWidth: 3,
    borderColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkHecho: { backgroundColor: colores.acierto, borderColor: colores.acierto },
  checkTexto: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.textoSuave },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  tachado: { textDecorationLine: 'line-through', color: colores.textoSuave },
});
