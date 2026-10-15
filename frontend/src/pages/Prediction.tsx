import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiGet, apiPost, ApiError } from '../api/client'
import type { SystemStatus, ZhgDemoResponse } from '../api/types'
import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import ZhgReferenceCard from '../components/ZhgReferenceCard'
import { ErrorState, LoadingSkeleton } from '../components/states'
import { formatCop, formatCopPerHa } from '../lib/format'
import styles from './Prediction.module.css'

interface ExperimentalResult {
  status: string
  experiment_id: string
  target: string
  unit: string
  prediction_cop_ha: number
  estimated_proxy_total_cop: number | null
  warnings: string[]
  is_experimental: boolean
  predicts_land_value: boolean
  disclaimer: string
}

const DESTINOS = [
  'Agropecuario', 'Religioso', 'Habitacional', 'Institucional', 'Comercial',
  'Educativo', 'Minería hidrocarburos', 'Recreacional',
  'Lote urbanizado no construido', 'Cultural',
]

const NUMERIC_FIELDS: { key: string; label: string; step?: string; min?: string; max?: string }[] = [
  { key: 'area_terreno_catastral_m2', label: 'Área catastral del terreno (m²)', min: '0.01' },
  { key: 'area_zhf_m2', label: 'Área ZHF (m²)', min: '0.01' },
  { key: 'area_construida_m2', label: 'Área construida (m²)', min: '0' },
  { key: 'tr_latitud', label: 'Latitud (grados)', step: 'any', min: '-6', max: '13' },
  { key: 'tr_longitud', label: 'Longitud (grados)', step: 'any', min: '-80', max: '-66' },
]

const SELECT_FIELDS: { key: string; label: string; options: string[] }[] = [
  { key: 'destino_economico', label: 'Destino económico', options: DESTINOS },
  { key: 'zhf_dispon', label: 'Disponibilidad ZHF', options: ['2', '3', '4'] },
  { key: 'zhf_influe', label: 'Influencia ZHF', options: ['3', '5', '8'] },
  { key: 'zhf_uso_ac', label: 'Uso actual ZHF', options: ['12', '16'] },
]

const DATALIST_FIELDS: { key: string; label: string; suggestions: string[] }[] = [
  {
    key: 'ups', label: 'Uso principal del suelo (UPS)',
    suggestions: [
      'Zonas de desarrollo agropecuario sin restricciones',
      'Zonas de protección de los recursos naturales',
      'Zonas de desarrollo forestal',
    ],
  },
  { key: 'vus_vocaci', label: 'Vocación del suelo (VUS)', suggestions: ['FPP', 'ASPp', 'CPSm', 'CA', 'CTIc'] },
  { key: 'zhf_codigo', label: 'Código ZHF', suggestions: [] },
  { key: 'aht_vpoten', label: 'Aptitud potencial (AHT)', suggestions: [] },
  { key: 'clc_nivel1', label: 'Cobertura CLC · nivel 1', suggestions: ['2. Territorios Agrícolas', '3. Bosques y Áreas Seminaturales'] },
  { key: 'clc_nivel2', label: 'Cobertura CLC · nivel 2', suggestions: [] },
  { key: 'clc_nivel3', label: 'Cobertura CLC · nivel 3', suggestions: [] },
  { key: 'clc_nivel4', label: 'Cobertura CLC · nivel 4', suggestions: [] },
  { key: 'clc_nivel5', label: 'Cobertura CLC · nivel 5', suggestions: [] },
  { key: 'clc_nivel6', label: 'Cobertura CLC · nivel 6', suggestions: [] },
]

function BlockedOfficialCard({ onCheck }: { onCheck: () => void }) {
  return (
    <div className={styles.blockCard}>
      <h2 className={styles.sectionTitle}>Predicción oficial: no disponible</h2>
      <p>
        El backend responde <span className="mono">503 MODEL_NOT_READY</span> para la
        predicción oficial: la variable objetivo (valor exclusivo del suelo en COP/ha) no
        está validada. Este comportamiento es intencional y este frontend lo respeta.
      </p>
      <button type="button" className={styles.checkButton} onClick={onCheck}>
        Comprobar estado oficial (real)
      </button>
    </div>
  )
}

function ZhgLookupSection() {
  const [input, setInput] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const id = input.trim()
    if (id) setSelectedId(id)
  }

  return (
    <section className={styles.expSection} aria-label="Consulta de referencia ZHG">
      <p className={`mono ${styles.conceptTag}`}>
        Referencia ZHG · dato económico territorial existente en la base
      </p>
      <h2 className={styles.sectionTitle}>Consulta de referencia de valor (no es predicción)</h2>
      <p>
        Consulta el valor unitario de referencia por zona geoeconómica de un predio,
        expresado en COP/ha. Es un dato de las fuentes, no una estimación de
        inteligencia artificial.
      </p>
      <form className={styles.searchForm} onSubmit={submit} role="search">
        <label className={styles.searchLabel} htmlFor="zhg-public-id">
          Identificador público del predio
        </label>
        <div className={styles.searchRow}>
          <input
            id="zhg-public-id"
            className={styles.searchInput}
            type="text"
            placeholder="p_ab12cd34ef567890"
            value={input}
            maxLength={32}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className={styles.searchButton}>
            Consultar referencia ZHG
          </button>
        </div>
      </form>
      {selectedId && <ZhgReferenceCard publicId={selectedId} />}
    </section>
  )
}

function ZhgDemoSection() {
  const [input, setInput] = useState('')

  const status = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system/status'),
    staleTime: 60_000,
  })

  const demo = useMutation({
    mutationFn: (publicId: string) =>
      apiPost<ZhgDemoResponse>('/predictions/experimental-zhg', { public_id: publicId }),
  })

  const enabled = status.data?.experimental_zhg?.habilitado === true
  const ready = status.data?.experimental_zhg?.disponible === true

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const id = input.trim()
    if (!id) return
    demo.reset()
    demo.mutate(id)
  }

  return (
    <section className={styles.expSection} aria-label="Demostración experimental de ML">
      <p className={`mono ${styles.demoKicker}`}>Predicción ML · demostración experimental</p>
      <h2 className={styles.sectionTitle}>Demostración experimental (zonas conocidas)</h2>

      {!enabled ? (
        <>
          <p>
            La demostración experimental está{' '}
            <strong>desactivada en este entorno</strong>{' '}
            (<span className="mono">EXPERIMENTAL_ZHG_ENABLED=false</span>). Solo se
            habilita localmente, con el artefacto{' '}
            <span className="mono">exp-zhg-001-demo</span> presente y verificado.
          </p>
          <p className={styles.expNote}>
            Aunque se habilite, su estimación sería una{' '}
            <strong>demostración experimental</strong> para predios de zonas conocidas,
            siempre junto a la referencia ZHG consultable; no constituye un avalúo
            individual certificado.
          </p>
        </>
      ) : !ready ? (
        <p className={styles.expNote}>
          El artefacto de la demostración no está disponible en este servidor.
        </p>
      ) : (
        <>
          <p>
            Demostración con el modelo experimental (Random Forest) para{' '}
            <strong>predios de una única zona conocida</strong>. La estimación se muestra
            siempre junto a la referencia ZHG y su diferencia.
          </p>
          <form className={styles.searchForm} onSubmit={submit}>
            <label className={styles.searchLabel} htmlFor="zhg-demo-id">
              Identificador público del predio
            </label>
            <div className={styles.searchRow}>
              <input
                id="zhg-demo-id"
                className={styles.searchInput}
                type="text"
                placeholder="p_ab12cd34ef567890"
                value={input}
                maxLength={32}
                onChange={(e) => setInput(e.target.value)}
              />
              <button type="submit" className={styles.searchButton} disabled={demo.isPending}>
                {demo.isPending ? 'Calculando…' : 'Ejecutar demostración experimental'}
              </button>
            </div>
          </form>

          {demo.isError && (
            <div className={styles.resultError} role="alert">
              {demo.error instanceof ApiError
                ? `${demo.error.status} ${demo.error.code}: ${demo.error.message}`
                : 'No se pudo ejecutar la demostración.'}
            </div>
          )}

          {demo.isSuccess && demo.data && (
            <div className={styles.demoResult} role="status">
              <p className={`mono ${styles.resultCode}`}>
                {demo.data.model_status} · {demo.data.model_id}
              </p>
              <div className={styles.demoGrid}>
                <div>
                  <p className={styles.demoLabel}>Referencia ZHG conocida</p>
                  <p className={styles.demoValue}>
                    {formatCopPerHa(demo.data.reference_zhg_cop_ha)}
                  </p>
                </div>
                <div>
                  <p className={styles.demoLabel}>Estimación experimental</p>
                  <p className={`${styles.demoValue} ${styles.demoEstimate}`}>
                    {formatCopPerHa(demo.data.predicted_zhg_cop_ha)}
                  </p>
                </div>
                <div>
                  <p className={styles.demoLabel}>Diferencia</p>
                  <p className={`${styles.demoValue} mono`}>
                    {formatCop(demo.data.absolute_difference_cop_ha)}
                    {demo.data.relative_difference_pct != null &&
                      ` (${demo.data.relative_difference_pct} %)`}
                  </p>
                </div>
              </div>
              <p className={styles.demoMeta}>
                Zona {demo.data.zone_code} · dominio:{' '}
                <span className="mono">{demo.data.domain_status}</span> · unidad{' '}
                <span className="mono">{demo.data.unit}</span>
              </p>
              <ul className={styles.warnings}>
                {demo.data.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
              <p className={styles.demoDisclaimer}>{demo.data.disclaimer}</p>
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default function Prediction() {
  const [officialResult, setOfficialResult] = useState<string | null>(null)
  const [form, setForm] = useState<Record<string, string>>({
    area_terreno_catastral_m2: '',
    destino_economico: 'Agropecuario',
  })

  const status = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system/status'),
    staleTime: 60_000,
  })

  const officialCheck = useMutation({
    mutationFn: () => apiPost('/predictions', { features: {} }),
    onSuccess: () => setOfficialResult('Respuesta inesperada: el endpoint respondió sin bloqueo.'),
    onError: (error: unknown) => {
      if (error instanceof ApiError) {
        setOfficialResult(`${error.status} ${error.code} — ${error.message}`)
      } else {
        setOfficialResult('No se pudo contactar la API.')
      }
    },
  })

  const experimental = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiPost<ExperimentalResult>('/predictions/experimental', payload),
  })

  if (status.isLoading) {
    return (
      <div className="container">
        <PageHeader kicker="Predicción" title="Estimador" />
        <LoadingSkeleton label="Consultando el estado del sistema…" />
      </div>
    )
  }

  if (status.isError) {
    return (
      <div className="container">
        <PageHeader kicker="Predicción" title="Estimador" />
        <ErrorState message="No se pudo consultar el estado del sistema." onRetry={() => status.refetch()} />
      </div>
    )
  }

  const experimentalEnabled = status.data!.experimental_model?.habilitado

  function setField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function buildPayload(): Record<string, unknown> {
    const features: Record<string, unknown> = {}
    for (const field of NUMERIC_FIELDS) {
      const raw = form[field.key]
      if (raw === '' || raw === undefined) continue
      features[field.key] = Number(raw)
    }
    for (const field of [...SELECT_FIELDS, ...DATALIST_FIELDS]) {
      const raw = form[field.key]
      if (raw && raw.trim() !== '') features[field.key] = raw
    }
    return { features }
  }

  function submitExperimental(event: React.FormEvent) {
    event.preventDefault()
    experimental.reset()
    experimental.mutate(buildPayload())
  }

  return (
    <div className="container">
      <PageHeader
        kicker="Predicción · Simulador"
        title="Estimador"
        lede="Estado honesto del sistema predictivo. No existen estimaciones simuladas: todo lo que se muestra proviene de respuestas reales de la API."
      />

      <ZhgLookupSection />

      <p className={`mono ${styles.conceptTag}`}>
        Predicción ML · funcionalidad experimental no habilitada oficialmente
      </p>
      <BlockedOfficialCard onCheck={() => officialCheck.mutate()} />
      {officialCheck.isPending && (
        <p className="mono" role="status">Consultando el endpoint oficial…</p>
      )}
      {officialResult && (
        <p className={styles.officialResult} role="status">
          Respuesta real del backend: <span className="mono">{officialResult}</span>
        </p>
      )}

      <ZhgDemoSection />

      {/* Experimento proxy histórico (avalúo total/ha): se muestra SOLO si su
          flag local está activo. Desactivado por defecto, no se presenta al
          usuario final para evitar confundirlo con la demostración ZHG. */}
      {experimentalEnabled && (
      <section className={styles.expSection}>
        <h2 className={styles.sectionTitle}>Predicción experimental (proxy)</h2>
            <p>
              La inferencia experimental está habilitada en este entorno. El formulario
              usa exclusivamente las variables admitidas por el backend y el resultado se
              rotula como experimental.
            </p>

            <form className={styles.form} onSubmit={submitExperimental}>
              <fieldset className={styles.fieldset}>
                <legend>Variables numéricas</legend>
                <div className={styles.fieldGrid}>
                  {NUMERIC_FIELDS.map((field) => (
                    <label key={field.key} className={styles.field}>
                      <span>{field.label}</span>
                      <input
                        type="number"
                        step={field.step ?? 'any'}
                        min={field.min}
                        max={field.max}
                        value={form[field.key] ?? ''}
                        onChange={(e) => setField(field.key, e.target.value)}
                      />
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset className={styles.fieldset}>
                <legend>Variables categóricas</legend>
                <div className={styles.fieldGrid}>
                  {SELECT_FIELDS.map((field) => (
                    <label key={field.key} className={styles.field}>
                      <span>{field.label}</span>
                      <select
                        value={form[field.key] ?? ''}
                        onChange={(e) => setField(field.key, e.target.value)}
                      >
                        <option value="">Sin dato</option>
                        {field.options.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </label>
                  ))}
                  {DATALIST_FIELDS.map((field) => (
                    <label key={field.key} className={styles.field}>
                      <span>{field.label}</span>
                      <input
                        type="text"
                        list={`dl-${field.key}`}
                        maxLength={200}
                        value={form[field.key] ?? ''}
                        onChange={(e) => setField(field.key, e.target.value)}
                        placeholder="Opcional"
                      />
                      <datalist id={`dl-${field.key}`}>
                        {field.suggestions.map((s) => (
                          <option key={s} value={s} />
                        ))}
                      </datalist>
                    </label>
                  ))}
                </div>
              </fieldset>

              <div className={styles.formActions}>
                <button type="submit" className={styles.submit} disabled={experimental.isPending}>
                  {experimental.isPending ? 'Calculando…' : 'Ejecutar estimación experimental'}
                </button>
                <p className={styles.formNote}>
                  Campos vacíos: el backend aplica el mismo manejo de faltantes del
                  entrenamiento (mediana numérica / «SIN_DATO» categórico) y lo avisa.
                </p>
              </div>
            </form>

            {experimental.isError && (
              <div className={styles.resultError} role="alert">
                {experimental.error instanceof ApiError
                  ? `${experimental.error.status} ${experimental.error.code}: ${experimental.error.message}`
                  : 'No se pudo ejecutar la estimación.'}
              </div>
            )}

            {experimental.isSuccess && experimental.data && (
              <div className={styles.resultCard} role="status">
                <p className={`mono ${styles.resultCode}`}>{experimental.data.status}</p>
                <p className={styles.resultValue}>
                  {formatCopPerHa(experimental.data.prediction_cop_ha)}
                </p>
                <p className={styles.resultMeta}>
                  {experimental.data.target} · experimento {experimental.data.experiment_id} ·
                  {experimental.data.estimated_proxy_total_cop != null &&
                    ` total orientativo del proxy: ${formatCop(experimental.data.estimated_proxy_total_cop)}`}
                </p>
                {experimental.data.warnings.length > 0 && (
                  <ul className={styles.warnings}>
                    {experimental.data.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                )}
                <Disclaimer title="Qué significa este número">
                  <p>
                    COP/ha = pesos colombianos por hectárea del <em>proxy</em>. Es una
                    estimación experimental de un avalúo catastral total por hectárea;
                    <strong> no es el valor del suelo</strong> y no debe usarse como
                    avalúo ni como referencia comercial.
                  </p>
                </Disclaimer>
              </div>
            )}
      </section>
      )}

      <p className={`mono ${styles.conceptTag}`}>
        Avalúo oficial · no emitido por este software
      </p>
      <p className={styles.expNote}>
        Atlas Vivo no expide avalúos catastrales ni valoraciones comerciales. Todo
        valor mostrado es un dato de referencia o una estimación experimental de
        apoyo académico.
      </p>
    </div>
  )
}
