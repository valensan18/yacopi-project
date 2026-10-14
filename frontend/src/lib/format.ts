export const NO_DATA = 'No disponible'

const nf = new Intl.NumberFormat('es-CO')
const nf1 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 })
const nf2 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 })

export function formatInt(value: number): string {
  return nf.format(Math.round(value))
}

export function formatNumber(value: number, decimals = 1): string {
  return decimals === 1 ? nf1.format(value) : nf2.format(value)
}

/** m² → texto legible: "4,8 ha" si ≥ 1 ha, si no en m². */
export function formatArea(m2: number | null | undefined): string {
  if (m2 === null || m2 === undefined || !Number.isFinite(m2)) return NO_DATA
  if (m2 >= 10_000) return `${nf1.format(m2 / 10_000)} ha`
  return `${nf.format(m2)} m²`
}

export function formatCoordinates(
  lat: number | null | undefined,
  lon: number | null | undefined,
): string {
  if (lat == null || lon == null || !Number.isFinite(lat) || !Number.isFinite(lon)) {
    return NO_DATA
  }
  return `${nf2.format(lat)}, ${nf2.format(lon)}`
}

/** COP/ha con separador de miles. */
export function formatCopPerHa(value: number): string {
  return `${nf.format(Math.round(value))} COP/ha`
}

/** COP total con separador de miles. */
export function formatCop(value: number): string {
  return `${nf.format(Math.round(value))} COP`
}
