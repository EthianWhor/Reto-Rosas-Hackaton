import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import type { Rol } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { colores, espacio, texto } from '@/tema';

// Administración de las personas que usan la tablet: agregar (con su PIN y su rol) y quitar.
// Quitar no borra a la persona en Supabase: la desactiva, para no perder lo que marcó o practicó.

export default function Trabajadores() {
  const { usuario, usuarios, crearPersona, quitarPersona } = useOperario();
  const [nombre, setNombre] = useState('');
  const [pin, setPin] = useState('');
  const [rol, setRol] = useState<Rol>('trabajador');
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');

  if (usuario?.rol !== 'admin') return <Text style={styles.vacio}>Solo la administración puede ver esta pantalla.</Text>;

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
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>Personas</Text>
      <Text style={styles.cuerpo}>
        {usuarios.filter((u) => u.rol === 'trabajador').length} trabajadores · {admins} en administración
      </Text>

      {usuarios.map((u) => (
        <View key={u.id} style={styles.fila}>
          <View style={styles.filaTexto}>
            <Text style={styles.filaTitulo}>{u.nombre}</Text>
            <Text style={styles.cuerpo}>{u.rol === 'admin' ? 'Administración' : 'Trabajador'}</Text>
          </View>
          {/* No se puede quitar a uno mismo ni al último admin, para no quedar sin acceso. */}
          {u.id !== usuario.id && !(u.rol === 'admin' && admins === 1) && (
            <Pressable
              accessibilityRole="button"
              disabled={ocupado}
              onPress={() => hacer(() => quitarPersona(u.id))}
              style={styles.quitar}
            >
              <Text style={styles.quitarTexto}>Quitar</Text>
            </Pressable>
          )}
        </View>
      ))}

      <Text style={styles.seccion}>Agregar persona</Text>
      <TextInput value={nombre} onChangeText={setNombre} placeholder="Nombre" style={styles.input} autoCapitalize="words" />
      <TextInput
        value={pin}
        onChangeText={(t) => setPin(t.replace(/\D/g, '').slice(0, 4))}
        placeholder="PIN de 4 números"
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
            <Text style={[styles.rolTexto, rol === r && { color: '#fff' }]}>{r === 'admin' ? 'Administración' : 'Trabajador'}</Text>
          </Pressable>
        ))}
      </View>
      {!!error && <Text style={styles.error}>{error}</Text>}
      <BotonGrande titulo="Agregar" color="#1B5E20" deshabilitado={ocupado || !nombre.trim() || !pinValido} onPress={agregar} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 720, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  vacio: { fontSize: texto.subtitulo, color: colores.texto, padding: espacio.xl, textAlign: 'center' },
  error: { fontSize: texto.cuerpo, color: colores.error },
  seccion: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto, marginTop: espacio.l },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  quitar: { paddingVertical: espacio.s, paddingHorizontal: espacio.m, borderRadius: 12, borderWidth: 2, borderColor: colores.error },
  quitarTexto: { color: colores.error, fontWeight: '700', fontSize: 16 },
  input: {
    fontSize: texto.subtitulo,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 12,
    padding: espacio.m,
  },
  roles: { flexDirection: 'row', gap: espacio.m },
  rol: { flex: 1, padding: espacio.m, borderRadius: 12, borderWidth: 2, borderColor: '#455A64', alignItems: 'center' },
  rolSi: { backgroundColor: '#455A64' },
  rolTexto: { fontSize: texto.cuerpo, fontWeight: '700', color: '#455A64' },
});
