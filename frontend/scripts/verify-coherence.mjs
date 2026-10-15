/**
 * Verificación de coherencia global de textos (Fase 9).
 * Comprueba el contenido RENDERIZADO por página en escritorio y móvil.
 * Uso: node scripts/verify-coherence.mjs
 */

import { chromium } from '@playwright/test'

const BASE = 'http://127.0.0.1:5173'

async function bodyText(page, route, waitSelector = null, timeout = 25_000) {
  await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' })
  if (waitSelector) {
    await page.waitForSelector(waitSelector, { state: 'attached', timeout })
  }
  await page.waitForTimeout(1_500)
  return page.evaluate(() => document.body.textContent ?? '')
}

async function audit(viewport, label) {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport })
  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  const checks = {}

  const home = await bodyText(page, '/', 'text=¿Cuánto vale una hectárea?')
  checks.footerActual = home.includes(
    'Atlas Vivo es un prototipo académico de análisis territorial del suelo rural de Yacopí',
  )
  checks.footerSinProxy = !home.includes('proxy de avalúo catastral total por hectárea')
  checks.inicioDemoActual = home.includes('demostración experimental de Random Forest')
  checks.inicioEnlacePrediccion = home.includes('Ir a la predicción')

  const analisis = await bodyText(page, '/exploracion', '.js-plotly-plot')
  checks.analisisDiferencia = analisis.includes('predicción ni una métrica de un modelo')
  checks.analisisEnlaces = analisis.includes('Modelos') && analisis.includes('Predicción')

  const modelos = await bodyText(page, '/modelos', 'text=Experimentos del valor del suelo')
  checks.modelosHistorico = modelos.includes('Experimento proxy (histórico, Fase 2)')
  checks.modelosZhg = modelos.includes('Experimentos del valor del suelo (ZHG)')
  checks.modelosLedeActual = !modelos.includes('solo hay un experimento con un proxy')

  const metodologia = await bodyText(page, '/metodologia', 'text=Ruta CRISP-DM')
  checks.metodologiaHistorico = metodologia.includes('Experimentos históricos')

  const acerca = await bodyText(page, '/acerca-de', 'text=Propósito')
  checks.acercaExtendida = acerca.includes(
    'prototipo académico de consulta y análisis territorial',
  )

  const glosario = await bodyText(page, '/glosario', '#glosario-busqueda')
  checks.glosarioTerminoHistorico = glosario.includes('Experimento histórico (proxy)')

  const prediccion = await bodyText(page, '/prediccion', 'text=Demostración experimental')
  checks.prediccionDemo = prediccion.includes('Demostración experimental')
  checks.prediccionSinProxyVisible = !prediccion.includes('Predicción experimental (proxy)')

  checks.erroresConsola = consoleErrors.length
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1_200)
  await page.screenshot({ path: `../docs/capturas/f9_home_${label}.png` })
  await page.goto(`${BASE}/prediccion`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1_200)
  await page.screenshot({ path: `../docs/capturas/f9_prediccion_${label}.png` })
  await browser.close()
  return checks
}

const desktop = await audit({ width: 1440, height: 900 }, 'desktop')
const mobile = await audit({ width: 390, height: 844 }, 'movil')
console.log(JSON.stringify({ desktop, mobile }, null, 2))
