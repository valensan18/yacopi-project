import { describe, expect, it } from 'vitest'

import type { MapPoints } from '../api/types'
import {
  adaptiveRadiusFactor,
  countByDestino,
  DEFAULT_OPACITY,
  DEFAULT_RADIUS,
  effectiveRadius,
  MAX_RADIUS,
  MIN_RADIUS,
} from '../lib/map-utils'

describe('adaptiveRadiusFactor', () => {
  it('reduce en vista general y amplía en zoom cercano', () => {
    expect(adaptiveRadiusFactor(8)).toBeLessThan(1)
    expect(adaptiveRadiusFactor(11)).toBeLessThan(1)
    expect(adaptiveRadiusFactor(14)).toBeGreaterThan(1)
    expect(adaptiveRadiusFactor(17)).toBeGreaterThan(adaptiveRadiusFactor(14))
  })
})

describe('effectiveRadius', () => {
  it('respeta el rango del slider y el ajuste manual', () => {
    expect(MIN_RADIUS).toBeGreaterThanOrEqual(1.5)
    expect(MAX_RADIUS).toBeLessThanOrEqual(7)
    const base = 4
    expect(effectiveRadius(base, 11, false)).toBe(base)
    expect(effectiveRadius(base, 11, true)).toBeCloseTo(base * 0.85)
    expect(effectiveRadius(base, 16, true)).toBeCloseTo(base * 1.6)
  })
})

describe('valores por defecto', () => {
  it('opacidad inicial 70 % y radio equilibrado', () => {
    expect(DEFAULT_OPACITY).toBe(0.7)
    expect(DEFAULT_RADIUS).toBeGreaterThanOrEqual(2)
    expect(DEFAULT_RADIUS).toBeLessThanOrEqual(4)
  })
})

describe('countByDestino', () => {
  it('cuenta solo sobre los registros cargados', () => {
    const points: MapPoints = {
      type: 'FeatureCollection',
      crs: { type: 'name', properties: { name: 'EPSG:4326' } },
      features: [
        { type: 'Feature', geometry: { type: 'Point', coordinates: [-74.3, 5.5] }, properties: { public_id: 'p_1', destino_economico: 'Agropecuario', subzona: '05' } },
        { type: 'Feature', geometry: { type: 'Point', coordinates: [-74.4, 5.6] }, properties: { public_id: 'p_2', destino_economico: 'Agropecuario', subzona: '14' } },
        { type: 'Feature', geometry: { type: 'Point', coordinates: [-74.5, 5.7] }, properties: { public_id: 'p_3', destino_economico: null, subzona: '08' } },
      ],
      aviso: 'aviso',
    }
    const counts = countByDestino(points)
    expect(counts['Agropecuario']).toBe(2)
    expect(counts['Sin destino']).toBe(1)
  })
})
