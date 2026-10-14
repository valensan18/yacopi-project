import { lazy, Suspense, useEffect, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { motion } from 'motion/react'
import { Link } from 'react-router-dom'
import { apiGet } from '../api/client'
import type { MapPoints, OverviewStats } from '../api/types'
import { initSmoothScroll, prefersReducedMotion, supportsWebGL } from '../lib/motion-setup'
import Scene3DFallback from '../components/Scene3DFallback'
import styles from './Home.module.css'

gsap.registerPlugin(ScrollTrigger)

const Scene3D = lazy(() => import('../components/Scene3D'))

const formatCOP = new Intl.NumberFormat('es-CO')
const formatDec = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 })

interface Kpi {
  label: string
  value: number
  format: Intl.NumberFormat
  unit: string
  note: string
}

function Hero() {
  const heroRef = useRef<HTMLElement>(null)
  const progressRef = useRef({ value: 0 })
  const webgl = useMemo(() => supportsWebGL(), [])

  const { data: points } = useQuery<MapPoints>({
    queryKey: ['map-points'],
    queryFn: () => apiGet<MapPoints>('/maps/points', { limit: 8000 }),
    staleTime: 5 * 60_000,
  })

  useEffect(() => {
    if (prefersReducedMotion()) return
    const ctx = gsap.context(() => {
      gsap.to(progressRef.current, {
        value: 1,
        ease: 'none',
        scrollTrigger: {
          trigger: heroRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: 0.7,
        },
      })
    }, heroRef)
    return () => ctx.revert()
  }, [])

  return (
    <section className={styles.hero} ref={heroRef} aria-label="Portada">
      <div className={styles.scene} aria-hidden="true">
        {webgl && points ? (
          <Suspense fallback={<Scene3DFallback pointCount={points.features.length} />}>
            <Scene3D points={points} progressRef={progressRef} />
          </Suspense>
        ) : (
          <Scene3DFallback pointCount={points?.features.length ?? 0} />
        )}
      </div>

      <div className={styles.heroOverlay} aria-hidden="true" />

      <div className={`container ${styles.heroContent}`}>
        <p className={`mono ${styles.heroKicker}`} data-reveal>
          Observatorio Territorial · Yacopí, Cundinamarca
        </p>
        <h1 className={styles.heroTitle} data-reveal>
          ATLAS
          <br />
          <span>VIVO</span>
        </h1>
        <p className={styles.heroSub} data-reveal>
          Una lectura viva del suelo rural: predios, territorio y datos reales del
          municipio, desde la cartografía hasta el aprendizaje supervisado.
        </p>
        <div className={styles.heroActions} data-reveal>
          <Link to="/predios" className={styles.primaryCta}>
            Explorar predios
          </Link>
          <Link to="/metodologia" className={styles.secondaryCta}>
            Conocer la metodología
          </Link>
        </div>
        <p className={styles.heroLabel} aria-hidden="true">
          Relieve ilustrativo · Puntos: coordenadas referenciales de predios reales
          (color por destino económico)
        </p>
      </div>

      <div className={styles.scrollCue} aria-hidden="true">
        <span />
        Desliza para descubrir el territorio
      </div>
    </section>
  )
}

function KpiSection() {
  const sectionRef = useRef<HTMLElement>(null)

  const { data, isLoading, isError } = useQuery<OverviewStats>({
    queryKey: ['overview'],
    queryFn: () => apiGet<OverviewStats>('/statistics/overview'),
    staleTime: 5 * 60_000,
  })

  const kpis: Kpi[] = useMemo(() => {
    if (!data) return []
    return [
      { label: 'Predios consolidados', value: data.total_predios, format: formatCOP, unit: '', note: 'una fila por predio, fuentes cruzadas' },
      { label: 'Con coordenadas', value: data.predios_con_coordenadas, format: formatCOP, unit: '', note: 'puntos referenciales ZHF' },
      { label: 'Con construcción registrada', value: data.con_construccion, format: formatCOP, unit: '', note: 'relevante para la etiqueta de suelo' },
      { label: 'Área catastral total', value: (data.area.total_m2 ?? 0) / 10_000, format: formatDec, unit: 'ha', note: 'suma de superficies declaradas' },
    ]
  }, [data])

  useEffect(() => {
    if (prefersReducedMotion() || !data) return
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>('[data-count]').forEach((el) => {
        const target = Number(el.dataset.count)
        const format = el.dataset.format
        const state = { value: 0 }
        gsap.to(state, {
          value: target,
          duration: 1.6,
          ease: 'power2.out',
          scrollTrigger: { trigger: el, start: 'top 88%' },
          onUpdate: () => {
            el.textContent = format === 'dec'
              ? formatDec.format(state.value)
              : formatCOP.format(Math.round(state.value))
          },
        })
      })
    }, sectionRef)
    return () => ctx.revert()
  }, [data])

  if (isError) {
    return (
      <section className={`container ${styles.section}`} ref={sectionRef}>
        <h2 className="section-title">El territorio en cifras</h2>
        <p role="alert" className={styles.errorNote}>
          No fue posible cargar las estadísticas desde la API. Verifica que el backend
          esté activo (puerto 8000).
        </p>
      </section>
    )
  }

  return (
    <section className={`grid-bg ${styles.kpiSection}`} ref={sectionRef}>
      <div className="container">
        <p className="section-kicker">El territorio en cifras</p>
        <h2 className="section-title" data-reveal>Un municipio, mil escalas</h2>
        <div className={styles.kpiGrid}>
          {isLoading && <p role="status">Cargando cifras reales…</p>}
          {kpis.map((kpi) => (
            <div className={styles.kpiCard} key={kpi.label} data-reveal>
              <p className={styles.kpiValue}>
                <span
                  data-count={kpi.value}
                  data-format={kpi.unit === 'ha' ? 'dec' : 'int'}
                >
                  0
                </span>
                {kpi.unit && <span className={styles.kpiUnit}>{kpi.unit}</span>}
              </p>
              <p className={styles.kpiLabel}>{kpi.label}</p>
              <p className={styles.kpiNote}>{kpi.note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function ModelSection() {
  return (
    <section className={`container ${styles.section}`}>
      <p className="section-kicker">Valor y territorio</p>
      <h2 className="section-title" data-reveal>
        ¿Cuánto vale una hectárea?
      </h2>
      <div className={styles.modelGrid}>
        <div className={styles.modelCopy} data-reveal>
          <p>
            El proyecto compara modelos supervisados (regresión regularizada, árboles,
            bosques aleatorios y CatBoost) con validación espacial y aleatoria.
            Los resultados se publican con sus métricas reales.
          </p>
          <p>
            <strong>Estado científico:</strong> la variable objetivo —el valor
            exclusivo del suelo en COP/ha— está{' '}
            <strong>pendiente de validación</strong>. Sin ella no existe un modelo
            oficial de predicción.
          </p>
        </div>
        <div className={styles.modelNotice} data-reveal>
          <p className="mono">Aviso metodológico</p>
          <p>
            El único modelo disponible es <strong>experimental</strong>: predice un{' '}
            <em>proxy</em> de avalúo catastral total por hectárea. No es el valor del
            suelo ni un avalúo oficial, y su inferencia está desactivada por defecto.
          </p>
          <Link to="/modelos" className={styles.textLink}>
            Ver comparación de modelos →
          </Link>
        </div>
      </div>
    </section>
  )
}

function ExploreSection() {
  const cards = [
    { to: '/predios', kicker: 'Catálogo', title: 'Predios', text: 'Busca y filtra los 7.709 predios consolidados con sus atributos reales.' },
    { to: '/mapa', kicker: 'Cartografía', title: 'Mapa', text: 'Explora la distribución territorial por destino económico y subzona.' },
    { to: '/exploracion', kicker: 'Ciencia', title: 'Análisis', text: 'Distribuciones, calidad de datos y errores por segmento.' },
  ]
  return (
    <section className={`container ${styles.section}`}>
      <p className="section-kicker">Explorar</p>
      <h2 className="section-title" data-reveal>Elige tu entrada al territorio</h2>
      <div className={styles.cardGrid}>
        {cards.map((card) => (
          <motion.div
            key={card.to}
            whileHover={{ y: -6 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            <Link to={card.to} className={styles.card} data-reveal>
              <p className="mono">{card.kicker}</p>
              <h3>{card.title}</h3>
              <p className={styles.cardText}>{card.text}</p>
              <span className={styles.cardArrow} aria-hidden="true">→</span>
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

export default function Home() {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (prefersReducedMotion()) return
    const cleanup = initSmoothScroll()
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>('[data-reveal]').forEach((el) => {
        gsap.fromTo(
          el,
          { y: 36, autoAlpha: 0 },
          {
            y: 0,
            autoAlpha: 1,
            duration: 0.7,
            ease: 'power3.out',
            scrollTrigger: { trigger: el, start: 'top 86%' },
          },
        )
      })
    }, rootRef)
    return () => {
      ctx.revert()
      cleanup?.()
    }
  }, [])

  return (
    <div ref={rootRef}>
      <Hero />
      <KpiSection />
      <ModelSection />
      <ExploreSection />
    </div>
  )
}
