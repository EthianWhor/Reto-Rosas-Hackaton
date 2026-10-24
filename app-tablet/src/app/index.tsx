import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Aparecer } from '@/componentes/animaciones';
import { Ingreso } from '@/componentes/Ingreso';
import { Marca } from '@/componentes/Marca';
import { Mosaico } from '@/componentes/Mosaico';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, texto } from '@/tema';

export default function Inicio() {
  const { usuario, salir } = useOperario();
  const arriba = useSafeAreaInsets().top;

  if (!usuario) return <Ingreso />;

  const admin = usuario.rol === 'admin';
  const opciones = admin
    ? [
        { titulo: 'Turno de hoy', detalle: 'Asistencia, reparto y avance', icono: 'people' as const, color: colores.primario, destacado: true, ruta: '/turno' as const },
        { titulo: 'Personas', icono: 'person-add' as const, color: colores.rosa, ruta: '/trabajadores' as const },
        { titulo: 'Lo que vio el robot', icono: 'hardware-chip' as const, color: '#7E57C2', ruta: '/hoy' as const },
      ]
    : [
        { titulo: 'Mi turno', detalle: 'Mis cuadrantes de hoy', icono: 'checkbox' as const, color: colores.primario, destacado: true, ruta: '/mi-turno' as const },
        { titulo: 'Practicar', detalle: '10 rosas reales', icono: 'flash' as const, color: colores.rosa, destacado: true, ruta: '/clasificar' as const },
        { titulo: 'Aprender', icono: 'book' as const, color: '#5E9C4B', ruta: '/aprender' as const },
        { titulo: 'Mi progreso', icono: 'trophy' as const, color: colores.oro, ruta: '/progreso' as const },
        { titulo: 'Lo que vio el robot', icono: 'hardware-chip' as const, color: '#7E57C2', ruta: '/hoy' as const },
        { titulo: 'Sanación', icono: 'medkit' as const, color: '#26A69A', etiqueta: 'Pronto', ruta: '/sanacion' as const },
      ];

  return (
    <ScrollView contentContainerStyle={[styles.contenido, { paddingTop: arriba + espacio.m }]}>
      <View style={styles.cabecera}>
        <Marca tamano={24} />
        <Pressable accessibilityRole="button" onPress={salir} style={styles.salir} hitSlop={8}>
          <Ionicons name="log-out-outline" size={20} color={colores.textoSuave} />
          <Text style={styles.salirTexto}>Salir</Text>
        </Pressable>
      </View>

      <Aparecer>
        <Text style={styles.saludo}>Hola, {usuario.nombre}</Text>
        {admin && <Text style={styles.rol}>Administración</Text>}
      </Aparecer>

      <View style={styles.rejilla}>
        {opciones.map(({ ruta, ...o }, i) => (
          <Aparecer key={o.titulo} retraso={80 + i * 60} estilo={'destacado' in o && o.destacado ? styles.ancho : styles.celda}>
            <Mosaico {...o} onPress={() => router.push(ruta)} />
          </Aparecer>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 760, width: '100%', alignSelf: 'center' },
  cabecera: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  salir: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  salirTexto: { fontFamily: fuente.negrita, color: colores.textoSuave, fontSize: texto.pequeno },
  saludo: { fontSize: 34, fontFamily: fuente.titulo, color: colores.texto },
  rol: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.rosaOscuro },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m },
  ancho: { width: '100%' },
  celda: { flexGrow: 1, flexBasis: '45%', minWidth: 150 },
});
