import { useCallback, useEffect, useRef } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'
import type { MapPoints } from '../../api/types'
import { effectiveRadius } from '../../lib/map-utils'
import { colorFor } from '../../lib/map-colors'

export interface LayerOptions {
  opacity: number
  radius: number
  adaptive: boolean
}

export interface LayerApi {
  applyOptions: () => void
}

interface ParcelLayerProps {
  points: MapPoints
  optionsRef: React.MutableRefObject<LayerOptions>
  apiRef: React.MutableRefObject<LayerApi | null>
  onCount: (n: number) => void
}

const canvasRenderer = L.canvas({ padding: 0.5 })

/**
 * Capa de puntos imperativa sobre renderer canvas.
 *
 * - Los marcadores se reconstruyen SOLO cuando cambia `points` (bbox/filtro).
 * - Opacidad/tamaño se aplican en vivo con setStyle (sin reconstruir
 *   geometrías ni volver a consultar la API), con rAF para no saturar.
 * - El tamaño adaptativo escucha zoomend; al desmontar se limpian capa y
 *   listeners (sin fugas).
 */
export default function ParcelLayer({ points, optionsRef, apiRef, onCount }: ParcelLayerProps) {
  const map = useMap()
  const layerRef = useRef<L.LayerGroup | null>(null)
  const rafRef = useRef<number | null>(null)

  const applyOptions = useCallback(() => {
    if (rafRef.current !== null) return
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null
      const layer = layerRef.current
      if (!layer) return
      const { opacity, radius, adaptive } = optionsRef.current
      const effective = effectiveRadius(radius, map.getZoom(), adaptive)
      layer.eachLayer((item) => {
        if (item instanceof L.CircleMarker) {
          item.setStyle({
            radius: effective,
            fillOpacity: opacity,
            opacity: Math.min(opacity + 0.25, 1),
          })
        }
      })
    })
  }, [map, optionsRef])

  useEffect(() => {
    apiRef.current = { applyOptions }
    return () => {
      apiRef.current = null
    }
  }, [apiRef, applyOptions])

  useEffect(() => {
    if (!layerRef.current) {
      layerRef.current = L.layerGroup().addTo(map)
    }
    const layer = layerRef.current
    layer.clearLayers()

    const { opacity, radius, adaptive } = optionsRef.current
    const effective = effectiveRadius(radius, map.getZoom(), adaptive)

    for (const feature of points.features) {
      const [lon, lat] = feature.geometry.coordinates
      const { public_id, destino_economico, subzona } = feature.properties
      const color = colorFor(destino_economico)
      const marker = L.circleMarker([lat, lon], {
        radius: effective,
        color,
        weight: 0.6,
        fillColor: color,
        fillOpacity: opacity,
        opacity: Math.min(opacity + 0.25, 1),
        renderer: canvasRenderer,
      })
      marker.bindPopup(
        '<div class="map-popup">' +
          `<p class="map-popup-id">${public_id}</p>` +
          `<p>${destino_economico ?? 'Destino no disponible'}</p>` +
          `${subzona ? `<p class="map-popup-sub">Subzona ${subzona}</p>` : ''}` +
          `<a href="/predios/${public_id}">Abrir ficha →</a>` +
          '</div>',
      )
      layer.addLayer(marker)
    }
    onCount(points.features.length)
  }, [map, points, optionsRef, onCount])

  useEffect(() => {
    const onZoom = () => {
      if (optionsRef.current.adaptive) applyOptions()
    }
    map.on('zoomend', onZoom)
    return () => {
      map.off('zoomend', onZoom)
      layerRef.current?.remove()
      layerRef.current = null
    }
  }, [map, optionsRef, applyOptions])

  return null
}
