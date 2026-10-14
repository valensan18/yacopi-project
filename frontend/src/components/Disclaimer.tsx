import styles from './Disclaimer.module.css'

interface DisclaimerProps {
  title?: string
  children: React.ReactNode
}

export default function Disclaimer({
  title = 'Aviso metodológico',
  children,
}: DisclaimerProps) {
  return (
    <aside className={styles.disclaimer}>
      <p className={`mono ${styles.title}`}>{title}</p>
      <div className={styles.body}>{children}</div>
    </aside>
  )
}
