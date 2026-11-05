# Matriz de variables objetivo

Qué se predijo exactamente en cada etapa. **Ningún experimento usó la misma
variable que otro**, salvo la demo que reutiliza el objetivo ZHG con otro
propósito.

| EXPERIMENTO | VARIABLE Y | FÓRMULA / ORIGEN | VARIABLES X | FUENTES | FILTROS | MODELOS | VALIDACIÓN | RESULTADO | LIMITACIÓN |
|---|---|---|---|---|---|---|---|---|---|
| exp-proxy-001 (Fase 2) | avalúo catastral **total** por hectárea (`proxy_avaluo_total_cop_ha`) | `valor_avaluo_total × 10000 / area_terreno_catastral` | 19 features (áreas, lat, lon, destino, ZHF, CLC) | `03_predios_consolidados.csv` | ninguno (n=7.694) | Dummy, Ridge, Árbol, RF, CatBoost | test espacial sellado + aleatorio | RF espacial MAE 3.226.230, R² 0,74 | Incluye construcciones; NO es valor de suelo; el área está en Y y en X |
| exp-zhg-001 (Fase 5) | referencia ZHG zonal (`valor_zona_dominante_cop_ha`) | valor de la zona geoeconómica predominante (COP/ha) | mismas 19 features sin variables zonales | `01`+`02` normalizadas | predios con zona única (cobertura "consistente"/"dudosa"; n=7.709 con objetivo 11 valores) | Dummy, Ridge, Árbol, RF, CatBoost | filas / predio / espacial / zonas completas fuera | RF predio MAE 73.765, espacial 132.183, zonas fuera 423.363; R² zona −1,70 → **rechazado** | Solo 11 valores posibles; generalización a zonas nuevas insuficiente |
| exp-zhg-001-ponderado (Fase 5) | `valor_ponderado_cop_ha` | promedio de valores zonales ponderado por % de intersección | idem | idem | predios con ponderado disponible (n=2.785; 651 valores únicos) | idem | idem | RF predio 88.865, espacial 145.604, zonas fuera 288.973; R² zona −0,55 → **rechazado** | Iguales limitaciones zonales |
| exp-zhg-001-demo (Fase 7B) | `valor_zona_dominante_cop_ha` | idem ZHG | idem (features.json del artefacto) | dataset completo | ninguno (ajuste sobre **7.709**) | RandomForest (depth 30, leaf 1, 513 árboles) | **ninguna independiente** (ajuste final) | solo consultas en zonas conocidas; demo off por defecto | No es modelo validado; métricas de Fase 5 no lo evalúan |
| exp-valor-terreno-001 A (experimental, protocolo v2) | `VALOR_TERRENO_Ha` | `valor_avaluo × 10000 / area_terreno_m2` | 19 features sin fuga (sin avalúo ni zonales) | CSV crudo de intersecciones + ZHF | construcción == 0 (n=4.676) | Dummy, Ridge(log), Árbol, RF, CatBoost | predio / espacial (independientes) / LOZO | RF test predio MAE 248.296, R² 0,69; **test espacial independiente R² 0,171 (CatBoost −0,075)** | Avalúo catastral total; sin fecha; no es valor comercial; generalización espacial limitada |
| exp-valor-terreno-001 B (experimental, protocolo v2) | `VALOR_TERRENO_Ha` | idem | idem | idem | 0 < construcción ≤ 32 (n=986) | idem | idem | test predio R² 0,12–0,15 (7 extremos > 50 M); espacial RF 0,863/CatBoost 0,646 | Cocientes de áreas mínimas dominan el error del test predio |
| **Modelo oficial** | (pendiente) | valor exclusivo de terreno validado | — | — | — | — | — | **no existe; 503 MODEL_NOT_READY** | Etiqueta `pending_verification` |

## Por qué son diferentes entre sí

1. **Proxy (Fase 2):** el avalúo total incluye edificaciones; 3.033 predios
   tienen construcción. Predice un "precio del inmueble por hectárea", no el
   suelo.
2. **ZHG (Fase 5):** el objetivo solo admite 11 valores (uno por zona); un
   modelo que identifique la zona memoriza la respuesta. Por eso la validación
   decisiva fue dejar zonas completas fuera, donde todos los modelos
   colapsaron (R² negativos).
3. **VALOR_TERRENO_Ha (rama experimental):** avalúo catastral total entre
   área del terreno; variación continua (5.654 valores únicos), pero sigue
   siendo avalúo catastral (no valor de mercado) y hereda la relación con la
   zona (correlación avalúo vs zonal×área = 0,73; 0,91 en predios de una
   sola zona).
4. **Demo RF:** no es un experimento de evaluación; es un artefacto para
   mostrar el flujo del software, ajustado a todos los datos.

## Regla para no confundir métricas

Cada métrica se reporta con su experimento, partición y n. Las cifras de
Fase 2 (proxy), Fase 5 (ZHG) y de la rama experimental **no son comparables
entre sí** porque cambian la variable objetivo y la cohorte.
