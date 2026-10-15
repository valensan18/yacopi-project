import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import Glossary from '../pages/Glossary'
import HelpTip from '../components/HelpTip'

describe('Glosario', () => {
  it('muestra términos y filtra por búsqueda', async () => {
    render(
      <MemoryRouter>
        <Glossary />
      </MemoryRouter>,
    )
    expect(screen.getByText('Predio')).toBeInTheDocument()
    expect(screen.getByText('MAE')).toBeInTheDocument()

    const search = screen.getByLabelText('Buscar término')
    await userEvent.type(search, 'avalúo catastral')
    await waitFor(() => {
      expect(screen.getByText('Avalúo catastral')).toBeInTheDocument()
    })
    expect(screen.queryByText('MAE')).not.toBeInTheDocument()
  })

  it('filtra por categoría', async () => {
    render(
      <MemoryRouter>
        <Glossary />
      </MemoryRouter>,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Estadística y aprendizaje automático' }))
    expect(screen.getByText('Random Forest (bosque aleatorio)')).toBeInTheDocument()
    expect(screen.queryByText('Predio')).not.toBeInTheDocument()
  })
})

describe('HelpTip (accesibilidad)', () => {
  it('se abre y cierra con teclado y anuncia estado', async () => {
    render(
      <HelpTip label="Explicación de ejemplo">
        Contenido de la ayuda.
      </HelpTip>,
    )
    const button = screen.getByRole('button', { name: 'Explicación de ejemplo' })
    expect(button).toHaveAttribute('aria-expanded', 'false')

    button.focus()
    await userEvent.keyboard('{Enter}')
    expect(button).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Contenido de la ayuda.')).toBeInTheDocument()

    await userEvent.keyboard('{Escape}')
    await waitFor(() => {
      expect(button).toHaveAttribute('aria-expanded', 'false')
    })
  })
})
