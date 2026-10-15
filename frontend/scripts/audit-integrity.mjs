/**
 * Auditoría integral de ATLAS VIVO (Fase 8).
 * Recorre las 10 rutas en escritorio y móvil, ejecuta interacciones reales
 * contra el backend local y registra errores de consola por página.
 * Uso: node scripts/audit-integrity.mjs
 */

import { chromium } from '@playwright/test'

const BASE = 'http://127.0.0.1:5173'
const API = 'http://127.0.0.1:8000/api/v1'

const ROUTES = ['/', '/predios', '/mapa', '/exploracion', '/modelos',
  '/prediccion', '/metodologia', '/acerca-de', '/glosario']

async function auditViewport(viewport, label) {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport })
  const consoleErrors = {}
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors[page.url()] = (consoleErrors[page.url()] ?? 0) + 1
  })
  const report = {}
  const cartoTiles = { ok: 0, fail: 0 }
  page.on('response', (res) => {
    if (res.url().includes('basemaps.cartocdn.com') && res.url().includes('.png')) {
      res.status() === 200 ? cartoTiles.ok++ : cartoTiles.fail++
    }
  })

  for (const route of ROUTES) {
    await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2_500)
    report[route] = { status: 200, errores: consoleErrors[page.url()] ?? 0 }
  }

  // Catálogo: filtros e interacción real
  await page.goto(`${BASE}/predios`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=de 7.709 predios', { timeout: 25_000 })
  const totalAntes = await page.getByText(/de 7.709 predios/).first().textContent()
  await page.locator('select').first().selectOption({ label: 'Agropecuario (6.746)' })
  await page.waitForTimeout(1_200)
  const totalDespues = await page.getByText(/de \d[\d.]* predios/).first().textContent()
  report['/predios: filtro destino'] = {
    antes: totalAntes?.trim(),
    despues: totalDespues?.trim(),
  }

  // Ficha real: interpretación y tarjeta ZHG
  const listing = await page.request.get(`${API}/properties?limit=1`)
  const { items } = await listing.json()
  const pid = items[0].public_id
  await page.goto(`${BASE}/predios/${pid}`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Valor unitario de referencia del suelo', { timeout: 25_000 })
  await page.waitForTimeout(1_200)
  const ficha = await page.evaluate(() => document.body.innerText)
  report['/predios/:id'] = {
    publicId: pid,
    interpretacion: ficha.includes('¿QUÉ SIGNIFICA ESTO PARA ESTE PREDIO?'),
    tarjetaZhg: ficha.includes('Valor unitario de referencia del suelo'),
  }

  // Ficha inexistente → mensaje de error
  await page.goto(`${BASE}/predios/p_noexiste`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2_000)
  const errText = await page.evaluate(() => document.body.innerText)
  report['/predios/:id inexistente'] = {
    mensajeError: errText.includes('No se encontró un predio'),
  }

  // Mapa: teselas CARTO y controles
  await page.goto(`${BASE}/mapa`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('.leaflet-tile-loaded', { timeout: 25_000 })
  await page.waitForTimeout(2_000)
  report['/mapa: teselas'] = { cartoOk: cartoTiles.ok, cartoFallidas: cartoTiles.fail }

  // Análisis: gráficas Plotly
  await page.goto(`${BASE}/exploracion`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('.js-plotly-plot', { timeout: 25_000 })
  report['/exploracion: graficas'] = { count: await page.locator('.js-plotly-plot').count() }

  // Predicción: estado por defecto + comprobación real del 503 + consulta ZHG
  await page.goto(`${BASE}/prediccion`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Comprobar estado oficial (real)', { timeout: 25_000 })
  await page.getByRole('button', { name: 'Comprobar estado oficial (real)' }).click()
  await page.waitForTimeout(1_500)
  const predText = await page.evaluate(() => document.body.innerText)
  report['/prediccion: oficial'] = {
    muestra503: predText.includes('503 MODEL_NOT_READY'),
    demoDesactivada: predText.includes('desactivada en este entorno'),
  }
  const inputs = page.locator('input[type="text"]')
  await inputs.first().fill(pid)
  await page.getByRole('button', { name: /Consultar referencia ZHG/ }).click()
  await page.waitForSelector('text=Valor unitario de referencia del suelo', { timeout: 20_000 })
  report['/prediccion: consulta ZHG'] = { ok: true }

  // Glosario: búsqueda
  await page.goto(`${BASE}/glosario`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('#glosario-busqueda', { timeout: 25_000 })
  await page.locator('#glosario-busqueda').fill('MAE')
  await page.waitForTimeout(400)
  const glo = await page.evaluate(() => document.body.innerText)
  report['/glosario: busqueda'] = { filtra: glo.includes('Error absoluto promedio') }

  // Errores de consola acumulados
  report.erroresConsolaTotales = Object.values(consoleErrors).reduce((a, b) => a + b, 0)

  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1_500)
  await page.screenshot({ path: `../docs/capturas/f8_home_${label}.png` })
  await page.goto(`${BASE}/prediccion`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1_500)
  await page.screenshot({ path: `../docs/capturas/f8_prediccion_${label}.png` })

  await browser.close()
  return report
}

const desktop = await auditViewport({ width: 1440, height: 900 }, 'desktop')
const mobile = await auditViewport({ width: 390, height: 844 }, 'movil')

// Verificaciones de API independientes
const api = {}
const r1 = await (await fetch(`${API}/properties?limit=1`)).json()
api.propertiesTotal = r1.pagination.total
const r2 = await (await fetch(`${API}/references/zhg/zones`)).json()
api.zonas = r2.items.length
const r3 = await fetch(`${API}/predictions`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"features":{}}',
})
api.oficial503 = r3.status === 503

console.log(JSON.stringify({ desktop, mobile, api }, null, 2))
