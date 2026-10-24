import { Ionicons } from '@expo/vector-icons';
import { router, type Href } from 'expo-router';
import type { ComponentProps } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Aparecer } from '@/componentes/animaciones';
import { Ingreso } from '@/componentes/Ingreso';
import { Marca } from '@/componentes/Marca';
import { Mosaico } from '@/componentes/Mosaico';
import { ROLES, type Rol } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, texto } from '@/tema';

type Opcion = {
  titulo: string;
  detalle?: string;
  icono: ComponentProps<typeof Ionicons>['name'];
  color: string;
  destacado?: boolean;
  etiqueta?: string;
  ruta: Href;
};

const INFORME: Opcion = { titulo: 'Informe del robot', icono: 'hardware-chip', color: '#7E57C2', ruta: '/hoy' };
const DUDOSAS: Opcion = { titulo: 'Rosas dudosas', detalle: 'El robot necesita tu ojo', icono: 'help-circle', color: colores.oro, ruta: '/revisar' };

// Lo que ve cada rol en el inicio. El experto no ve los juegos de práctica; revisa las dudas del robot.
const MENU: Record<Rol, Opcion[]> = {
  admin: [
    { titulo: 'Turno de hoy', detalle: 'Asistencia y avance', icono: 'people', color: colores.primario, destacado: true, ruta: '/turno' },
    { titulo: 'Usuarios', icono: 'person-add', color: colores.rosa, ruta: '/trabajadores' },
    INFORME,
    { ...DUDOSAS, destacado: false },
    { titulo: 'Modo turnero', detalle: 'Dejar esta tablet fija en el tablero del turno', icono: 'tv', color: '#455A64', destacado: true, ruta: '/activar-turnero' },
  ],
  experto: [
    { titulo: 'Mi turno', detalle: 'Mis cuadrantes de hoy', icono: 'checkbox', color: colores.primario, destacado: true, ruta: '/mi-turno' },
    { ...DUDOSAS, destacado: true },
    { ...INFORME, destacado: true, detalle: 'Rosas listas por cuadrante' },
  ],
  aprendiz: [
    { titulo: 'Mi turno', detalle: 'Mis cuadrantes de hoy', icono: 'checkbox', color: colores.primario, destacado: true, ruta: '/mi-turno' },
    { titulo: 'Practicar', detalle: '10 rosas reales', icono: 'flash', color: colores.rosa, destacado: true, ruta: '/clasificar' },
    { titulo: 'Aprender', icono: 'book', color: '#5E9C4B', ruta: '/aprender' },
    { titulo: 'Mi progreso', icono: 'trophy', color: colores.oro, ruta: '/progreso' },
    INFORME,
    { titulo: 'Sanación', icono: 'medkit', color: '#26A69A', ruta: '/sanacion' },
  ],
};

export default function Inicio() {
  const { usuario, salir } = useOperario();
  const arriba = useSafeAreaInsets().top;

  if (!usuario) return <Ingreso />;

  const rol = ROLES[usuario.rol];
  const opciones = MENU[usuario.rol];

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
        <Text style={styles.saludo} numberOfLines={1} adjustsFontSizeToFit>
          Hola, {usuario.nombre.split(' ')[0]}
        </Text>
        <View style={[styles.rol, { backgroundColor: rol.fondo }]}>
          <Ionicons name={rol.icono} size={14} color={rol.color} />
          <Text style={[styles.rolTexto, { color: rol.color }]}>{rol.nombre}</Text>
        </View>
      </Aparecer>

      <View style={styles.rejilla}>
        {opciones.map(({ ruta, ...o }, i) => (
          <Aparecer key={o.titulo} retraso={80 + i * 60} estilo={o.destacado ? styles.ancho : styles.celda}>
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
  rol: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4, marginTop: espacio.xs },
  rolTexto: { fontSize: 13, fontFamily: fuente.negrita },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: espacio.m },
  ancho: { width: '100%' },
  // Siempre la mitad del ancho, aunque la última quede sola, para que todas midan lo mismo.
  celda: { width: '48%' },
});
