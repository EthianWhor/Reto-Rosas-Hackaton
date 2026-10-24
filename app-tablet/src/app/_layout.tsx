import {
  Nunito_600SemiBold,
  Nunito_800ExtraBold,
  Nunito_900Black,
  useFonts,
} from '@expo-google-fonts/nunito';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { OperarioProvider, useOperario } from '@/logica/operario';
import { colores, fuente } from '@/tema';

SplashScreen.preventAutoHideAsync();

export default function Layout() {
  const [cargadas, error] = useFonts({ Nunito_600SemiBold, Nunito_800ExtraBold, Nunito_900Black });

  useEffect(() => {
    if (cargadas || error) SplashScreen.hideAsync();
  }, [cargadas, error]);

  if (!cargadas && !error) return null;

  return (
    <OperarioProvider>
      <StatusBar style="dark" />
      <Navegacion />
    </OperarioProvider>
  );
}

// Sin sesión solo se ve el ingreso (index); las pantallas de administración, solo con rol admin.
// Si la sesión se cierra, la app vuelve sola al ingreso.
function Navegacion() {
  const { usuario } = useOperario();
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colores.fondo },
        headerShadowVisible: false,
        headerTintColor: colores.primario,
        headerTitleStyle: { fontFamily: fuente.negrita, color: colores.texto },
        contentStyle: { backgroundColor: colores.fondo },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false, title: 'RoseApp' }} />
      <Stack.Protected guard={!!usuario}>
        <Stack.Screen name="hoy" options={{ title: 'Lo que vio el robot' }} />
        <Stack.Screen name="mi-turno" options={{ title: 'Mi turno' }} />
        <Stack.Screen name="aprender" options={{ title: 'Aprender' }} />
        <Stack.Screen name="clasificar" options={{ headerShown: false, title: 'Practicar' }} />
        <Stack.Screen name="sanacion" options={{ title: 'Sanación' }} />
        <Stack.Screen name="progreso" options={{ title: 'Mi progreso' }} />
      </Stack.Protected>
      <Stack.Protected guard={usuario?.rol === 'admin'}>
        <Stack.Screen name="turno" options={{ title: 'Turno de hoy' }} />
        <Stack.Screen name="trabajadores" options={{ title: 'Personas' }} />
      </Stack.Protected>
    </Stack>
  );
}
