import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Parcels from '../pages/Parcels'
import ParcelDetail from '../pages/ParcelDetail'
import Models from '../pages/Models'
import Prediction from '../pages/Prediction'
import Methodology from '../pages/Methodology'

const statusFixture = {
  data_status: 'audited_and_curated',
  dataset_version: 'dataset-v1',
  model_status: 'label_pending',
  model_ready: false,
  target_unit: 'COP/ha',
  experimental_model: { disponible: false, habilitado: false },
  experimental_zhg: { habilitado: false, disponible: false },
  reason: 'etiqueta pendiente',
  public_notice: 'Información académica',
}

const valorV1Fixture = {
  public_id: 'p_abc123',
  model_id: 'atlas-vivo-rf-v1',
  model_version: '1.0.0',
  model_role: 'demostracion_academica',
  target: 'VALOR_TERRENO_Ha',
  target_description: 'valor catastral unitario derivado del avalúo total',
  unit: 'COP/ha',
  predicted_cop_ha: 505000,
  reference_zhg_cop_ha: 456041.7,
  reference_zhg_note: 'Referencia geoeconómica ZHG consultada de los datos',
  absolute_difference_vs_zhg_cop_ha: 48958.3,
  relative_difference_vs_zhg_pct: 10.74,
  zone_code: '07',
  applicability_status: 'admitted',
  applicability_conditions: ['Predio sin construcción registrada (escenario A).'],
  evaluation_context: {
    test_sellado_v2_espacial: {
      n: 689,
      rf: { mae_cop_ha: 767064.08, mdape: 0.1169, r2: 0.171 },
      referencia_zhg: { mae_cop_ha: 817030.0, mdape: 0.0565 },
    },
    estabilidad_5_pliegues_espaciales: {
      rf_gana_mae_en: 0,
      rf_gana_mdape_en: 0,
      rf_mae_mediana: 259000,
      zhg_mae_mediana: 197000,
      rf_mdape_mediana: 0.2,
      zhg_mdape_mediana: 0.054,
    },
  },
  reference_date: null,
  limitations: [
    'Demostración académica: el modelo no superó a la referencia ZHG en MAE ni MdAPE.',
    'No existe todavía un modelo definitivo aprobado.',
  ],
  disclaimer: 'Estimación orientativa de valor catastral unitario. No constituye un avalúo.',
}

const overviewFixture = {
  total_predios: 7709,
  por_destino_economico: [
    { key: 'Agropecuario', n: 6746 },
    { key: 'Religioso', n: 627 },
  ],
  por_subzona: [{ key: '14', n: 3554 }],
  con_construccion: 3033,
  sin_construccion: 4676,
  con_alertas_calidad: 6492,
  area: { total_m2: 100_000_000, media_m2: 12975.5, min_m2: 10, max_m2: 500_000, n: 7709 },
  predios_con_coordenadas: 7694,
  dataset_version: 'dataset-v1',
}

const parcelsFixture = {
  items: [
    {
      public_id: 'p_abc123',
      destino_economico: 'Agropecuario',
      area_terreno_catastral_m2: 50000,
      area_zhf_m2: 51000,
      area_construida_m2: 0,
      latitud: 5.55,
      longitud: -74.35,
      subzona: '05',
      coincide_zhf: 1,
      cantidad_intersecciones: 1,
      cantidad_zonas_zhg: 1,
      tiene_alertas_calidad: false,
      n_alertas_calidad: 0,
    },
  ],
  pagination: { limit: 20, offset: 0, total: 7709 },
  dataset_version: 'dataset-v1',
  public_notice: 'aviso',
}

const detailFixture = {
  item: {
    ...parcelsFixture.items[0],
    area_zhf_m2: null,
    latitud: null,
    longitud: null,
    features: { zhf_codigo: '05', clc_nivel1: '2. Territorios Agrícolas' },
    quality_flags: ['contiene_construccion'],
  },
  dataset_version: 'dataset-v1',
  public_notice: 'aviso',
}

const modelsFixture = {
  models: [
    {
      experiment_id: 'exp-proxy-001',
      modelo: 'forest',
      mae_test_espacial_cop_ha: 3226230,
      r2_test_espacial: 0.74,
      etiqueta: 'proxy_avaluo_total_cop_ha',
      status: 'experimental',
      production_eligible: false,
    },
  ],
  official_model: null,
  label_status: 'pending_verification',
  disclaimer: 'Modelos experimentales',
}

const zhgReferenceFixture = {
  public_id: 'p_abc123',
  unit: 'COP/ha',
  reference_type: 'zhg_zonal_reference',
  zones: [
    { zone_code: '03', value_cop_ha: 1368119.6, area_intersection_m2: 25000, share_pct: 50 },
    { zone_code: '06', value_cop_ha: 547247.2, area_intersection_m2: 25000, share_pct: 50 },
  ],
  dominant_zone: {
    zone_code: '06',
    value_cop_ha: 547247.2,
    share_pct: 50,
    note: 'zona con mayor participación del predio; no representa automáticamente el valor unitario de toda la propiedad cuando hay varias zonas',
  },
  weighted_reference: null,
  provisional_weighted_reference: {
    value_cop_ha: 957683.4,
    coverage_status: 'dudosa',
    status_label: 'cálculo PROVISIONAL (cobertura dudosa 1–5 %): no es una consolidación validada',
  },
  coverage_status: 'dudosa',
  source_description: 'valor_hectarea_agropecuario = ZHG_VALOR_ por zona',
  reference_date: null,
  limitations: [
    'Referencia zonal catastral; no es un avalúo individual certificado del predio.',
    'No es una predicción de aprendizaje automático.',
  ],
}

function mockFetch(routes: Record<string, unknown>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      const ordered = Object.entries(routes).sort(
        (a, b) => b[0].length - a[0].length,
      )
      // prefiero la coincidencia más específica (sufijo exacto de la URL)
      for (const [needle, payload] of ordered) {
        if (url.endsWith(needle)) {
          const esError = (payload as { error?: unknown }).error != null
          return new Response(JSON.stringify(payload), {
            status: esError ? 422 : 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
      }
      for (const [needle, payload] of ordered) {
        if (url.includes(needle)) {
          const esError = (payload as { error?: unknown }).error != null
          return new Response(JSON.stringify(payload), {
            status: esError ? 422 : 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
      }
      return new Response('{}', { status: 404 })
    }),
  )
}

function renderAt(pattern: string, element: React.ReactNode, entry?: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry ?? pattern]}>
        <Routes>
          <Route path={pattern} element={element} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Pantalla Predios', () => {
  it('muestra el total real y filas de la API', async () => {
    mockFetch({ '/statistics/overview': overviewFixture, '/properties': parcelsFixture })
    renderAt('/predios', <Parcels />)
    await waitFor(() => {
      expect(screen.getByText(/7.709 predios/)).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('p_abc123')).toBeInTheDocument()
      expect(screen.getByText(/de 7.709 predios/)).toBeInTheDocument()
    })
  })
})

describe('Pantalla Detalle de predio', () => {
  it('representa nulos como No disponible y muestra la referencia ZHG', async () => {
    mockFetch({
      '/properties/p_abc123': detailFixture,
      '/zhg-reference': zhgReferenceFixture,
    })
    renderAt('/predios/:public_id', <ParcelDetail />, '/predios/p_abc123')
    await waitFor(() => {
      expect(screen.getAllByText('p_abc123').length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText('No disponible').length).toBeGreaterThan(0)
    expect(screen.getByText('Registra superficie construida')).toBeInTheDocument()
    expect(screen.queryByText('contiene_construccion')).not.toBeInTheDocument()
    await waitFor(() => {
      expect(
        screen.getByText('Valor unitario de referencia del suelo'),
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/PROVISIONAL/)).toBeInTheDocument()
    expect(screen.getByText('dato · no predicción')).toBeInTheDocument()
  })
})

describe('Pantalla Modelos', () => {
  it('muestra estado pendiente y el experimento real', async () => {
    mockFetch({ '/system/status': statusFixture, '/models': modelsFixture })
    renderAt('/modelos', <Models />)
    await waitFor(() => {
      expect(screen.getByText('label_pending')).toBeInTheDocument()
    })
    expect(screen.getByText('exp-proxy-001')).toBeInTheDocument()
    expect(screen.getAllByText(/Random Forest/).length).toBeGreaterThan(0)
    expect(screen.getByText(/3.226.230 COP\/ha/)).toBeInTheDocument()
  })
})

describe('Pantalla Predicción', () => {
  it('muestra el modelo desactivado cuando el flag está apagado, sin apartados antiguos', async () => {
    mockFetch({ '/system/status': statusFixture })
    renderAt('/prediccion', <Prediction />)
    await waitFor(() => {
      expect(screen.getByText('VALOR_V1_ENABLED=false')).toBeInTheDocument()
    })
    expect(screen.getByText('Estimación catastral con inteligencia artificial')).toBeInTheDocument()
    expect(screen.getByText(/no está habilitado en este entorno/)).toBeInTheDocument()
    expect(screen.queryByText(/503 MODEL_NOT_READY/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Consulta de referencia de valor/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Demostración experimental \(zonas conocidas\)/)).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /Consultar estimación/ }),
    ).toBeDisabled()
  })

  it('consulta una estimación real cuando el modelo está activo', async () => {
    mockFetch({
      '/system/status': {
        ...statusFixture,
        valor_v1: { habilitado: true, disponible: true, model_id: 'atlas-vivo-rf-v1', model_version: '1.0.0' },
      },
      '/predictions/valor-terreno-v1': valorV1Fixture,
      '/properties': parcelsFixture,
    })
    renderAt('/prediccion', <Prediction />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Consultar estimación/ })).toBeEnabled()
    })
    const input = screen.getByRole('combobox', { name: 'Identificador público del predio' })
    await userEvent.type(input, 'p_ab')
    const option = await screen.findByRole('option', { name: /p_abc123/ })
    await userEvent.click(option)
    await userEvent.click(screen.getByRole('button', { name: /Consultar estimación/ }))
    await waitFor(() => {
      expect(screen.getByText(/505\.000 COP\/ha/)).toBeInTheDocument()
    })
    expect(screen.getByText(/atlas-vivo-rf-v1/)).toBeInTheDocument()
    expect(screen.getByText('Referencia ZHG (dato territorial)')).toBeInTheDocument()
    expect(screen.getByText(/456\.042 COP\/ha/)).toBeInTheDocument()
    expect(screen.getByText(/Diferencia de la estimación frente a la referencia/)).toBeInTheDocument()
    expect(screen.getByText(/pertenece al inventario con el que se ajustó el modelo/)).toBeInTheDocument()
  })

  it('muestra el motivo cuando el predio no cumple las condiciones', async () => {
    mockFetch({
      '/system/status': {
        ...statusFixture,
        valor_v1: { habilitado: true, disponible: true, model_id: 'atlas-vivo-rf-v1', model_version: '1.0.0' },
      },
      '/predictions/valor-terreno-v1': {
        error: {
          code: 'UNSUPPORTED_PARCEL',
          message: 'El predio no tiene características compatibles',
          details: { razon: 'el predio registra construcción; la demostración solo admite el escenario A (construcción = 0)' },
        },
      },
      '/properties': parcelsFixture,
    })
    renderAt('/prediccion', <Prediction />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Consultar estimación/ })).toBeEnabled()
    })
    const input = screen.getByRole('combobox', { name: 'Identificador público del predio' })
    await userEvent.type(input, 'p_ab')
    const option = await screen.findByRole('option', { name: /p_abc123/ })
    await userEvent.click(option)
    await userEvent.click(screen.getByRole('button', { name: /Consultar estimación/ }))
    await waitFor(() => {
      expect(screen.getByText(/422 UNSUPPORTED_PARCEL/)).toBeInTheDocument()
    })
    expect(screen.getByText(/no cumple las condiciones de aplicación/)).toBeInTheDocument()
    expect(screen.getByText(/el predio registra construcción/)).toBeInTheDocument()
  })
})

describe('Pantalla Metodología', () => {
  it('presenta la ruta CRISP-DM sin datos de red', () => {
    renderAt('/metodologia', <Methodology />)
    expect(screen.getByText(/Ruta CRISP-DM/)).toBeInTheDocument()
    expect(screen.getAllByText(/7\.709/).length).toBeGreaterThan(0)
    expect(screen.getByText(/validación pendiente/i)).toBeInTheDocument()
  })
})
