import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { APP_DESCRIPTION_CORTA } from '../lib/appContent'
import styles from './AppShell.module.css'

const NAV_ITEMS = [
  { to: '/', label: 'Inicio', exact: true },
  { to: '/predios', label: 'Predios' },
  { to: '/mapa', label: 'Mapa' },
  { to: '/prediccion', label: 'Predicción' },
  { to: '/exploracion', label: 'Análisis' },
  { to: '/modelos', label: 'Modelos' },
  { to: '/metodologia', label: 'Metodología' },
  { to: '/glosario', label: 'Glosario' },
  { to: '/acerca-de', label: 'Acerca' },
]

function BrandMark() {
  return (
    <span className={styles.brand} aria-hidden="true">
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
        <circle cx="13" cy="13" r="4" stroke="currentColor" strokeWidth="1.4" />
        <path d="M13 3c4 3.2 6 6.4 6 10a6 6 0 1 1-12 0c0-3.6 2-6.8 6-10Z" stroke="currentColor" strokeWidth="1.4" />
        <path d="M13 1.5c6.5 4.2 9.5 8.2 9.5 11.5a9.5 9.5 0 0 1-19 0C3.5 9.7 6.5 5.7 13 1.5Z" stroke="currentColor" strokeWidth="0.7" opacity="0.5" />
      </svg>
    </span>
  )
}

export default function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo} aria-label="Atlas Vivo, inicio">
          <BrandMark />
          <span className={styles.logoText}>
            ATLAS VIVO
            <small>Observatorio Territorial de Yacopí</small>
          </span>
        </Link>

        <nav className={styles.nav} aria-label="Navegación principal">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.active : ''}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className={styles.menuButton}
          aria-expanded={menuOpen}
          aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      <AnimatePresence>
        {menuOpen && (
          <motion.nav
            className={styles.mobileMenu}
            aria-label="Navegación móvil"
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.exact}
                className={({ isActive }) =>
                  `${styles.mobileLink} ${isActive ? styles.active : ''}`
                }
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </motion.nav>
        )}
      </AnimatePresence>

      <main id="contenido">
        <Outlet />
      </main>

      <footer className={styles.footer}>
        <div className="container">
          <p className={styles.footerText}>
            <strong>ATLAS VIVO</strong> · {APP_DESCRIPTION_CORTA}
          </p>
          <p className={styles.footerMono}>
            dataset {location.pathname === '/' ? '—' : ''} · municipio de Yacopí,
            Cundinamarca · Colombia
          </p>
        </div>
      </footer>
    </div>
  )
}
