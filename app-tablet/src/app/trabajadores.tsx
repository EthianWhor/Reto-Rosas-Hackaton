import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import type { Rol } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Administración de las personas que usan la tablet: agregar (con su PIN y su rol) y quitar.
// Quitar no borra a la persona en Supabase: la desactiva, para no perder lo que marcó o practicó.

export default function Trabajadores() {
  const { usuario, usuarios, crearPersona, quitarPersona } = useOperario();
  const [nombre, setNombre] = useState('');
  const [pin, setPin] = useState('');
  const [rol, setRol] = useState<Rol>('trabajador');
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');

  if (usuario?.rol !== 'admin') return <Text style={styles.vacio}>Solo para administración.</Text>;

  const pinValido = /^\d{4}$/.test(pin);
  const admins = usuarios.filter((u) => u.rol === 'admin').length;

  async function hacer(accion: () => Promise<void>) {
    setOcupado(true);
    setError('');
    try {
      await accion();
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setOcupado(false);
    }
  }

  async function agregar() {
    if (await hacer(() => crearPersona(nombre.trim(), rol, pin))) {
      setNombre('');
      setPin('');
      setRol('trabajador');
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.contenido} keyboardShouldPersistTaps="handled">
      <View style={styles.formulario}>
        <Text style={styles.seccion}>Nueva persona</Text>
        <TextInput
          value={nombre}
          onChangeText={setNombre}
          placeholder="Nombre"
          placeholderTextColor={colores.gris}
          style={styles.input}
          autoCapitalize="words"
        />
        <TextInput
          value={pin}
          onChangeText={(t) => setPin(t.replace(/\D/g, '').slice(0, 4))}
          placeholder="PIN (4 números)"
          placeholderTextColor={colores.gris}
          keyboardType="number-pad"
          style={styles.input}
        />
        <View style={styles.roles}>
          {(['trabajador', 'admin'] as Rol[]).map((r) => (
            <Pressable
              key={r}
              accessibilityRole="radio"
              accessibilityState={{ selected: rol === r }}
              onPress={() => setRol(r)}
              style={[styles.rol, rol === r && styles.rolSi]}
            >
              <Text style={[styles.rolTexto, rol === r && { color: '#fff' }]}>{r === 'admin' ? 'Admin' : 'Trabajador'}</Text>
            </Pressable>
          ))}
        </View>
        {!!error && <Text style={styles.error}>{error}</Text>}
        <BotonGrande titulo="Agregar" icono="person-add" deshabilitado={ocupado || !nombre.trim() || !pinValido} onPress={agregar} />
      </View>

      <Text style={styles.seccion}>Equipo · {usuarios.length}</Text>
      {usuarios.map((u, i) => (
        <Aparecer key={u.id} retraso={i * 30}>
          <View style={styles.fila}>
            <View style={[styles.avatar, { backgroundColor: u.rol === 'admin' ? '#455A64' : colores.rosa }]}>
              <Text style={styles.inicial}>{u.nombre.charAt(0)}</Text>
            </View>
            <View style={styles.filaTexto}>
              <Text style={styles.filaTitulo}>{u.nombre}</Text>
              <Text style={styles.cuerpo}>{u.rol === 'admin' ? 'Admin' : 'Trabajador'}</Text>
            </View>
            {/* No se puede quitar a uno mismo ni al último admin, para no quedar sin acceso. */}
            {u.id !== usuario.id && !(u.rol === 'admin' && admins === 1) && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`Quitar a ${u.nombre}`}
                disabled={ocupado}
                onPress={() => hacer(() => quitarPersona(u.id))}
                style={({ pressed }) => [styles.quitar, pressed && { opacity: 0.6 }]}
                hitSlop={8}
              >
                <Ionicons name="trash-outline" size={22} color={colores.error} />
              </Pressable>
            )}
          </View>
        </Aparecer>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 720, width: '100%', alignSelf: 'center' },
  vacio: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto, padding: espacio.xl, textAlign: 'center' },
  cuerpo: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.textoSuave },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  seccion: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  formulario: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, ...sombra },
  input: {
    fontSize: texto.subtitulo,
    fontFamily: fuente.normal,
    color: colores.texto,
    backgroundColor: colores.fondo,
    borderWidth: 2,
    borderColor: colores.borde,
    borderRadius: 16,
    padding: espacio.m,
  },
  roles: { flexDirection: 'row', gap: espacio.m },
  rol: { flex: 1, padding: espacio.m, borderRadius: 16, borderWidth: 2, borderColor: colores.borde, alignItems: 'center' },
  rolSi: { backgroundColor: colores.rosaOscuro, borderColor: colores.rosaOscuro },
  rolTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.textoSuave },
  fila: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, backgroundColor: colores.tarjeta, borderRadius: 20, padding: espacio.m, ...sombra },
  avatar: { width: 46, height: 46, borderRadius: 23, justifyContent: 'center', alignItems: 'center' },
  inicial: { fontSize: 22, fontFamily: fuente.titulo, color: '#fff' },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.cuerpo + 2, fontFamily: fuente.negrita, color: colores.texto },
  quitar: { width: 44, height: 44, borderRadius: 22, backgroundColor: colores.errorSuave, justifyContent: 'center', alignItems: 'center' },
});
