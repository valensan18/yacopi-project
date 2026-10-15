import styles from './InterpretationCard.module.css'

interface InterpretationCardProps {
  title?: string
  children: React.ReactNode
  variant?: 'default' | 'warning'
}

/**
 * Bloque "¿Qué significa esto para este predio?" — explicación contextual
 * breve construida con los datos reales de la pantalla (nunca genérica).
 */
export default function InterpretationCard({
  title = '¿Qué significa esto para este predio?',
  children,
  variant = 'default',
}: InterpretationCardProps) {
  return (
    <aside className={`${styles.card} ${styles[variant]}`}>
      <p className={`mono ${styles.title}`}>{title}</p>
      <div className={styles.body}>{children}</div>
    </aside>
  )
}
