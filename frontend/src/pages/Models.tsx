import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { SystemStatus } from '../api/types'
import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import { ErrorState, LoadingSkeleton } from '../components/states'
import { formatCopPerHa, formatInt } from '../lib/format'
import styles from './Models.module.css'

interface ModelsListResponse {
  models: {
    experiment_id: string
    modelo: string
    mae_test_espacial_cop_ha: number
    r2_test_espacial: number
    etiqueta: string
    status: string
    production_eligible: boolean
  }[]
  official_model: null
  label_status: string
  disclaimer: string
}

// Resultados reales del experimento exp-proxy-001, documentados en
// docs/04_metodologia_ml.md (métricas ejecutadas, no inventadas).
const DOCUMENTED_TEST_SPATIAL = [
  { modelo: 'Baseline (mediana)', mae: 6592762, r2: -0.03, mdape: 57.6, n: 1353 },
  { modelo: 'Ridge', mae: 15196282, r2: -0.11, mdape: 703.8, n: 1353 },
  { modelo: 'Árbol de decisión', mae: 4215432, r2: 0.53, mdape: 24.1, n: 1353 },
  { modelo: 'Random Forest', mae: 3226230, r2: 0.74, mdape: 24.6, n: 1353 },
  { modelo: 'CatBoost', mae: 3730373, r2: 0.76, mdape: 47.6, n: 1353 },
]

const DOCUMENTED_TEST_RANDOM = [
  { modelo: 'Baseline (mediana)', mae: 7889929, r2: -0.02, n: 1155 },
  { modelo: 'Ridge', mae: 13581815, r2: 0.4, n: 1155 },
  { modelo: 'Árbol de decisión', mae: 4176143, r2: 0.66, n: 1155 },
  { modelo: 'Random Forest', mae: 2674886, r2: 0.82, n: 1155 },
  { modelo: 'CatBoost', mae: 3336590, r2: 0.81, n: 1155 },
]

function MetricTable({
  rows,
  columns,
}: {
  rows: { modelo: string; mae: number; r2: number; mdape?: number; n: number }[]
  columns: 'spatial' | 'random'
}) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <caption className={styles.caption}>
          {columns === 'spatial'
            ? 'Métricas reales en el test espacial sellado (exp-proxy-001)'
            : 'Métricas reales en el test aleatorio (exp-proxy-001)'}
        </caption>
        <thead>
          <tr>
            <th scope="col">Modelo</th>
            <th scope="col" className={styles.num}>MAE (COP/ha)</th>
            <th scope="col" className={styles.num}>R²</th>
            {columns === 'spatial' && (
              <th scope="col" className={styles.num}>MdAPE (%)</th>
            )}
            <th scope="col" className={styles.num}>n</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.modelo} className={row.modelo === 'Random Forest' ? styles.selected : ''}>
              <td>{row.modelo}</td>
              <td className={`${styles.num} mono`}>{formatInt(row.mae)}</td>
              <td className={`${styles.num} mono`}>{row.r2.toFixed(2)}</td>
              {columns === 'spatial' && (
                <td className={`${styles.num} mono`}>{row.mdape?.toFixed(1)}</td>
              )}
              <td className={`${styles.num} mono`}>{formatInt(row.n)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Models() {
  const status = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system/status'),
    staleTime: 60_000,
  })

  const models = useQuery<ModelsListResponse>({
    queryKey: ['models'],
    queryFn: () => apiGet<ModelsListResponse>('/models'),
    staleTime: 60_000,
  })

  if (status.isLoading || models.isLoading) {
    return (
      <div className="container">
        <PageHeader kicker="Modelos" title="Sistema predictivo" />
        <LoadingSkeleton label="Consultando el estado del modelo…" />
      </div>
    )
  }

  if (status.isError || models.isError) {
    return (
      <div className="container">
        <PageHeader kicker="Modelos" title="Sistema predictivo" />
        <ErrorState
          message="No se pudo consultar el estado del sistema de modelos."
          onRetry={() => {
            status.refetch()
            models.refetch()
          }}
        />
      </div>
    )
  }

  const estado = status.data!
  const registry = models.data!
  const registered = registry.models.filter((m) => m.experiment_id === 'exp-proxy-001')[0]

  return (
    <div className="container">
      <PageHeader
        kicker="Modelos · Ciencia"
        title="Sistema predictivo"
        lede="Estado real del componente de aprendizaje automático. El modelo oficial del valor exclusivo del suelo no existe todavía; solo hay un experimento con un proxy, debidamente rotulado."
      />

      <section className={styles.statusSection}>
        <h2 className={styles.sectionTitle}>Estado del modelo oficial</h2>
        <div className={styles.statusCard}>
          <p className={`mono ${styles.statusCode}`}>{estado.model_status}</p>
          <p>
            <strong>Validación pendiente.</strong> Los CSV del estudio no contienen un
            valor exclusivo del terreno por predio (con método, fecha y superficie
            documentados). Por eso el endpoint oficial responde 503 y ninguna pantalla
            muestra una estimación de suelo.
          </p>
          <p className={styles.statusReason}>{estado.reason}</p>
        </div>
      </section>

      <section className={styles.statusSection}>
        <h2 className={styles.sectionTitle}>Experimento proxy (Ruta B)</h2>
        <p>
          Para comparar metodológicamente los algoritmos se entrenó un modelo con una
          variable <strong>diferente</strong>: el{' '}
          <strong>avalúo catastral total por hectárea</strong> (avalúo total ÷ área
          catastral). Este proxy puede incluir el componente de construcciones y{' '}
          <strong>no es el valor del suelo</strong>.
        </p>
        {registered ? (
          <div className={styles.expCard}>
            <p className="mono">{registered.experiment_id}</p>
            <p>
              Algoritmo: <strong>{registered.modelo}</strong> · MAE test espacial{' '}
              <strong>{formatCopPerHa(registered.mae_test_espacial_cop_ha)}</strong> · R²{' '}
              <strong>{registered.r2_test_espacial.toFixed(2)}</strong>
            </p>
            <p className={styles.expNote}>
              Objetivo real entrenado: <span className="mono">{registered.etiqueta}</span> ·
              estado: <span className="mono">{registered.status}</span> · elegible para
              producción: <span className="mono">false</span>
            </p>
          </div>
        ) : (
          <p className={styles.expNote}>Sin artefactos registrados en este entorno.</p>
        )}
      </section>

      <section className={styles.statusSection}>
        <h2 className={styles.sectionTitle}>Avalúo total por hectárea vs. valor del suelo</h2>
        <div className={styles.twoCol}>
          <p>
            El <strong>avalúo catastral total</strong> valora el inmueble completo; 3.033
            de los 7.709 predios consolidados registran superficie construida. Dividirlo
            por el área produce un proxy en COP/ha, útil para experimentar, pero no
            equivale al <strong>valor exclusivo del terreno</strong>.
          </p>
          <p>
            Además, el área aparece en el denominador del proxy y también como variable
            de entrada: parte de la aparente capacidad del modelo es una relación
            mecánica, no una capacidad independiente de valoración.
          </p>
        </div>
      </section>

      <section className={styles.statusSection}>
        <h2 className={styles.sectionTitle}>Métricas reales del experimento (exp-proxy-001)</h2>
        <p className={styles.tableNote}>
          Valores ejecutados y documentados en <span className="mono">docs/04_metodologia_ml.md</span>.
          La selección se hizo por menor MAE en el test espacial sellado.
        </p>
        <h3 className={styles.subTitle}>Validación espacial (grupos geográficos separados)</h3>
        <MetricTable rows={DOCUMENTED_TEST_SPATIAL} columns="spatial" />
        <h3 className={styles.subTitle}>Validación aleatoria (referencia metodológica)</h3>
        <MetricTable rows={DOCUMENTED_TEST_RANDOM} columns="random" />
        <p className={styles.tableNote}>
          La validación espacial es más exigente que la aleatoria (Random Forest: R² 0,74
          frente a 0,82): los predios vecinos comparten territorio y la partición aleatoria
          infla el rendimiento si no se controla. Por eso se reportan ambas.
        </p>
      </section>

      <Disclaimer title="Advertencias metodológicas">
        <p>
          El modelo experimental <strong>no es un estimador validado del valor comercial
          del terreno</strong> ni un avalúo oficial. Sus métricas describen la capacidad de
          reproducir un proxy catastral, con las limitaciones de área y construcciones ya
          señaladas. Ridge empeoró el baseline (MAE 15,2 M COP/ha en el test espacial):
          se reporta sin ocultarlo.
        </p>
      </Disclaimer>
    </div>
  )
}
