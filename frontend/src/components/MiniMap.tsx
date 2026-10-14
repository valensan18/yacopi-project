import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'
import styles from './MiniMap.module.css'

interface MiniMapProps {
  lat: number
  lon: number
  label: string
}

export default function MiniMap({ lat, lon, label }: MiniMapProps) {
  return (
    <div className={styles.mapBox} data-lenis-prevent>
      <MapContainer
        center={[lat, lon]}
        zoom={14}
        scrollWheelZoom={false}
        style={{ height: '100%', width: '100%', background: '#0b1613' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <CircleMarker
          center={[lat, lon]}
          radius={8}
          pathOptions={{ color: '#c97b4a', weight: 2, fillColor: '#c97b4a', fillOpacity: 0.9 }}
        >
          <Tooltip>{label}</Tooltip>
        </CircleMarker>
      </MapContainer>
    </div>
  )
}
