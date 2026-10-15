/**
 * Verificación visual de la demostración ZHG ACTIVADA (Fase 7D).
 * Requiere backend local con EXPERIMENTAL_ZHG_ENABLED=true.
 * Uso: node scripts/verify-demo-enabled.mjs
 */

import { chromium } from '@playwright/test'

const BASE = 'http://127.0.0.1:5173'
const PUBLIC_ID = process.argv[2] ?? 'p_0018bf75088b5a93'

async function audit(viewport, label) {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport })
  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })

  await page.goto(`${BASE}/prediccion`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('text=Demostración experimental', { timeout: 25_000 })
  await page.waitForTimeout(1_200)

  // formulario de la demo visible (segundo input de public_id)
  const inputs = page.locator('input[type="text"]')
  const demoInput = inputs.last()
  await demoInput.fill(PUBLIC_ID)
  await page.getByRole('button', { name: /Ejecutar demostración experimental/ }).click()
  await page.waitForSelector('text=Referencia ZHG conocida', { timeout: 20_000 })
  await page.waitForTimeout(1_200)

  const bodyText = await page.evaluate(() => document.body.innerText)

  const checks = {}
  checks.formularioDemo = await inputs.count() > 0
  checks.referencia = bodyText.includes('REFERENCIA ZHG CONOCIDA')
  checks.estimacion = bodyText.includes('ESTIMACIÓN EXPERIMENTAL')
  checks.diferencia = bodyText.includes('DIFERENCIA')
  checks.modelo = bodyText.includes('EXP-ZHG-001-DEMO')
  checks.advertenciaAjuste = bodyText.includes(
    'forma parte de los datos utilizados para ajustar',
  )
  checks.sinBloqueProxy = !bodyText.includes('Predicción experimental (proxy)')
  checks.oficial503 = bodyText.includes('503 MODEL_NOT_READY')
  checks.erroresConsola = consoleErrors.length

  await page.screenshot({ path: `../docs/capturas/f7d_demo_${label}.png`, fullPage: false })
  await browser.close()
  return checks
}

const desktop = await audit({ width: 1440, height: 900 }, 'desktop')
const mobile = await audit({ width: 390, height: 844 }, 'movil')
console.log(JSON.stringify({ desktop, mobile }, null, 2))
