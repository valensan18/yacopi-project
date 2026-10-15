import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { ParcelPage } from '../api/types'
import { formatArea } from '../lib/format'
import styles from './ParcelSelector.module.css'

interface ParcelSelectorProps {
  id: string
  value: string
  onChange: (publicId: string) => void
  placeholder?: string
}

/**
 * Buscador/selector de predios por identificador público (reutiliza el
 * catálogo vía el prefijo). Mantiene public_id opacos: nunca muestra
 * identificadores privados.
 */
export default function ParcelSelector({
  id,
  value,
  onChange,
  placeholder = 'Busca un predio por su identificador…',
}: ParcelSelectorProps) {
  const [query, setQuery] = useState(value)
  const [open, setOpen] = useState(false)
  const [highlight, setHighlight] = useState(-1)
  const debounceRef = useRef<number | null>(null)
  const [prefix, setPrefix] = useState('')

  useEffect(() => {
    if (debounceRef.current !== null) window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(() => {
      setPrefix(query.trim())
    }, 300)
    return () => {
      if (debounceRef.current !== null) window.clearTimeout(debounceRef.current)
    }
  }, [query])

  const results = useQuery<ParcelPage>({
    queryKey: ['parcel-selector', prefix],
    queryFn: () =>
      apiGet<ParcelPage>('/properties', {
        public_id_prefix: prefix,
        limit: 8,
        sort: 'public_id',
      }),
    enabled: prefix.length >= 2,
    staleTime: 60_000,
  })

  const options = results.data?.items ?? []

  function select(publicId: string) {
    onChange(publicId)
    setQuery(publicId)
    setOpen(false)
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (!open || options.length === 0) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlight((h) => Math.min(h + 1, options.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlight((h) => Math.max(h - 1, 0))
    } else if (event.key === 'Enter' && highlight >= 0) {
      event.preventDefault()
      select(options[highlight].public_id)
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className={styles.container}>
      <input
        id={id}
        className={styles.input}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={`${id}-listbox`}
        aria-autocomplete="list"
        autoComplete="off"
        placeholder={placeholder}
        value={query}
        maxLength={32}
        onChange={(e) => {
          setQuery(e.target.value)
          onChange(e.target.value)
          setOpen(true)
          setHighlight(-1)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        onKeyDown={onKeyDown}
      />
      {open && options.length > 0 && (
        <ul id={`${id}-listbox`} role="listbox" className={styles.listbox}>
          {options.map((parcel, index) => (
            <li
              key={parcel.public_id}
              role="option"
              aria-selected={parcel.public_id === value}
              className={`${styles.option} ${index === highlight ? styles.highlighted : ''}`}
              onMouseDown={(e) => {
                e.preventDefault()
                select(parcel.public_id)
              }}
            >
              <span className="mono">{parcel.public_id}</span>
              <span className={styles.meta}>
                {parcel.destino_economico ?? '—'} ·{' '}
                {formatArea(parcel.area_terreno_catastral_m2)}
              </span>
            </li>
          ))}
        </ul>
      )}
      {open && prefix.length >= 2 && results.isSuccess && options.length === 0 && (
        <p className={styles.empty}>No hay predios que coincidan con «{prefix}».</p>
      )}
    </div>
  )
}
