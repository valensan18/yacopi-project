import { describe, expect, it } from 'vitest'

import { getBasemapConfig } from '../lib/basemap'

describe('getBasemapConfig (mapa base ATLAS VIVO)', () => {
  it('usa CARTO Dark Matter con clave codificada correctamente', () => {
    const cfg = getBasemapConfig('clave de prueba/xyz!')
    expect(cfg.provider).toBe('carto-dark')
    expect(cfg.url).toBe(
      'https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=' +
        encodeURIComponent('clave de prueba/xyz!'),
    )
    expect(cfg.url).not.toContain('clave de prueba/xyz!')
    expect(cfg.attribution).toContain('CARTO')
    expect(cfg.attribution).toContain('OpenStreetMap')
  })

  it('usa OpenStreetMap estándar como respaldo sin clave', () => {
    const cfg = getBasemapConfig('')
    expect(cfg.provider).toBe('osm')
    expect(cfg.url).toBe('https://tile.openstreetmap.org/{z}/{x}/{y}.png')
    expect(cfg.attribution).not.toContain('CARTO')
    expect(cfg.attribution).toContain('OpenStreetMap')
  })
})
