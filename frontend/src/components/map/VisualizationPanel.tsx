import {
  MAX_OPACITY,
  MAX_RADIUS,
  MIN_OPACITY,
  MIN_RADIUS,
} from '../../lib/map-utils'
import HelpTip from '../HelpTip'
import styles from './VisualizationPanel.module.css'

interface VisualizationPanelProps {
  opacity: number
  size: number
  adaptive: boolean
  onOpacityChange: (value: number) => void
  onSizeChange: (value: number) => void
  onAdaptiveChange: (value: boolean) => void
  onReset: () => void
  onFitBounds: () => void
  loadedCount: number
  visibleCount: number
  filterActive: boolean
  systemTotal: number | null
  systemWithCoords: number | null
  open: boolean
  onToggleOpen: () => void
}

export default function VisualizationPanel({
  opacity,
  size,
  adaptive,
  onOpacityChange,
  onSizeChange,
  onAdaptiveChange,
  onReset,
  onFitBounds,
  loadedCount,
  visibleCount,
  filterActive,
  systemTotal,
  systemWithCoords,
  open,
  onToggleOpen,
}: VisualizationPanelProps) {
  return (
    <section className={styles.panel} aria-label="Panel de visualización">
      <button
        type="button"
        className={styles.header}
        aria-expanded={open}
        aria-controls="viz-panel-body"
        onClick={onToggleOpen}
      >
        <span>Visualización</span>
        <span aria-hidden="true" className={styles.chevron}>{open ? '−' : '+'}</span>
      </button>

      {open && (
        <div id="viz-panel-body" className={styles.body}>
          <p className={styles.panelNote}>
            Cada punto del mapa es un predio con coordenadas referenciales de la
            fuente ZHF (no un polígono oficial). El color corresponde al destino
            económico registrado; las diferencias de color no representan
            diferencias de valor económico.{' '}
            <HelpTip label="Qué significan los puntos del mapa">
              Los puntos son ubicaciones referenciales de predios. El color indica
              el destino económico. Las capas y los filtros solo cambian la
              visualización: nunca alteran los datos de los predios.
            </HelpTip>
          </p>
          <div className={styles.control}>
            <label htmlFor="opacidad-puntos">
              Opacidad de los puntos
            </label>
            <div className={styles.sliderRow}>
              <input
                id="opacidad-puntos"
                type="range"
                min={Math.round(MIN_OPACITY * 100)}
                max={Math.round(MAX_OPACITY * 100)}
                step={5}
                value={Math.round(opacity * 100)}
                onChange={(e) => onOpacityChange(Number(e.target.value) / 100)}
              />
              <output className={styles.value} htmlFor="opacidad-puntos">
                {Math.round(opacity * 100)}&nbsp;%
              </output>
            </div>
          </div>

          <div className={styles.control}>
            <label htmlFor="tamano-puntos">Tamaño de los puntos</label>
            <div className={styles.sliderRow}>
              <input
                id="tamano-puntos"
                type="range"
                min={MIN_RADIUS}
                max={MAX_RADIUS}
                step={0.5}
                value={size}
                onChange={(e) => onSizeChange(Number(e.target.value))}
              />
              <output className={styles.value} htmlFor="tamano-puntos">
                {size.toLocaleString('es-CO')}&nbsp;px
              </output>
            </div>
          </div>

          <label className={styles.checkRow}>
            <input
              type="checkbox"
              checked={adaptive}
              onChange={(e) => onAdaptiveChange(e.target.checked)}
            />
            <span>Ajustar tamaño según zoom</span>
          </label>

          <div className={styles.actions}>
            <button type="button" onClick={onReset} className={styles.secondary}>
              Restablecer visualización
            </button>
            <button type="button" onClick={onFitBounds} className={styles.primary}>
              Ver todo el territorio
            </button>
          </div>

          <dl className={styles.summary}>
            {systemTotal != null && systemWithCoords != null && (
              <div>
                <dt>Sistema</dt>
                <dd>
                  {systemTotal.toLocaleString('es-CO')} predios ·{' '}
                  {systemWithCoords.toLocaleString('es-CO')} con coordenadas
                </dd>
              </div>
            )}
            <div>
              <dt>Vista actual</dt>
              <dd>{loadedCount.toLocaleString('es-CO')} registros cargados</dd>
            </div>
            {filterActive && (
              <div>
                <dt>Filtro de categorías</dt>
                <dd>{visibleCount.toLocaleString('es-CO')} puntos visibles</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </section>
  )
}
