import styles from './Scene3DFallback.module.css'

export default function Scene3DFallback({ pointCount }: { pointCount: number }) {
  return (
    <div className={styles.fallback} aria-hidden="true">
      <div className={styles.contours} />
      <div className={styles.dots} />
      <span className={styles.label}>
        Vista 2D de respaldo · {pointCount.toLocaleString('es-CO')} puntos de predios
        (WebGL no disponible en este dispositivo)
      </span>
    </div>
  )
}
