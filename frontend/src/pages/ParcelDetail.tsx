import { lazy, Suspense } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { ParcelDetailItem, ParcelDetailResponse } from '../api/types'
import PageHeader from '../components/PageHeader'
import { DataQualityBadge } from '../components/DataQualityBadge'
import Disclaimer from '../components/Disclaimer'
import ZhgReferenceCard from '../components/ZhgReferenceCard'
import InterpretationCard from '../components/InterpretationCard'
import HelpTip from '../components/HelpTip'
import { interpretFlags, interpretGeneral } from '../lib/interpretation'
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
  ['zhf_codigo', 'Código de zona homogénea física (ZHF)'],
  ['zhf_dispon', 'Disponibilidad o condición física registrada (ZHF)'],
  ['zhf_influe', 'Influencia o accesibilidad territorial (ZHF)'],
  ['zhf_uso_ac', 'Uso actual del suelo registrado (ZHF)'],
  ['aht_vpoten', 'Aptitud o potencial territorial (AHT)'],
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
            <InterpretationCard>
              {interpretGeneral(item).map((line) => (
                <p key={line}>{line}</p>
              ))}
            </InterpretationCard>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>
                Identificación{' '}
                <HelpTip label="Qué significa la identificación del predio">
                  Identifica al predio dentro del catálogo público. El identificador
                  es opaco: no revela matrículas ni datos personales. El destino
                  económico es la categoría registrada en la fuente, y la subzona es
                  una subdivisión geoeconómica interna.
                </HelpTip>
              </h2>
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
              <h2 className={styles.sectionTitle}>
                Superficies{' '}
                <HelpTip label="Qué significan las superficies">
                  El área catastral es la registrada en la fuente predial; el área
                  ZHF proviene de la otra fuente del estudio. Cuando difieren mucho,
                  se marca una alerta de calidad y se evitan cálculos de
                  consolidación que podrían ser engañosos.
                </HelpTip>
              </h2>
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
              <h2 className={styles.sectionTitle}>
                Ubicación{' '}
                <HelpTip label="Qué significa la ubicación">
                  Las coordenadas son puntos referenciales de la fuente ZHF: sirven
                  para ubicar el predio en el mapa, pero no representan un polígono
                  catastral oficial.
                </HelpTip>
              </h2>
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
              <h2 className={styles.sectionTitle}>
                Atributos territoriales{' '}
                <HelpTip label="Qué significan los atributos territoriales">
                  Son clasificaciones de las fuentes (zonas homogéneas físicas,
                  coberturas, vocación). Los códigos se muestran tal como vienen en
                  la fuente; su decodificación oficial no está disponible en este
                  proyecto, por lo que no se les asigna un significado inventado.
                </HelpTip>
              </h2>
              <dl className={styles.definitionGrid}>
                {FEATURE_LABELS.map(([key, label]) => (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>{item.features[key] || NO_DATA}</dd>
                  </div>
                ))}
              </dl>
              <p className={styles.codeFootnote}>
                Los códigos (ZHF, AHT, UPS…) se muestran tal como vienen en la
                fuente. Su decodificación semántica oficial está pendiente de
                diccionario; no se inventan significados.
              </p>
            </section>

            <ZhgReferenceCard publicId={item.public_id} />

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>
                Alertas de calidad{' '}
                <HelpTip label="Qué significan las alertas de calidad">
                  Son avisos sobre inconsistencias o faltantes de las fuentes. No
                  eliminan el predio: indican qué información conviene revisar
                  antes de sacar conclusiones.
                </HelpTip>
              </h2>
              {item.quality_flags.length === 0 ? (
                <p className={styles.note}>Sin alertas de calidad registradas.</p>
              ) : (
                <>
                  <ul className={styles.flagList}>
                    {item.quality_flags.map((flag) => (
                      <li key={flag} title={flag}>
                        <span>{FLAG_LABELS[flag] ?? flag}</span>
                      </li>
                    ))}
                  </ul>
                  <InterpretationCard
                    title="Qué significan estas alertas para este predio"
                    variant="warning"
                  >
                    {interpretFlags(item.quality_flags).map((line) => (
                      <p key={line}>{line}</p>
                    ))}
                  </InterpretationCard>
                </>
              )}
            </section>
          </article>

          <aside className={styles.aside}>
            <Disclaimer title="Sobre los valores">
              <p>
                Esta ficha muestra la <strong>referencia zonal ZHG</strong> del
                suelo (dato económico territorial verificado en las fuentes),
                pero <strong>no un avalúo individual certificado</strong> del
                predio: la fuente no permite respaldar un valor exclusivo del
                terreno ni una tasación oficial.
              </p>
            </Disclaimer>
          </aside>
        </div>
      )}
    </div>
  )
}
