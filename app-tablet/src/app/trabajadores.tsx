import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { ROLES, type Rol, type UsuarioAdmin } from '@/data/usuarios';
import { listarUsuarios, reiniciarAcceso } from '@/logica/cuentas';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Usuarios por rol, para coordinación. Promueve (aprendiz → experto), da códigos de activación y
// reinicia el acceso de quien olvidó su PIN. Coordinación nunca ve ni pone el PIN de nadie.
// Quitar no borra en Supabase: desactiva, para no perder su historia.

const ORDEN: Rol[] = ['admin', 'experto', 'aprendiz'];
const SECCION: Record<Rol, string> = { admin: 'Coordinación', experto: 'Expertos', aprendiz: 'En capacitación' };

type Confirmar = { id: string; accion: 'reiniciar' | 'quitar' } | null;

export default function Usuarios() {
  const { usuario, usuarios, token, cambiarRol, quitarPersona } = useOperario();
  const [lista, setLista] = useState<UsuarioAdmin[] | null>(null);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [confirmar, setConfirmar] = useState<Confirmar>(null);
  const [codigo, setCodigo] = useState<{ nombre: string; codigo: string } | null>(null);

  const cargar = useCallback(async () => {
    if (!token) return;
    try {
      setLista(await listarUsuarios(token));
    } catch (e) {
      setError((e as Error).message);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      cargar();
    }, [cargar]),
  );
  // Si alguien activa su usuario o se agrega a otra persona en otra tablet, la lista se actualiza.
  useEffect(() => {
    cargar();
  }, [usuarios, cargar]);

  if (!usuario || !token) return null;
  if (!lista) {
    return (
      <View style={styles.centro}>
        {error ? <Text style={styles.error}>{error}</Text> : <ActivityIndicator size="large" color={colores.primario} />}
      </View>
    );
  }

  const admins = lista.filter((u) => u.rol === 'admin').length;

  async function hacer(id: string, accion: () => Promise<void>) {
    setOcupado(id);
    setError('');
    setConfirmar(null);
    try {
      await accion();
      await cargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setOcupado(null);
    }
  }

  const darCodigo = (u: UsuarioAdmin) =>
    hacer(u.id, async () => setCodigo({ nombre: u.nombre, codigo: await reiniciarAcceso(token!, u.id) }));

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <BotonGrande titulo="Registrar usuario" icono="person-add" onPress={() => router.push('/nuevo-usuario')} />

      {codigo && (
        <Aparecer estilo={styles.codigoCaja}>
          <View style={{ flex: 1 }}>
            <Text style={styles.codigoTitulo}>Nuevo código de {codigo.nombre}</Text>
            <Text style={styles.codigo} selectable>
              {codigo.codigo.slice(0, 3)} {codigo.codigo.slice(3)}
            </Text>
            <Text style={styles.nota}>Entrégaselo en persona: con él crea su PIN. No se vuelve a mostrar.</Text>
          </View>
          <Pressable onPress={() => setCodigo(null)} hitSlop={10} accessibilityLabel="Cerrar">
            <Ionicons name="close" size={24} color={colores.textoSuave} />
          </Pressable>
        </Aparecer>
      )}
      {!!error && <Text style={styles.error}>{error}</Text>}

      {ORDEN.map((rol) => {
        const grupo = lista.filter((u) => u.rol === rol);
        if (grupo.length === 0) return null;
        return (
          <View key={rol} style={styles.grupo}>
            <Text style={styles.seccion}>
              {SECCION[rol]} · {grupo.length}
            </Text>
            {grupo.map((u, i) => {
              const esYo = u.id === usuario.id;
              // No se puede quitar ni reiniciar a uno mismo, ni quitar al último de coordinación.
              const sePuedeQuitar = !esYo && !(u.rol === 'admin' && admins === 1);
              const pregunta = confirmar?.id === u.id ? confirmar.accion : null;
              return (
                <Aparecer key={u.id} retraso={i * 30}>
                  <View style={[styles.fila, ocupado === u.id && { opacity: 0.5 }]}>
                    <View style={styles.filaArriba}>
                      <View style={[styles.avatar, { backgroundColor: u.pendiente ? colores.gris : ROLES[u.rol].color }]}>
                        <Text style={styles.inicial}>{u.nombre.charAt(0)}</Text>
                      </View>
                      <View style={styles.filaTexto}>
                        <Text style={styles.filaTitulo} numberOfLines={1}>
                          {u.nombre}
                          {esYo ? ' (tú)' : ''}
                        </Text>
                        {(u.correo || u.telefono) && (
                          <Text style={styles.contacto} numberOfLines={1}>
                            {[u.telefono, u.correo].filter(Boolean).join(' · ')}
                          </Text>
                        )}
                        {u.pendiente && (
                          <Text style={[styles.estado, { color: u.bloqueado ? colores.error : colores.oro }]}>
                            {u.bloqueado ? 'Bloqueado: dale un código nuevo' : 'Falta activar su usuario'}
                          </Text>
                        )}
                      </View>
                      {sePuedeQuitar && (
                        <Pressable
                          accessibilityRole="button"
                          accessibilityLabel={`Quitar a ${u.nombre}`}
                          onPress={() => setConfirmar({ id: u.id, accion: 'quitar' })}
                          style={({ pressed }) => [styles.iconoAccion, { backgroundColor: colores.errorSuave }, pressed && { opacity: 0.6 }]}
                          hitSlop={6}
                        >
                          <Ionicons name="trash-outline" size={20} color={colores.error} />
                        </Pressable>
                      )}
                    </View>

                    {pregunta ? (
                      <View style={styles.confirmar}>
                        <Text style={styles.confirmarTexto}>
                          {pregunta === 'quitar'
                            ? `¿Quitar a ${u.nombre}?`
                            : `¿Reiniciar el acceso de ${u.nombre}? Su PIN deja de servir.`}
                        </Text>
                        <View style={styles.acciones}>
                          <Chip texto="Cancelar" color={colores.textoSuave} onPress={() => setConfirmar(null)} />
                          <Chip
                            texto={pregunta === 'quitar' ? 'Sí, quitar' : 'Sí, reiniciar'}
                            color={colores.error}
                            relleno
                            onPress={() => (pregunta === 'quitar' ? hacer(u.id, () => quitarPersona(u.id)) : darCodigo(u))}
                          />
                        </View>
                      </View>
                    ) : (
                      !esYo && (
                        <View style={styles.acciones}>
                          {u.rol === 'aprendiz' && !u.pendiente && (
                            <Chip texto="Promover a experto" icono="star" color={ROLES.experto.color} relleno onPress={() => hacer(u.id, () => cambiarRol(u.id, 'experto'))} />
                          )}
                          {u.rol === 'experto' && (
                            <Chip texto="Volver a capacitación" color={colores.textoSuave} onPress={() => hacer(u.id, () => cambiarRol(u.id, 'aprendiz'))} />
                          )}
                          {u.pendiente ? (
                            <Chip texto="Nuevo código" icono="key" color={colores.primario} onPress={() => darCodigo(u)} />
                          ) : (
                            <Chip texto="Reiniciar acceso" icono="key-outline" color={colores.textoSuave} onPress={() => setConfirmar({ id: u.id, accion: 'reiniciar' })} />
                          )}
                        </View>
                      )
                    )}
                  </View>
                </Aparecer>
              );
            })}
          </View>
        );
      })}
    </ScrollView>
  );
}

function Chip({
  texto: etiqueta,
  icono,
  color,
  relleno,
  onPress,
}: {
  texto: string;
  icono?: 'star' | 'key' | 'key-outline';
  color: string;
  relleno?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        { borderColor: color, backgroundColor: relleno ? color : 'transparent' },
        pressed && { transform: [{ scale: 0.95 }] },
      ]}
    >
      {icono && <Ionicons name={icono} size={14} color={relleno ? '#fff' : color} />}
      <Text style={[styles.chipTexto, { color: relleno ? '#fff' : color }]}>{etiqueta}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 720, width: '100%', alignSelf: 'center' },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  grupo: { gap: espacio.s },
  seccion: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  fila: { backgroundColor: colores.tarjeta, borderRadius: 20, padding: espacio.m, gap: espacio.s, ...sombra },
  filaArriba: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  avatar: { width: 46, height: 46, borderRadius: 23, justifyContent: 'center', alignItems: 'center' },
  inicial: { fontSize: 22, fontFamily: fuente.titulo, color: '#fff' },
  filaTexto: { flex: 1 },
  filaTitulo: { fontSize: texto.cuerpo + 2, fontFamily: fuente.negrita, color: colores.texto },
  contacto: { fontSize: 13, fontFamily: fuente.normal, color: colores.textoSuave },
  estado: { fontSize: 13, fontFamily: fuente.negrita, marginTop: 2 },
  iconoAccion: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  acciones: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.s, paddingLeft: 46 + espacio.m },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 2, borderRadius: 14, paddingHorizontal: 10, paddingVertical: 5 },
  chipTexto: { fontSize: 13, fontFamily: fuente.negrita },
  confirmar: { gap: espacio.s, backgroundColor: colores.errorSuave, borderRadius: 14, padding: espacio.m },
  confirmarTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.texto },
  codigoCaja: { flexDirection: 'row', gap: espacio.m, backgroundColor: colores.rosaSuave, borderRadius: 20, padding: espacio.m },
  codigoTitulo: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.texto },
  codigo: { fontSize: 36, fontFamily: fuente.titulo, color: colores.primario, letterSpacing: 4 },
  nota: { fontSize: 13, fontFamily: fuente.normal, color: colores.textoSuave },
});
