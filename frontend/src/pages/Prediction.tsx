import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiGet, apiPost, ApiError, isTimeoutError } from '../api/client'
import type { SystemStatus, ValorV1Response } from '../api/types'
import PageHeader from '../components/PageHeader'
import ParcelSelector from '../components/ParcelSelector'
import { ErrorState, LoadingSkeleton } from '../components/states'
import { formatCopPerHa } from '../lib/format'
import styles from './Prediction.module.css'

interface Estabilidad {
  rf_gana_mae_en?: number
  rf_gana_mdape_en?: number
  rf_mae_mediana?: number
  zhg_mae_mediana?: number
}

function mensajeDeError(error: unknown): { titulo: string; detalles: string[] } {
  if (isTimeoutError(error)) {
    return { titulo: 'La consulta excedió el tiempo de espera.', detalles: ['Inténtalo de nuevo.'] }
  }
  if (error instanceof ApiError) {
    const detalles: string[] = []
    if (error.code === 'VALOR_V1_DISABLED' || error.code === 'VALOR_V1_UNAVAILABLE') {
      detalles.push('El modelo académico no está disponible en este entorno en este momento.')
    }
    if (error.code === 'UNSUPPORTED_PARCEL' || error.code === 'OUT_OF_DOMAIN') {
      detalles.push('El predio consultado no cumple las condiciones de aplicación del modelo (construcción registrada igual a cero y características dentro del dominio observado).')
      const razon = (error.details as Record<string, unknown> | undefined)?.razon
      if (typeof razon === 'string') detalles.push(`Motivo del backend: ${razon}`)
      const campos = (error.details as Record<string, unknown> | undefined)?.campos_fuera_de_dominio
      if (Array.isArray(campos)) detalles.push(...campos.map((c) => String(c)))
    }
    if (error.status === 429) {
      detalles.push('Se alcanzó el límite de consultas por minuto; espera un momento e inténtalo de nuevo.')
    }
    if (error.code === 'PROPERTY_NOT_FOUND') {
      detalles.push('No existe un predio con ese identificador público.')
    }
    return {
      titulo: `${error.status} ${error.code} — ${error.message}`,
      detalles: detalles.length ? detalles : ['Revisa el identificador y vuelve a intentarlo.'],
    }
  }
  return { titulo: 'No se pudo contactar la API.', detalles: ['Verifica tu conexión e inténtalo de nuevo.'] }
}

export default function Prediction() {
  const [input, setInput] = useState('')

  const status = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system/status'),
    staleTime: 60_000,
  })

  const estimacion = useMutation({
    mutationFn: (publicId: string) =>
      apiPost<ValorV1Response>('/predictions/valor-terreno-v1', { public_id: publicId }),
  })

  const habilitado = status.data?.valor_v1?.habilitado === true
  const disponible = status.data?.valor_v1?.disponible === true

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const id = input.trim()
    if (!id) return
    estimacion.reset()
    estimacion.mutate(id)
  }

  if (status.isLoading) {
    return (
      <div className="container">
        <PageHeader
          kicker="Predicción"
          title="Estimación catastral con inteligencia artificial"
          lede="Modelo Atlas Vivo · Random Forest v1"
        />
        <LoadingSkeleton label="Consultando el estado del modelo…" />
      </div>
    )
  }

  if (status.isError) {
    return (
      <div className="container">
        <PageHeader
          kicker="Predicción"
          title="Estimación catastral con inteligencia artificial"
          lede="Modelo Atlas Vivo · Random Forest v1"
        />
        <ErrorState
          message="No se pudo consultar el estado del sistema."
          onRetry={() => status.refetch()}
        />
      </div>
    )
  }

  const evaluacion = (estimacion.data?.evaluation_context ?? {}) as Record<string, unknown>
  const estabilidad = (evaluacion.estabilidad_5_pliegues_espaciales ?? {}) as Estabilidad

  return (
    <div className="container">
      <PageHeader
        kicker="Predicción · Modelo académico"
        title="Estimación catastral con inteligencia artificial"
        lede="Modelo Atlas Vivo · Random Forest v1 — estimación orientativa de valor catastral unitario (COP/ha) para predios sin construcción registrada."
      />

      <section className={styles.expSection} aria-label="Estimación con el modelo RF v1">
        <form className={styles.searchForm} onSubmit={submit} role="search">
          <label className={styles.searchLabel} htmlFor="valor-v1-id">
            Identificador público del predio
          </label>
          <div className={styles.searchRow}>
            <ParcelSelector id="valor-v1-id" value={input} onChange={setInput} />
            <button
              type="submit"
              className={styles.searchButton}
              disabled={estimacion.isPending || !habilitado || !disponible}
            >
              {estimacion.isPending ? 'Consultando…' : 'Consultar estimación'}
            </button>
          </div>
        </form>

        {!habilitado && (
          <div className={styles.unavailableCard} role="status">
            <p className={`mono ${styles.unavailableCode}`}>VALOR_V1_ENABLED=false</p>
            <p>
              El modelo académico no está habilitado en este entorno. La
              infraestructura está preparada; la estimación no está disponible
              temporalmente.
            </p>
          </div>
        )}

        {habilitado && !disponible && (
          <div className={styles.unavailableCard} role="status">
            <p className={`mono ${styles.unavailableCode}`}>ARTEFACTO NO CARGADO</p>
            <p>
              El artefacto del modelo no está disponible en este servidor. La
              estimación no está disponible temporalmente.
            </p>
          </div>
        )}

        {estimacion.isError && (
          <div className={styles.resultError} role="alert">
            <p className={styles.errorTitle}>{mensajeDeError(estimacion.error).titulo}</p>
            <ul className={styles.errorDetails}>
              {mensajeDeError(estimacion.error).detalles.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ul>
          </div>
        )}

        {estimacion.isSuccess && estimacion.data && (
          <div className={styles.resultCard} role="status">
            <p className={styles.resultValue}>{formatCopPerHa(estimacion.data.predicted_cop_ha)}</p>
            <p className={styles.resultMeta}>
              Estimación calculada con <span className="mono">{estimacion.data.model_id}</span>{' '}
              · versión <span className="mono">{estimacion.data.model_version}</span> ·{' '}
              {estimacion.data.unit}
            </p>
            <p className={styles.resultTarget}>
              Variable objetivo: <span className="mono">{estimacion.data.target}</span> —
              valor catastral unitario derivado del avalúo total, para predios sin
              construcción registrada.
            </p>

            <div className={styles.demoGrid}>
              {estimacion.data.reference_zhg_cop_ha != null && (
                <div className={styles.refBlock}>
                  <p className={styles.demoLabel}>Referencia ZHG (dato territorial)</p>
                  <p className={styles.demoValue}>
                    {formatCopPerHa(estimacion.data.reference_zhg_cop_ha)}
                  </p>
                  <p className={styles.refNote}>
                    Valor geoeconómico zonal consultado de los datos; no es una
                    predicción del modelo.
                  </p>
                </div>
              )}
              {estimacion.data.absolute_difference_vs_zhg_cop_ha != null && (
                <div className={styles.refBlock}>
                  <p className={styles.demoLabel}>Diferencia de la estimación frente a la referencia</p>
                  <p className={`${styles.demoValue} mono`}>
                    {formatCopPerHa(estimacion.data.absolute_difference_vs_zhg_cop_ha)}
                    {estimacion.data.relative_difference_vs_zhg_pct != null &&
                      ` (${estimacion.data.relative_difference_vs_zhg_pct} %)`}
                  </p>
                </div>
              )}
            </div>

            <p className={styles.fitNote}>
              Este predio pertenece al inventario con el que se ajustó el modelo
              (4.676 predios del escenario A): esta consulta demuestra la
              inferencia real y no constituye una evaluación independiente.
            </p>

            <details className={styles.demoDetails}>
              <summary>Metodología, métricas y limitaciones</summary>
              <p className={styles.expNote}>
                Condiciones de aplicación: predio sin construcción registrada,
                área positiva y características dentro de los rangos observados
                en el entrenamiento. Métricas de validación independientes
                (partición espacial sellada, 689 predios): MAE del modelo ≈
                767.064 COP/ha (MdAPE ≈ 11,7 %) frente a la referencia ZHG ≈
                817.030 COP/ha (MdAPE ≈ 5,7 %). Estabilidad en 5 particiones
                espaciales: el modelo ganó en MAE {estabilidad.rf_gana_mae_en ?? 0}/5
                y en MdAPE {estabilidad.rf_gana_mdape_en ?? 0}/5 — su desempeño es
                limitado y depende del territorio.
              </p>
              <ul className={styles.warnings}>
                {estimacion.data.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
              <p className={styles.expNote}>
                Resultados científicos completos, experimentos históricos y
                decisiones metodológicas:{' '}
                <Link to="/modelos" className={styles.methodLink}>
                  página de Modelos
                </Link>
                .
              </p>
            </details>

            <p className={styles.demoDisclaimer}>{estimacion.data.disclaimer}</p>
          </div>
        )}
      </section>

      <p className={styles.expNote}>
        Atlas Vivo no expide avalúos catastrales ni valoraciones comerciales.
        Toda cifra mostrada es una estimación académica orientativa o un dato
        territorial de referencia.
      </p>
    </div>
  )
}
