import { useMemo, useState } from 'react'
import PageHeader from '../components/PageHeader'
import { CATEGORY_LABELS, GLOSSARY } from '../lib/glossary'
import styles from './Glossary.module.css'

export default function Glossary() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string>('todas')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return GLOSSARY.filter((entry) => {
      if (category !== 'todas' && entry.categoria !== category) return false
      if (!q) return true
      return (
        entry.termino.toLowerCase().includes(q) ||
        entry.definicion.toLowerCase().includes(q)
      )
    })
  }, [query, category])

  return (
    <div className="container">
      <PageHeader
        kicker="Glosario"
        title="Términos en lenguaje sencillo"
        lede="Consulta el significado de los conceptos que aparecen en Atlas Vivo. Donde la fuente no documenta un significado, se indica expresamente: no se inventan definiciones."
      />

      <div className={styles.controls} role="search">
        <label className={styles.searchLabel} htmlFor="glosario-busqueda">
          Buscar término
        </label>
        <input
          id="glosario-busqueda"
          className={styles.search}
          type="search"
          placeholder="Ej.: avalúo, MAE, ZHG…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className={styles.categories} role="group" aria-label="Filtrar por categoría">
          {['todas', 'catastro', 'ml', 'calidad'].map((value) => (
            <button
              key={value}
              type="button"
              className={`${styles.categoryButton} ${category === value ? styles.categoryActive : ''}`}
              aria-pressed={category === value}
              onClick={() => setCategory(value)}
            >
              {value === 'todas' ? 'Todas' : CATEGORY_LABELS[value as 'catastro' | 'ml' | 'calidad']}
            </button>
          ))}
        </div>
      </div>

      <p className={`mono ${styles.count}`} aria-live="polite">
        {filtered.length} término{filtered.length === 1 ? '' : 's'}
      </p>

      <dl className={styles.list}>
        {filtered.map((entry) => (
          <div key={entry.termino} className={styles.entry}>
            <dt className={styles.term}>
              {entry.termino}
              <span className={styles.categoryTag}>
                {CATEGORY_LABELS[entry.categoria]}
              </span>
            </dt>
            <dd className={styles.definition}>{entry.definicion}</dd>
            {entry.interpretacion && (
              <dd className={styles.interpretation}>
                <strong>Cómo interpretarlo:</strong> {entry.interpretacion}
              </dd>
            )}
            {entry.limitaciones && (
              <dd className={styles.limitation}>
                <strong>Limitaciones:</strong> {entry.limitaciones}
              </dd>
            )}
          </div>
        ))}
      </dl>

      {filtered.length === 0 && (
        <p className={styles.empty}>
          No hay términos que coincidan con «{query}».
        </p>
      )}
    </div>
  )
}
