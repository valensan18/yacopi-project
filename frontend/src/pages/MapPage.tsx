import 'leaflet/dist/leaflet.css'
import { useCallback, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import L from 'leaflet'
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet'
import { apiGet } from '../api/client'
import type { MapPoints, OverviewStats } from '../api/types'
import { getBasemapConfig } from '../lib/basemap'
import {
  DEFAULT_OPACITY,
  DEFAULT_RADIUS,
  countByDestino,
} from '../lib/map-utils'
import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import { EmptyState, ErrorState, LoadingSkeleton } from '../components/states'
import ParcelLayer from '../components/map/ParcelLayer'
import type { LayerApi, LayerOptions } from '../components/map/ParcelLayer'
import MapLegend from '../components/map/MapLegend'
import VisualizationPanel from '../components/map/VisualizationPanel'
import styles from './MapPage.module.css'

const MUNICIPIO = { lat: 5.57, lon: -74.34, zoom: 11 }

function BboxTracker({ onBboxChange }: { onBboxChange: (b: L.LatLngBounds) => void }) {
  const map = useMapEvents({
    moveend() {
      onBboxChange(map.getBounds())
    },
  })
  return null
}

export default function MapPage() {
  const mapRef = useRef<L.Map | null>(null)
  const [bbox, setBbox] = useState<L.LatLngBounds | null>(null)
  const [visibleDestinos, setVisibleDestinos] = useState<Set<string> | null>(null)
  const [loadedCount, setLoadedCount] = useState(0)
  const [opacity, setOpacity] = useState(DEFAULT_OPACITY)
  const [size, setSize] = useState(DEFAULT_RADIUS)
  const [adaptive, setAdaptive] = useState(true)
  const [legendOpen, setLegendOpen] = useState(true)
  const [vizOpen, setVizOpen] = useState(true)

  const optionsRef = useRef<LayerOptions>({
    opacity: DEFAULT_OPACITY,
    radius: DEFAULT_RADIUS,
    adaptive: true,
  })
  const layerApiRef = useRef<LayerApi | null>(null)
  const pendingBbox = useRef<L.LatLngBounds | null>(null)

  const handleBboxChange = useCallback((bounds: L.LatLngBounds) => {
    pendingBbox.current = bounds
    window.setTimeout(() => {
      const current = pendingBbox.current
      if (!current) return
      setBbox((prev) => {
        if (
          prev &&
          prev.getWest().toFixed(4) === current.getWest().toFixed(4) &&
          prev.getEast().toFixed(4) === current.getEast().toFixed(4) &&
          prev.getSouth().toFixed(4) === current.getSouth().toFixed(4) &&
          prev.getNorth().toFixed(4) === current.getNorth().toFixed(4)
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

  const overview = useQuery<OverviewStats>({
    queryKey: ['overview'],
    queryFn: () => apiGet<OverviewStats>('/statistics/overview'),
    staleTime: 5 * 60_000,
  })

  const counts = useMemo(() => (query.data ? countByDestino(query.data) : {}), [query.data])

  const filteredPoints = useMemo(() => {
    if (!query.data) return undefined
    if (!visibleDestinos) return query.data
    return {
      ...query.data,
      features: query.data.features.filter((f) =>
        visibleDestinos.has(f.properties.destino_economico ?? 'Sin destino'),
      ),
    }
  }, [query.data, visibleDestinos])

  const filterActive = visibleDestinos !== null
  const visibleCount = filteredPoints?.features.length ?? 0

  function applyOptions(next: Partial<LayerOptions>) {
    Object.assign(optionsRef.current, next)
    layerApiRef.current?.applyOptions()
  }

  function handleOpacity(value: number) {
    setOpacity(value)
    applyOptions({ opacity: value })
  }

  function handleSize(value: number) {
    setSize(value)
    applyOptions({ radius: value })
  }

  function handleAdaptive(value: boolean) {
    setAdaptive(value)
    applyOptions({ adaptive: value })
  }

  function handleReset() {
    setOpacity(DEFAULT_OPACITY)
    setSize(DEFAULT_RADIUS)
    setAdaptive(true)
    applyOptions({ opacity: DEFAULT_OPACITY, radius: DEFAULT_RADIUS, adaptive: true })
  }

  function handleFitBounds() {
    const map = mapRef.current
    if (!map) return
    const features = query.data?.features ?? []
    if (features.length === 0) {
      map.setView([MUNICIPIO.lat, MUNICIPIO.lon], MUNICIPIO.zoom)
      return
    }
    const bounds = L.latLngBounds(
      features.map((f) => [f.geometry.coordinates[1], f.geometry.coordinates[0]] as [number, number]),
    )
    map.fitBounds(bounds, { padding: [24, 24] })
  }

  function toggleDestino(destino: string) {
    setVisibleDestinos((prev) => {
      const next = new Set(prev ?? Object.keys(counts))
      if (next.has(destino)) next.delete(destino)
      else next.add(destino)
      return next
    })
  }

  const basemap = getBasemapConfig()

  return (
    <div className={styles.page}>
      <div className="container">
        <PageHeader
          kicker="Cartografía · ATLAS"
          title="Mapa"
          lede="Distribución real de los predios con coordenadas referenciales (fuente ZHF). Son puntos, no polígonos catastrales: esta visualización no representa límites prediales oficiales."
        />
      </div>

      <div className={`container ${styles.mapArea}`} data-lenis-prevent data-testid="map-container">
        <div className={styles.panels}>
          <VisualizationPanel
            opacity={opacity}
            size={size}
            adaptive={adaptive}
            onOpacityChange={handleOpacity}
            onSizeChange={handleSize}
            onAdaptiveChange={handleAdaptive}
            onReset={handleReset}
            onFitBounds={handleFitBounds}
            loadedCount={loadedCount}
            visibleCount={visibleCount}
            filterActive={filterActive}
            systemTotal={overview.data?.total_predios ?? null}
            systemWithCoords={overview.data?.predios_con_coordenadas ?? null}
            open={vizOpen}
            onToggleOpen={() => setVizOpen((open) => !open)}
          />
          <MapLegend
            counts={counts}
            visibleDestinos={visibleDestinos}
            onToggle={toggleDestino}
            onShowAll={() => setVisibleDestinos(null)}
            onHideAll={() => setVisibleDestinos(new Set())}
            open={legendOpen}
            onToggleOpen={() => setLegendOpen((open) => !open)}
          />
        </div>

        {query.isError && (
          <ErrorState
            message="No se pudieron cargar los puntos desde la API. Verifica el backend y recarga."
            onRetry={() => query.refetch()}
          />
        )}

        {!query.isError && (
          <MapContainer
            ref={mapRef}
            center={[MUNICIPIO.lat, MUNICIPIO.lon]}
            zoom={MUNICIPIO.zoom}
            className={styles.map}
            preferCanvas
          >
            <TileLayer attribution={basemap.attribution} url={basemap.url} />
            <BboxTracker onBboxChange={handleBboxChange} />
            {query.data && filteredPoints && (
              <ParcelLayer
                points={filteredPoints}
                optionsRef={optionsRef}
                apiRef={layerApiRef}
                onCount={setLoadedCount}
              />
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
