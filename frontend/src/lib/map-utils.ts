/**
 * Utilidades puras del mapa (testeables sin Leaflet):
 * - Factor de radio adaptativo según zoom.
 * - Conteos por categoría sobre los registros cargados.
 */

import type { MapPoints } from '../api/types'

export const DEFAULT_OPACITY = 0.7
export const DEFAULT_RADIUS = 3.2
export const MIN_RADIUS = 1.5
export const MAX_RADIUS = 7
export const MIN_OPACITY = 0.15
export const MAX_OPACITY = 1

/**
 * Factor multiplicador del radio según el nivel de zoom.
 * Vista general (z<=9): puntos más pequeños; intermedio: equilibrado;
 * cercano (z>=16): bien visibles y seleccionables.
 */
export function adaptiveRadiusFactor(zoom: number): number {
  if (zoom <= 9) return 0.6
  if (zoom <= 12) return 0.85
  if (zoom <= 15) return 1.2
  return 1.6
}

export function effectiveRadius(base: number, zoom: number, adaptive: boolean): number {
  return adaptive ? base * adaptiveRadiusFactor(zoom) : base
}

export function countByDestino(
  points: MapPoints,
): Record<string, number> {
  const result: Record<string, number> = {}
  for (const feature of points.features) {
    const key = feature.properties.destino_economico ?? 'Sin destino'
    result[key] = (result[key] ?? 0) + 1
  }
  return result
}
