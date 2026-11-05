import { chromium } from "@playwright/test"
import path from "node:path"
import { fileURLToPath } from "node:url"

const dir = path.dirname(fileURLToPath(import.meta.url))
const htmlPath = path.resolve(dir, "../../entrega_docente/ATLAS_VIVO_INFORME_ACADEMICO.html")
const pdfPath = path.resolve(dir, "../../entrega_docente/ATLAS_VIVO_INFORME_ACADEMICO.pdf")

const browser = await chromium.launch()
const page = await browser.newPage()
await page.goto("file:///" + htmlPath.replace(/\\/g, "/"), { waitUntil: "networkidle" })
await page.pdf({ path: pdfPath, format: "A4", printBackground: true, margin: { top: "18mm", bottom: "18mm" } })
await browser.close()
console.log("PDF generado:", pdfPath)
