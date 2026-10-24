import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { useOperario } from '@/logica/operario';
import { fechaLarga } from '@/logica/reporte';
import { duracion, type ConfigTurno } from '@/logica/turno';
import { useTurno } from '@/logica/useTurno';
import { colores, espacio, texto } from '@/tema';

// Pantalla de la coordinadora: quién vino hoy, cuánto dura el turno y cómo quedó el reparto de
// los cuadrantes que el robot encontró con rosas en punto 3, con el avance de cada persona.

export default function Turno() {
  const { usuario } = useOperario();
  const { datos, reparto, trabajadores, error, cambiarConfig, cambiarPresente } = useTurno();

  if (usuario?.rol !== 'admin') return <Text style={styles.vacio}>Solo la administración puede ver esta pantalla.</Text>;
  if (!datos && error) return <Text style={styles.vacio}>{error}</Text>;
  if (!datos || !reparto) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  const { config } = datos;
  const capacidad = config.horasCorte * 60;
  const totalCuadrantes = Object.values(reparto.porTrabajador).reduce((s, r) => s + r.tareas.length, 0);
  const totalHechos = Object.keys(datos.hechos).length;
  const cambiar = (campo: keyof ConfigTurno, paso: number, minimo: number) =>
    cambiarConfig({ ...config, [campo]: Math.max(minimo, config[campo] + paso) });

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>Turno · {fechaLarga(datos.reporte.fecha)}</Text>
      <Text style={styles.cuerpo}>
        {datos.presentes.length} de {trabajadores.length} trabajadores presentes · {totalHechos} de {totalCuadrantes}{' '}
        cuadrantes hechos
      </Text>
      {!!error && <Text style={styles.aviso}>{error}</Text>}

      <Text style={styles.seccion}>Duración del turno</Text>
      <View style={styles.ajustes}>
        <Ajuste texto="Horas de corte" valor={`${config.horasCorte} h`} menos={() => cambiar('horasCorte', -0.5, 0.5)} mas={() => cambiar('horasCorte', 0.5, 0.5)} />
        <Ajuste texto="Por rosa" valor={`${config.segundosPorRosa} s`} menos={() => cambiar('segundosPorRosa', -5, 5)} mas={() => cambiar('segundosPorRosa', 5, 5)} />
        <Ajuste texto="Llegar a un cuadrante" valor={`${config.minutosPorCuadrante} min`} menos={() => cambiar('minutosPorCuadrante', -1, 0)} mas={() => cambiar('minutosPorCuadrante', 1, 0)} />
      </View>

      {reparto.sinAsignar.length > 0 && (
        <Text style={styles.aviso}>
          ⚠ {reparto.sinAsignar.length} cuadrantes con {reparto.sinAsignar.reduce((s, t) => s + t.cuadrante.optimo, 0)} rosas
          no caben en el turno ({duracion(reparto.sinAsignar.reduce((s, t) => s + t.minutos, 0))} de trabajo). Hace falta
          más gente o más horas.
        </Text>
      )}

      <Text style={styles.seccion}>Trabajadores (toca para marcar quién vino)</Text>
      {trabajadores.map((t) => {
        const presente = datos.presentes.includes(t.id);
        const suyo = reparto.porTrabajador[t.id];
        const hechos = suyo ? suyo.tareas.filter((x) => datos.hechos[x.cuadrante.cuadrante_id]).length : 0;
        return (
          <Pressable
            key={t.id}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: presente }}
            onPress={() => cambiarPresente(t.id, !presente)}
            style={({ pressed }) => [styles.fila, !presente && styles.ausente, pressed && { opacity: 0.7 }]}
          >
            <View style={[styles.check, presente && styles.checkSi]}>
              <Text style={styles.checkTexto}>{presente ? '✓' : ''}</Text>
            </View>
            <View style={styles.filaTexto}>
              <Text style={styles.filaTitulo}>{t.nombre}</Text>
              {presente && suyo ? (
                <Text style={styles.cuerpo}>
                  {suyo.tareas.length > 0
                    ? `Camas ${[...new Set(suyo.tareas.map((x) => x.cuadrante.cama))].join(', ')} · ${duracion(suyo.minutos)} de ${duracion(capacidad)}`
                    : 'Sin cuadrantes para cortar'}
                </Text>
              ) : (
                <Text style={styles.cuerpo}>No vino hoy</Text>
              )}
            </View>
            {presente && suyo && suyo.tareas.length > 0 && (
              <Text style={styles.avance}>
                {hechos}/{suyo.tareas.length}
              </Text>
            )}
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

function Ajuste({ texto: etiqueta, valor, menos, mas }: { texto: string; valor: string; menos: () => void; mas: () => void }) {
  return (
    <View style={styles.ajuste}>
      <Text style={styles.cuerpo}>{etiqueta}</Text>
      <View style={styles.ajusteFila}>
        <Pressable accessibilityRole="button" accessibilityLabel={`Menos ${etiqueta}`} onPress={menos} style={styles.paso}>
          <Text style={styles.pasoTexto}>−</Text>
        </Pressable>
        <Text style={styles.valor}>{valor}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={`Más ${etiqueta}`} onPress={mas} style={styles.paso}>
          <Text style={styles.pasoTexto}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 900, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  vacio: { fontSize: texto.subtitulo, color: colores.texto, padding: espacio.xl, textAlign: 'center' },
  seccion: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto, marginTop: espacio.m },
  ajustes: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m },
  ajuste: {
    flexGrow: 1,
    minWidth: 220,
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colores.borde,
    padding: espacio.m,
    alignItems: 'center',
    gap: espacio.s,
  },
  ajusteFila: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  paso: { width: 56, height: 56, borderRadius: 28, backgroundColor: '#455A64', justifyContent: 'center', alignItems: 'center' },
  pasoTexto: { color: '#fff', fontSize: 30, fontWeight: '800' },
  valor: { fontSize: texto.subtitulo, fontWeight: '800', color: colores.texto, minWidth: 90, textAlign: 'center' },
  aviso: { fontSize: texto.cuerpo, color: colores.error },
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
  ausente: { opacity: 0.55 },
  check: {
    width: 44,
    height: 44,
    borderRadius: 10,
    borderWidth: 3,
    borderColor: colores.textoSuave,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkSi: { backgroundColor: colores.acierto, borderColor: colores.acierto },
  checkTexto: { color: '#fff', fontSize: 22, fontWeight: '800' },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  avance: { fontSize: texto.subtitulo, fontWeight: '800', color: colores.acierto },
});
