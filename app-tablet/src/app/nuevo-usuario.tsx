import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type ScrollViewInstance,
  type TextInputInstance,
  type TextInputProps,
} from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { ROLES, validar, type Rol } from '@/data/usuarios';
import { crearUsuario } from '@/logica/cuentas';
import { useOperario } from '@/logica/operario';
import { useAlturaTeclado } from '@/logica/useTeclado';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

const DETALLE: Record<Rol, string> = {
  aprendiz: 'Corta y practica con el juego',
  experto: 'Corta y revisa las dudas del robot',
  admin: 'Organiza el turno y los usuarios',
};

// Alta de un usuario. La coordinación registra los datos; la persona crea su propio PIN después,
// con el código que aparece al final (la coordinación nunca conoce el PIN).
export default function NuevoUsuario() {
  const { token } = useOperario();
  const teclado = useAlturaTeclado();
  const desplazar = useRef<ScrollViewInstance>(null);
  const campoCorreo = useRef<TextInputInstance>(null);
  const campoTelefono = useRef<TextInputInstance>(null);

  const [nombre, setNombre] = useState('');
  const [correo, setCorreo] = useState('');
  const [telefono, setTelefono] = useState('');
  const [rol, setRol] = useState<Rol>('aprendiz');
  const [tocados, setTocados] = useState<Record<string, boolean>>({});
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');
  const [creado, setCreado] = useState<{ nombre: string; codigo: string } | null>(null);

  // Cuando sale el teclado, se baja hasta el final para que el botón quede a la vista.
  useEffect(() => {
    if (teclado > 0) setTimeout(() => desplazar.current?.scrollToEnd({ animated: true }), 50);
  }, [teclado]);

  const errores = { nombre: validar.nombre(nombre), correo: validar.correo(correo), telefono: validar.telefono(telefono) };
  const listo = !errores.nombre && !errores.correo && !errores.telefono;

  async function agregar() {
    setTocados({ nombre: true, correo: true, telefono: true });
    if (!listo || !token) return;
    setOcupado(true);
    setError('');
    try {
      const { codigo } = await crearUsuario(token, { nombre, correo, telefono, rol });
      setCreado({ nombre: nombre.trim(), codigo });
    } catch (e) {
      setError((e as Error).message);
    }
    setOcupado(false);
  }

  if (creado) {
    return (
      <View style={styles.centro}>
        <Aparecer estilo={styles.tarjetaCodigo}>
          <Ionicons name="key" size={40} color={colores.primario} />
          <Text style={styles.tituloCodigo}>Código de {creado.nombre}</Text>
          <Text style={styles.codigo} selectable>
            {creado.codigo.slice(0, 3)} {creado.codigo.slice(3)}
          </Text>
          <Text style={styles.ayuda}>
            Entrégaselo en persona. Con él activa su usuario en esta tablet y crea su propio PIN. No se vuelve a mostrar.
          </Text>
          <BotonGrande titulo="Listo" icono="checkmark" onPress={() => router.back()} estilo={{ alignSelf: 'stretch' }} />
        </Aparecer>
      </View>
    );
  }

  return (
    <ScrollView
      ref={desplazar}
      contentContainerStyle={[styles.contenido, { paddingBottom: espacio.xl + teclado }]}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.tarjeta}>
        <Campo
          etiqueta="Nombre completo"
          valor={nombre}
          onChangeText={setNombre}
          error={tocados.nombre ? errores.nombre : ''}
          onBlur={() => setTocados((t) => ({ ...t, nombre: true }))}
          placeholder="Ej. María López"
          autoCapitalize="words"
          autoComplete="name"
          returnKeyType="next"
          onSubmitEditing={() => campoCorreo.current?.focus()}
        />
        <Campo
          ref={campoCorreo}
          etiqueta="Correo (opcional)"
          valor={correo}
          onChangeText={setCorreo}
          error={tocados.correo ? errores.correo : ''}
          onBlur={() => setTocados((t) => ({ ...t, correo: true }))}
          placeholder="maria@correo.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          returnKeyType="next"
          onSubmitEditing={() => campoTelefono.current?.focus()}
        />
        <Campo
          ref={campoTelefono}
          etiqueta="Teléfono (opcional)"
          valor={telefono}
          onChangeText={(t) => setTelefono(t.replace(/[^\d\s+()-]/g, ''))}
          error={tocados.telefono ? errores.telefono : ''}
          onBlur={() => setTocados((t) => ({ ...t, telefono: true }))}
          placeholder="300 123 4567"
          keyboardType="phone-pad"
          autoComplete="tel"
          returnKeyType="done"
        />

        <Text style={styles.etiqueta}>Rol</Text>
        <View style={styles.roles}>
          {(['aprendiz', 'experto', 'admin'] as Rol[]).map((r) => {
            const info = ROLES[r];
            const elegido = rol === r;
            return (
              <Pressable
                key={r}
                accessibilityRole="radio"
                accessibilityState={{ selected: elegido }}
                onPress={() => setRol(r)}
                style={[styles.rol, elegido && { backgroundColor: info.color, borderColor: info.color }]}
              >
                <Ionicons name={info.icono} size={22} color={elegido ? '#fff' : info.color} />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.rolTexto, { color: elegido ? '#fff' : colores.texto }]}>{info.nombre}</Text>
                  <Text style={[styles.rolDetalle, { color: elegido ? 'rgba(255,255,255,0.9)' : colores.textoSuave }]}>
                    {DETALLE[r]}
                  </Text>
                </View>
                {elegido && <Ionicons name="checkmark-circle" size={22} color="#fff" />}
              </Pressable>
            );
          })}
        </View>

        {!!error && <Text style={styles.error}>{error}</Text>}
        <BotonGrande titulo="Registrar" icono="person-add" deshabilitado={ocupado} onPress={agregar} />
        <Text style={styles.nota}>La persona creará su propio PIN con el código que aparece al registrar.</Text>
      </View>
    </ScrollView>
  );
}

type CampoProps = TextInputProps & { etiqueta: string; valor: string; error: string; ref?: React.Ref<TextInputInstance> };

function Campo({ etiqueta, valor, error, ref, ...props }: CampoProps) {
  return (
    <View style={styles.campo}>
      <Text style={styles.etiqueta}>{etiqueta}</Text>
      <TextInput
        ref={ref}
        value={valor}
        placeholderTextColor={colores.gris}
        style={[styles.input, !!error && styles.inputError]}
        {...props}
      />
      {!!error && <Text style={styles.errorCampo}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, maxWidth: 560, width: '100%', alignSelf: 'center' },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.s, ...sombra },
  campo: { gap: espacio.xs, marginBottom: espacio.s },
  etiqueta: { fontSize: texto.pequeno, fontFamily: fuente.negrita, color: colores.textoSuave },
  input: {
    fontSize: texto.cuerpo + 2,
    fontFamily: fuente.normal,
    color: colores.texto,
    backgroundColor: colores.fondo,
    borderWidth: 2,
    borderColor: colores.borde,
    borderRadius: 16,
    padding: espacio.m,
  },
  inputError: { borderColor: colores.error },
  errorCampo: { fontSize: 13, fontFamily: fuente.negrita, color: colores.error },
  roles: { gap: espacio.s, marginBottom: espacio.m },
  rol: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, padding: espacio.m, borderRadius: 16, borderWidth: 2, borderColor: colores.borde },
  rolTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita },
  rolDetalle: { fontSize: 13, fontFamily: fuente.normal },
  error: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.error },
  nota: { fontSize: 13, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.l },
  tarjetaCodigo: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, alignItems: 'center', maxWidth: 420, width: '100%', ...sombra },
  tituloCodigo: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  codigo: { fontSize: 48, fontFamily: fuente.titulo, color: colores.primario, letterSpacing: 6 },
  ayuda: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
});
