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
        <Stack.Screen name="aprender" options={{ title: 'Las 3 categorías' }} />
        <Stack.Screen name="clasificar" options={{ title: 'Juego: clasifica el botón' }} />
        <Stack.Screen name="sanacion" options={{ title: 'Sanación después del corte' }} />
        <Stack.Screen name="progreso" options={{ title: 'Mi progreso' }} />
      </Stack>
    </OperarioProvider>
  );
}
