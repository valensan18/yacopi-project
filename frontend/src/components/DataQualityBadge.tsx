import styles from './DataQualityBadge.module.css'

export function DataQualityBadge({ count }: { count: number }) {
  if (count === 0) {
    return (
      <span className={`${styles.badge} ${styles.ok}`} title="Sin alertas de calidad">
        Sin alertas
      </span>
    )
  }
  return (
    <span className={`${styles.badge} ${styles.warn}`} title={`${count} alertas de calidad`}>
      {count} {count === 1 ? 'alerta' : 'alertas'}
    </span>
  )
}
