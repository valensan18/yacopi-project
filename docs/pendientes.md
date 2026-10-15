# Pendientes del proyecto — registro de bloqueos y solicitudes

Regla (guía maestra §0): ante una fuente técnica o decisión faltante, registrar
aquí impacto, responsable y criterio de resolución, y continuar con tareas
independientes.

| # | Pendiente | Impacto | Responsable | Criterio de resolución | Estado |
|---|---|---|---|---|---|
| 1 | **Valor exclusivo de terreno por predio (COP/ha)** con método, fecha y superficie documentados | Bloquea ML oficial (Fase 2 production). Sin esto solo Ruta B experimental | Director disciplinar / equipo | Columna o archivo unible por `numero_predial` con definición comprobada | ABIERTO |
| 2 | Diccionario técnico de ambas fuentes (`AREA_TERRE`, `valor_avaluo`, `ZHG_VALOR_`, `ZHG_VALOR1`, códigos ZHF/UPS/CLC) | Codificación correcta de categorías y fechas | Gestor catastral / director | Documento oficial de definiciones | ABIERTO |
| 3 | Fecha de corte y fecha base de valoración de los CSV | Etiquetado temporal y evaluación por ventana | Fuente de datos | Fechas verificadas por campo | ABIERTO |
| 4 | Autorización de divulgación (identificadores, coordenadas, mapas) | Qué se publica en API/Git | Equipo académico | Confirmación escrita de permisos | ABIERTO |
| 5 | Confirmar vigencia normativa para el artículo (Ley 2294/2023 art. 49, Res. 1040/2023, 746/2024, Conjunta 1456/2024) | Citas del artículo | Estudiantes | Textos oficiales verificados a fecha de redacción | ABIERTO |
| 6 | Login de `gh` CLI como valensan18 | Verificar `private=true` y colaboradores del repo | Usuario | `gh auth status` muestra valensan18 | EN PROCESO |
| 7 | VPS para Fase 7 | Despliegue real | Usuario | Proveedor y accesos disponibles | DIFERIDO (acordado) |
| 8 | Confirmar que GitHub acepta el correo noreply `342352447+valensan18@users.noreply.github.com` | Atribución de commits | Usuario | Settings → Emails con "Keep my email addresses private" activo; verificar commit publicado | ABIERTO |
| 9 | 15 predios sin coincidencia ZHF (sin coordenadas ni atributos ZHF/CLC) | Cobertura de mapa y de features X | Fuente de datos | Explicación de por qué faltan en ZHF o archivo con sus atributos | ABIERTO |
| 10 | `fa_element` (471 vacíos) y `aht_vpoten` (40): regla de manejo de faltantes | Selección de variables | Equipo ML | Regla documentada antes de entrenar | **RESUELTO (Fase 2):** `fa_element` excluido del experimento por cobertura; categóricas usan marcador `SIN_DATO` (ADR-0003) |
| 11 | `SINAP_NOMB`/`SINAP_CATE` no usados aún | Cobertura de variables ambientales | Equipo ML | Decisión con diccionario oficial | ABIERTO (diferido; no están en allowlist) |
| 12 | Decisión del director sobre el valor académico del experimento proxy (exp-proxy-001) y posibles experimentos adicionales (log(y), sin coordenadas, subset sin construcción) | Alcance del artículo | Director disciplinar | Criterio formal sobre qué se publica como resultado experimental | ABIERTO |
| 14 | Decisión del director sobre cómo presentar el valor del suelo en el software tras la Fase 5: opción A (consulta directa de referencia zonal ZHG, no-ML), opción B (modelo ML experimental con limitaciones) u opción C (solicitar datos de valor exclusivo de terreno) | Componente predictivo del anteproyecto | Director disciplinar + equipo | Decisión documentada; mientras tanto `POST /predictions` sigue 503 | ABIERTO (Fase 5 concluyó sin ganador; ver docs/06) |
| 13 | Inferencia online del modelo experimental: ¿activar `POST /predictions` con el artefacto proxy marcado como experimental, o mantener 503 global hasta etiqueta validada? | Diseño Fase 3/8 | Director + equipo | Decisión documentada antes de exponer inferencia | **RESUELTO (Fase 3):** oficial → 503 global; experimental → `POST /predictions/experimental` desactivado por defecto y solo desarrollo (ADR-0004). Sigue pendiente la aprobación académica del proxy (#12) |
