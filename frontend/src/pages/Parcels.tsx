import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiGet, ApiError } from '../api/client'
import type { OverviewStats, ParcelPage } from '../api/types'
import PageHeader from '../components/PageHeader'
import { DataQualityBadge } from '../components/DataQualityBadge'
import HelpTip from '../components/HelpTip'
import { EmptyState, ErrorState, LoadingSkeleton } from '../components/states'
import { formatArea, formatCoordinates, formatInt } from '../lib/format'
import styles from './Parcels.module.css'

const LIMITS = [20, 50, 100]
const SORTS = [
  { value: 'public_id', label: 'Identificador' },
  { value: 'destino_economico', label: 'Destino económico' },
  { value: 'area', label: 'Área' },
  { value: 'subzona', label: 'Subzona' },
  { value: 'latitud', label: 'Latitud' },
  { value: 'longitud', label: 'Longitud' },
]

export default function Parcels() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchInput, setSearchInput] = useState('')

  const destino = searchParams.get('destino') ?? ''
  const subzona = searchParams.get('subzona') ?? ''
  const minArea = searchParams.get('min_area_m2') ?? ''
  const maxArea = searchParams.get('max_area_m2') ?? ''
  const sort = searchParams.get('sort') ?? 'public_id'
  const sortDesc = searchParams.get('sort_desc') === '1'
  const limit = Number(searchParams.get('limit') ?? 20)
  const offset = Number(searchParams.get('offset') ?? 0)

  const { data: overview } = useQuery<OverviewStats>({
    queryKey: ['overview'],
    queryFn: () => apiGet<OverviewStats>('/statistics/overview'),
    staleTime: 5 * 60_000,
  })

  const query = useQuery<ParcelPage>({
    queryKey: ['parcels-estimables', destino, subzona, minArea, maxArea, sort, sortDesc, limit, offset],
    queryFn: () =>
      apiGet<ParcelPage>('/properties', {
        destino, subzona,
        min_area_m2: minArea, max_area_m2: maxArea,
        sort, sort_desc: sortDesc ? '1' : '0',
        limit, offset,
        solo_estimables: '1',
      }),
  })

  function updateParam(patch: Record<string, string | number | null>) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === '' || value === 0 || value === '0') {
        next.delete(key)
      } else {
        next.set(key, String(value))
      }
    }
    setSearchParams(next, { replace: false })
  }

  function goToPage(newOffset: number) {
    const clamped = Math.max(0, newOffset)
    updateParam({ offset: clamped })
  }

  function submitSearch(event: React.FormEvent) {
    event.preventDefault()
    const id = searchInput.trim()
    if (id) navigate(`/predios/${encodeURIComponent(id)}`)
  }

  const total = query.data?.pagination.total
  const pages = total && limit ? Math.max(1, Math.ceil(total / limit)) : null
  const currentPage = limit ? Math.floor(offset / limit) + 1 : 1

  const esIndisponibilidad =
    query.isError &&
    query.error instanceof ApiError &&
    (query.error.code === 'VALOR_V1_DISABLED' || query.error.code === 'VALOR_V1_UNAVAILABLE')

  return (
    <div className="container">
      <PageHeader
        kicker="Catálogo · Estimación RF v1"
        title="Predios con estimación disponible"
        lede="Este listado muestra únicamente los predios compatibles con el modelo académico Random Forest v1 (sin construcción registrada y dentro del dominio observado). La base consolidada de 7.709 predios permanece intacta: este catálogo no borra ni modifica registros."
      />

      <p className={styles.disclaimer}>
        Las estimaciones son académicas y orientativas; no constituyen avalúos
        oficiales ni comerciales.
      </p>

      <form className={styles.searchForm} onSubmit={submitSearch} role="search">
        <label className={styles.searchLabel} htmlFor="buscar-predio">
          Buscar por identificador público{' '}
          <HelpTip label="Qué es el identificador público">
            Es un código interno del catálogo (como «p_ab12…») que identifica el
            predio sin revelar matrículas ni datos personales. Escribe uno
            completo para abrir su ficha.
          </HelpTip>
        </label>
        <div className={styles.searchRow}>
          <input
            id="buscar-predio"
            className={styles.searchInput}
            type="text"
            placeholder="p_ab12cd34ef567890"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            maxLength={32}
          />
          <button type="submit" className={styles.searchButton}>
            Ir al detalle
          </button>
        </div>
        <p className={styles.searchHint}>
          La búsqueda abre la ficha exacta del identificador indicado (la búsqueda parcial
          por texto requiere una ampliación futura del endpoint).
        </p>
      </form>

      <div className={styles.filters} aria-label="Filtros del catálogo">
        <label className={styles.field}>
          <span>Destino económico</span>
          <select
            value={destino}
            onChange={(e) => updateParam({ destino: e.target.value, offset: 0 })}
          >
            <option value="">Todos</option>
            {overview?.por_destino_economico.map((d) => (
              <option key={d.key} value={d.key}>{d.key} ({formatInt(d.n)})</option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>Subzona</span>
          <select
            value={subzona}
            onChange={(e) => updateParam({ subzona: e.target.value, offset: 0 })}
          >
            <option value="">Todas</option>
            {overview?.por_subzona.map((s) => (
              <option key={s.key} value={s.key}>Subzona {s.key} ({formatInt(s.n)})</option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>Área mínima (m²)</span>
          <input
            type="number"
            min={0}
            value={minArea}
            onChange={(e) => updateParam({ min_area_m2: e.target.value, offset: 0 })}
            placeholder="0"
          />
        </label>

        <label className={styles.field}>
          <span>Área máxima (m²)</span>
          <input
            type="number"
            min={0}
            value={maxArea}
            onChange={(e) => updateParam({ max_area_m2: e.target.value, offset: 0 })}
            placeholder="Sin límite"
          />
        </label>

        <label className={styles.field}>
          <span>Ordenar por</span>
          <select
            value={sort}
            onChange={(e) => updateParam({ sort: e.target.value, offset: 0 })}
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>Dirección</span>
          <select
            value={sortDesc ? 'desc' : 'asc'}
            onChange={(e) => updateParam({ sort_desc: e.target.value === 'desc' ? '1' : '0', offset: 0 })}
          >
            <option value="asc">Ascendente</option>
            <option value="desc">Descendente</option>
          </select>
        </label>
      </div>

      {query.isLoading && <LoadingSkeleton label="Consultando predios…" />}

      {esIndisponibilidad && (
        <div className={styles.unavailableCard} role="status">
          <p className={`mono ${styles.unavailableCode}`}>
            {query.error instanceof ApiError ? query.error.code : 'NO DISPONIBLE'}
          </p>
          <p>
            La estimación RF v1 no está habilitada o su artefacto no está
            disponible en este entorno: no se puede mostrar el listado de
            predios compatibles en este momento.
          </p>
        </div>
      )}

      {query.isError && !esIndisponibilidad && (
        <ErrorState
          message="Verifica que el backend esté activo en el puerto 8000 e inténtalo de nuevo."
          onRetry={() => query.refetch()}
        />
      )}

      {query.isSuccess && query.data.items.length === 0 && (
        <EmptyState message="Ningún predio coincide con los filtros seleccionados." />
      )}

      {query.isSuccess && query.data.items.length > 0 && (
        <>
          <div className={styles.resultBar} aria-live="polite">
            <span className="mono">
              {formatInt(offset + 1)}–{formatInt(offset + query.data.items.length)} de{' '}
              {formatInt(total ?? 0)} predios
            </span>
            <span className="mono">dataset {query.data.dataset_version}</span>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <caption className={styles.caption}>
                Predios compatibles con la estimación RF v1 — resultados reales
                paginados de la API
              </caption>
              <thead>
                <tr>
                  <th scope="col">Identificador público</th>
                  <th scope="col">Destino</th>
                  <th scope="col" className={styles.num}>Área terreno</th>
                  <th scope="col" className={styles.num}>Construcción</th>
                  <th scope="col">Subzona</th>
                  <th scope="col">Coordenadas</th>
                  <th scope="col">
                    Calidad{' '}
                    <HelpTip label="Qué significa la columna de calidad">
                      Indica si el predio tiene alertas por inconsistencias o
                      faltantes en las fuentes. «Sin alertas» no significa que
                      los datos estén certificados; «N alertas» invita a revisar
                      la ficha antes de sacar conclusiones.
                    </HelpTip>
                  </th>
                  <th scope="col"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((parcel) => (
                  <tr key={parcel.public_id}>
                    <td className="mono">{parcel.public_id}</td>
                    <td>{parcel.destino_economico ?? '—'}</td>
                    <td className={`${styles.num} mono`}>
                      {formatArea(parcel.area_terreno_catastral_m2)}
                    </td>
                    <td className={`${styles.num} mono`}>
                      {parcel.area_construida_m2 != null && parcel.area_construida_m2 > 0
                        ? formatArea(parcel.area_construida_m2)
                        : '—'}
                    </td>
                    <td className="mono">
                      {parcel.subzona ? `Subzona ${parcel.subzona}` : '—'}
                    </td>
                    <td className="mono">
                      {formatCoordinates(parcel.latitud, parcel.longitud)}
                    </td>
                    <td>
                      <DataQualityBadge count={parcel.n_alertas_calidad} />
                    </td>
                    <td>
                      <Link
                        className={styles.rowLink}
                        to={`/prediccion?public_id=${parcel.public_id}`}
                        aria-label={`Consultar estimación del predio ${parcel.public_id}`}
                      >
                        Estimar →
                      </Link>{' '}
                      <Link
                        className={styles.rowLink}
                        to={`/predios/${parcel.public_id}`}
                        aria-label={`Ver ficha del predio ${parcel.public_id}`}
                      >
                        Ficha →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <nav className={styles.pagination} aria-label="Paginación de predios">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => goToPage(offset - limit)}
            >
              ← Anterior
            </button>
            <span className="mono" aria-live="polite">
              Página {formatInt(currentPage)} de {formatInt(pages ?? 1)}
            </span>
            <button
              type="button"
              disabled={offset + limit >= (total ?? 0)}
              onClick={() => goToPage(offset + limit)}
            >
              Siguiente →
            </button>
            <label className={styles.limitField}>
              <span>Por página</span>
              <select
                value={limit}
                onChange={(e) => updateParam({ limit: Number(e.target.value), offset: 0 })}
              >
                {LIMITS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </label>
          </nav>
        </>
      )}
    </div>
  )
}
