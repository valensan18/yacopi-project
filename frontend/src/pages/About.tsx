import PageHeader from '../components/PageHeader'
import Disclaimer from '../components/Disclaimer'
import { APP_DESCRIPTION_EXTENDIDA } from '../lib/appContent'
import styles from './About.module.css'

const TECNOLOGIAS = [
  ['Procesamiento y datos', 'Python · pandas · GeoPandas · SQLite'],
  ['Aprendizaje automático', 'scikit-learn · CatBoost · SHAP (offline)'],
  ['Backend', 'FastAPI · Pydantic v2 · Uvicorn'],
  ['Frontend', 'React · TypeScript · Vite · TanStack Query'],
  ['Visualización', 'Leaflet · Plotly · Three.js (React Three Fiber)'],
  ['Animación', 'GSAP · ScrollTrigger · Lenis · Motion'],
]

export default function About() {
  return (
    <div className="container">
      <PageHeader
        kicker="Acerca del proyecto"
        title="ATLAS VIVO"
        lede="Observatorio Territorial de Yacopí: un prototipo académico que integra datos reales, análisis estadístico y aprendizaje supervisado en una experiencia cartográfica."
      />

      <div className={styles.grid}>
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Propósito</h2>
          <p>
            Consultar, visualizar y comprender el suelo rural del municipio de Yacopí,
            Cundinamarca, con información real. El sistema no sustituye el catastro ni
            produce avalúos: es una herramienta académica de apoyo al análisis
            territorial.
          </p>
        </section>

        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Contexto académico</h2>
          <p>
            Proyecto de grado en modalidad artículo del programa de Ingeniería de
            Sistemas y Computación, guiado por la metodología CRISP-DM y un enfoque
            ágil. El equipo y la institución se omiten deliberadamente de esta interfaz.
          </p>
        </section>

        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Alcance geográfico</h2>
          <p>
            Municipio de Yacopí, Cundinamarca, Colombia. La base consolida 7.709 predios
            de las fuentes disponibles; no se afirma que sea la totalidad de predios
            rurales del municipio.
          </p>
        </section>

        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Arquitectura general</h2>
          <ol className={styles.flow}>
            <li>CSV originales → auditoría y consolidación (offline)</li>
            <li>SQLite curada → API FastAPI (consulta, estadísticas, mapas)</li>
            <li>Referencias zonales ZHG (dato) + artefacto experimental verificado</li>
            <li>React consume la API; la predicción oficial permanece bloqueada</li>
          </ol>
        </section>
      </div>

      <section className={styles.techSection}>
        <h2 className={styles.cardTitle}>Tecnologías</h2>
        <dl className={styles.techList}>
          {TECNOLOGIAS.map(([area, stack]) => (
            <div key={area}>
              <dt>{area}</dt>
              <dd className="mono">{stack}</dd>
            </div>
          ))}
        </dl>
      </section>

      <Disclaimer title="Limitaciones y advertencias">
        <p>
          {APP_DESCRIPTION_EXTENDIDA}
        </p>
        <p>
          Los datos descriptivos provienen de dos fuentes sin diccionario oficial ni
          fechas de valoración. El componente predictivo es una{' '}
          <strong>demostración experimental de Random Forest</strong> que estima un
          valor unitario de referencia zonal en COP/ha: no constituye un avalúo
          individual certificado ni un precio comercial, no tiene evaluación
          independiente para el artefacto actual y no se ha demostrado que generalice
          a zonas nuevas. La predicción oficial permanece deshabilitada.
        </p>
      </Disclaimer>
    </div>
  )
}
