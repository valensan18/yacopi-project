import styles from './Placeholder.module.css'

interface PlaceholderProps {
  title: string
  description: string
  eta: string
}

export default function Placeholder({ title, description, eta }: PlaceholderProps) {
  return (
    <section className={`container ${styles.page}`}>
      <p className="section-kicker">En construcción</p>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.description}>{description}</p>
      <p className={`mono ${styles.eta}`}>{eta}</p>
    </section>
  )
}
