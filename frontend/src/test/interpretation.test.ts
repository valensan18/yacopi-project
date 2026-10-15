import { describe, expect, it } from 'vitest'

import type { ZhgDemoResponse, ZhgReferenceResponse } from '../api/types'
import {
  domainLabel,
  interpretCoverage,
  interpretDemo,
  interpretFlags,
  interpretZones,
} from '../lib/interpretation'

const monozona: ZhgReferenceResponse = {
  public_id: 'p_x',
  unit: 'COP/ha',
  reference_type: 'zhg_zonal_reference',
  zones: [{ zone_code: '07', value_cop_ha: 456041.7, area_intersection_m2: 50000, share_pct: 100 }],
  dominant_zone: { zone_code: '07', value_cop_ha: 456041.7, share_pct: 100, note: 'zona predominante' },
  weighted_reference: null,
  provisional_weighted_reference: null,
  coverage_status: 'consistente',
  source_description: '…',
  reference_date: null,
  limitations: [],
}

describe('interpretaciones contextuales', () => {
  it('monozona: explica la referencia real sin presentarla como avalúo', () => {
    const lines = interpretZones(monozona)
    const joined = lines.join(' ')
    expect(joined).toContain('456.042')
    expect(joined).toContain('zona geoeconómica 07')
    expect(joined).toContain('no significa que el predio completo tenga ese precio')
  })

  it('multizona: advierte que no es adecuado un único valor', () => {
    const multi: ZhgReferenceResponse = {
      ...monozona,
      zones: [
        { zone_code: '02', value_cop_ha: 1824156.1, area_intersection_m2: 1000, share_pct: 12.63 },
        { zone_code: '07', value_cop_ha: 456041.7, area_intersection_m2: 7000, share_pct: 87.37 },
      ],
    }
    const lines = interpretZones(multi)
    expect(lines.join(' ')).toContain('2 zonas geoeconómicas')
    expect(lines.join(' ')).toContain('No necesariamente es adecuado utilizar un único valor')
  })

  it('cobertura no apta: explica la ausencia de consolidación', () => {
    expect(interpretCoverage('no_apta')).toContain('más del 5 %')
    expect(interpretCoverage('no_apta')).toContain('no muestra cálculos de consolidación')
  })

  it('banderas: explica la inconsistencia de áreas', () => {
    const lines = interpretFlags(['area_geometrica_zhg_difiere_mas_5pct_zhf'])
    expect(lines[0]).toContain('no coinciden suficientemente')
  })

  it('demo: destaca ajuste y ausencia de evaluación independiente', () => {
    const demo: ZhgDemoResponse = {
      public_id: 'p_x',
      model_id: 'exp-zhg-001-demo',
      model_status: 'experimental',
      unit: 'COP/ha',
      target_description: '…',
      reference_zhg_cop_ha: 456041.7,
      predicted_zhg_cop_ha: 462619.97,
      absolute_difference_cop_ha: 6578.27,
      relative_difference_pct: 1.44,
      zone_code: '07',
      domain_status: 'in_domain',
      source_description: '…',
      reference_date: null,
      limitations: [],
      evaluation_context: {},
      disclaimer: '…',
    }
    const interp = interpretDemo(demo)
    expect(interp.destacadas[0]).toContain('participó en el ajuste')
    expect(interp.destacadas[0]).toContain('no es una evaluación independiente')
    expect(interp.complemento).toContain('462.620')
    expect(interp.complemento).toContain('6.578')
    expect(interp.complemento).toContain('no demuestra que vaya a acertar en terrenos nuevos')
  })

  it('traduce in_domain a lenguaje humano', () => {
    expect(domainLabel('in_domain')).toContain('dentro de los rangos y categorías admitidos')
    expect(domainLabel('in_domain')).toContain('no significa precisión garantizada')
    expect(domainLabel('otro')).toBe('otro')
  })
})
