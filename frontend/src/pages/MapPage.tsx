import 'leaflet/dist/leaflet.css'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import L from 'leaflet'
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { apiGet } from '../api/client'
import type { MapPoints } from '../api/types'
import { getBasemapConfig } from '../lib/basemap'
import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import { EmptyState, ErrorState, LoadingSkeleton } from '../components/states'
import styles from './MapPage.module.css'

const DESTINO_COLORS: Record<string, string> = {
  Agropecuario: '#2f6b52',
  Habitacional: '#e8b44f',
  Comercial: '#f4efe6',
  Religioso: '#c97b4a',
  Institucional: '#c97b4a',
  Educativo: '#c97b4a',
  Cultural: '#c97b4a',
}
const DEFAULT_COLOR = '#8fa39a'

const MUNICIPIO = { lat: 5.57, lon: -74.34, zoom: 11 }

function colorFor(destino: string | null): string {
  return DESTINO_COLORS[destino ?? ''] ?? DEFAULT_COLOR
}

function ParcelLayer({ points, onCount }: { points: MapPoints; onCount: (n: number) => void }) {
  const map = useMap()
  const layerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!layerRef.current) {
      layerRef.current = L.layerGroup().addTo(map)
    }
    const layer = layerRef.current
    layer.clearLayers()
    for (const feature of points.features) {
      const [lon, lat] = feature.geometry.coordinates
      const { public_id, destino_economico, subzona } = feature.properties
      const marker = L.circleMarker([lat, lon], {
        radius: 3.2,
        color: colorFor(destino_economico),
        weight: 0.6,
        fillColor: colorFor(destino_economico),
        fillOpacity: 0.85,
        renderer: canvasRenderer,
      })
      marker.bindPopup(
        `<div class="${styles.popup}">` +
          `<p class="mono">${public_id}</p>` +
          `<p>${destino_economico ?? 'Destino no disponible'}</p>` +
          `${subzona ? `<p class="mono">Subzona ${subzona}</p>` : ''}` +
          `<a href="/predios/${public_id}">Abrir ficha →</a>` +
          `</div>`,
      )
      layer.addLayer(marker)
    }
    onCount(points.features.length)
    return () => {
      layer.clearLayers()
    }
  }, [map, points, onCount])

  return null
}

const canvasRenderer = L.canvas({ padding: 0.5 })

function BboxController({ onBboxChange }: { onBboxChange: (b: L.LatLngBounds) => void }) {
  const map = useMapEvents({
    moveend() {
      onBboxChange(map.getBounds())
    },
  })
  return null
}

export default function MapPage() {
  const [bbox, setBbox] = useState<L.LatLngBounds | null>(null)
  const [visibleDestinos, setVisibleDestinos] = useState<Set<string> | null>(null)
  const [loadedCount, setLoadedCount] = useState(0)
  const pendingBbox = useRef<L.LatLngBounds | null>(null)

  const handleBboxChange = useCallback((bounds: L.LatLngBounds) => {
    pendingBbox.current = bounds
    // Micro-retardo para evitar peticiones durante el gesto continuo de zoom
    window.setTimeout(() => {
      const current = pendingBbox.current
      if (!current) return
      const west = current.getWest().toFixed(4)
      const east = current.getEast().toFixed(4)
      const south = current.getSouth().toFixed(4)
      const north = current.getNorth().toFixed(4)
      setBbox((prev) => {
        if (
          prev &&
          prev.getWest().toFixed(4) === west &&
          prev.getEast().toFixed(4) === east &&
          prev.getSouth().toFixed(4) === south &&
          prev.getNorth().toFixed(4) === north
        ) {
          return prev
        }
        return current
      })
    }, 350)
  }, [])

  const queryParams: Record<string, string | number> = bbox
    ? {
        min_lat: bbox.getSouth(),
        min_lon: bbox.getWest(),
        max_lat: bbox.getNorth(),
        max_lon: bbox.getEast(),
        limit: 8000,
      }
    : { limit: 8000 }

  const query = useQuery<MapPoints>({
    queryKey: ['map-bbox', bbox?.getSouth(), bbox?.getWest(), bbox?.getNorth(), bbox?.getEast()],
    queryFn: () => apiGet<MapPoints>('/maps/points', queryParams),
    staleTime: 5 * 60_000,
    placeholderData: (prev) => prev,
  })

  const counts = useMemo(() => {
    if (!query.data) return {}
    const result: Record<string, number> = {}
    for (const f of query.data.features) {
      const key = f.properties.destino_economico ?? 'Sin destino'
      result[key] = (result[key] ?? 0) + 1
    }
    return result
  }, [query.data])

  const filteredPoints = useMemo(() => {
    if (!query.data) return undefined
    if (!visibleDestinos) return query.data
    return {
      ...query.data,
      features: query.data.features.filter(
        (f) => visibleDestinos.has(f.properties.destino_economico ?? 'Sin destino'),
      ),
    }
  }, [query.data, visibleDestinos])

  const hasFilters = visibleDestinos && visibleDestinos.size !== Object.keys(counts).length

  return (
    <div className={styles.page}>
      <div className="container">
        <PageHeader
          kicker="Cartografía · ATLAS"
          title="Mapa"
          lede="Distribución real de los predios con coordenadas referenciales (fuente ZHF). Son puntos, no polígonos catastrales: esta visualización no representa límites prediales oficiales."
        />
      </div>

      <div className="container">
        <div className={styles.controls} aria-label="Filtros del mapa">
          {Object.entries(counts).length > 0 && (
            <fieldset className={styles.destinoFilter}>
              <legend>Destino económico (mostrar/ocultar)</legend>
              {Object.entries(counts)
                .sort((a, b) => b[1] - a[1])
                .map(([destino, n]) => {
                  const checked = !visibleDestinos || visibleDestinos.has(destino)
                  return (
                    <label key={destino} className={styles.destinoOption}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => {
                          setVisibleDestinos((prev) => {
                            const next = new Set(prev ?? Object.keys(counts))
                            if (next.has(destino)) next.delete(destino)
                            else next.add(destino)
                            return next
                          })
                        }}
                      />
                      <span
                        className={styles.swatch}
                        style={{ background: colorFor(destino === 'Sin destino' ? null : destino) }}
                        aria-hidden="true"
                      />
                      {destino} ({n.toLocaleString('es-CO')})
                    </label>
                  )
                })}
            </fieldset>
          )}
          <p className={`mono ${styles.countNote}`} aria-live="polite">
            {loadedCount.toLocaleString('es-CO')} puntos cargados en la vista actual
            {hasFilters ? ' · filtro de capas activo' : ''}
          </p>
        </div>
      </div>

      <div className={`container ${styles.mapWrap}`} data-lenis-prevent>
        {query.isError && (
          <ErrorState
            message="No se pudieron cargar los puntos desde la API. Verifica el backend y recarga."
            onRetry={() => query.refetch()}
          />
        )}
        {!query.isError && (
          <MapContainer
            center={[MUNICIPIO.lat, MUNICIPIO.lon]}
            zoom={MUNICIPIO.zoom}
            className={styles.map}
            preferCanvas
          >
            <TileLayer
              attribution={getBasemapConfig().attribution}
              url={getBasemapConfig().url}
            />
            <BboxController onBboxChange={handleBboxChange} />
            {query.isLoading && !query.data && null}
            {query.data && filteredPoints && (
              <ParcelLayer points={filteredPoints} onCount={setLoadedCount} />
            )}
          </MapContainer>
        )}
        {query.isLoading && !query.data && (
          <div className={styles.mapOverlay}>
            <LoadingSkeleton label="Cargando puntos del mapa…" />
          </div>
        )}
      </div>

      <div className="container">
        {query.isSuccess && query.data.features.length === 0 && (
          <EmptyState message="No hay puntos en esta zona del mapa." />
        )}
        <Disclaimer title="Naturaleza de los datos">
          <p>
            Puntos referenciales de los registros ZHF (TR_LATITUD/TR_LONGITUD). No se
            muestran polígonos prediales, elevaciones ni límites oficiales. El mapa usa
            teselas de CARTO/OpenStreetMap con su atribución correspondiente.
          </p>
          <p>
            El gesto de desplazamiento de la página no interfiere con el zoom ni con el
            arrastre del mapa.
          </p>
        </Disclaimer>
      </div>
    </div>
  )
}
