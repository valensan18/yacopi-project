# Preguntas para el profesor

Decisiones metodológicas que requieren confirmación docente antes de avanzar
hacia un modelo definitivo.

## Sobre la variable de respuesta

1. **Fecha y procedencia de `valor_avaluo`**: ¿es el avalúo catastral vigente
   y de qué año/vigencia? (no aparece en los CSV).
2. **Contenido del avalúo**: ¿`valor_avaluo` corresponde al avalúo catastral
   **total** (suelo + construcción) o a un avalúo exclusivo del terreno?
   La auditoría indica que no hay campo separado de avalúo de terreno.
3. **Umbral de 32 m²**: confirmar que el filtro del trabajo original se aplica
   sobre el **área construida** y no sobre el área del terreno, y si existe
   documento fuente.
4. **Criterio para áreas mínimas**: ¿cómo trató el trabajo original los
   predios con área muy pequeña (p. ej. < 100 m²) que producen cocientes
   extremos (hasta 1.354 M COP/ha)? ¿Se excluyen, se acotan o se conservan?

## Sobre el alcance interpretativo

5. ¿Es aceptable presentar VALOR_TERRENO_Ha como "avalúo catastral por
   hectárea" (no como valor comercial ni de mercado)?
6. La variable está fuertemente asociada al valor zonal (corr 0,91 en predios
   de una sola zona). ¿El objetivo del modelo es **refinar** la referencia
   zonal con atributos prediales, o se espera una fuente independiente?
7. ¿El criterio de aceptación de un modelo definitivo debe exigir
   generalización a zonas no vistas (como en Fase 5), o basta interpolación
   dentro del municipio?

## Sobre los datos

8. ¿Hay un diccionario oficial de los códigos ZHF/ZHG/CLC que deba usarse en
   la interpretación?
9. ¿Se dispone de la fecha de vigencia de los valores zonales ZHG
   (`valor_hectarea_agropecuario`)?
10. ¿Las diferencias de área entre fuentes (ZHF vs catastral, 4.924 predios
    > 5 %) tienen explicación institucional?

## Sobre el producto

11. Si se acepta un modelo experimental del escenario A, ¿se publica como
    demostración (off por defecto) o se activa el endpoint oficial (cambiaría
    el estado 503)?
12. ¿Se autoriza documentar el trabajo del profesor (fórmula VALOR_TERRENO_Ha)
    dentro del repositorio académico?
