import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useState } from 'react';
import { ActivityIndicator, Animated, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Aparecer, useSacudir } from '@/componentes/animaciones';
import { Marca } from '@/componentes/Marca';
import type { Usuario } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const COLORES_AVATAR = ['#D7263D', '#F06292', '#C2185B', '#FF8A65', '#AB47BC', '#EC407A'];
const TECLAS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'volver', '0', 'borrar'];

function colorDe(u: Usuario, i: number) {
  return u.rol === 'admin' ? '#455A64' : COLORES_AVATAR[i % COLORES_AVATAR.length];
}

// Ingreso en la tablet compartida: cada persona toca su nombre y escribe su PIN.
export function Ingreso() {
  const { usuarios, entrar, recargarUsuarios, cerradaPorInactividad } = useOperario();
  const arriba = useSafeAreaInsets().top;
  const [elegido, setElegido] = useState<{ usuario: Usuario; color: string } | null>(null);
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [revisando, setRevisando] = useState(false);
  const { x: sacudida, sacudir } = useSacudir();

  async function tecla(digito: string) {
    if (!elegido || revisando) return;
    const nuevo = (pin + digito).slice(0, 4);
    setPin(nuevo);
    setError('');
    if (nuevo.length < 4) return;
    setRevisando(true);
    try {
      if (!(await entrar(elegido.usuario, nuevo))) {
        setError('PIN incorrecto');
        sacudir();
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
      }
    } catch (e) {
      setError((e as Error).message);
    }
    setRevisando(false);
    setPin('');
  }

  function pulsar(t: string) {
    if (t === 'borrar') setPin(pin.slice(0, -1));
    else if (t === 'volver') {
      setElegido(null);
      setPin('');
      setError('');
    } else tecla(t);
  }

  if (elegido) {
    return (
      <View style={[styles.centro, { paddingTop: arriba }]}>
        <Aparecer estilo={styles.centrado}>
          <View style={[styles.avatarGrande, { backgroundColor: elegido.color }]}>
            <Text style={styles.inicialGrande}>{elegido.usuario.nombre.charAt(0)}</Text>
          </View>
          <Text style={styles.titulo}>{elegido.usuario.nombre}</Text>
          <Text style={styles.cuerpo}>Escribe tu PIN</Text>
        </Aparecer>

        <Animated.View style={[styles.puntos, { transform: [{ translateX: sacudida }] }]}>
          {[0, 1, 2, 3].map((i) => (
            <View
              key={i}
              style={[styles.punto, i < pin.length && styles.puntoLleno, !!error && styles.puntoError]}
            />
          ))}
        </Animated.View>
        <View style={styles.aviso}>
          {revisando ? <ActivityIndicator color={colores.primario} /> : !!error && <Text style={styles.error}>{error}</Text>}
        </View>

        <View style={styles.teclado}>
          {TECLAS.map((t) => (
            <Pressable
              key={t}
              accessibilityRole="button"
              accessibilityLabel={t === 'borrar' ? 'Borrar' : t === 'volver' ? 'Volver' : t}
              style={({ pressed }) => [styles.tecla, t.length > 1 && styles.teclaSuave, pressed && styles.teclaPulsada]}
              onPress={() => pulsar(t)}
            >
              {t === 'borrar' ? (
                <Ionicons name="backspace-outline" size={28} color={colores.textoSuave} />
              ) : t === 'volver' ? (
                <Ionicons name="arrow-back" size={28} color={colores.textoSuave} />
              ) : (
                <Text style={styles.teclaTexto}>{t}</Text>
              )}
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={[styles.contenido, { paddingTop: arriba + espacio.l }]}>
      <Marca tamano={30} />
      <View>
        <Text style={styles.titulo}>¿Quién eres?</Text>
        {cerradaPorInactividad && <Text style={styles.cuerpo}>Tu sesión se cerró por inactividad.</Text>}
      </View>
      {usuarios.length === 0 && (
        <Pressable onPress={() => recargarUsuarios().catch(() => {})} style={styles.sinConexion}>
          <Ionicons name="cloud-offline-outline" size={22} color={colores.error} />
          <Text style={styles.error}>Sin conexión. Toca para reintentar.</Text>
        </Pressable>
      )}
      <View style={styles.rejilla}>
        {usuarios.map((u, i) => {
          const color = colorDe(u, i);
          return (
            <Aparecer key={u.id} retraso={i * 40}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={u.nombre}
                onPress={() => setElegido({ usuario: u, color })}
                style={({ pressed }) => [styles.persona, pressed && { transform: [{ scale: 0.95 }] }]}
              >
                <View style={[styles.avatar, { backgroundColor: color }]}>
                  <Text style={styles.inicial}>{u.nombre.charAt(0)}</Text>
                </View>
                <Text style={styles.nombre} numberOfLines={1}>
                  {u.nombre}
                </Text>
                {u.rol === 'admin' && (
                  <View style={styles.insignia}>
                    <Ionicons name="shield-checkmark" size={12} color="#455A64" />
                    <Text style={styles.insigniaTexto}>Admin</Text>
                  </View>
                )}
              </Pressable>
            </Aparecer>
          );
        })}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 900, width: '100%', alignSelf: 'center' },
  centro: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: espacio.l, gap: espacio.m },
  centrado: { alignItems: 'center', gap: espacio.s },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  sinConexion: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m },
  persona: {
    width: 140,
    paddingVertical: espacio.l,
    borderRadius: 24,
    backgroundColor: colores.tarjeta,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    alignItems: 'center',
    gap: espacio.s,
  },
  avatar: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center' },
  inicial: { fontSize: 30, fontFamily: fuente.titulo, color: '#fff' },
  nombre: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto, maxWidth: 120 },
  insignia: { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: '#ECEFF1', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  insigniaTexto: { fontSize: 12, fontFamily: fuente.negrita, color: '#455A64' },
  avatarGrande: { width: 96, height: 96, borderRadius: 48, justifyContent: 'center', alignItems: 'center', ...sombra },
  inicialGrande: { fontSize: 46, fontFamily: fuente.titulo, color: '#fff' },
  puntos: { flexDirection: 'row', gap: espacio.l, marginTop: espacio.s },
  punto: { width: 22, height: 22, borderRadius: 11, borderWidth: 3, borderColor: colores.rosa },
  puntoLleno: { backgroundColor: colores.primario, borderColor: colores.primario },
  puntoError: { borderColor: colores.error },
  aviso: { height: 28, justifyContent: 'center' },
  teclado: { flexDirection: 'row', flexWrap: 'wrap', width: 3 * 92 + 2 * espacio.m, gap: espacio.m },
  tecla: {
    width: 92,
    height: 76,
    borderRadius: 22,
    backgroundColor: colores.tarjeta,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  teclaSuave: { backgroundColor: 'transparent', borderColor: 'transparent' },
  teclaPulsada: { transform: [{ translateY: 3 }], borderBottomWidth: 2 },
  teclaTexto: { fontSize: 32, fontFamily: fuente.titulo, color: colores.texto },
});
