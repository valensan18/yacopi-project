/**
 * Verificación visual de accesibilidad y comprensión (Fase 7E).
 * Requiere backend y frontend locales corriendo.
 * Uso: node scripts/verify-comprension.mjs
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
  const checks = {}

  // 1. Glosario: búsqueda y categorías
  await page.goto(`${BASE}/glosario`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('#glosario-busqueda', { timeout: 25_000 })
  await page.locator('#glosario-busqueda').fill('MAE')
  await page.waitForTimeout(400)
  const body1 = await page.evaluate(() => document.body.innerText)
  checks.glosarioBusqueda = body1.includes('MAE') && !body1.includes('Zona homogénea física (ZHF)')

  // 2. Ficha: interpretación contextual + HelpTip operable por teclado
  const listing = await page.request.get('http://127.0.0.1:8000/api/v1/properties?limit=1')
  const { items } = await listing.json()
  await page.goto(`${BASE}/predios/${items[0].public_id}`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=¿Qué significa esto para este predio?', { timeout: 25_000 })
  await page.waitForTimeout(1_200)
  const body2 = await page.evaluate(() => document.body.innerText)
  checks.interpretacionFicha = body2.includes('¿QUÉ SIGNIFICA ESTO PARA ESTE PREDIO?')
  checks.interpretacionConDatoReal = body2.includes('clasificado con destino económico')

  const tip = page.getByRole('button', { name: /Qué significa la identificación del predio/ }).first()
  await tip.focus()
  await page.keyboard.press('Enter')
  await page.waitForTimeout(300)
  checks.helpTipTeclado = await page.getByText(/identificador es opaco/).count() > 0
  await page.keyboard.press('Escape')

  checks.erroresConsola = consoleErrors.length
  await page.screenshot({ path: `../docs/capturas/f7e_comprension_${label}.png`, fullPage: false })
  await browser.close()
  return checks
}

const desktop = await audit({ width: 1440, height: 900 }, 'desktop')
const mobile = await audit({ width: 390, height: 844 }, 'movil')
console.log(JSON.stringify({ desktop, mobile }, null, 2))
