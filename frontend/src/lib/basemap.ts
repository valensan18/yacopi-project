/**
 * Configuración del mapa base de ATLAS VIVO.
 *
 * CARTO Basemaps Dark Matter es el mapa base principal cuando existe la clave
 * en `VITE_CARTO_BASEMAPS_KEY` (frontend/.env.local, NO versionado).
 *
 * AVISO DE SEGURIDAD: las variables VITE_* se incrustan en el bundle y son
 * visibles en el navegador; la clave de CARTO no es un secreto protegido.
 * Se recomienda configurar restricciones de dominio (allowlist) desde el
 * panel de CARTO Basemaps.
 *
 * Si no hay clave, se usa OpenStreetMap estándar como respaldo (sin teselas
 * de CARTO con marcas de agua).
 */

export interface BasemapConfig {
  url: string
  attribution: string
  provider: 'carto-dark' | 'osm'
}

const ENV_KEY = ((import.meta.env.VITE_CARTO_BASEMAPS_KEY as string | undefined) ?? '').trim()

export function getBasemapConfig(key?: string): BasemapConfig {
  const cartoKey = (key ?? ENV_KEY).trim()
  if (cartoKey) {
    return {
      url:
        'https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png?key=' +
        encodeURIComponent(cartoKey),
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      provider: 'carto-dark',
    }
  }
  return {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    provider: 'osm',
  }
}
