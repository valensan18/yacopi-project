/**
 * Verificación funcional del mapa ATLAS VIVO (Fase 4.1).
 *
 * Uso (con FastAPI y Vite corriendo):
 *   node scripts/verify-map.mjs
 *
 * Comprueba en un navegador real: carga del mapa, teselas CARTO, sliders de
 * opacidad/tamaño (sin recargas), botones del panel, leyenda, contadores y
 * versión móvil. No imprime credenciales.
 */

import { chromium } from '@playwright/test'

const BASE = 'http://127.0.0.1:5173'
const results = {}

async function auditPage(page, label) {
  const consoleErrors = []
  const cartoTiles = { ok: 0, fail: 0 }
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('response', (res) => {
    if (res.url().includes('basemaps.cartocdn.com') && res.url().includes('.png')) {
      if (res.status() === 200) {
        cartoTiles.ok += 1
      } else {
        cartoTiles.fail += 1
      }
    }
  })

  await page.goto(`${BASE}/mapa`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('[data-testid="map-container"]', { timeout: 25_000 })
  await page.waitForSelector('.leaflet-tile-loaded', { timeout: 25_000 })
  await page.waitForTimeout(2_500)

  const checks = {}

  checks.mapaVisible = await page.locator('.leaflet-container').isVisible()
  checks.panelVisualizacion = await page.getByRole('button', { name: /Visualización/ }).count()
  checks.leyenda = await page.getByRole('button', { name: /Categorías/ }).count()

  const setRange = (selector, value) =>
    page.locator(selector).evaluate((el, v) => {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value',
      ).set
      setter.call(el, String(v))
      el.dispatchEvent(new Event('input', { bubbles: true }))
      el.dispatchEvent(new Event('change', { bubbles: true }))
    }, value)

  // Slider de opacidad: cambiar a 40 % sin error ni refetch
  await setRange('#opacidad-puntos', 40)
  await page.waitForTimeout(400)
  checks.valorOpacidad = await page.locator('output[for="opacidad-puntos"]').textContent()

  // Slider de tamaño: cambiar a 6 px
  await setRange('#tamano-puntos', 6)
  await page.waitForTimeout(400)
  checks.valorTamano = await page.locator('output[for="tamano-puntos"]').textContent()

  // Restablecer visualización
  await page.getByRole('button', { name: /Restablecer/ }).click()
  await page.waitForTimeout(300)
  checks.opacidadTrasReset = await page.locator('output[for="opacidad-puntos"]').textContent()
  checks.tamanoTrasReset = await page.locator('output[for="tamano-puntos"]').textContent()

  // Ver todo el territorio
  await page.getByRole('button', { name: /Ver todo el territorio/ }).click()
  await page.waitForTimeout(1_200)

  // Zoom con los controles nativos de Leaflet
  const tilesAntesZoom = cartoTiles.ok
  await page.locator('.leaflet-control-zoom-in').click()
  await page.waitForTimeout(900)
  await page.locator('.leaflet-control-zoom-in').click()
  await page.waitForTimeout(900)
  checks.zoomFunciona = cartoTiles.ok > tilesAntesZoom

  // Leyenda: colapsar, ocultar todas, mostrar todas
  const legendHeader = page.getByRole('button', { name: /Categorías/ }).first()
  await legendHeader.click()
  checks.legendAriaExpanded = await legendHeader.getAttribute('aria-expanded')
  await legendHeader.click()
  const hideAll = await page.getByRole('button', { name: /Ocultar todas/ }).count()
  if (hideAll) {
    await page.getByRole('button', { name: /Ocultar todas/ }).click()
    await page.waitForTimeout(300)
    await page.getByRole('button', { name: /Mostrar todas/ }).click()
    await page.waitForTimeout(300)
  }
  checks.filtrosLeyenda = hideAll

  checks.tilesCartoOk = cartoTiles.ok
  checks.tilesCartoFallidas = cartoTiles.fail
  checks.erroresConsola = consoleErrors.length

  results[label] = checks
  if (consoleErrors.length) {
    results[`${label}_errores`] = consoleErrors.slice(0, 3)
  }
  page.removeAllListeners('console')
  page.removeAllListeners('response')
}

const browser = await chromium.launch()

const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await auditPage(desktop, 'escritorio')
await desktop.close()

const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } })
await auditPage(mobile, 'movil')
await mobile.close()

await browser.close()
console.log(JSON.stringify(results, null, 2))
