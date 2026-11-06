# Justificación: ¿por qué habilitar una demostración si el modelo no está validado?

## Contexto de la decisión

La evaluación de estabilidad (5 particiones espaciales independientes)
demostró que el Random Forest del escenario A **no supera** a la referencia
ZHG en MAE ni MdAPE en ningún pliegue. Con ese resultado se **detuvo su
promoción como predictor recomendado** (docs/18). Sin embargo, el equipo
necesita demostrar en la presustentación que el sistema ejecuta un flujo
completo y real de aprendizaje automático. La opción autorizada es
publicarlo como **demostración académica** con restricciones estrictas.

## Razones que justifican la demostración

1. **El flujo es real**: datos → preprocesamiento → Random Forest →
   `model.predict()` → respuesta API → interfaz. Nada es simulado.
2. **Transparencia total**: cada respuesta incluye las métricas reales,
   incluida la derrota frente a ZHG en las 5 particiones. No se oculta ni
   se suaviza.
3. **Separación inequívoca**: la interfaz distingue la referencia ZHG
   (dato territorial) de la estimación del modelo (predicción), y declara
   el carácter demostrativo en el aviso legal.
4. **Valor metodológico**: demuestra control de dominio (construcción = 0,
   rangos, categorías), manejo honesto de errores y trazabilidad del
   artefacto (manifiesto, hashes, semilla, versiones).

## Por qué NO es un avalúo ni un predictor oficial

- El endpoint oficial permanece en 503 MODEL_NOT_READY.
- La variable objetivo es un cociente del avalúo catastral **total**, sin
  fecha de vigencia verificable.
- El modelo no supera consistentemente a la referencia zonal.
- Todos los mensajes usan "estimación orientativa de valor catastral
  unitario", nunca "precio de mercado", "avalúo comercial" ni "valor
  oficial del terreno".

## Riesgos asumidos y controles

| Riesgo | Control |
|---|---|
| Que se interprete como avalúo | Avisos legales en API e interfaz; rol `demostracion_academica` |
| Que parezca validado | Métricas de derrota frente a ZHG visibles en el resultado |
| Exposición de datos privados | Solo public_id; artefacto sin numero_predial ni avalúos; cargado desde fuente local verificada |
| Habilitación accidental en producción | Flag `VALOR_V1_ENABLED=false` por defecto en Docker/compose |
| Inestabilidad del desempeño | Documentada por partición (zonas 1, 9, 10, 11 con errores altos) |
