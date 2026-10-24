import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useEffect, useRef, useState, type ComponentProps } from 'react';
import {
  ActivityIndicator,
  BackHandler,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BotonGrande } from '@/componentes/BotonGrande';
import { Marca } from '@/componentes/Marca';
import { TecladoNumerico } from '@/componentes/TecladoNumerico';
import { Aparecer, BarraProgreso, LluviaDePetalos, Rebote, useSacudir } from '@/componentes/animaciones';
import type { Usuario } from '@/data/usuarios';
import { ROLES } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { fechaLarga } from '@/logica/reporte';
import { revisar, supabase } from '@/logica/supabase';
import { duracion, type Tarea } from '@/logica/turno';
import { LARGO_CODIGO, useTurnero } from '@/logica/turnero';
import { useTurno } from '@/logica/useTurno';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Tablero del modo turnero. La tablet queda fija en la entrada: cada persona toca su nombre y ve a
// dónde ir. Ver su turno no pide nada; marcar un cuadrante pide su PIN (así nadie marca por otro).
// Sin tocar la pantalla un minuto, vuelve sola al tablero y cierra la sesión de quien la usó.
const VOLVER_MS = 60_000;

type Vista =
  | { tipo: 'tablero' }
  | { tipo: 'persona'; id: string }
  | { tipo: 'salir' }
  | { tipo: 'emergencia'; admin?: Usuario };

/** Lo que se quería marcar antes de pedir el PIN. */
type Pendiente = { cuadrantes: string[]; hecho: boolean };

export default function Turnero() {
  const { usuario, usuarios, entrar, salir } = useOperario();
  const { datos, reparto, trabajadores, error, cambiarHecho } = useTurno();
  const { activadoPor } = useTurnero();
  const [vista, setVista] = useState<Vista>({ tipo: 'tablero' });
  const [pidePin, setPidePin] = useState<Pendiente | null>(null);
  const [petalos, setPetalos] = useState(0);
  const [hora, setHora] = useState(new Date());
  const ultimoToque = useRef(Date.now());
  const arriba = useSafeAreaInsets().top;
  const { width } = useWindowDimensions();
  const columnas = width >= 900 ? 4 : width >= 600 ? 3 : 2;
  const angosta = width < 480;
  const { activo } = useTurnero();

  // Al salir con el código, vuelve al ingreso (en Android la pila no siempre cambia sola).
  useEffect(() => {
    if (!activo) router.replace('/');
  }, [activo]);

  function volverAlTablero() {
    setPidePin(null);
    setVista({ tipo: 'tablero' });
    salir();
  }

  // El botón "atrás" de Android no saca del turnero: a lo más, vuelve al tablero.
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (vista.tipo !== 'tablero') volverAlTablero();
      return true;
    });
    return () => sub.remove();
  });

  // Reloj de la pantalla y regreso automático al tablero.
  useEffect(() => {
    const reloj = setInterval(() => {
      setHora(new Date());
      if (vista.tipo !== 'tablero' && Date.now() - ultimoToque.current > VOLVER_MS) volverAlTablero();
    }, 5_000);
    return () => clearInterval(reloj);
  });

  const tocar = () => {
    ultimoToque.current = Date.now();
    return false;
  };

  const presentes = datos && reparto ? trabajadores.filter((t) => datos.presentes.includes(t.id)) : [];
  const avance = (id: string) => {
    const tareas = reparto?.porTrabajador[id]?.tareas ?? [];
    return { tareas, hechas: tareas.filter((t) => datos?.hechos[t.cuadrante.cuadrante_id]).length };
  };
  const totalCuadrantes = presentes.reduce((s, p) => s + avance(p.id).tareas.length, 0);
  const totalHechos = presentes.reduce((s, p) => s + avance(p.id).hechas, 0);
  const totalRosas = presentes.reduce((s, p) => s + avance(p.id).tareas.reduce((r, t) => r + t.cuadrante.optimo, 0), 0);

  function marcar(persona: Usuario, p: Pendiente) {
    if (usuario?.id !== persona.id) return setPidePin(p);
    const { tareas, hechas } = avance(persona.id);
    p.cuadrantes.forEach((c) => cambiarHecho(c, persona.id, p.hecho));
    if (p.hecho) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
      if (hechas + p.cuadrantes.length === tareas.length) setPetalos((n) => n + 1);
    }
  }

  let contenido;
  if (vista.tipo === 'salir') {
    contenido = <SalirConCodigo onCancelar={() => setVista({ tipo: 'tablero' })} onOlvido={() => setVista({ tipo: 'emergencia' })} />;
  } else if (vista.tipo === 'emergencia') {
    contenido = (
      <Emergencia
        admins={usuarios.filter((u) => u.rol === 'admin')}
        admin={vista.admin}
        onElegir={(admin) => setVista({ tipo: 'emergencia', admin })}
        onCancelar={() => setVista({ tipo: 'tablero' })}
      />
    );
  } else if (!datos || !reparto) {
    contenido = (
      <View style={styles.centro}>
        {error ? <Aviso icono="cloud-offline-outline" texto={error} /> : <ActivityIndicator size="large" color={colores.primario} />}
      </View>
    );
  } else if (vista.tipo === 'persona') {
    const persona = presentes.find((p) => p.id === vista.id);
    if (!persona) {
      contenido = <Aviso icono="person-outline" texto="Esta persona ya no está en el turno de hoy." />;
    } else if (pidePin) {
      contenido = (
        <PinPersona
          persona={persona}
          titulo={`${persona.nombre.split(' ')[0]}, escribe tu PIN`}
          detalle="Para marcar tus cuadrantes"
          entrar={(pin) => entrar(persona, pin)}
          onListo={() => {
            // La sesión recién abierta llega en el siguiente render: se marca desde ahí.
            marcarConSesion(persona, pidePin);
            setPidePin(null);
          }}
          onCancelar={() => setPidePin(null)}
        />
      );
    } else {
      contenido = (
        <TurnoPersona
          persona={persona}
          tareas={avance(persona.id).tareas}
          hechos={datos.hechos}
          conSesion={usuario?.id === persona.id}
          onMarcar={(p) => marcar(persona, p)}
          onVolver={volverAlTablero}
        />
      );
    }
  } else {
    contenido = (
      <ScrollView contentContainerStyle={styles.tablero}>
        <Aparecer estilo={styles.resumen}>
          <Text style={styles.fecha}>{fechaLarga(datos.reporte.fecha)}</Text>
          <View style={styles.filaResumen}>
            <Rebote clave={totalHechos}>
              <Text style={styles.contador}>
                {totalHechos}
                <Text style={styles.contadorTotal}>/{totalCuadrantes}</Text>
              </Text>
            </Rebote>
            <Text style={styles.resumenTexto}>
              cuadrantes listos · {presentes.length} en turno · {totalRosas} rosas para cortar
            </Text>
          </View>
          <BarraProgreso valor={totalCuadrantes ? totalHechos / totalCuadrantes : 0} />
        </Aparecer>

        <Text style={styles.pregunta}>¿Quién eres?</Text>
        {presentes.length === 0 ? (
          <Aviso icono="people-outline" texto="Coordinación todavía no ha marcado quién vino hoy." />
        ) : (
          <View style={styles.rejilla}>
            {presentes.map((p, i) => {
              const { tareas, hechas } = avance(p.id);
              const listo = tareas.length > 0 && hechas === tareas.length;
              const rol = ROLES[p.rol];
              return (
                <Aparecer key={p.id} retraso={i * 40} estilo={{ width: `${100 / columnas - 2}%` }}>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={p.nombre}
                    onPress={() => {
                      ultimoToque.current = Date.now();
                      setVista({ tipo: 'persona', id: p.id });
                    }}
                    style={({ pressed }) => [styles.tarjeta, listo && styles.tarjetaLista, pressed && { transform: [{ scale: 0.97 }] }]}
                  >
                    <View style={[styles.avatar, { backgroundColor: listo ? colores.acierto : rol.color }]}>
                      {listo ? (
                        <Ionicons name="checkmark" size={30} color="#fff" />
                      ) : (
                        <Text style={styles.avatarLetra}>{p.nombre[0]}</Text>
                      )}
                    </View>
                    <Text style={styles.nombre} numberOfLines={1} adjustsFontSizeToFit>
                      {p.nombre}
                    </Text>
                    <Text style={[styles.estado, listo && { color: colores.aciertoOscuro }]}>
                      {tareas.length === 0 ? 'Sin cuadrantes' : listo ? '¡Terminó!' : `${hechas} de ${tareas.length}`}
                    </Text>
                  </Pressable>
                </Aparecer>
              );
            })}
          </View>
        )}
        {reparto.sinAsignar.length > 0 && (
          <Text style={styles.nota}>
            {reparto.sinAsignar.length} cuadrantes con rosas no caben en el turno de hoy. Coordinación los ve en "Turno de hoy".
          </Text>
        )}
        <Text style={styles.nota}>
          {datos.origen === 'ejemplo' ? 'Reporte de ejemplo' : `Ronda del robot ${datos.reporte.id_ronda}`} · se actualiza en vivo
        </Text>
      </ScrollView>
    );
  }

  // Marca lo pendiente apenas la sesión de la persona está abierta.
  const porMarcar = useRef<{ persona: Usuario; p: Pendiente } | null>(null);
  function marcarConSesion(persona: Usuario, p: Pendiente) {
    porMarcar.current = { persona, p };
  }
  useEffect(() => {
    const espera = porMarcar.current;
    if (espera && usuario?.id === espera.persona.id) {
      porMarcar.current = null;
      marcar(espera.persona, espera.p);
    }
  });

  return (
    <View style={styles.pantalla} onStartShouldSetResponderCapture={tocar}>
      <View style={[styles.barra, { paddingTop: arriba + espacio.s }]}>
        <Marca tamano={angosta ? 18 : 22} />
        <View style={styles.modo}>
          <Ionicons name="tv-outline" size={14} color={colores.primario} />
          {!angosta && <Text style={styles.modoTexto}>Turnero</Text>}
        </View>
        <View style={{ flex: 1 }} />
        <Text style={[styles.hora, angosta && { fontSize: texto.cuerpo }]} numberOfLines={1}>
          {`${hora.getHours() % 12 || 12}:${String(hora.getMinutes()).padStart(2, '0')}`}
        </Text>
        {vista.tipo !== 'salir' && vista.tipo !== 'emergencia' && (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Salir del modo turnero"
            hitSlop={10}
            onPress={() => {
              salir();
              setPidePin(null);
              setVista({ tipo: 'salir' });
            }}
            style={styles.candado}
          >
            <Ionicons name="lock-closed" size={18} color={colores.textoSuave} />
          </Pressable>
        )}
      </View>
      {contenido}
      {!!activadoPor && vista.tipo === 'tablero' && <Text style={styles.pie}>Activado por {activadoPor}</Text>}
      <LluviaDePetalos disparo={petalos} cantidad={36} />
    </View>
  );
}

function TurnoPersona({
  persona,
  tareas,
  hechos,
  conSesion,
  onMarcar,
  onVolver,
}: {
  persona: Usuario;
  tareas: Tarea[];
  hechos: Record<string, string>;
  conSesion: boolean;
  onMarcar: (p: Pendiente) => void;
  onVolver: () => void;
}) {
  const hechas = tareas.filter((t) => hechos[t.cuadrante.cuadrante_id]).length;
  const listo = tareas.length > 0 && hechas === tareas.length;
  const faltan = tareas.filter((t) => !hechos[t.cuadrante.cuadrante_id]).map((t) => t.cuadrante.cuadrante_id);
  const camas = [...new Set(tareas.map((t) => t.cuadrante.cama))].sort((a, b) => a - b);
  const minutos = tareas.reduce((s, t) => s + t.minutos, 0);
  const rosas = tareas.reduce((s, t) => s + t.cuadrante.optimo, 0);
  const zona = camas.length === 0 ? '' : camas.length === 1 ? `Cama ${camas[0]}` : `Camas ${camas[0]} a ${camas[camas.length - 1]}`;

  return (
    <ScrollView contentContainerStyle={styles.tablero}>
      <Pressable accessibilityRole="button" onPress={onVolver} style={styles.volver} hitSlop={8}>
        <Ionicons name="arrow-back" size={22} color={colores.primario} />
        <Text style={styles.volverTexto}>No soy {persona.nombre.split(' ')[0]}</Text>
      </Pressable>

      <Aparecer estilo={[styles.resumen, listo && styles.resumenListo]}>
        <Text style={styles.saludo}>Hola, {persona.nombre.split(' ')[0]}</Text>
        {tareas.length === 0 ? (
          <Text style={styles.resumenTexto}>Hoy no tienes cuadrantes para cortar.</Text>
        ) : (
          <>
            <View style={styles.zona}>
              <Ionicons name="location" size={26} color={colores.primario} />
              <Text style={styles.zonaTexto}>{zona}</Text>
            </View>
            <View style={styles.filaResumen}>
              <Rebote clave={hechas}>
                <Text style={styles.contador}>
                  {hechas}
                  <Text style={styles.contadorTotal}>/{tareas.length}</Text>
                </Text>
              </Rebote>
              <Text style={styles.resumenTexto}>{listo ? '¡Turno completo!' : `${rosas} rosas · ~${duracion(minutos)}`}</Text>
            </View>
            <BarraProgreso valor={hechas / tareas.length} color={colores.acierto} />
          </>
        )}
      </Aparecer>

      {tareas.map(({ cuadrante: c, minutos: m }, i) => {
        const hecho = !!hechos[c.cuadrante_id];
        return (
          <Aparecer key={c.cuadrante_id} retraso={80 + i * 40}>
            <Pressable
              accessibilityRole="checkbox"
              accessibilityState={{ checked: hecho }}
              accessibilityLabel={`Cama ${c.cama}, metros ${c.desde_m} a ${c.hasta_m}`}
              onPress={() => onMarcar({ cuadrantes: [c.cuadrante_id], hecho: !hecho })}
              style={({ pressed }) => [styles.fila, hecho && styles.filaHecha, pressed && { transform: [{ scale: 0.98 }] }]}
            >
              <Rebote clave={hecho ? 1 : 0} estilo={[styles.check, hecho && styles.checkHecho]}>
                {hecho ? <Ionicons name="checkmark" size={30} color="#fff" /> : <Text style={styles.checkTexto}>{i + 1}</Text>}
              </Rebote>
              <View style={{ flex: 1 }}>
                <Text style={[styles.filaTitulo, hecho && styles.tachado]}>
                  Cama {c.cama} · metros {c.desde_m}–{c.hasta_m}
                </Text>
                <Text style={[styles.cuerpo, { textAlign: 'left' }]}>
                  {c.optimo} rosas · ~{duracion(m)}
                </Text>
              </View>
            </Pressable>
          </Aparecer>
        );
      })}

      {faltan.length > 0 && (
        <BotonGrande
          titulo="Terminé mi turno"
          subtitulo={`Marca los ${faltan.length} cuadrantes que faltan`}
          icono="checkmark-done"
          color={colores.acierto}
          onPress={() => onMarcar({ cuadrantes: faltan, hecho: true })}
        />
      )}
      <Text style={styles.nota}>
        {conSesion ? 'Tu sesión se cierra sola al volver al tablero.' : 'Para marcar te pedimos tu PIN.'}
      </Text>
    </ScrollView>
  );
}

/** PIN de 4 números de una persona. `entrar` devuelve false si no coincide. */
function PinPersona({
  persona,
  titulo,
  detalle,
  entrar,
  onListo,
  onCancelar,
}: {
  persona: Usuario;
  titulo: string;
  detalle: string;
  entrar: (pin: string) => Promise<boolean>;
  onListo: () => void;
  onCancelar: () => void;
}) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const { x, sacudir } = useSacudir();

  async function cambiar(v: string) {
    setPin(v);
    setError('');
    if (v.length < 4) return;
    setOcupado(true);
    try {
      if (await entrar(v)) return onListo();
      setError('PIN incorrecto');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setOcupado(false);
    }
    setPin('');
    sacudir();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
  }

  return (
    <ScrollView contentContainerStyle={styles.teclado}>
      <View style={[styles.avatar, styles.avatarGrande, { backgroundColor: ROLES[persona.rol].color }]}>
        <Text style={[styles.avatarLetra, { fontSize: 40 }]}>{persona.nombre[0]}</Text>
      </View>
      <Text style={styles.pregunta}>{titulo}</Text>
      <Text style={styles.cuerpo}>{detalle}</Text>
      <TecladoNumerico longitud={4} valor={pin} onCambio={cambiar} onVolver={onCancelar} error={error} ocupado={ocupado} sacudida={x} />
    </ScrollView>
  );
}

function SalirConCodigo({ onCancelar, onOlvido }: { onCancelar: () => void; onOlvido: () => void }) {
  const { salirConCodigo } = useTurnero();
  const [codigo, setCodigo] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const { x, sacudir } = useSacudir();

  async function cambiar(v: string) {
    setCodigo(v);
    setError('');
    if (v.length < LARGO_CODIGO) return;
    setOcupado(true);
    const mensaje = await salirConCodigo(v);
    setOcupado(false);
    if (!mensaje) return;
    setError(mensaje);
    setCodigo('');
    sacudir();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
  }

  return (
    <ScrollView contentContainerStyle={styles.teclado}>
      <View style={[styles.avatar, styles.avatarGrande, { backgroundColor: colores.primario }]}>
        <Ionicons name="lock-closed" size={36} color="#fff" />
      </View>
      <Text style={styles.pregunta}>Salir del modo turnero</Text>
      <Text style={styles.cuerpo}>Escribe el código que eligió coordinación al activarlo.</Text>
      <TecladoNumerico longitud={LARGO_CODIGO} valor={codigo} onCambio={cambiar} onVolver={onCancelar} error={error} ocupado={ocupado} sacudida={x} />
      <Pressable accessibilityRole="button" onPress={onOlvido} hitSlop={8}>
        <Text style={styles.enlace}>¿Olvidaste el código? Entra con un PIN de coordinación</Text>
      </Pressable>
    </ScrollView>
  );
}

// Si nadie recuerda el código, una persona de coordinación confirma su PIN. No abre su sesión:
// solo se comprueba el PIN y se cierra de inmediato.
function Emergencia({
  admins,
  admin,
  onElegir,
  onCancelar,
}: {
  admins: Usuario[];
  admin?: Usuario;
  onElegir: (a: Usuario) => void;
  onCancelar: () => void;
}) {
  const { salirSinCodigo } = useTurnero();
  if (admin) {
    return (
      <PinPersona
        persona={admin}
        titulo={`PIN de ${admin.nombre}`}
        detalle="Al confirmarlo, la tablet sale del modo turnero."
        entrar={async (pin) => {
          const token = revisar(await supabase.rpc('entrar', { p_persona: admin.id, p_pin: pin })) as string | null;
          if (token) supabase.rpc('salir', { p_token: token }).then(() => {});
          return !!token;
        }}
        onListo={() => salirSinCodigo()}
        onCancelar={onCancelar}
      />
    );
  }
  return (
    <ScrollView contentContainerStyle={styles.teclado}>
      <Text style={styles.pregunta}>¿Quién de coordinación eres?</Text>
      <View style={styles.listaAdmins}>
        {admins.map((a) => (
          <BotonGrande key={a.id} titulo={a.nombre} icono="shield-checkmark" claro onPress={() => onElegir(a)} />
        ))}
      </View>
      <BotonGrande titulo="Volver al tablero" icono="arrow-back" claro onPress={onCancelar} />
    </ScrollView>
  );
}

function Aviso({ icono, texto: mensaje }: { icono: ComponentProps<typeof Ionicons>['name']; texto: string }) {
  return (
    <Aparecer estilo={styles.aviso}>
      <Ionicons name={icono} size={56} color={colores.rosa} />
      <Text style={styles.avisoTexto}>{mensaje}</Text>
    </Aparecer>
  );
}

const styles = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: colores.fondo },
  barra: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.s,
    paddingHorizontal: espacio.l,
    paddingBottom: espacio.s,
  },
  modo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colores.rosaSuave,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  modoTexto: { fontSize: 13, fontFamily: fuente.negrita, color: colores.primario },
  hora: { flexShrink: 1, fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto },
  candado: {
    flexShrink: 0,
    width: 44,
    height: 44,
    borderRadius: 20,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  tablero: { padding: espacio.l, gap: espacio.m, maxWidth: 1000, width: '100%', alignSelf: 'center', paddingBottom: 80 },
  resumen: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, ...sombra },
  resumenListo: { backgroundColor: colores.aciertoSuave },
  fecha: { fontSize: texto.pequeno, fontFamily: fuente.negrita, color: colores.textoSuave, textTransform: 'uppercase', letterSpacing: 1 },
  filaResumen: { flexDirection: 'row', alignItems: 'baseline', gap: espacio.m, flexWrap: 'wrap' },
  contador: { fontSize: 48, fontFamily: fuente.titulo, color: colores.acierto },
  contadorTotal: { fontSize: 28, color: colores.textoSuave },
  resumenTexto: { flexShrink: 1, fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
  pregunta: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  rejilla: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: espacio.m },
  tarjeta: {
    alignItems: 'center',
    gap: espacio.s,
    backgroundColor: colores.tarjeta,
    borderRadius: 22,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    paddingVertical: espacio.l,
    paddingHorizontal: espacio.s,
    height: 172,
    justifyContent: 'center',
  },
  tarjetaLista: { borderColor: colores.acierto, backgroundColor: colores.aciertoSuave },
  avatar: { width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center' },
  avatarGrande: { width: 84, height: 84, borderRadius: 42 },
  avatarLetra: { fontSize: 28, fontFamily: fuente.titulo, color: '#fff' },
  nombre: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  estado: { fontSize: texto.pequeno + 1, fontFamily: fuente.negrita, color: colores.textoSuave },
  nota: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.gris, textAlign: 'center' },
  pie: { position: 'absolute', bottom: espacio.s, alignSelf: 'center', fontSize: 12, fontFamily: fuente.normal, color: colores.gris },
  volver: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', paddingVertical: espacio.xs },
  volverTexto: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.primario },
  saludo: { fontSize: 32, fontFamily: fuente.titulo, color: colores.texto },
  zona: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  zonaTexto: { fontSize: texto.subtitulo + 3, fontFamily: fuente.titulo, color: colores.primario },
  fila: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    backgroundColor: colores.tarjeta,
    borderRadius: 20,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    padding: espacio.m,
  },
  filaHecha: { borderColor: colores.acierto, backgroundColor: colores.aciertoSuave },
  check: { width: 52, height: 52, borderRadius: 16, borderWidth: 3, borderColor: colores.borde, justifyContent: 'center', alignItems: 'center' },
  checkHecho: { backgroundColor: colores.acierto, borderColor: colores.acierto },
  checkTexto: { fontSize: texto.subtitulo, fontFamily: fuente.titulo, color: colores.textoSuave },
  filaTitulo: { fontSize: texto.cuerpo + 2, fontFamily: fuente.titulo, color: colores.texto },
  tachado: { textDecorationLine: 'line-through', color: colores.textoSuave },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
  teclado: { padding: espacio.l, gap: espacio.m, alignItems: 'center', maxWidth: 460, width: '100%', alignSelf: 'center' },
  enlace: { fontSize: texto.cuerpo, fontFamily: fuente.negrita, color: colores.primario, textAlign: 'center' },
  listaAdmins: { alignSelf: 'stretch', gap: espacio.s },
  aviso: { alignItems: 'center', gap: espacio.m, padding: espacio.xl },
  avisoTexto: { fontSize: texto.subtitulo, fontFamily: fuente.negrita, color: colores.texto, textAlign: 'center' },
});
