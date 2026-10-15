import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { ZhgReferenceResponse } from '../api/types'
import { formatArea, formatCopPerHa, formatInt, NO_DATA } from '../lib/format'
import { ErrorState, LoadingSkeleton } from './states'
import styles from './ZhgReferenceCard.module.css'

const COVERAGE_LABELS: Record<string, string> = {
  consistente: 'Cobertura consistente (≤1 %)',
  dudosa: 'Cobertura dudosa (1–5 %)',
  no_apta: 'Cobertura inconsistente (>5 %)',
}

export default function ZhgReferenceCard({ publicId }: { publicId: string }) {
  const query = useQuery<ZhgReferenceResponse>({
    queryKey: ['zhg-reference', publicId],
    queryFn: () => apiGet<ZhgReferenceResponse>(`/properties/${publicId}/zhg-reference`),
    staleTime: 5 * 60_000,
  })

  return (
    <section className={styles.card} aria-label="Referencia económica territorial ZHG">
      <header className={styles.header}>
        <div>
          <p className={`mono ${styles.kicker}`}>Referencia económica territorial · ZHG</p>
          <h2 className={styles.title}>Valor unitario de referencia del suelo</h2>
        </div>
        <span className={`mono ${styles.tag}`}>dato · no predicción</span>
      </header>

      {query.isLoading && <LoadingSkeleton label="Consultando referencias ZHG…" />}
      {query.isError && (
        <ErrorState
          message="No se pudieron consultar las referencias ZHG de este predio."
          onRetry={() => query.refetch()}
        />
      )}

      {query.isSuccess && query.data && query.data.zones.length === 0 && (
        <p className={styles.note}>Este predio no tiene referencias ZHG asociadas en la base.</p>
      )}

      {query.isSuccess && query.data && query.data.zones.length > 0 && (
        <>
          {query.data.zones.length === 1 ? (
            <div className={styles.single}>
              <p className={styles.singleValue}>
                {formatCopPerHa(query.data.zones[0].value_cop_ha ?? 0)}
              </p>
              <p className={`mono ${styles.singleMeta}`}>
                Zona {query.data.zones[0].zone_code} · participación{' '}
                {query.data.zones[0].share_pct != null
                  ? `${formatInt(query.data.zones[0].share_pct)} %`
                  : NO_DATA}
              </p>
            </div>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <caption className={styles.caption}>
                  Este predio intersecta varias zonas geoeconómicas
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Zona</th>
                    <th scope="col" className={styles.num}>Valor (COP/ha)</th>
                    <th scope="col" className={styles.num}>Área intersección</th>
                    <th scope="col" className={styles.num}>Participación</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.zones.map((zone) => (
                    <tr
                      key={zone.zone_code}
                      className={
                        zone.zone_code === query.data.dominant_zone?.zone_code
                          ? styles.dominant
                          : ''
                      }
                    >
                      <td className="mono">{zone.zone_code}</td>
                      <td className={`${styles.num} mono`}>
                        {zone.value_cop_ha != null
                          ? formatInt(zone.value_cop_ha)
                          : NO_DATA}
                      </td>
                      <td className={`${styles.num} mono`}>
                        {formatArea(zone.area_intersection_m2)}
                      </td>
                      <td className={`${styles.num} mono`}>
                        {zone.share_pct != null
                          ? `${formatInt(zone.share_pct)} %`
                          : NO_DATA}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {query.data.dominant_zone && (
                <p className={styles.dominantNote}>
                  Zona predominante: {query.data.dominant_zone.zone_code}.{' '}
                  {query.data.dominant_zone.note}
                </p>
              )}
            </div>
          )}

          <div className={styles.consolidation}>
            <p className={styles.coverageLabel}>
              <span
                className={`${styles.coverageDot} ${styles[query.data.coverage_status ?? 'no_apta']}`}
                aria-hidden="true"
              />
              {COVERAGE_LABELS[query.data.coverage_status ?? 'no_apta']}
            </p>
            {query.data.weighted_reference && (
              <p className={styles.weighted}>
                Referencia consolidada (ponderada por área):{' '}
                <strong className="mono">
                  {formatCopPerHa(query.data.weighted_reference.value_cop_ha)}
                </strong>
                <span className={`mono ${styles.statusNote}`}>
                  {query.data.weighted_reference.status_label}
                </span>
              </p>
            )}
            {query.data.provisional_weighted_reference && (
              <p className={`${styles.weighted} ${styles.provisional}`}>
                Cálculo provisional: <strong className="mono">
                  {formatCopPerHa(query.data.provisional_weighted_reference.value_cop_ha)}
                </strong>
                <span className={`mono ${styles.statusNote}`}>
                  {query.data.provisional_weighted_reference.status_label}
                </span>
              </p>
            )}
            {!query.data.weighted_reference && !query.data.provisional_weighted_reference && (
              <p className={styles.noWeighted}>
                No se muestra una consolidación ponderada: la cobertura de superficies
                no es consistente para este predio.
              </p>
            )}
          </div>

          <ul className={styles.limitations}>
            {query.data.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
