/** Colores de categorías del mapa (misma paleta que la escena 3D). */

export const DESTINO_COLORS: Record<string, string> = {
  Agropecuario: '#2f6b52',
  Habitacional: '#e8b44f',
  Comercial: '#f4efe6',
  Religioso: '#c97b4a',
  Institucional: '#c97b4a',
  Educativo: '#c97b4a',
  Cultural: '#c97b4a',
}

export const DEFAULT_COLOR = '#8fa39a'

export function colorFor(destino: string | null | undefined): string {
  return DESTINO_COLORS[destino ?? ''] ?? DEFAULT_COLOR
}
