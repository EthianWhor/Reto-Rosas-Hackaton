import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer, BarraProgreso } from '@/componentes/animaciones';
import { useOperario } from '@/logica/operario';
import { fechaLarga } from '@/logica/reporte';
import { duracion, type ConfigTurno } from '@/logica/turno';
import { useTurno } from '@/logica/useTurno';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Pantalla de la coordinadora: quién vino hoy, cuánto dura el turno y cómo quedó el reparto de
// los cuadrantes que el robot encontró con rosas en punto 3, con el avance de cada persona.

export default function Turno() {
  const { usuario } = useOperario();
  const { datos, reparto, trabajadores, error, cambiarConfig, cambiarPresente } = useTurno();

  if (usuario?.rol !== 'admin') return <Text style={styles.vacio}>Solo para administración.</Text>;
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
  // La asistencia guardada puede incluir a personas que ya se quitaron: solo cuentan las activas.
  const presentes = trabajadores.filter((t) => datos.presentes.includes(t.id)).length;
  const cambiar = (campo: keyof ConfigTurno, paso: number, minimo: number) =>
    cambiarConfig({ ...config, [campo]: Math.max(minimo, config[campo] + paso) });

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Aparecer estilo={styles.resumen}>
        <Text style={styles.fecha}>{fechaLarga(datos.reporte.fecha)}</Text>
        <View style={styles.cifras}>
          <Cifra valor={`${presentes}/${trabajadores.length}`} etiqueta="Presentes" />
          <Cifra valor={`${totalHechos}/${totalCuadrantes}`} etiqueta="Cuadrantes" />
        </View>
        <BarraProgreso valor={totalCuadrantes ? totalHechos / totalCuadrantes : 0} color={colores.acierto} />
      </Aparecer>
      {!!error && <Text style={styles.error}>{error}</Text>}

      <Text style={styles.seccion}>Turno</Text>
      <View style={styles.ajustes}>
        <Ajuste texto="Horas de corte" valor={`${config.horasCorte} h`} menos={() => cambiar('horasCorte', -0.5, 0.5)} mas={() => cambiar('horasCorte', 0.5, 0.5)} />
        <Ajuste texto="Por rosa" valor={`${config.segundosPorRosa} s`} menos={() => cambiar('segundosPorRosa', -5, 5)} mas={() => cambiar('segundosPorRosa', 5, 5)} />
        <Ajuste texto="Por cuadrante" valor={`${config.minutosPorCuadrante} min`} menos={() => cambiar('minutosPorCuadrante', -1, 0)} mas={() => cambiar('minutosPorCuadrante', 1, 0)} />
      </View>

      {reparto.sinAsignar.length > 0 && (
        <View style={styles.aviso}>
          <Ionicons name="warning" size={22} color={colores.error} />
          <Text style={styles.avisoTexto}>
            Faltan manos: {reparto.sinAsignar.length} cuadrantes ({reparto.sinAsignar.reduce((s, t) => s + t.cuadrante.optimo, 0)} rosas) no
            caben en el turno.
          </Text>
        </View>
      )}

      <Text style={styles.seccion}>¿Quién vino?</Text>
      {trabajadores.map((t, i) => {
        const presente = datos.presentes.includes(t.id);
        const suyo = reparto.porTrabajador[t.id];
        const hechos = suyo ? suyo.tareas.filter((x) => datos.hechos[x.cuadrante.cuadrante_id]).length : 0;
        const camas = suyo ? [...new Set(suyo.tareas.map((x) => x.cuadrante.cama))] : [];
        return (
          <Aparecer key={t.id} retraso={i * 40}>
            <Pressable
              accessibilityRole="checkbox"
              accessibilityState={{ checked: presente }}
              accessibilityLabel={t.nombre}
              onPress={() => cambiarPresente(t.id, !presente)}
              style={({ pressed }) => [styles.fila, !presente && styles.ausente, pressed && { transform: [{ scale: 0.98 }] }]}
            >
              <View style={[styles.check, presente && styles.checkSi]}>
                {presente && <Ionicons name="checkmark" size={26} color="#fff" />}
              </View>
              <View style={styles.filaTexto}>
                <Text style={styles.filaTitulo}>{t.nombre}</Text>
                <Text style={styles.cuerpo}>
                  {!presente
                    ? 'No vino'
                    : camas.length > 0
                      ? `Camas ${camas[0]}–${camas[camas.length - 1]} · ${duracion(suyo!.minutos)} de ${duracion(capacidad)}`
                      : 'Sin cuadrantes'}
                </Text>
              </View>
              {presente && suyo && suyo.tareas.length > 0 && (
                <Text style={[styles.avance, hechos === suyo.tareas.length && { color: colores.acierto }]}>
                  {hechos}/{suyo.tareas.length}
                </Text>
              )}
            </Pressable>
          </Aparecer>
        );
      })}
    </ScrollView>
  );
}

function Cifra({ valor, etiqueta }: { valor: string; etiqueta: string }) {
  return (
    <View>
      <Text style={styles.cifra}>{valor}</Text>
      <Text style={styles.cuerpo}>{etiqueta}</Text>
    </View>
  );
}

function Ajuste({ texto: etiqueta, valor, menos, mas }: { texto: string; valor: string; menos: () => void; mas: () => void }) {
  return (
    <View style={styles.ajuste}>
      <Text style={styles.cuerpo}>{etiqueta}</Text>
      <View style={styles.ajusteFila}>
        <Pressable accessibilityRole="button" accessibilityLabel={`Menos ${etiqueta}`} onPress={menos} style={({ pressed }) => [styles.paso, pressed && styles.pasoPulsado]}>
          <Ionicons name="remove" size={26} color={colores.primario} />
        </Pressable>
        <Text style={styles.valor}>{valor}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={`Más ${etiqueta}`} onPress={mas} style={({ pressed }) => [styles.paso, pressed && styles.pasoPulsado]}>
          <Ionicons name="add" size={26} color={colores.primario} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 820, width: '100%', alignSelf: 'center' },
  vacio: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto, padding: espacio.xl, textAlign: 'center' },
  resumen: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, ...sombra },
  fecha: { fontSize: texto.pequeno, fontFamily: fuente.negrita, color: colores.textoSuave, textTransform: 'uppercase', letterSpacing: 1 },
  cifras: { flexDirection: 'row', gap: espacio.xl },
  cifra: { fontSize: 36, fontFamily: fuente.titulo, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  seccion: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, marginTop: espacio.m },
  ajustes: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m },
  ajuste: { flexGrow: 1, minWidth: 200, backgroundColor: colores.tarjeta, borderRadius: 20, padding: espacio.m, alignItems: 'center', gap: espacio.s, ...sombra },
  ajusteFila: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  paso: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colores.rosaSuave,
    borderBottomWidth: 4,
    borderBottomColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pasoPulsado: { transform: [{ translateY: 2 }], borderBottomWidth: 2 },
  valor: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, minWidth: 80, textAlign: 'center' },
  aviso: { flexDirection: 'row', alignItems: 'center', gap: espacio.s, backgroundColor: colores.errorSuave, borderRadius: 16, padding: espacio.m },
  avisoTexto: { flex: 1, fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
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
  ausente: { opacity: 0.5 },
  check: { width: 44, height: 44, borderRadius: 12, borderWidth: 3, borderColor: colores.borde, justifyContent: 'center', alignItems: 'center' },
  checkSi: { backgroundColor: colores.acierto, borderColor: colores.acierto },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  avance: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.textoSuave },
});
