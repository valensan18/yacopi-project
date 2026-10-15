import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('react-plotly.js', () => ({ default: () => null }))

import AppShell from '../components/AppShell'
import Home from '../pages/Home'
import About from '../pages/About'
import Analysis from '../pages/Analysis'
import {
  APP_DESCRIPTION_CORTA,
  APP_DESCRIPTION_EXTENDIDA,
  ESTADO_PREDICCION_OFICIAL,
  EXPERIMENTOS_HISTORICOS_DESCRIPCION,
  MODELO_EXPERIMENTAL_DESCRIPCION,
} from '../lib/appContent'

const overviewFixture = {
  total_predios: 7709,
  por_destino_economico: [{ key: 'Agropecuario', n: 6746 }],
  por_subzona: [{ key: '14', n: 3554 }],
  con_construccion: 3033,
  sin_construccion: 4676,
  con_alertas_calidad: 6492,
  area: { total_m2: 100_000_000, media_m2: 12975.5, min_m2: 10, max_m2: 500_000, n: 7709 },
  predios_con_coordenadas: 7694,
  dataset_version: 'dataset-v1',
}

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

function mockFetch(routes: Record<string, unknown>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      for (const [needle, payload] of Object.entries(routes).sort((a, b) => b[0].length - a[0].length)) {
        if (url.endsWith(needle) || url.includes(needle)) {
          return new Response(JSON.stringify(payload), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
      }
      return new Response('{}', { status: 404 })
    }),
  )
}

function renderWith(ui: React.ReactNode, entry = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Fuente centralizada y coherencia global (regresión)', () => {
  it('el footer usa la descripción centralizada actual', () => {
    mockFetch({ '/system/status': statusFixture })
    renderWith(<AppShell />)
    expect(screen.getAllByText((_, element) =>
      element?.textContent?.includes(APP_DESCRIPTION_CORTA) ?? false,
    ).length).toBeGreaterThan(0)
    expect(screen.queryByText(/proxy de avalúo catastral total por hectárea/i)).not.toBeInTheDocument()
  })

  it('la portada no presenta el proxy como modelo actual', async () => {
    mockFetch({
      '/system/status': statusFixture,
      '/statistics/overview': overviewFixture,
      '/maps/points': { type: 'FeatureCollection', features: [] },
    })
    renderWith(<Home />)
    await waitFor(() => {
      expect(screen.getByText('Aviso metodológico')).toBeInTheDocument()
    })
    expect(screen.queryByText(/proxy de avalúo catastral total por hectárea/i)).not.toBeInTheDocument()
    expect(screen.getByText(/demostración experimental de Random Forest/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Ir a la predicción/i })).toBeInTheDocument()
  })

  it('Análisis distingue sus gráficas de la predicción y enlaza Modelos y Predicción', async () => {
    mockFetch({
      '/statistics/overview': overviewFixture,
      '/statistics/distributions': {
        field: 'area_terreno_catastral_m2',
        bins: [{ rango: '<=0.5 ha', n: 100 }, { rango: '0.5-1 ha', n: 200 }],
        dataset_version: 'dataset-v1',
      },
    })
    renderWith(<Analysis />, '/exploracion')
    await waitFor(() => {
      expect(screen.getByText(/predicción ni una métrica de un modelo/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: 'Modelos' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Predicción' })).toBeInTheDocument()
  })

  it('Acerca de usa la descripción extendida centralizada', () => {
    renderWith(<About />)
    expect(screen.getAllByText((_, element) =>
      element?.textContent?.includes(APP_DESCRIPTION_EXTENDIDA) ?? false,
    ).length).toBeGreaterThan(0)
    expect(screen.queryByText(/estimula un proxy de avalúo/i)).not.toBeInTheDocument()
  })

  it('las constantes centrales distinguen los conceptos clave', () => {
    expect(MODELO_EXPERIMENTAL_DESCRIPCION).toContain('Random Forest')
    expect(MODELO_EXPERIMENTAL_DESCRIPCION).toContain('7.709')
    expect(EXPERIMENTOS_HISTORICOS_DESCRIPCION).toContain('Fase 2')
    expect(EXPERIMENTOS_HISTORICOS_DESCRIPCION).toContain('no se mezclan')
    expect(ESTADO_PREDICCION_OFICIAL).toContain('503')
    expect(APP_DESCRIPTION_CORTA).toContain('No emite avalúos individuales certificados')
  })
})
