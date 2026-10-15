/**
 * Interpretación contextual determinística (Fase 7E).
 * Genera explicaciones breves con los valores REALES del predio o resultado.
 * No es un modelo de IA: solo reglas verificables sobre los datos mostrados.
 */

import type {
  ParcelDetailItem,
  ZhgDemoResponse,
  ZhgReferenceResponse,
} from '../api/types'
import { formatArea, formatCopPerHa, formatInt, formatNumber } from './format'

export const FLAG_EXPLANATIONS: Record<string, string> = {
  sin_coincidencia_zhf:
    'Este predio no aparece en la fuente de zonas físicas (ZHF), por lo que varios de sus atributos territoriales no están disponibles.',
  multiples_intersecciones_zhg:
    'El predio se relaciona con más de una porción geoeconómica: consulta la tabla de zonas para ver cada referencia.',
  interseccion_filas_exactamente_duplicadas:
    'La fuente contiene filas repetidas para este predio; los datos se consolidaron sin duplicar el área.',
  porcentajes_zhg_no_suman_100:
    'Las participaciones de zona registradas no suman 100 % exacto; revisar la fuente.',
  suma_area_intersecciones_difiere_mas_5pct_area_catastral:
    'La suma de las porciones geográficas difiere más del 5 % del área catastral: las superficies de las fuentes no coinciden suficientemente.',
  area_zhf_difiere_mas_5pct_area_catastral:
    'El área registrada en la fuente ZHF difiere más del 5 % de la catastral: esta diferencia limita la confiabilidad de los cálculos de área.',
  area_geometrica_zhg_difiere_mas_5pct_zhf:
    'Las superficies calculadas a partir de diferentes fuentes no coinciden suficientemente. Esta diferencia limita la confiabilidad de algunos cálculos asociados al área.',
  zona_zhg_zhf_diferente_de_zhg_dominante:
    'La zona geoeconómica declarada en una fuente no coincide con la predominante calculada: conviene revisar la asignación de zona.',
  zhf_codpred_repetido:
    'El identificador aparece repetido en la fuente ZHF; se usó un registro de referencia.',
  area_catastral_no_positiva:
    'El área catastral registrada no es un valor positivo válido.',
  contiene_construccion:
    'El predio registra superficie construida: por eso el avalúo total no puede tratarse como valor exclusivo del suelo.',
}

export function interpretFlags(flags: string[]): string[] {
  if (flags.length === 0) {
    return ['Este predio no tiene alertas de calidad registradas en las fuentes.']
  }
  return flags
    .map((flag) => FLAG_EXPLANATIONS[flag] ?? `Alerta de calidad registrada (${flag}).`)
    .filter(Boolean)
}

export function interpretCoverage(coverageStatus: string | null): string {
  switch (coverageStatus) {
    case 'consistente':
      return 'Las superficies de las fuentes coinciden dentro del 1 %: la consolidación ponderada mostrada es admisible.'
    case 'dudosa':
      return 'Las superficies de las fuentes difieren entre 1 % y 5 %: cualquier cálculo ponderado se marca como provisional y no debe tomarse como valor confirmado.'
    case 'no_apta':
      return 'Las fuentes consultadas presentan diferencias importantes en las superficies registradas (más del 5 %). Por esta razón, el sistema no muestra cálculos de consolidación que podrían ser engañosos.'
    default:
      return 'No hay información de cobertura disponible para este predio.'
  }
}

export function interpretZones(reference: ZhgReferenceResponse): string[] {
  const lines: string[] = []
  if (reference.zones.length === 0) {
    return ['Este predio no tiene referencias ZHG asociadas en la base, así que no es posible interpretar un valor de referencia.']
  }

  if (reference.zones.length === 1) {
    const zone = reference.zones[0]
    lines.push(
      zone.value_cop_ha != null
        ? `El terreno se encuentra asociado a la zona geoeconómica ${zone.zone_code}, cuyo valor unitario de referencia registrado es de aproximadamente ${formatCopPerHa(zone.value_cop_ha)}. Este dato describe una referencia territorial y no significa que el predio completo tenga ese precio ni que pueda venderse por ese valor.`
        : `El terreno se asocia a la zona ${zone.zone_code}, pero su valor unitario no está disponible en la fuente.`,
    )
  } else {
    lines.push(
      `Este predio se relaciona con ${formatInt(reference.zones.length)} zonas geoeconómicas (${reference.zones.map((z) => z.zone_code).join(', ')}). Cada zona puede tener una referencia diferente. No necesariamente es adecuado utilizar un único valor sin revisar la consistencia de las superficies.`,
    )
  }

  if (reference.dominant_zone && reference.zones.length > 1) {
    lines.push(
      `La zona predominante es la ${reference.dominant_zone.zone_code}: representa la mayor participación dentro de las intersecciones registradas, no el valor de toda la propiedad.`,
    )
  }

  lines.push(interpretCoverage(reference.coverage_status))
  return lines
}

export function interpretGeneral(item: ParcelDetailItem): string[] {
  const lines: string[] = []
  lines.push(
    `Este predio está clasificado con destino económico «${item.destino_economico ?? 'No disponible'}» y registra un área catastral de ${formatArea(item.area_terreno_catastral_m2)}.`,
  )
  if (item.area_construida_m2 != null && item.area_construida_m2 > 0) {
    lines.push(
      `Registra ${formatArea(item.area_construida_m2)} de superficie construida: por eso ningún valor total disponible puede leerse como valor exclusivo del suelo.`,
    )
  }
  if (item.latitud != null && item.longitud != null) {
    lines.push('El predio cuenta con coordenadas referenciales, por lo que puede ubicarse en el mapa.')
  } else {
    lines.push('Este predio no tiene coordenadas disponibles en las fuentes: no se puede mostrar su ubicación en el mapa.')
  }
  return lines
}

export interface DemoInterpretation {
  destacadas: string[]
  complemento: string
}

export function interpretDemo(body: ZhgDemoResponse): DemoInterpretation {
  const destacadas: string[] = []
  destacadas.push(
    'Este predio participó en el ajuste del modelo experimental. La diferencia mostrada no es una evaluación independiente de exactitud.',
  )
  destacadas.push('El resultado no constituye un avalúo certificado ni reemplaza la referencia ZHG.')

  const ref = body.reference_zhg_cop_ha
  const est = body.predicted_zhg_cop_ha
  const diff = body.absolute_difference_cop_ha
  const sign = diff > 0 ? 'por encima' : diff < 0 ? 'por debajo' : 'prácticamente igual a'
  const complemento =
    `El modelo calculó ${formatCopPerHa(est)} para este predio, ${sign} la referencia zonal conocida (${formatCopPerHa(ref)}). ` +
    `La diferencia es de ${formatCopPerHa(diff)}${body.relative_difference_pct != null ? ` (${formatNumber(body.relative_difference_pct)} %)` : ''}. ` +
    'Comparar ambos resultados ayuda a entender cómo responde el modelo en este caso, pero no demuestra que vaya a acertar en terrenos nuevos.'
  return { destacadas, complemento }
}

export function domainLabel(status: string): string {
  switch (status) {
    case 'in_domain':
      return 'Los datos del predio están dentro de los rangos y categorías admitidos por la demostración experimental. Esto no significa precisión garantizada ni validación independiente.'
    default:
      return status
  }
}
