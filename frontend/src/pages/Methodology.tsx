import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import styles from './Methodology.module.css'

const CRISP_DM = [
  {
    etapa: '1 · Comprensión del problema',
    estado: 'completada',
    texto:
      'Delimitación del objetivo: estimar el valor del suelo rural de Yacopí con aprendizaje supervisado y exponerlo en un prototipo de consulta. La variable objetivo ideal se definió como valor exclusivo del terreno en COP/ha.',
  },
  {
    etapa: '2 · Comprensión de los datos',
    estado: 'completada',
    texto:
      'Dos fuentes reales: intersecciones geoeconómicas (9.447 filas) y zonas homogéneas físicas ZHF (7.968 filas), unidas por identificador predial. Sin diccionario oficial ni fechas de valoración.',
  },
  {
    etapa: '3 · Preparación',
    estado: 'completada',
    texto:
      'Normalización conservadora, una fila por predio (7.709 consolidados), banderas de calidad sin eliminar registros, verificación de CRS (9377/3116) y exportación a EPSG:4326.',
  },
  {
    etapa: '4 · Modelado',
    estado: 'experimental',
    texto:
      'Comparación de baseline, Ridge, árbol, Random Forest y CatBoost. Primero con un proxy experimental de avalúo total por hectárea (Fase 2, histórico) y luego con la referencia zonal ZHG (Fase 5, experimento vigente). Ajuste solo con validación espacial agrupada; test sellado.',
  },
  {
    etapa: '5 · Evaluación',
    estado: 'experimental',
    texto:
      'Métricas reales en test espacial y aleatorio, errores por subzona/tamaño/uso y análisis de importancia. El modelo oficial sigue bloqueado: etiqueta de suelo pendiente.',
  },
  {
    etapa: '6 · Puesta en uso',
    estado: 'en_desarrollo',
    texto:
      'Backend FastAPI y frontend React integrados. La inferencia oficial permanece deshabilitada (503) y la experimental solo existe en desarrollo.',
  },
]

const ESTADOS: Record<string, { label: string; className: string }> = {
  completada: { label: 'Completada', className: 'done' },
  experimental: { label: 'Experimental', className: 'exp' },
  en_desarrollo: { label: 'En desarrollo', className: 'wip' },
}

function AsideNote({ children }: { children: React.ReactNode }) {
  return (
    <aside className={styles.asideNote} aria-label="Nota al margen">
      <p className={`mono ${styles.asideKicker}`}>Nota</p>
      {children}
    </aside>
  )
}

export default function Methodology() {
  return (
    <div className={styles.page}>
      <div className="container">
        <PageHeader
          kicker="Metodología · TERRITORIO"
          title="Cómo se construyó el observatorio"
          lede="Recorrido académico del proyecto, desde las fuentes hasta el software. Cada afirmación de esta página está respaldada por la documentación y los resultados ejecutados del repositorio."
        />
      </div>

      <div className="container">
        <section className={styles.timelineSection}>
          <h2 className={styles.sectionTitle}>Ruta CRISP-DM</h2>
          <ol className={styles.timeline}>
            {CRISP_DM.map((paso) => {
              const estado = ESTADOS[paso.estado]
              return (
                <li key={paso.etapa} className={styles.timelineItem}>
                  <div className={styles.timelineHead}>
                    <span className={`mono ${styles.timelineState} ${styles[estado.className]}`}>
                      {estado.label}
                    </span>
                    <h3 className={styles.timelineTitle}>{paso.etapa}</h3>
                  </div>
                  <p className={styles.timelineText}>{paso.texto}</p>
                </li>
              )
            })}
          </ol>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Fuentes de datos</h2>
          <p>
            El estudio usa dos archivos reales del municipio:{' '}
            <strong>intersecciones de zonas geoeconómicas</strong> (9.447 filas, 17
            columnas) y <strong>zonas homogéneas físicas ZHF</strong> (7.968 filas, 28
            columnas). Se unen por identificador predial respetando ceros iniciales.
          </p>
          <AsideNote>
            Ningún CSV trae una etiqueta validada de valor exclusivo del suelo: el
            avalúo disponible es total (puede incluir construcciones) y los precios de
            zona son referencias preasignadas, no observaciones independientes.
          </AsideNote>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Consolidación y control de calidad</h2>
          <p>
            La tabla analítica mantiene <strong>una fila por predio</strong>: 7.709
            predios únicos (7.694 coincidentes entre fuentes, 227 solo-ZHF y 15 solo de
            la primera fuente). Las discrepancias no se corrigen a ciegas: se marcan
            como alertas. Hallazgos principales:
          </p>
          <ul className={styles.facts}>
            <li>4.924 predios con área ZHF que difiere más del 5 % del área catastral.</li>
            <li>843 predios con zona geoeconómica discordante entre fuentes.</li>
            <li>3.033 predios registran superficie construida positiva.</li>
            <li>106 predios con discrepancia geométrica mayor al 5 % entre fuentes.</li>
            <li>CRS verificados: 9377 y 3116; mapas exportados en EPSG:4326.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Preparación de variables</h2>
          <p>
            El modelo experimental usa <strong>19 variables</strong>: 5 numéricas (tres
            áreas y coordenadas) y 14 categóricas (ZHF, UPS y coberturas CLC), con
            marcador «SIN_DATO» para faltantes. Existe una lista explícita de columnas{' '}
            <strong>prohibidas</strong> (precios zonales, códigos geoeconómicos,
            derivados del avalúo y geometrías crudas) que el pipeline rechaza por diseño.
          </p>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Entrenamiento y evaluación espacial</h2>
          <p>
            Cohorte de 7.694 predios. Particiones congeladas: aleatoria por predio y{' '}
            <strong>espacial</strong> (grupos geográficos construidos sin mirar la
            etiqueta). El ajuste de hiperparámetros usó únicamente validación agrupada y
            el test sellado se evaluó una sola vez. Resultados y comparación completa en
            la pantalla <Link to="/modelos" className={styles.inlineLink}>Modelos</Link>.
          </p>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Experimentos históricos: limitaciones del proxy catastral</h2>
          <p>
            Como experimento histórico (Fase 2) se evaluó un modelo cuyo objetivo era
            el <strong>avalúo catastral total por hectárea</strong>. Se conserva por
            trazabilidad técnica, pero no es el modelo de la demostración actual
            (Random Forest sobre la referencia zonal ZHG). Tres límites de aquel
            experimento: (1) puede incluir construcciones; (2) el área está en el
            denominador del proxy y también entre las entradas, generando una relación
            mecánica parcial; (3) no hay fecha de valoración ni diccionario oficial de
            códigos. Por eso ningún resultado se presenta como valor del suelo.
          </p>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Validación pendiente</h2>
          <p>
            El sistema mantiene dos estados explícitos: análisis sin modelo (activo) y
            predicción validada (inexistente por ahora). Mientras el equipo académico no
            aporte una columna verificada de valor exclusivo del terreno por predio, el
            endpoint oficial responde <span className="mono">503 MODEL_NOT_READY</span>.
          </p>
        </section>
      </div>
    </div>
  )
}
