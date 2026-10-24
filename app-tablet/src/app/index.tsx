import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import { Ingreso } from '@/componentes/Ingreso';
import { useOperario } from '@/logica/operario';
import { colores, espacio, texto } from '@/tema';

export default function Inicio() {
  const { usuario, salir } = useOperario();

  if (!usuario) return <Ingreso />;

  const admin = usuario.rol === 'admin';

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>Hola, {usuario.nombre}</Text>
      <Text style={styles.cuerpo}>{admin ? 'Administración del turno' : '¿Qué quieres hacer hoy?'}</Text>

      <View style={styles.menu}>
        {admin ? (
          <>
            <BotonGrande
              titulo="Turno de hoy"
              subtitulo="Quién vino, reparto de cuadrantes y avance"
              color="#1B5E20"
              onPress={() => router.push('/turno')}
            />
            <BotonGrande
              titulo="Trabajadores"
              subtitulo="Agregar y quitar personas"
              color="#455A64"
              onPress={() => router.push('/trabajadores')}
            />
            <BotonGrande
              titulo="Lo que encontró el robot"
              subtitulo="Orden de corte de todo el invernadero"
              color="#6D4C41"
              onPress={() => router.push('/hoy')}
            />
          </>
        ) : (
          <>
            <BotonGrande
              titulo="Mi turno de hoy"
              subtitulo="Los cuadrantes que me tocan"
              color="#1B5E20"
              onPress={() => router.push('/mi-turno')}
            />
            <BotonGrande
              titulo="Lo que encontró el robot"
              subtitulo="Orden de corte de todo el invernadero"
              color="#6D4C41"
              onPress={() => router.push('/hoy')}
            />
            <BotonGrande
              titulo="Aprender las 3 categorías"
              subtitulo="Muy pronto · Punto óptimo · Muy tarde"
              color="#6D4C41"
              onPress={() => router.push('/aprender')}
            />
            <BotonGrande
              titulo="Juego: clasifica el botón"
              subtitulo="Mira la rosa y decide"
              onPress={() => router.push('/clasificar')}
            />
            <BotonGrande
              titulo="Sanación después del corte"
              subtitulo="En construcción"
              color="#33691E"
              onPress={() => router.push('/sanacion')}
            />
            <BotonGrande titulo="Mi progreso" color="#455A64" onPress={() => router.push('/progreso')} />
          </>
        )}
      </View>

      <BotonGrande titulo={`Salir · no soy ${usuario.nombre}`} color={colores.textoSuave} onPress={salir} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 720, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  menu: { gap: espacio.m, marginVertical: espacio.m },
});
