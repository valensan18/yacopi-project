/**
 * FUENTE ÚNICA de descripciones institucionales de ATLAS VIVO.
 * Cualquier página o componente que presente el propósito, los conceptos o
 * las limitaciones generales del software DEBE usar estas constantes, para
 * evitar contradicciones futuras (ver test de regresión content.test.tsx).
 */

export const APP_NAME = 'Atlas Vivo'

export const APP_DESCRIPTION_CORTA =
  'Atlas Vivo es un prototipo académico de análisis territorial del suelo ' +
  'rural de Yacopí. Ofrece referencias zonales ZHG y una demostración ' +
  'experimental de Machine Learning. No emite avalúos individuales ' +
  'certificados ni determina precios comerciales.'

export const APP_DESCRIPTION_EXTENDIDA =
  'Atlas Vivo es un prototipo académico de consulta y análisis territorial ' +
  'del suelo rural de Yacopí. Integra referencias zonales ZHG y una ' +
  'demostración experimental de aprendizaje automático que estima valores ' +
  'unitarios de referencia del suelo en COP/ha. Sus resultados no ' +
  'constituyen avalúos individuales certificados ni precios comerciales.'

export const REFERENCIA_ZHG_DESCRIPCION =
  'Valor unitario de referencia asociado a una zona geoeconómica (ZHG), ' +
  'expresado en COP/ha. Es un dato territorial consultable: no es un avalúo ' +
  'individual certificado ni un precio comercial del predio.'

export const MODELO_EXPERIMENTAL_DESCRIPCION =
  'Demostración experimental de Machine Learning basada en Random Forest. ' +
  'Su objetivo experimental es estimar el valor unitario de referencia ' +
  'zonal del suelo (COP/ha) a partir de características territoriales. ' +
  'El artefacto actual se ajustó con los 7.709 predios disponibles: ninguna ' +
  'consulta constituye una evaluación independiente y no se ha demostrado ' +
  'que generalice a zonas nuevas.'

export const DIFERENCIA_REFERENCIA_VS_ESTIMACION =
  'La referencia ZHG es un dato conocido consultable; la estimación del ' +
  'modelo es un cálculo experimental que se muestra junto a la referencia ' +
  'para comparar, sin reemplazarla.'

export const EXPERIMENTOS_HISTORICOS_DESCRIPCION =
  'Experimentos anteriores conservados por trazabilidad, incluyendo el ' +
  'proxy de avalúo catastral total por hectárea (Fase 2). No son el modelo ' +
  'de la demostración actual y sus métricas no se mezclan con las del ' +
  'experimento ZHG.'

export const ESTADO_PREDICCION_OFICIAL =
  'La predicción oficial permanece deshabilitada (HTTP 503 MODEL_NOT_READY) ' +
  'porque el valor exclusivo del suelo por predio aún no está validado.'

export const NO_AVALUOS =
  'Atlas Vivo no emite avalúos individuales certificados ni determina ' +
  'precios comerciales de los terrenos.'

export const LIMITACIONES_GENERALES: string[] = [
  NO_AVALUOS,
  'El modelo experimental no tiene validación independiente para el ' +
    'artefacto actual y no se ha demostrado que generalice a zonas nuevas.',
  'Los códigos territoriales se muestran tal como vienen en la fuente; su ' +
    'decodificación oficial no está disponible en este proyecto.',
  'La fecha de vigencia de la referencia ZHG no está acreditada en los ' +
    'datos recibidos.',
]
