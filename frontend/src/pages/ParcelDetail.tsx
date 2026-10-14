import { lazy, Suspense } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { ParcelDetailItem, ParcelDetailResponse } from '../api/types'
import PageHeader from '../components/PageHeader'
import { DataQualityBadge } from '../components/DataQualityBadge'
import Disclaimer from '../components/Disclaimer'
import { EmptyState, ErrorState, LoadingSkeleton } from '../components/states'
import { formatArea, formatCoordinates, NO_DATA } from '../lib/format'
import styles from './ParcelDetail.module.css'

const MiniMap = lazy(() => import('../components/MiniMap'))

const FLAG_LABELS: Record<string, string> = {
  sin_coincidencia_zhf: 'Sin coincidencia con la fuente ZHF',
  multiples_intersecciones_zhg: 'Varias intersecciones geoeconómicas',
  interseccion_filas_exactamente_duplicadas: 'Filas de intersección duplicadas',
  porcentajes_zhg_no_suman_100: 'Porcentajes de zona no suman 100 %',
  suma_area_intersecciones_difiere_mas_5pct_area_catastral:
    'Suma de intersecciones difiere >5 % del área catastral',
  area_zhf_difiere_mas_5pct_area_catastral:
    'Área ZHF difiere >5 % del área catastral',
  area_geometrica_zhg_difiere_mas_5pct_zhf:
    'Área geométrica difiere >5 % entre fuentes',
  zona_zhg_zhf_diferente_de_zhg_dominante:
    'Zona geoeconómica discordante entre fuentes',
  zhf_codpred_repetido: 'Identificador repetido en la fuente ZHF',
  area_catastral_no_positiva: 'Área catastral no positiva',
  contiene_construccion: 'Registra superficie construida',
}

const FEATURE_LABELS: [string, string][] = [
  ['zhf_codigo', 'Código ZHF'],
  ['zhf_dispon', 'Disponibilidad ZHF'],
  ['zhf_influe', 'Influencia ZHF'],
  ['zhf_uso_ac', 'Uso actual ZHF'],
  ['aht_vpoten', 'Aptitud potencial (AHT)'],
  ['fa_element', 'Elemento (frontera agrícola)'],
  ['vus_vocaci', 'Vocación del suelo (VUS)'],
  ['ups', 'Uso principal del suelo (UPS)'],
  ['clc_nivel1', 'Cobertura CLC · nivel 1'],
  ['clc_nivel2', 'Cobertura CLC · nivel 2'],
  ['clc_nivel3', 'Cobertura CLC · nivel 3'],
  ['clc_nivel4', 'Cobertura CLC · nivel 4'],
  ['clc_nivel5', 'Cobertura CLC · nivel 5'],
  ['clc_nivel6', 'Cobertura CLC · nivel 6'],
]

export default function ParcelDetail() {
  const { public_id } = useParams<{ public_id: string }>()

  const query = useQuery<ParcelDetailResponse>({
    queryKey: ['parcel-detail', public_id],
    queryFn: () => apiGet<ParcelDetailResponse>(`/properties/${public_id}`),
    enabled: Boolean(public_id),
  })

  const item: ParcelDetailItem | undefined = query.data?.item

  return (
    <div className="container">
      <PageHeader
        kicker="Ficha predial"
        title={item?.public_id ?? 'Predio'}
        lede={
          item
            ? 'Información real servida por la API. Los valores ausentes en la fuente se muestran como «No disponible», sin estimaciones.'
            : undefined
        }
      >
        <Link to="/predios" className={styles.backLink}>
          ← Volver al catálogo
        </Link>
      </PageHeader>

      {query.isLoading && <LoadingSkeleton label="Consultando la ficha del predio…" />}

      {query.isError && (
        <ErrorState
          message={`No se encontró un predio con el identificador «${public_id}» o la API no respondió.`}
          onRetry={() => query.refetch()}
        />
      )}

      {query.isSuccess && !item && (
        <EmptyState message={`No existe un predio con el identificador «${public_id}».`} />
      )}

      {item && (
        <div className={styles.layout}>
          <article className={styles.main}>
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Identificación</h2>
              <dl className={styles.definitionGrid}>
                <div>
                  <dt>Identificador público</dt>
                  <dd className="mono">{item.public_id}</dd>
                </div>
                <div>
                  <dt>Destino económico</dt>
                  <dd>{item.destino_economico ?? NO_DATA}</dd>
                </div>
                <div>
                  <dt>Subzona</dt>
                  <dd className="mono">{item.subzona ? `Subzona ${item.subzona}` : NO_DATA}</dd>
                </div>
                <div>
                  <dt>Coincidencia con ZHF</dt>
                  <dd>{item.coincide_zhf === 1 ? 'Coincide con ambas fuentes' : 'Solo en la primera fuente'}</dd>
                </div>
                <div>
                  <dt>Calidad</dt>
                  <dd><DataQualityBadge count={item.n_alertas_calidad} /></dd>
                </div>
                <div>
                  <dt>Intersecciones geoeconómicas</dt>
                  <dd className="mono">
                    {item.cantidad_intersecciones != null
                      ? `${item.cantidad_intersecciones} (${item.cantidad_zonas_zhg ?? NO_DATA} zonas)`
                      : NO_DATA}
                  </dd>
                </div>
              </dl>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Superficies</h2>
              <dl className={styles.definitionGrid}>
                <div>
                  <dt>Área catastral del terreno</dt>
                  <dd className="mono">{formatArea(item.area_terreno_catastral_m2)}</dd>
                </div>
                <div>
                  <dt>Área según fuente ZHF</dt>
                  <dd className="mono">{formatArea(item.area_zhf_m2)}</dd>
                </div>
                <div>
                  <dt>Área construida declarada</dt>
                  <dd className="mono">
                    {item.area_construida_m2 != null
                      ? formatArea(item.area_construida_m2)
                      : NO_DATA}
                  </dd>
                </div>
              </dl>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Ubicación</h2>
              <dl className={styles.definitionGrid}>
                <div>
                  <dt>Coordenadas referenciales</dt>
                  <dd className="mono">
                    {formatCoordinates(item.latitud, item.longitud)}
                  </dd>
                </div>
              </dl>
              {item.latitud != null && item.longitud != null ? (
                <Suspense fallback={<p className="mono">Cargando mapa…</p>}>
                  <MiniMap
                    lat={item.latitud}
                    lon={item.longitud}
                    label={`Predio ${item.public_id}`}
                  />
                </Suspense>
              ) : (
                <p className={styles.note}>
                  Sin coordenadas disponibles para este predio (no se muestra mapa).
                </p>
              )}
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Atributos territoriales</h2>
              <dl className={styles.definitionGrid}>
                {FEATURE_LABELS.map(([key, label]) => (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>{item.features[key] || NO_DATA}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Alertas de calidad</h2>
              {item.quality_flags.length === 0 ? (
                <p className={styles.note}>Sin alertas de calidad registradas.</p>
              ) : (
                <ul className={styles.flagList}>
                  {item.quality_flags.map((flag) => (
                    <li key={flag}>
                      <span className="mono">{flag}</span>
                      <span>{FLAG_LABELS[flag] ?? flag}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </article>

          <aside className={styles.aside}>
            <Disclaimer title="Sobre los valores">
              <p>
                Esta ficha muestra datos catastrales y territoriales descriptivos.{' '}
                <strong>No se muestra ningún avalúo del suelo</strong>: la fuente no
                permite respaldar un valor exclusivo del terreno para este predio.
              </p>
            </Disclaimer>
          </aside>
        </div>
      )}
    </div>
  )
}
