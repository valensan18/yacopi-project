export interface ExperimentalModelInfo {
  disponible: boolean
  habilitado: boolean
  experiment_id?: string
  modelo?: string
  mae_test_espacial_cop_ha?: number
  r2_test_espacial?: number
  target?: string
  es_etiqueta_oficial?: boolean
}

export interface ExperimentalZhgInfo {
  habilitado: boolean
  disponible: boolean
  model_id?: string
}

export interface SystemStatus {
  data_status: string
  dataset_version: string | null
  model_status: string
  model_ready: boolean
  target_unit: string
  experimental_model: ExperimentalModelInfo
  experimental_zhg?: ExperimentalZhgInfo
  reason: string
  public_notice: string
}

export interface AreaStats {
  n: number
  min_m2: number | null
  max_m2: number | null
  media_m2: number | null
  total_m2: number | null
}

export interface OverviewStats {
  total_predios: number
  por_destino_economico: { key: string; n: number }[]
  por_subzona: { key: string; n: number }[]
  con_construccion: number
  sin_construccion: number
  con_alertas_calidad: number
  area: AreaStats
  predios_con_coordenadas: number
  dataset_version: string
}

export interface MapPointFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: {
    public_id: string
    destino_economico: string | null
    subzona: string | null
  }
}

export interface MapPoints {
  type: 'FeatureCollection'
  crs: { type: string; properties: { name: string } }
  features: MapPointFeature[]
  aviso: string
}

export interface ParcelSummary {
  public_id: string
  destino_economico: string | null
  area_terreno_catastral_m2: number | null
  area_zhf_m2: number | null
  area_construida_m2: number | null
  latitud: number | null
  longitud: number | null
  subzona: string | null
  coincide_zhf: number
  cantidad_intersecciones: number | null
  cantidad_zonas_zhg: number | null
  tiene_alertas_calidad: boolean
  n_alertas_calidad: number
}

export interface ParcelPage {
  items: ParcelSummary[]
  pagination: { limit: number; offset: number; total: number }
  dataset_version: string
  public_notice: string
}

export interface ParcelDetailItem extends ParcelSummary {
  features: Record<string, string | null>
  quality_flags: string[]
}

export interface ParcelDetailResponse {
  item: ParcelDetailItem
  dataset_version: string
  public_notice: string
}

export interface ApiErrorPayload {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    request_id?: string
  }
}

export interface ZoneReferenceItem {
  zone_code: string
  value_cop_ha: number
  source_column: string
}

export interface ZhgZonesResponse {
  items: ZoneReferenceItem[]
  unit: string
  reference_type: string
  source_description: string
  reference_date: null
  limitations: string[]
}

export interface ParcelZoneItem {
  zone_code: string
  value_cop_ha: number | null
  area_intersection_m2: number | null
  share_pct: number | null
}

export interface DominantZone {
  zone_code: string
  value_cop_ha: number | null
  share_pct: number | null
  note: string
}

export interface WeightedReference {
  value_cop_ha: number
  coverage_status: string
  status_label: string
}

export interface ZhgReferenceResponse {
  public_id: string
  unit: string
  reference_type: string
  zones: ParcelZoneItem[]
  dominant_zone: DominantZone | null
  weighted_reference: WeightedReference | null
  provisional_weighted_reference: WeightedReference | null
  coverage_status: string | null
  source_description: string
  reference_date: null
  limitations: string[]
}

export interface ZhgDemoResponse {
  public_id: string
  model_id: string
  model_status: string
  unit: string
  target_description: string
  reference_zhg_cop_ha: number
  predicted_zhg_cop_ha: number
  absolute_difference_cop_ha: number
  relative_difference_pct: number | null
  zone_code: string
  domain_status: string
  source_description: string
  reference_date: null
  limitations: string[]
  evaluation_context: Record<string, unknown>
  disclaimer: string
}
