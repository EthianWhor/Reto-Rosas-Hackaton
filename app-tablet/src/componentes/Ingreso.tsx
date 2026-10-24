import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Aparecer, useSacudir } from '@/componentes/animaciones';
import { Marca } from '@/componentes/Marca';
import { TecladoNumerico } from '@/componentes/TecladoNumerico';
import { ROLES, validar, type Usuario } from '@/data/usuarios';
import { activarUsuario, listarPendientes, verificarCodigo } from '@/logica/cuentas';
import { useOperario } from '@/logica/operario';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const COLORES_AVATAR = ['#D7263D', '#F06292', '#C2185B', '#FF8A65', '#AB47BC', '#EC407A'];

const colorDe = (u: Pick<Usuario, 'rol'>, i: number) => (u.rol === 'admin' ? '#455A64' : COLORES_AVATAR[i % COLORES_AVATAR.length]);

type Pendiente = { id: string; nombre: string };

// Pasos: elegir a quién → PIN (entrar). O, para activar: elegir nombre → código → PIN nuevo → confirmar.
type Paso =
  | { tipo: 'lista' }
  | { tipo: 'pin'; usuario: Usuario; color: string }
  | { tipo: 'pendientes'; lista: Pendiente[] | null }
  | { tipo: 'codigo'; persona: Pendiente }
  | { tipo: 'nuevoPin'; persona: Pendiente; codigo: string }
  | { tipo: 'confirmar'; persona: Pendiente; codigo: string; pin: string };

// Ingreso en la tablet compartida.
export function Ingreso() {
  const { usuarios, entrar, abrirSesion, recargarUsuarios, cerradaPorInactividad } = useOperario();
  const arriba = useSafeAreaInsets().top;
  const [paso, setPaso] = useState<Paso>({ tipo: 'lista' });
  const [valor, setValor] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const { x: sacudida, sacudir } = useSacudir();

  // Columnas que llenan el ancho: 2 en un celular, más en una tablet.
  const { width } = useWindowDimensions();
  const ancho = Math.min(width, 900) - 2 * espacio.l;
  const columnas = Math.max(2, Math.floor((ancho + espacio.m) / (150 + espacio.m)));
  const anchoTarjeta = (ancho - espacio.m * (columnas - 1)) / columnas;

  function ir(nuevo: Paso) {
    setPaso(nuevo);
    setValor('');
    setError('');
  }

  function fallar(mensaje: string) {
    setError(mensaje);
    setValor('');
    sacudir();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
  }

  // Al entrar a "Activar mi usuario" (o volver a esa lista) se pide la lista de pendientes.
  const cargarPendientes = paso.tipo === 'pendientes' && paso.lista === null;
  useEffect(() => {
    if (!cargarPendientes) return;
    listarPendientes()
      .then((lista) => setPaso({ tipo: 'pendientes', lista }))
      .catch((e) => {
        setError((e as Error).message);
        setPaso({ tipo: 'pendientes', lista: [] });
      });
  }, [cargarPendientes]);

  async function escribir(v: string) {
    setValor(v);
    setError('');
    const largo = paso.tipo === 'codigo' ? 6 : 4;
    if (v.length < largo || ocupado) return;
    setOcupado(true);
    try {
      if (paso.tipo === 'pin') {
        if (!(await entrar(paso.usuario, v))) fallar('PIN incorrecto');
      } else if (paso.tipo === 'codigo') {
        const problema = await verificarCodigo(paso.persona.id, v);
        if (problema) fallar(problema);
        else ir({ tipo: 'nuevoPin', persona: paso.persona, codigo: v });
      } else if (paso.tipo === 'nuevoPin') {
        const problema = validar.pin(v);
        if (problema) fallar(problema);
        else ir({ tipo: 'confirmar', persona: paso.persona, codigo: paso.codigo, pin: v });
      } else if (paso.tipo === 'confirmar') {
        if (v !== paso.pin) {
          fallar('No coinciden. Crea tu PIN otra vez.');
          setPaso({ tipo: 'nuevoPin', persona: paso.persona, codigo: paso.codigo });
        } else {
          const r = await activarUsuario(paso.persona.id, paso.codigo, v);
          if (r.token) {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
            // El rol lo dio coordinación al registrarla: se toma de la lista recién cargada.
            const lista = await recargarUsuarios().catch(() => usuarios);
            abrirSesion(r.token, lista.find((u) => u.id === paso.persona.id) ?? { ...paso.persona, rol: 'aprendiz' });
          } else fallar(r.error ?? 'No se pudo activar.');
        }
      }
    } catch (e) {
      fallar((e as Error).message);
    }
    setOcupado(false);
  }

  // --- Teclado (PIN, código, PIN nuevo y confirmación)
  if (paso.tipo === 'pin' || paso.tipo === 'codigo' || paso.tipo === 'nuevoPin' || paso.tipo === 'confirmar') {
    const persona = paso.tipo === 'pin' ? paso.usuario : paso.persona;
    const color = paso.tipo === 'pin' ? paso.color : colores.rosa;
    const titulos = {
      pin: 'Escribe tu PIN',
      codigo: 'Escribe tu código de 6 números',
      nuevoPin: 'Crea tu PIN de 4 números',
      confirmar: 'Escríbelo otra vez',
    };
    return (
      <ScrollView contentContainerStyle={[styles.centro, { paddingTop: arriba + espacio.m }]}>
        <Aparecer key={paso.tipo} estilo={styles.centrado}>
          <View style={[styles.avatarGrande, { backgroundColor: color }]}>
            <Text style={styles.inicialGrande}>{persona.nombre.charAt(0)}</Text>
          </View>
          <Text style={styles.titulo}>{persona.nombre}</Text>
          <Text style={styles.cuerpo}>{titulos[paso.tipo]}</Text>
          {paso.tipo === 'nuevoPin' && <Text style={styles.nota}>Que no sea fácil de adivinar: nada de 1111 ni 1234.</Text>}
        </Aparecer>
        <TecladoNumerico
          longitud={paso.tipo === 'codigo' ? 6 : 4}
          valor={valor}
          onCambio={escribir}
          onVolver={() => ir(paso.tipo === 'pin' ? { tipo: 'lista' } : { tipo: 'pendientes', lista: null })}
          error={error}
          ocupado={ocupado}
          sacudida={sacudida}
        />
      </ScrollView>
    );
  }

  // --- Activar: ¿quién eres? (solo personas registradas que no han creado su PIN)
  if (paso.tipo === 'pendientes') {
    return (
      <ScrollView contentContainerStyle={[styles.contenido, { paddingTop: arriba + espacio.l }]}>
        <Pressable onPress={() => ir({ tipo: 'lista' })} style={styles.atras} hitSlop={8}>
          <Ionicons name="arrow-back" size={24} color={colores.primario} />
          <Text style={styles.atrasTexto}>Volver</Text>
        </Pressable>
        <View>
          <Text style={styles.titulo}>Activar mi usuario</Text>
          <Text style={[styles.cuerpo, { textAlign: 'left' }]}>Toca tu nombre. Necesitas el código que te dio coordinación.</Text>
        </View>
        {!!error && <Text style={styles.error}>{error}</Text>}
        {paso.lista?.length === 0 && (
          <View style={styles.vacio}>
            <Ionicons name="checkmark-done-circle-outline" size={40} color={colores.gris} />
            <Text style={styles.cuerpo}>No hay usuarios por activar. Pídele a coordinación que te registre.</Text>
          </View>
        )}
        {paso.lista?.map((p, i) => (
          <Aparecer key={p.id} retraso={i * 40}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Activar a ${p.nombre}`}
              onPress={() => ir({ tipo: 'codigo', persona: p })}
              style={({ pressed }) => [styles.filaPendiente, pressed && { transform: [{ scale: 0.98 }] }]}
            >
              <View style={[styles.avatar, { backgroundColor: colores.rosa, width: 48, height: 48 }]}>
                <Text style={[styles.inicial, { fontSize: 22 }]}>{p.nombre.charAt(0)}</Text>
              </View>
              <Text style={styles.nombrePendiente}>{p.nombre}</Text>
              <Ionicons name="chevron-forward" size={24} color={colores.gris} />
            </Pressable>
          </Aparecer>
        ))}
      </ScrollView>
    );
  }

  // --- ¿Quién eres?
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
          const rol = ROLES[u.rol];
          return (
            <Aparecer key={u.id} retraso={i * 40}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={u.nombre}
                onPress={() => ir({ tipo: 'pin', usuario: u, color })}
                style={({ pressed }) => [styles.persona, { width: anchoTarjeta }, pressed && { transform: [{ scale: 0.95 }] }]}
              >
                <View style={[styles.avatar, { backgroundColor: color }]}>
                  <Text style={styles.inicial}>{u.nombre.charAt(0)}</Text>
                </View>
                <Text style={styles.nombre} numberOfLines={1}>
                  {u.nombre}
                </Text>
                <View style={[styles.insignia, { backgroundColor: rol.fondo }]}>
                  <Ionicons name={rol.icono} size={12} color={rol.color} />
                  <Text style={[styles.insigniaTexto, { color: rol.color }]}>{rol.nombre}</Text>
                </View>
              </Pressable>
            </Aparecer>
          );
        })}
      </View>

      <Pressable accessibilityRole="button" onPress={() => ir({ tipo: 'pendientes', lista: null })} style={({ pressed }) => [styles.activar, pressed && { opacity: 0.7 }]}>
        <Ionicons name="key-outline" size={22} color={colores.primario} />
        <Text style={styles.activarTexto}>¿Eres nuevo? Activa tu usuario</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 900, width: '100%', alignSelf: 'center' },
  centro: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: espacio.l, gap: espacio.m },
  centrado: { alignItems: 'center', gap: espacio.s },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
  nota: { fontSize: 13, fontFamily: fuente.normal, color: colores.gris, textAlign: 'center' },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  sinConexion: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.m },
  // Todas las tarjetas miden lo mismo, tengan el rol que tengan.
  persona: {
    height: 178,
    justifyContent: 'center',
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
  nombre: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto, maxWidth: '90%' },
  insignia: { flexDirection: 'row', alignItems: 'center', gap: 3, borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  insigniaTexto: { fontSize: 12, fontFamily: fuente.negrita },
  avatarGrande: { width: 88, height: 88, borderRadius: 44, justifyContent: 'center', alignItems: 'center', ...sombra },
  inicialGrande: { fontSize: 42, fontFamily: fuente.titulo, color: '#fff' },
  activar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: espacio.s,
    padding: espacio.m,
    borderRadius: 18,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: colores.rosa,
  },
  activarTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.primario },
  atras: { flexDirection: 'row', alignItems: 'center', gap: espacio.xs },
  atrasTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.primario },
  vacio: { alignItems: 'center', gap: espacio.s, padding: espacio.l },
  filaPendiente: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, backgroundColor: colores.tarjeta, borderRadius: 20, padding: espacio.m, ...sombra },
  nombrePendiente: { flex: 1, fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto },
});
