import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useState, type ComponentProps } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import { TecladoNumerico } from '@/componentes/TecladoNumerico';
import { Aparecer, useSacudir } from '@/componentes/animaciones';
import { useOperario } from '@/logica/operario';
import { LARGO_CODIGO, useTurnero } from '@/logica/turnero';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

type Paso = { tipo: 'explicar' } | { tipo: 'codigo' } | { tipo: 'confirmar'; codigo: string };

const PUNTOS: { icono: ComponentProps<typeof Ionicons>['name']; texto: string }[] = [
  { icono: 'tv-outline', texto: 'La tablet queda fija en el tablero del turno de hoy, con el avance en vivo.' },
  { icono: 'person-circle-outline', texto: 'Cada persona toca su nombre y ve su zona y sus cuadrantes, en orden.' },
  { icono: 'keypad-outline', texto: 'Para marcar un cuadrante o terminar su turno, escribe su PIN.' },
  { icono: 'lock-closed-outline', texto: 'Nadie puede salir del tablero sin el código que elijas ahora.' },
];

// Solo coordinación: elige un código de 6 números (dos veces) y deja la tablet en modo turnero.
// Al activarlo se cierra la sesión de coordinación, para que nadie quede con sus permisos.
export default function ActivarTurnero() {
  const { usuario, salir } = useOperario();
  const { activar } = useTurnero();
  const [paso, setPaso] = useState<Paso>({ tipo: 'explicar' });
  const [valor, setValor] = useState('');
  const [error, setError] = useState('');
  const { x, sacudir } = useSacudir();

  function fallar(mensaje: string) {
    setError(mensaje);
    setValor('');
    sacudir();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
  }

  async function cambiar(v: string) {
    setValor(v);
    setError('');
    if (v.length < LARGO_CODIGO) return;
    if (paso.tipo === 'codigo') {
      if (/^(\d)\1+$/.test(v) || '0123456789'.includes(v) || '9876543210'.includes(v)) {
        return fallar('Ese código es muy fácil de adivinar');
      }
      setValor('');
      setPaso({ tipo: 'confirmar', codigo: v });
    } else if (paso.tipo === 'confirmar') {
      if (v !== paso.codigo) {
        setPaso({ tipo: 'codigo' });
        return fallar('No coinciden. Elige el código otra vez');
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      await activar(v, usuario?.nombre ?? 'Coordinación');
      salir();
      router.replace('/turnero');
    }
  }

  if (paso.tipo === 'explicar') {
    return (
      <ScrollView contentContainerStyle={styles.contenido}>
        <Aparecer estilo={styles.cabeza}>
          <View style={styles.icono}>
            <Ionicons name="tv" size={40} color="#fff" />
          </View>
          <Text style={styles.titulo}>Modo turnero</Text>
          <Text style={styles.suave}>Para la tablet de la entrada del invernadero.</Text>
        </Aparecer>
        <View style={styles.tarjeta}>
          {PUNTOS.map((p, i) => (
            <Aparecer key={p.texto} retraso={60 * i} estilo={styles.punto}>
              <Ionicons name={p.icono} size={26} color={colores.primario} />
              <Text style={styles.cuerpo}>{p.texto}</Text>
            </Aparecer>
          ))}
        </View>
        <BotonGrande titulo="Elegir el código de salida" icono="arrow-forward" onPress={() => setPaso({ tipo: 'codigo' })} />
        <Text style={styles.nota}>Guárdalo bien: si se olvida, alguien de coordinación puede salir con su PIN.</Text>
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={[styles.contenido, { alignItems: 'center' }]}>
      <Text style={styles.titulo}>{paso.tipo === 'codigo' ? 'Elige un código de salida' : 'Escríbelo otra vez'}</Text>
      <Text style={styles.suave}>
        {paso.tipo === 'codigo' ? `${LARGO_CODIGO} números. Lo vas a necesitar para salir del turnero.` : 'Para confirmar que lo recuerdas.'}
      </Text>
      <TecladoNumerico
        longitud={LARGO_CODIGO}
        valor={valor}
        onCambio={cambiar}
        onVolver={() => {
          setValor('');
          setError('');
          setPaso(paso.tipo === 'confirmar' ? { tipo: 'codigo' } : { tipo: 'explicar' });
        }}
        error={error}
        sacudida={x}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 560, width: '100%', alignSelf: 'center' },
  cabeza: { alignItems: 'center', gap: espacio.s },
  icono: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: colores.primario,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 5,
    borderBottomColor: colores.primarioOscuro,
  },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto, textAlign: 'center' },
  suave: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 24, padding: espacio.l, gap: espacio.m, ...sombra },
  punto: { flexDirection: 'row', alignItems: 'center', gap: espacio.m },
  cuerpo: { flex: 1, fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.texto },
  nota: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: colores.gris, textAlign: 'center' },
});
