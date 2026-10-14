import styles from './PageHeader.module.css'

interface PageHeaderProps {
  kicker: string
  title: string
  lede?: string
  children?: React.ReactNode
}

export default function PageHeader({ kicker, title, lede, children }: PageHeaderProps) {
  return (
    <header className={styles.header}>
      <p className="section-kicker">{kicker}</p>
      <h1 className={styles.title}>{title}</h1>
      {lede && <p className={styles.lede}>{lede}</p>}
      {children}
    </header>
  )
}
