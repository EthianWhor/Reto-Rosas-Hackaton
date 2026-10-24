import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';

import type { Reporte } from '@/data/reporte';
import { cortaEnTurno } from '@/data/usuarios';
import { useOperario } from '@/logica/operario';
import { cargarReporte, type Origen } from '@/logica/reporte';
import { supabase } from '@/logica/supabase';
import {
  guardarConfig,
  guardarPresentes,
  leerConfig,
  leerHechos,
  leerPresentes,
  marcarHecho,
  repartir,
  type ConfigTurno,
} from '@/logica/turno';

/**
 * Todo lo del turno de hoy: reporte del robot, quién vino, configuración, reparto y avance.
 * Escucha los cambios de Supabase en vivo: si alguien marca un cuadrante en otra tablet, se ve aquí.
 */
export function useTurno() {
  const { usuarios, token } = useOperario();
  const trabajadores = useMemo(() => usuarios.filter(cortaEnTurno), [usuarios]);
  const [error, setError] = useState('');
  const [datos, setDatos] = useState<{
    reporte: Reporte;
    origen: Origen;
    config: ConfigTurno;
    presentes: string[];
    hechos: Record<string, string>;
  } | null>(null);

  const recargar = useCallback(async () => {
    try {
      const { reporte, origen } = await cargarReporte();
      const [config, presentes, hechos] = await Promise.all([
        leerConfig(),
        leerPresentes(reporte.fecha, trabajadores),
        leerHechos(reporte.id_ronda),
      ]);
      setDatos({ reporte, origen, config, presentes, hechos });
      setError('');
    } catch (e) {
      setError((e as Error).message);
    }
  }, [trabajadores]);

  useFocusEffect(
    useCallback(() => {
      recargar();
    }, [recargar]),
  );

  useEffect(() => {
    const canal = supabase
      .channel('turno')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'cuadrantes_hechos' }, () => recargar())
      .on('postgres_changes', { event: '*', schema: 'public', table: 'asistencia' }, () => recargar())
      .on('postgres_changes', { event: '*', schema: 'public', table: 'config_turno' }, () => recargar())
      .on('postgres_changes', { event: '*', schema: 'public', table: 'reportes' }, () => recargar())
      .subscribe();
    return () => {
      supabase.removeChannel(canal);
    };
  }, [recargar]);

  const reparto = useMemo(
    () =>
      datos &&
      repartir(
        datos.reporte,
        trabajadores.filter((t) => datos.presentes.includes(t.id)),
        datos.config,
      ),
    [datos, trabajadores],
  );

  // Cada cambio se muestra de una vez y luego se guarda; si falla, se recarga lo que hay en la base.
  async function guardar(cambio: () => Promise<void>, nuevos: Partial<NonNullable<typeof datos>>) {
    if (!datos || !token) return;
    setDatos({ ...datos, ...nuevos });
    try {
      await cambio();
      setError('');
    } catch (e) {
      setError((e as Error).message);
      recargar();
    }
  }

  const cambiarConfig = (config: ConfigTurno) => guardar(() => guardarConfig(token!, config), { config });

  function cambiarPresente(id: string, presente: boolean) {
    if (!datos) return;
    const presentes = presente ? [...datos.presentes, id] : datos.presentes.filter((p) => p !== id);
    return guardar(() => guardarPresentes(token!, datos.reporte.fecha, presentes), { presentes });
  }

  function cambiarHecho(cuadranteId: string, usuarioId: string, hecho: boolean) {
    if (!datos) return;
    const hechos = { ...datos.hechos };
    if (hecho) hechos[cuadranteId] = usuarioId;
    else delete hechos[cuadranteId];
    return guardar(() => marcarHecho(token!, datos.reporte.id_ronda, cuadranteId, hecho), { hechos });
  }

  return { datos, reparto, trabajadores, error, recargar, cambiarConfig, cambiarPresente, cambiarHecho };
}
