/**
 * Verificación funcional de la ficha predial (Fase 6B, ajustes finales).
 * Uso: node scripts/verify-detail.mjs
 */

import { chromium } from '@playwright/test'

const BASE = 'http://127.0.0.1:5173'

async function audit(viewport, label) {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport })
  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })

  // obtener un public_id real desde el backend del usuario
  const listing = await page.request.get('http://127.0.0.1:8000/api/v1/properties?limit=1')
  const { items } = await listing.json()
  const publicId = items[0].public_id

  await page.goto(`${BASE}/predios/${publicId}`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Valor unitario de referencia del suelo', { timeout: 25_000 })
  await page
    .waitForSelector('section:has-text("Valor unitario de referencia del suelo")')
    .catch(() => {})
  await page.waitForTimeout(2_000)

  const card = page
    .locator('section')
    .filter({ hasText: 'Valor unitario de referencia del suelo' })
    .first()
  const cardText = await card.innerText().catch(() => '')

  const checks = {}
  checks.tarjetaZhg = cardText.includes('dato · no predicción')
  checks.vigencia = cardText.includes('Vigencia de la referencia: no disponible')
  const bodyText = await page.evaluate(() => document.body.innerText)
  checks.sinCodigosInternosAlertas = !bodyText.includes(
    'area_geometrica_zhg_difiere_mas_5pct_zhf',
  )
  checks.participacionAclarada = cardText.includes(
    'intersecciones zonales registradas',
  )
  checks.notaCodigosAtributos = bodyText.includes(
    'decodificación semántica oficial está pendiente',
  )
  checks.erroresConsola = consoleErrors.length

  await page.screenshot({ path: `../docs/capturas/f6b_detalle_${label}.png`, fullPage: false })
  await browser.close()
  return { publicId, ...checks }
}

const desktop = await audit({ width: 1440, height: 900 }, 'desktop')
const mobile = await audit({ width: 390, height: 844 }, 'movil')
console.log(JSON.stringify({ desktop, mobile }, null, 2))
