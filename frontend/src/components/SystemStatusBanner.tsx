import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { SystemStatus } from '../api/types'
import styles from './SystemStatusBanner.module.css'

const SHORT_TEXT = 'Modelo predictivo pendiente de validación'

function fullText(data: SystemStatus): string {
  const pending = !data.model_ready
  const base = pending
    ? 'Modelo predictivo pendiente de validación: el valor exclusivo del suelo (COP/ha) aún no está confirmado.'
    : 'Modelo validado disponible.'
  if (data.experimental_model?.habilitado) {
    return `${base} Inferencia experimental del proxy activa (solo desarrollo).`
  }
  return `${base} La predicción oficial permanece deshabilitada.`
}

export default function SystemStatusBanner() {
  const [expanded, setExpanded] = useState(false)
  const { data, isLoading, isError } = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system/status'),
    staleTime: 60_000,
  })

  if (isLoading) {
    return <div className={styles.banner} role="status">Consultando estado del sistema…</div>
  }
  if (isError || !data) {
    return (
      <div className={`${styles.banner} ${styles.error}`} role="status">
        No se pudo conectar con la API (¿está corriendo el backend en el puerto 8000?)
      </div>
    )
  }

  const pending = !data.model_ready
  const text = fullText(data)

  return (
    <div className={`${styles.banner} ${pending ? styles.pending : styles.ready}`} role="status">
      <span className={styles.dot} aria-hidden="true" />
      <span className={styles.summary}>
        <span className={styles.short}>{SHORT_TEXT}</span>
        <span className={styles.full}>{text}</span>
      </span>
      <button
        type="button"
        className={styles.detailsButton}
        aria-expanded={expanded}
        aria-controls="banner-detalles"
        onClick={() => setExpanded((open) => !open)}
      >
        {expanded ? 'Ocultar detalles' : 'Ver detalles'}
      </button>
      <span className={styles.badge}>{data.dataset_version ?? 'dataset sin versión'}</span>
      <span id="banner-detalles" className={`${styles.details} ${expanded ? styles.detailsOpen : ''}`}>
        {text}
      </span>
    </div>
  )
}
