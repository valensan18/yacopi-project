# Texto académico para el documento de Valentina

> Sección sugerida (metodología/resultados) — redactado para integrar en el
> documento del proyecto, conservando la terminología de Atlas Vivo.

## Estimación del valor catastral unitario con aprendizaje supervisado

Se construyó una variable de respuesta derivada del avalúo catastral total:

VALOR_TERRENO_Ha = (VALOR_AVALUO × 10000) / AREA_TERRENO_M2,

expresada en COP/ha, restringida al escenario A: predios sin construcción
registrada (4.676 registros). Esta variable es un valor catastral unitario
derivado del avalúo total; no corresponde a un precio comercial observado
ni a un valor exclusivo de suelo verificado, y no se dispone de una fecha
de vigencia confirmada del avalúo.

Se evaluaron cinco algoritmos (referencia de la media, regresión Ridge,
árbol de decisión, Random Forest y CatBoost) bajo el protocolo v2 de Atlas
Vivo, que emplea validaciones independientes por predio y por bloques
geográficos, con separación estricta entre entrenamiento y prueba. El
preprocesamiento (imputación, estandarización y codificación one-hot) se
ajustó exclusivamente con los datos de entrenamiento, y se excluyeron por
fuga las variables zonales y el avalúo.

Los resultados de la validación espacial sellada (689 predios) mostraron
para Random Forest un MAE de 767.064 COP/ha y un MdAPE de 11,69 %, frente a
la referencia geoeconómica ZHG, que como dato territorial alcanzó un MAE de
817.030 COP/ha y un MdAPE de 5,65 %. Una evaluación de estabilidad con
cinco particiones espaciales independientes evidenció que el modelo no
superó a la referencia ZHG en MAE ni en MdAPE en ninguno de los cinco
pliegues (mediana de MAE: 259.492 frente a 196.891 COP/ha). El desempeño
del modelo depende del territorio evaluado, con errores mayores en zonas
con pocos predios o niveles propios.

Dado lo anterior, el modelo se integró como **demostración académica
operativa** y no como predictor recomendado: la aplicación ejecuta el flujo
completo (datos, preprocesamiento, inferencia real con Random Forest y
respuesta de la API), mostrando siempre la estimación junto a la referencia
ZHG y con las métricas reales de validación. La predicción oficial
permanece bloqueada (503 MODEL_NOT_READY) hasta disponer de una variable de
suelo exclusivo validada, y la plataforma distingue explícitamente entre
datos territoriales consultados, referencias zonales, estimaciones
experimentales y avalúos.

Limitaciones principales: ausencia de fecha de vigencia del avalúo,
variable objetivo derivada de un avalúo total, cocientes extremos por áreas
mínimas y dependencia espacial del desempeño. Estas condiciones delimitan
el alcance interpretativo de cualquier estimación emitida por el sistema.
