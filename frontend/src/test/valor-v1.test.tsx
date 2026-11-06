import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Prediction from '../pages/Prediction'

const statusFixture = {
  data_status: 'audited_and_curated',
  dataset_version: 'dataset-v1',
  model_status: 'label_pending',
  model_ready: false,
  target_unit: 'COP/ha',
  experimental_model: { disponible: false, habilitado: false },
  experimental_zhg: { habilitado: false, disponible: false },
  valor_v1: { habilitado: true, disponible: true, model_id: 'atlas-vivo-rf-v1', model_version: '1.0.0' },
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

function renderPrediction(entry?: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry ?? '/prediccion']}>
        <Prediction />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function mockFetch(routes: Record<string, unknown>) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes('/predictions/valor-terreno-v1')) {
      const payload = routes['/predictions/valor-terreno-v1']
      const esError = (payload as { error?: unknown })?.error != null
      return new Response(JSON.stringify(payload), {
        status: esError ? 503 : 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    for (const [needle, payload] of Object.entries(routes).sort(
      (a, b) => b[0].length - a[0].length,
    )) {
      if (url.endsWith(needle)) {
        return new Response(JSON.stringify(payload), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
    }
    return new Response('{}', { status: 404 })
  }) as unknown as typeof fetch
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Estimación catastral con inteligencia artificial (RF v1)', () => {
  it('muestra indisponibilidad clara cuando el flag está apagado', async () => {
    mockFetch({
      '/system/status': { ...statusFixture, valor_v1: { habilitado: false, disponible: false } },
    })
    renderPrediction()
    await waitFor(() => {
      expect(screen.getByText('VALOR_V1_ENABLED=false')).toBeInTheDocument()
    })
    expect(screen.getByText(/no está habilitado en este entorno/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Consultar estimación/ })).toBeDisabled()
  })

  it('estima y muestra la referencia ZHG separada de la predicción', async () => {
    mockFetch({
      '/system/status': statusFixture,
      '/predictions/valor-terreno-v1': valorV1Fixture,
    })
    const user = userEvent.setup()
    renderPrediction()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Consultar estimación/ })).toBeEnabled()
    })
    const input = screen.getByLabelText(/Identificador público del predio/, {
      selector: '#valor-v1-id',
    })
    await user.type(input, 'p_abc123')
    await user.click(screen.getByRole('button', { name: /Consultar estimación/ }))
    await waitFor(() => {
      expect(screen.getByText(/505\.000 COP\/ha/)).toBeInTheDocument()
    })
    expect(screen.getByText(/atlas-vivo-rf-v1/)).toBeInTheDocument()
    expect(screen.getByText('Referencia ZHG (dato territorial)')).toBeInTheDocument()
    expect(screen.getByText(/456\.042 COP\/ha/)).toBeInTheDocument()
    expect(screen.getByText(/pertenece al inventario con el que se ajustó el modelo/)).toBeInTheDocument()
    expect(screen.getByText(/ganó en MAE 0\/5/)).toBeInTheDocument()
    expect(screen.getByText(/No existe todavía un modelo definitivo aprobado/)).toBeInTheDocument()
  })

  it('muestra el error 503 de indisponibilidad del servicio', async () => {
    mockFetch({
      '/system/status': statusFixture,
      '/predictions/valor-terreno-v1': {
        error: {
          code: 'VALOR_V1_UNAVAILABLE',
          message: 'El artefacto del modelo RF v1 no está disponible o no superó la verificación de integridad',
        },
      },
    })
    const user = userEvent.setup()
    renderPrediction()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Consultar estimación/ })).toBeEnabled()
    })
    const input = screen.getByLabelText(/Identificador público del predio/, {
      selector: '#valor-v1-id',
    })
    await user.type(input, 'p_abc123')
    await user.click(screen.getByRole('button', { name: /Consultar estimación/ }))
    await waitFor(() => {
      expect(screen.getByText(/503 VALOR_V1_UNAVAILABLE/)).toBeInTheDocument()
    })
    expect(screen.getByText(/no está disponible en este entorno en este momento/)).toBeInTheDocument()
  })

  it('consulta automáticamente al llegar con ?public_id=', async () => {
    mockFetch({
      '/system/status': statusFixture,
      '/predictions/valor-terreno-v1': valorV1Fixture,
    })
    renderPrediction('/prediccion?public_id=p_abc123')
    await waitFor(() => {
      expect(screen.getByText(/505\.000 COP\/ha/)).toBeInTheDocument()
    })
    expect(screen.getByText(/atlas-vivo-rf-v1/)).toBeInTheDocument()
    expect(screen.getByText(/pertenece al inventario con el que se ajustó el modelo/)).toBeInTheDocument()
  })

  it('no renderiza los apartados antiguos', async () => {
    mockFetch({ '/system/status': statusFixture })
    renderPrediction()
    await waitFor(() => {
      expect(screen.getByText('Estimación catastral con inteligencia artificial')).toBeInTheDocument()
    })
    expect(screen.queryByText(/503 MODEL_NOT_READY/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Consulta de referencia de valor/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Demostración experimental \(zonas conocidas\)/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Simulador/)).not.toBeInTheDocument()
  })
})
