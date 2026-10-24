import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { OperarioProvider } from '@/logica/operario';
import { colores } from '@/tema';

export default function Layout() {
  return (
    <OperarioProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colores.fondo },
          headerTintColor: colores.texto,
          headerTitleStyle: { fontWeight: '700' },
          contentStyle: { backgroundColor: colores.fondo },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Punto de Corte' }} />
        <Stack.Screen name="hoy" options={{ title: 'Lo que encontró el robot' }} />
        <Stack.Screen name="mi-turno" options={{ title: 'Mi turno de hoy' }} />
        <Stack.Screen name="turno" options={{ title: 'Turno de hoy' }} />
        <Stack.Screen name="trabajadores" options={{ title: 'Trabajadores' }} />
        <Stack.Screen name="aprender" options={{ title: 'Las 3 categorías' }} />
        <Stack.Screen name="clasificar" options={{ title: 'Juego: clasifica el botón' }} />
        <Stack.Screen name="sanacion" options={{ title: 'Sanación después del corte' }} />
        <Stack.Screen name="progreso" options={{ title: 'Mi progreso' }} />
      </Stack>
    </OperarioProvider>
  );
}
