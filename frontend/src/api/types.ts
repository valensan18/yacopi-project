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

export interface SystemStatus {
  data_status: string
  dataset_version: string | null
  model_status: string
  model_ready: boolean
  target_unit: string
  experimental_model: ExperimentalModelInfo
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
