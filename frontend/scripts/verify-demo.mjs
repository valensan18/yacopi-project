/**
 * Verificación funcional de la demostración ML (Fase 7B) en estado por
 * defecto (desactivada). Uso: node scripts/verify-demo.mjs
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

  await page.goto(`${BASE}/prediccion`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Demostración experimental', { timeout: 25_000 })
  await page.waitForTimeout(1_500)
  const bodyText = await page.evaluate(() => document.body.innerText)

  const checks = {}
  checks.seccionDemo = bodyText.includes('Demostración experimental')
  checks.desactivadaPorDefecto = bodyText.includes('desactivada en este entorno')
  checks.sinBotonFalso = (await page
    .getByRole('button', { name: /Ejecutar demostración experimental/ })
    .count()) === 0
  checks.bloqueOficial503 = bodyText.includes('503 MODEL_NOT_READY')
  checks.referenciaZhg = bodyText.includes('Consulta de referencia de valor')
  checks.avaluoNoEmitido = bodyText.includes('NO EMITIDO POR ESTE SOFTWARE')
  checks.erroresConsola = consoleErrors.length

  await page.screenshot({ path: `../docs/capturas/f7b_demo_${label}.png`, fullPage: false })
  await browser.close()
  return checks
}

const desktop = await audit({ width: 1440, height: 900 }, 'desktop')
const mobile = await audit({ width: 390, height: 844 }, 'movil')
console.log(JSON.stringify({ desktop, mobile }, null, 2))
