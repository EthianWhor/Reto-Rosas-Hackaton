import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState, type ComponentProps } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer, BarraProgreso } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { CATEGORIAS } from '@/data/categorias';
import { useOperario } from '@/logica/operario';
import { leerRondas, matrizDeConfusion, type Ronda } from '@/logica/progreso';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const fechaCorta = (iso: string) => {
  const d = new Date(iso);
  return `${d.getDate()} ${MESES[d.getMonth()]} · ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};
const aciertosDe = (r: Ronda) => r.respuestas.filter((x) => x.correcta === x.elegida).length;

export default function Progreso() {
  const { nombre, token } = useOperario();
  const [rondas, setRondas] = useState<Ronda[] | null>(null);

  useFocusEffect(
    useCallback(() => {
      leerRondas(token, nombre).then(setRondas);
    }, [token, nombre]),
  );

  if (rondas === null) return null;

  if (rondas.length === 0) {
    return (
      <View style={styles.vacio}>
        <Aparecer estilo={styles.centrado}>
          <View style={styles.trofeo}>
            <Ionicons name="trophy" size={56} color="#fff" />
          </View>
          <Text style={styles.titulo}>Aún no has practicado</Text>
          <BotonGrande titulo="Practicar" icono="flash" color={colores.rosa} onPress={() => router.replace('/clasificar')} />
        </Aparecer>
      </View>
    );
  }

  const respuestas = rondas.flatMap((r) => r.respuestas);
  const aciertos = respuestas.filter((r) => r.correcta === r.elegida).length;
  const mejor = Math.max(...rondas.map((r) => aciertosDe(r) / r.respuestas.length));
  const matriz = matrizDeConfusion(rondas);

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Aparecer estilo={styles.resumen}>
        <Dato icono="star" color={colores.oro} valor={`${aciertos * 10}`} etiqueta="Puntos" />
        <Dato icono="flash" color={colores.rosa} valor={`${rondas.length}`} etiqueta="Rondas" />
        <Dato icono="ribbon" color={colores.acierto} valor={`${Math.round(mejor * 100)}%`} etiqueta="Mejor ronda" />
      </Aparecer>

      <Text style={styles.seccion}>Aciertos por categoría</Text>
      {CATEGORIAS.map((c, i) => {
        const fila = matriz[c.id];
        const total = Object.values(fila).reduce((a, b) => a + b, 0);
        const proporcion = total ? fila[c.id] / total : 0;
        const confusion = CATEGORIAS.filter((o) => o.id !== c.id && fila[o.id] > 0).sort((a, b) => fila[b.id] - fila[a.id])[0];
        return (
          <Aparecer key={c.id} retraso={100 + i * 80} estilo={styles.tarjeta}>
            <View style={styles.filaTitulo}>
              <Ionicons name={c.icono} size={22} color={c.color} />
              <Text style={styles.categoria}>{c.boton}</Text>
              <Text style={[styles.porcentaje, { color: c.color }]}>{total ? `${Math.round(proporcion * 100)}%` : '—'}</Text>
            </View>
            <BarraProgreso valor={proporcion} color={c.color} alto={12} />
            {confusion && <Text style={styles.nota}>La confundes con «{confusion.boton}»</Text>}
          </Aparecer>
        );
      })}

      <Text style={styles.seccion}>Últimas rondas</Text>
      <View style={styles.tarjeta}>
        {rondas
          .slice(-5)
          .reverse()
          .map((r, i) => {
            const a = aciertosDe(r);
            return (
              <View key={r.fecha} style={[styles.ronda, i > 0 && styles.separador]}>
                <Text style={styles.fecha}>{fechaCorta(r.fecha)}</Text>
                <Text style={styles.puntaje}>
                  {a}/{r.respuestas.length}
                </Text>
              </View>
            );
          })}
      </View>
    </ScrollView>
  );
}

function Dato({ icono, color, valor, etiqueta }: { icono: ComponentProps<typeof Ionicons>['name']; color: string; valor: string; etiqueta: string }) {
  return (
    <View style={[styles.dato, { borderColor: color }]}>
      <Ionicons name={icono} size={26} color={color} />
      <Text style={[styles.datoValor, { color }]}>{valor}</Text>
      <Text style={styles.datoEtiqueta}>{etiqueta}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  vacio: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  centrado: { alignItems: 'center', gap: espacio.l, width: 320 },
  trofeo: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colores.oro,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 6,
    borderBottomColor: '#C98422',
  },
  titulo: { fontSize: 26, fontFamily: fuente.titulo, color: colores.texto },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 760, width: '100%', alignSelf: 'center' },
  resumen: { flexDirection: 'row', gap: espacio.m },
  dato: { flex: 1, paddingVertical: espacio.m, borderRadius: 18, borderWidth: 2, backgroundColor: colores.tarjeta, alignItems: 'center', gap: 2 },
  datoValor: { fontSize: 24, fontFamily: fuente.titulo },
  datoEtiqueta: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.textoSuave },
  seccion: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, marginTop: espacio.m },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 20, padding: espacio.m, gap: espacio.s, ...sombra },
  filaTitulo: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  categoria: { flex: 1, fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
  porcentaje: { fontSize: 20, fontFamily: fuente.titulo },
  nota: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.textoSuave },
  ronda: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: espacio.s },
  separador: { borderTopWidth: 1, borderTopColor: colores.borde },
  fecha: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  puntaje: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
});
