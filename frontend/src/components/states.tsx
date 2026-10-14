import styles from './states.module.css'

export function LoadingSkeleton({ label = 'Cargando datos reales…' }: { label?: string }) {
  return (
    <div className={styles.skeleton} role="status" aria-live="polite">
      <span className={styles.skeletonBar} />
      <span className={styles.skeletonBar} />
      <span className={styles.skeletonBarShort} />
      <p className={styles.skeletonText}>{label}</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className={styles.error} role="alert">
      <p className={styles.errorTitle}>No se pudo cargar la información</p>
      <p className={styles.errorText}>{message}</p>
      {onRetry && (
        <button type="button" className={styles.retry} onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className={styles.empty} role="status">
      <p>{message}</p>
    </div>
  )
}
