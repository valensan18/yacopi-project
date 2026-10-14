import { colorFor } from '../../lib/map-colors'
import styles from './MapLegend.module.css'

interface MapLegendProps {
  counts: Record<string, number>
  visibleDestinos: Set<string> | null
  onToggle: (destino: string) => void
  onShowAll: () => void
  onHideAll: () => void
  open: boolean
  onToggleOpen: () => void
}

export default function MapLegend({
  counts,
  visibleDestinos,
  onToggle,
  onShowAll,
  onHideAll,
  open,
  onToggleOpen,
}: MapLegendProps) {
  const categories = Object.entries(counts).sort((a, b) => b[1] - a[1])
  const allVisible = !visibleDestinos
  const activeCount = allVisible
    ? categories.length
    : categories.filter(([key]) => visibleDestinos.has(key)).length

  return (
    <section className={styles.panel} aria-label="Leyenda del mapa">
      <button
        type="button"
        className={styles.header}
        aria-expanded={open}
        aria-controls="map-legend-body"
        onClick={onToggleOpen}
      >
        <span>
          Categorías <span className={styles.headerMeta}>· {activeCount}/{categories.length} activas</span>
        </span>
        <span aria-hidden="true" className={styles.chevron}>{open ? '−' : '+'}</span>
      </button>

      {open && (
        <div id="map-legend-body" className={styles.body}>
          <p className={styles.note}>
            Conteos sobre los registros cargados en la vista actual.
          </p>
          <div className={styles.actions}>
            <button type="button" onClick={onShowAll}>Mostrar todas</button>
            <button type="button" onClick={onHideAll}>Ocultar todas</button>
          </div>
          {categories.length === 0 && (
            <p className={styles.note}>Sin categorías en la vista actual.</p>
          )}
          {categories.map(([destino, count]) => {
            const checked = allVisible || visibleDestinos.has(destino)
            return (
              <label key={destino} className={styles.row}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggle(destino)}
                />
                <span
                  className={styles.swatch}
                  style={{ background: colorFor(destino === 'Sin destino' ? null : destino) }}
                  aria-hidden="true"
                />
                <span className={styles.label}>{destino}</span>
                <span className={styles.count}>{count.toLocaleString('es-CO')}</span>
              </label>
            )
          })}
        </div>
      )}
    </section>
  )
}
