import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { Usuario } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { colores, espacio, texto } from '@/tema';

// Ingreso en la tablet compartida: la persona toca su nombre y escribe su PIN de 4 dígitos.
// Sin teclado del sistema: botones grandes, pensados para usar con guantes o manos mojadas.

export function Ingreso() {
  const { usuarios, entrar, recargarUsuarios } = useOperario();
  const [elegido, setElegido] = useState<Usuario | null>(null);
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [revisando, setRevisando] = useState(false);

  async function tecla(digito: string) {
    if (!elegido || revisando) return;
    const nuevo = (pin + digito).slice(0, 4);
    setPin(nuevo);
    setError('');
    if (nuevo.length === 4) {
      setRevisando(true);
      try {
        if (!(await entrar(elegido, nuevo))) setError('PIN incorrecto. Intenta otra vez.');
      } catch (e) {
        setError((e as Error).message);
      }
      setRevisando(false);
      setPin('');
    }
  }

  if (elegido) {
    return (
      <View style={styles.centro}>
        <Text style={styles.titulo}>Hola, {elegido.nombre}</Text>
        <Text style={styles.cuerpo}>Escribe tu PIN</Text>
        <View style={styles.puntos}>
          {[0, 1, 2, 3].map((i) => (
            <View key={i} style={[styles.punto, i < pin.length && styles.puntoLleno]} />
          ))}
        </View>
        {revisando && <ActivityIndicator color={colores.primario} />}
        {!!error && <Text style={styles.error}>{error}</Text>}
        <View style={styles.teclado}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9', '←', '0', '✕'].map((t) => (
            <Pressable
              key={t}
              accessibilityRole="button"
              accessibilityLabel={t === '←' ? 'Borrar' : t === '✕' ? 'Volver' : t}
              style={({ pressed }) => [styles.tecla, pressed && { opacity: 0.6 }]}
              onPress={() => {
                if (t === '←') setPin(pin.slice(0, -1));
                else if (t === '✕') {
                  setElegido(null);
                  setPin('');
                  setError('');
                } else tecla(t);
              }}
            >
              <Text style={styles.teclaTexto}>{t}</Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>¿Quién eres?</Text>
      <Text style={styles.cuerpo}>Toca tu nombre para entrar.</Text>
      {usuarios.length === 0 && (
        <Text style={styles.error} onPress={() => recargarUsuarios().catch(() => {})}>
          No se pudo cargar la lista de personas. Revisa la conexión y toca aquí para reintentar.
        </Text>
      )}
      <View style={styles.rejilla}>
        {usuarios.map((u) => (
          <Pressable
            key={u.id}
            accessibilityRole="button"
            onPress={() => setElegido(u)}
            style={({ pressed }) => [styles.persona, u.rol === 'admin' && styles.admin, pressed && { opacity: 0.7 }]}
          >
            <Text style={styles.inicial}>{u.nombre.charAt(0)}</Text>
            <Text style={styles.nombre}>{u.nombre}</Text>
            {u.rol === 'admin' && <Text style={styles.rol}>Administración</Text>}
          </Pressable>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl, gap: espacio.m },
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 900, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m, marginTop: espacio.m },
  persona: {
    width: 150,
    paddingVertical: espacio.l,
    borderRadius: 20,
    backgroundColor: colores.tarjeta,
    borderWidth: 2,
    borderColor: colores.borde,
    alignItems: 'center',
    gap: espacio.s,
  },
  admin: { borderColor: '#455A64' },
  inicial: {
    fontSize: 36,
    fontWeight: '800',
    color: '#fff',
    backgroundColor: colores.primario,
    width: 64,
    height: 64,
    lineHeight: 64,
    textAlign: 'center',
    borderRadius: 32,
    overflow: 'hidden',
  },
  nombre: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  rol: { fontSize: 14, color: '#455A64' },
  puntos: { flexDirection: 'row', gap: espacio.m, marginVertical: espacio.m },
  punto: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: colores.texto },
  puntoLleno: { backgroundColor: colores.texto },
  error: { fontSize: texto.cuerpo, color: colores.error },
  teclado: { flexDirection: 'row', flexWrap: 'wrap', width: 3 * 96 + 2 * espacio.m, gap: espacio.m },
  tecla: {
    width: 96,
    height: 80,
    borderRadius: 16,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  teclaTexto: { fontSize: 32, fontWeight: '700', color: colores.texto },
});
