# Doc 18 — Diagnóstico del modelo operativo v1 (VALOR_TERRENO_Ha, RF escenario A)

**Fecha:** 2026-11-05 · **Rama de trabajo:** `experimental/valor-terreno-ha`
(los scripts y resultados se conservan allí; este diagnóstico también es
válido para la rama de revisión `revision-docente/valor-terreno-v2`).

**Decisión:** el candidato Random Forest (escenario A) **NO se promueve como
predictor recomendado**. La evaluación de estabilidad (ETAPA 1) demuestra que
no ofrece utilidad predictiva defendible frente a la referencia ZHG. Se
detiene la promoción según el criterio establecido y se presenta el
diagnóstico. No se construyó endpoint, interfaz ni rama de integración.

## 1. Variable exacta evaluada

```
VALOR_TERRENO_Ha = VALOR_AVALUO × 10000 / AREA_TERRENO_M2   [COP/ha]
```

- Avalúo catastral **total** (incluye construcciones) entre área del terreno.
- Cohorte: escenario A (construcción registrada = 0), **4.676 predios**.
- No es precio comercial, avalúo oficial vigente ni valor exclusivo de
  suelo; sin fecha de vigencia confirmada.

## 2. Verificaciones de la ETAPA 1

| # | Verificación | Resultado |
|---|---|---|
| 1 | Código/datasets del protocolo v2 | Confirmado: `ml/src/yacopi_ml/valor/` (modelos.py, dataset.py, splits.py, train.py, audit_r2.py) reproducen exactamente las métricas v2 |
| 2 | Fugas directas/indirectas | Sin fugas: se excluyen avalúo, valores/códigos zonales y área geoeconómica (`FEATURES_EXCLUIDAS`); sensibilidad sin `area_terreno_m2` casi sin efecto |
| 3 | Features disponibles en inferencia | Las 19 features se derivarían del dataset (mismo patrón `features.json` del artefacto demo, indexado por public_id); sin dependencia de la base de datos |
| 4 | Estabilidad con particiones espaciales independientes | **5 pliegues (semillas 101–505), sin usar el test sellado para ajustar nada**: ver tabla §3 |
| 5 | Comparación RF vs referencia ZHG (MAE, MdAPE, RMSE, R²) | RF pierde en MAE y MdAPE en **0 de 5** pliegues; ver §3 |
| 6 | Regiones/tipos con error excesivo | Zona 9 (336 predios del test sellado: MAE 1.295.036), zona 1 (MAE 5,2 M), zona 11 (MdAPE 95,4 %); ver §4 |
| 7 | Cobertura/áreas/calidad | 4.676 predios; 46 con área ≤ 100 m² (cocientes extremos); 12–32 sin dato ZHF imputados |
| 8 | Condiciones de aplicabilidad documentadas | Ver §5 |

## 3. Estabilidad: 5 particiones espaciales independientes (nueva evidencia)

`ml/src/yacopi_ml/valor/estabilidad.py` →
`ml/artifacts/exp-valor-terreno-001/estabilidad_rf_v1.json`.

| Pliegue (seed) | RF MAE | RF MdAPE | RF RMSE | RF R² | ZHG MAE | ZHG MdAPE | ZHG RMSE |
|---|---|---|---|---|---|---|---|
| 101 | 264.898 | 12,3 % | 956.112 | +0,566 | **196.891** | **5,4 %** | 1.395.627 |
| 202 | 259.492 | 21,4 % | 638.511 | +0,787 | **234.250** | **5,4 %** | 1.242.174 |
| 303 | 241.648 | 21,4 % | 903.483 | −2,634 | **76.114** | **5,4 %** | **374.216** |
| 404 | 154.331 | 15,2 % | 1.058.125 | −0,009 | **107.948** | **5,4 %** | **1.065.475** |
| 505 | 260.063 | 25,5 % | 720.090 | +0,722 | **218.568** | **5,4 %** | 1.235.017 |

- RF gana en MAE: **0/5** pliegues · gana en MdAPE: **0/5**.
- ZHG MdAPE ≈ 5,4 % constante; RF 12–26 %.
- R² mediano: RF 0,57 vs ZHG 0,18 (RF explica mejor la varianza cuando no
  colapsa, pero su error típico es peor).

Test sellado v2 (referencia histórica): RF MAE 767.064 vs ZHG 817.030
(única instancia a favor del RF en MAE); MdAPE 11,69 % vs **5,65 %**. La
ventaja del RF en el test sellado **no se replica** en las particiones
independientes.

## 4. Error excesivo por zona (test espacial sellado v2, RF)

| Zona | n | MAE | MdAPE |
|---|---|---|---|
| 1 | 3 | 5.199.039 | 42,5 % |
| 9 | 336 | 1.295.036 | 5,7 % |
| 10 | 105 | 411.222 | 38,7 % |
| 11 | 41 | 110.090 | 95,4 % |
| 7 | 11 | 276.160 | 4,2 % |

Las zonas con pocos predios y las de nivel propio sufren errores grandes;
el error relativo típico es malo en varias zonas (10, 11, 5).

## 5. Condiciones bajo las que la predicción tendría sentido

1. Predios rurales de Yacopí con construcción registrada **igual a cero**.
2. Áreas positivas; features dentro de los rangos del entrenamiento.
3. Solo como "estimación orientativa de valor catastral unitario derivado
   del avalúo total", nunca como precio de mercado ni avalúo oficial.
4. Mostrando SIEMPRE junto a la referencia ZHG, que en el error típico es
   mejor que el modelo.

## 6. Veredicto

El RF del escenario A **no supera el criterio de utilidad defendible frente
a la referencia ZHG** (0/5 pliegues en MAE y MdAPE; MdAPE 2–5 veces peor).
Conforme a la instrucción, **se detiene la promoción como predictor
recomendado** y no se ejecutan las etapas 2–6 (entrenamiento final,
endpoint, interfaz, integración). No se inventó un modelo alternativo.

## 7. Opciones para el equipo (requieren decisión, no se aplican automáticamente)

A. **No publicar ningún predictor ML v1**: la plataforma sigue ofreciendo la
   referencia ZHG como dato consultable (estado actual).
B. **Publicar RF v1 como demostración experimental transparente** (no como
   predictor recomendado): siempre acompañado de la referencia ZHG y con la
   advertencia de que el modelo no supera a la referencia en error típico.
   Requiere autorización y conservaría todos los avisos de limitación.
C. **Reintentar con el profesor confirmado** (vigencia del avalúo, contenido,
   tratamiento de áreas mínimas) antes de cualquier despliegue.

## 8. Restricciones respetadas

Sin cambios en producción, VPS, SQLite, modelos desplegados, Docker ni
frontend público. Oficial 503 MODEL_NOT_READY y demo desactivada. Sin push
en este diagnóstico (los scripts quedaron commitados en la rama
experimental local).
