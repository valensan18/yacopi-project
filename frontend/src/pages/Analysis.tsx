import { useQuery } from '@tanstack/react-query'
import Plot from 'react-plotly.js'
import { apiGet } from '../api/client'
import type { OverviewStats } from '../api/types'
import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import HelpTip from '../components/HelpTip'
import { ErrorState, LoadingSkeleton } from '../components/states'
import { formatInt, formatNumber } from '../lib/format'
import styles from './Analysis.module.css'

interface DistributionResponse {
  field: string
  bins: { rango?: string; valor?: string; n: number }[]
  dataset_version: string
}

const PLOT_FONT = {
  family: 'Public Sans Variable, sans-serif',
  color: '#f4efe6',
  size: 13,
}

const BASE_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: PLOT_FONT,
  margin: { l: 8, r: 8, t: 8, b: 8 },
  showlegend: false,
}

const PLOT_CONFIG = { displayModeBar: false, responsive: true }

function ChartSection({
  title,
  unit,
  source,
  summary,
  help,
  children,
}: {
  title: string
  unit: string
  source: string
  summary: string
  help: string
  children: React.ReactNode
}) {
  return (
    <section className={styles.chartSection}>
      <h2 className={styles.chartTitle}>
        {title}{' '}
        <HelpTip label={`Cómo interpretar: ${title}`}>{help}</HelpTip>
      </h2>
      <div className={styles.chart} role="img" aria-label={summary}>
        {children}
      </div>
      <p className={styles.chartMeta}>
        <span className="mono">{unit}</span>
        <span className={styles.chartSource}>{source}</span>
      </p>
      <p className={styles.chartSummary}>{summary}</p>
    </section>
  )
}

export default function Analysis() {
  const overview = useQuery<OverviewStats>({
    queryKey: ['overview'],
    queryFn: () => apiGet<OverviewStats>('/statistics/overview'),
    staleTime: 5 * 60_000,
  })

  const areas = useQuery<DistributionResponse>({
    queryKey: ['distribution', 'area_terreno_catastral_m2'],
    queryFn: () =>
      apiGet<DistributionResponse>('/statistics/distributions', {
        field: 'area_terreno_catastral_m2',
      }),
    staleTime: 5 * 60_000,
  })

  if (overview.isLoading || areas.isLoading) {
    return (
      <div className="container">
        <PageHeader kicker="Análisis" title="Datos" lede="Exploración estadística con datos reales." />
        <LoadingSkeleton label="Calculando distribuciones reales…" />
      </div>
    )
  }

  if (overview.isError || areas.isError) {
    return (
      <div className="container">
        <PageHeader kicker="Análisis" title="Datos" lede="Exploración estadística con datos reales." />
        <ErrorState
          message="No se pudieron cargar las estadísticas desde la API."
          onRetry={() => {
            overview.refetch()
            areas.refetch()
          }}
        />
      </div>
    )
  }

  const data = overview.data!
  const areaData = areas.data!
  const total = data.total_predios

  const destinoBars = {
    type: 'bar' as const,
    orientation: 'h' as const,
    x: data.por_destino_economico.map((d) => d.n).reverse(),
    y: data.por_destino_economico.map((d) => d.key).reverse(),
    marker: { color: '#2f6b52' },
  }

  const subzonaBars = {
    type: 'bar' as const,
    orientation: 'h' as const,
    x: data.por_subzona.map((s) => s.n).reverse(),
    y: data.por_subzona.map((s) => `Subzona ${s.key}`).reverse(),
    marker: { color: '#c97b4a' },
  }

  const areaBars = {
    type: 'bar' as const,
    x: areaData.bins.map((b) => b.rango ?? b.valor ?? ''),
    y: areaData.bins.map((b) => b.n),
    marker: { color: '#1e4d3b' },
  }

  const constructionDonut = {
    type: 'pie' as const,
    labels: ['Sin construcción registrada', 'Con construcción registrada'],
    values: [data.sin_construccion, data.con_construccion],
    hole: 0.62,
    marker: {
      colors: ['#1e4d3b', '#e8b44f'],
    },
    textinfo: 'label+percent' as const,
    textfont: { color: '#f4efe6', size: 12 },
  }

  const pctCoords = total ? (data.predios_con_coordenadas / total) * 100 : 0
  const pctAlerts = total ? (data.con_alertas_calidad / total) * 100 : 0

  return (
    <div className="container">
      <PageHeader
        kicker="Análisis · Ciencia"
        title="Territorio en datos"
        lede="Estadísticas descriptivas calculadas por la API sobre los 7.709 predios consolidados. Estas cifras describen la muestra real; no son resultados de aprendizaje automático."
      />

      <div className={styles.grid}>
        <ChartSection
          title="Predios por destino económico"
          help="Cada barra cuenta los predios de cada categoría económica registrada en la fuente. No es un valor económico: solo muestra cuántos predios hay por destino."
          unit="Predios (conteo)"
          source={`API · /statistics/overview · ${data.dataset_version}`}
          summary={`El destino Agropecuario concentra ${formatInt(data.por_destino_economico[0]?.n ?? 0)} de los ${formatInt(total)} predios, seguido de ${formatInt(data.por_destino_economico[1]?.n ?? 0)} predios ${data.por_destino_economico[1]?.key ?? ''}.`}
        >
          <Plot
            data={[destinoBars]}
            layout={{ ...BASE_LAYOUT, height: 340, xaxis: { showgrid: false }, yaxis: { automargin: true } }}
            config={PLOT_CONFIG}
            style={{ width: '100%' }}
          />
        </ChartSection>

        <ChartSection
          title="Predios por subzona"
          help="Muestra cu?ntos predios caen en cada subzona geoecon?mica. Sirve para ver c?mo se reparte el territorio estudiado."
          unit="Predios (conteo)"
          source={`API · /statistics/overview · ${data.dataset_version}`}
          summary={`Las subzonas con más registros son 14 (${formatInt(data.por_subzona[0]?.n ?? 0)}) y 05 (${formatInt(data.por_subzona[1]?.n ?? 0)}).`}
        >
          <Plot
            data={[subzonaBars]}
            layout={{ ...BASE_LAYOUT, height: 300, xaxis: { showgrid: false }, yaxis: { automargin: true } }}
            config={PLOT_CONFIG}
            style={{ width: '100%' }}
          />
        </ChartSection>

        <ChartSection
          title="Distribución del área catastral del terreno"
          help="El eje horizontal agrupa los predios por rango de tamaño en hectáreas y el vertical cuenta cuántos hay en cada rango. Permite ver si predominan predios pequeños o grandes."
          unit="Rangos de área (ha)"
          source={`API · /statistics/distributions · ${areaData.dataset_version}`}
          summary={`El área mediana de los predios es de ${formatNumber((data.area.media_m2 ?? 0) / 10_000)} ha; el predio más grande registra ${formatNumber((data.area.max_m2 ?? 0) / 10_000)} ha.`}
        >
          <Plot
            data={[areaBars]}
            layout={{ ...BASE_LAYOUT, height: 320, xaxis: { tickangle: -40, automargin: true }, yaxis: { showgrid: false } }}
            config={PLOT_CONFIG}
            style={{ width: '100%' }}
          />
        </ChartSection>

        <ChartSection
          title="Predios con construcción registrada"
          help="Proporción de predios con superficie construida registrada. Es relevante porque el avalúo total no puede leerse como valor exclusivo del suelo."
          unit="Predios (proporción)"
          source={`API · /statistics/overview · ${data.dataset_version}`}
          summary={`${formatInt(data.con_construccion)} predios (${formatNumber((data.con_construccion / total) * 100)} %) registran superficie construida: por eso el avalúo total no puede tratarse como valor exclusivo del suelo.`}
        >
          <Plot
            data={[constructionDonut]}
            layout={{ ...BASE_LAYOUT, height: 300, showlegend: true, legend: { orientation: 'h', y: -0.15 } }}
            config={PLOT_CONFIG}
            style={{ width: '100%' }}
          />
        </ChartSection>
      </div>

      <section className={styles.coverage}>
        <h2 className={styles.chartTitle}>Cobertura y calidad</h2>
        <div className={styles.coverageGrid}>
          <div className={styles.coverageCard}>
            <p className={styles.coverageValue}>{formatNumber(pctCoords)} %</p>
            <p className={styles.coverageLabel}>Predios con coordenadas referenciales</p>
            <p className="mono">{formatInt(data.predios_con_coordenadas)} / {formatInt(total)}</p>
          </div>
          <div className={styles.coverageCard}>
            <p className={styles.coverageValue}>{formatNumber(pctAlerts)} %</p>
            <p className={styles.coverageLabel}>Predios con al menos una alerta de calidad</p>
            <p className="mono">{formatInt(data.con_alertas_calidad)} / {formatInt(total)}</p>
          </div>
          <div className={styles.coverageCard}>
            <p className={styles.coverageValue}>{formatNumber((data.area.total_m2 ?? 0) / 10_000)} ha</p>
            <p className={styles.coverageLabel}>Área catastral acumulada declarada</p>
            <p className="mono">suma de superficies</p>
          </div>
        </div>
      </section>

      <Disclaimer title="Estadística descriptiva, no resultado de ML">
        <p>
          Todo lo anterior describe la muestra real del estudio. Ningún gráfico de esta
          pantalla es una predicción ni una métrica del modelo: los resultados de
          aprendizaje automático se presentan aparte, en la pantalla Modelos.
        </p>
      </Disclaimer>
    </div>
  )
}
