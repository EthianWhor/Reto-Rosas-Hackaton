import { useEffect, useMemo, useRef, type ReactNode } from 'react';
import { Animated, Easing, StyleSheet, useWindowDimensions, View, type StyleProp, type ViewStyle } from 'react-native';

import { colores } from '@/tema';

// Animaciones pequeñas de RoseApp. Todas usan Animated de React Native (vienen en Expo Go).

/** Entra subiendo y apareciendo. `retraso` sirve para que una lista entre en cascada. */
export function Aparecer({ children, retraso = 0, estilo }: { children: ReactNode; retraso?: number; estilo?: StyleProp<ViewStyle> }) {
  const v = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(v, {
      toValue: 1,
      duration: 380,
      delay: retraso,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [v, retraso]);
  return (
    <Animated.View
      style={[
        estilo,
        { opacity: v, transform: [{ translateY: v.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }) }] },
      ]}
    >
      {children}
    </Animated.View>
  );
}

/** Crece con rebote cada vez que cambia `clave` (por ejemplo, un número que sube). */
export function Rebote({ clave, children, estilo }: { clave: string | number; children: ReactNode; estilo?: StyleProp<ViewStyle> }) {
  const v = useRef(new Animated.Value(1)).current;
  const primera = useRef(true);
  useEffect(() => {
    if (primera.current) {
      primera.current = false;
      return;
    }
    v.setValue(0.6);
    Animated.spring(v, { toValue: 1, friction: 3, tension: 160, useNativeDriver: true }).start();
  }, [clave, v]);
  return <Animated.View style={[estilo, { transform: [{ scale: v }] }]}>{children}</Animated.View>;
}

/** Devuelve un valor para `translateX` y una función que lo sacude (respuesta equivocada). */
export function useSacudir() {
  const x = useRef(new Animated.Value(0)).current;
  const sacudir = () => {
    x.setValue(0);
    Animated.sequence(
      [14, -12, 10, -8, 5, 0].map((toValue) => Animated.timing(x, { toValue, duration: 55, useNativeDriver: true })),
    ).start();
  };
  return { x, sacudir };
}

/** Barra de avance que se llena con animación. `valor` entre 0 y 1. */
export function BarraProgreso({ valor, color = colores.acierto, alto = 16 }: { valor: number; color?: string; alto?: number }) {
  const v = useRef(new Animated.Value(valor)).current;
  useEffect(() => {
    Animated.timing(v, { toValue: valor, duration: 450, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [v, valor]);
  return (
    <View style={[styles.barra, { height: alto, borderRadius: alto / 2 }]}>
      <Animated.View
        style={{
          height: '100%',
          borderRadius: alto / 2,
          backgroundColor: color,
          width: v.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }),
        }}
      >
        <View style={[styles.brillo, { borderRadius: alto / 2 }]} />
      </Animated.View>
    </View>
  );
}

const COLORES_PETALO = ['#D7263D', '#F06292', '#F8BBD0', '#C2185B', '#FF8FA3'];

/** Lluvia de pétalos de rosa para celebrar. Cada vez que cambia `disparo`, caen pétalos nuevos. */
export function LluviaDePetalos({ disparo, cantidad = 18 }: { disparo: number; cantidad?: number }) {
  const { width, height } = useWindowDimensions();
  const petalos = useMemo(
    () =>
      Array.from({ length: cantidad }, () => ({
        x: Math.random() * width,
        deriva: (Math.random() - 0.5) * 120,
        giro: (Math.random() - 0.5) * 720,
        tamano: 12 + Math.random() * 12,
        retraso: Math.random() * 250,
        duracion: 1300 + Math.random() * 900,
        color: COLORES_PETALO[Math.floor(Math.random() * COLORES_PETALO.length)],
        v: new Animated.Value(0),
      })),
    // `disparo` está a propósito: cada disparo arma pétalos nuevos.
    [disparo, cantidad, width, height],
  );

  useEffect(() => {
    if (disparo === 0) return;
    Animated.parallel(
      petalos.map((p) =>
        Animated.timing(p.v, {
          toValue: 1,
          duration: p.duracion,
          delay: p.retraso,
          easing: Easing.in(Easing.quad),
          useNativeDriver: true,
        }),
      ),
    ).start();
  }, [petalos, disparo]);

  if (disparo === 0) return null;
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {petalos.map((p, i) => (
        <Animated.View
          key={i}
          style={[
            styles.petalo,
            {
              left: p.x,
              width: p.tamano,
              height: p.tamano * 1.4,
              backgroundColor: p.color,
              opacity: p.v.interpolate({ inputRange: [0, 0.8, 1], outputRange: [1, 1, 0] }),
              transform: [
                { translateY: p.v.interpolate({ inputRange: [0, 1], outputRange: [-40, height * 0.85] }) },
                { translateX: p.v.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0, p.deriva, p.deriva * 0.4] }) },
                { rotate: p.v.interpolate({ inputRange: [0, 1], outputRange: ['0deg', `${p.giro}deg`] }) },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  barra: { width: '100%', backgroundColor: colores.borde, overflow: 'hidden' },
  brillo: { position: 'absolute', top: 3, left: 8, right: 8, height: 4, backgroundColor: 'rgba(255,255,255,0.35)' },
  petalo: { position: 'absolute', top: 0, borderTopLeftRadius: 20, borderBottomRightRadius: 20, borderTopRightRadius: 4, borderBottomLeftRadius: 4 },
});
