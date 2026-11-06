import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const overviewFixture = {
  total_predios: 7709,
  con_construccion: 3033,
  predios_con_coordenadas: 7694,
  area: { total_m2: 123456789 },
  dataset_version: 'dataset-v1',
}

const statusFixture = {
  data_status: 'audited_and_curated',
  dataset_version: 'dataset-v1',
  model_status: 'label_pending',
  model_ready: false,
  target_unit: 'COP/ha',
  experimental_model: { disponible: false, habilitado: false },
  reason: 'etiqueta pendiente',
  public_notice: 'Información académica',
}

const pointsFixture = { type: 'FeatureCollection', features: [] }

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.includes('/statistics/overview')
        ? overviewFixture
        : url.includes('/system/status')
          ? statusFixture
          : url.includes('/maps/points')
            ? pointsFixture
            : {}
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }),
  )
})

describe('ATLAS VIVO — portada (Fase 4)', () => {
  it('renderiza el título de la marca', () => {
    renderApp()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('ATLAS')
  })

  it('no muestra el banner de modelo pendiente de validación (retirado)', async () => {
    renderApp()
    await waitFor(() => {
      expect(screen.getAllByText(/ATLAS VIVO/).length).toBeGreaterThan(0)
    })
    expect(screen.queryByText(/Modelo predictivo pendiente de validación/)).not.toBeInTheDocument()
  })

  it('usa el fallback 2D cuando no hay WebGL', async () => {
    renderApp()
    await waitFor(() => {
      expect(screen.getByText(/Vista 2D de respaldo/)).toBeInTheDocument()
    })
  })

  it('muestra el aviso metodológico del modelo experimental', () => {
    renderApp()
    expect(screen.getByText('Aviso metodológico')).toBeInTheDocument()
  })

  it('no muestra números de predios inventados sin datos cargados', async () => {
    renderApp()
    await waitFor(() => {
      const kpi = screen.getByText('Predios consolidados')
      expect(kpi).toBeInTheDocument()
    })
  })
})
