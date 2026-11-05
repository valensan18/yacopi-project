"""Genera y ejecuta los 13 cuadernos de reproduccion de la entrega docente.

Los cuadernos se crean en entrega_docente/notebooks/ con salidas reales.
Marcados como posteriores (no existian cuadernos originales en el repo).
Cada cuaderno declara su tipo: ENTRENA (ajusta modelos) o CONSULTA (lee
resultados previamente generados). Rutas portables: la raiz del repositorio
se resuelve en tiempo de ejecucion buscando data/raw.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "entrega_docente" / "notebooks"
OUT.mkdir(parents=True, exist_ok=True)

SHA_INT = hashlib.sha256(
    (ROOT / "data" / "raw" / "interseccion_terrenos_zhg_r1_yacopi.csv").read_bytes()
).hexdigest()
SHA_ZHF = hashlib.sha256((ROOT / "data" / "raw" / "zhf_yacopi.csv").read_bytes()).hexdigest()

NOTE = (
    "> **Cuaderno de reproducción (posterior).** Generado el 2026-10-23 como parte de la "
    "entrega docente. El repositorio original no contenía cuadernos versionados; "
    "estos reconstruyen los análisis a partir de los scripts y módulos existentes."
)

CELDA_RAIZ = (
    "import os\n"
    "from pathlib import Path\n\n"
    "def _raiz_repositorio() -> Path:\n"
    "    for p in [Path.cwd(), *Path.cwd().parents]:\n"
    "        if (p / 'data' / 'raw' / 'interseccion_terrenos_zhg_r1_yacopi.csv').exists():\n"
    "            return p\n"
    "    raise FileNotFoundError('No se encontro la raiz del repositorio (busca data/raw)')\n\n"
    "REPO = _raiz_repositorio()\n"
    "print('Raiz del repositorio resuelta (carpeta):', REPO.name, '| data/raw encontrado')"
)


def nb(titulo: str, tipo: str, celdas: list) -> None:
    notebook = new_notebook(
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.14"},
        },
        cells=[
            new_markdown_cell(f"# {titulo}\n\n{NOTE}\n\n**Tipo de ejecución: {tipo}**"),
            new_code_cell(CELDA_RAIZ),
            *celdas,
        ],
    )
    client = NotebookClient(notebook, timeout=900, kernel_name="python3")
    client.execute()
    partes = [p.strip().replace(" ", "_") for p in titulo.split("|")]
    nombre = "_".join(p for p in partes if p)
    (OUT / f"{nombre}.ipynb").write_text(nbformat.writes(notebook), encoding="utf-8")
    print("OK", titulo)


md = new_markdown_cell
cd = new_code_cell

TIPO_CONSULTA = "CONSULTA — lee resultados previamente generados; NO entrena modelos."
TIPO_CARGA = "CARGA DE DATOS — lee los CSV crudos; NO entrena modelos."
TIPO_ENTRENA = "ENTRENA — ajusta modelos reales sobre el dataset (puede tardar minutos)."

# ---------------------------------------------------------------- 00
nb(
    "00 | Contexto y trazabilidad",
    TIPO_CONSULTA,
    [
        md("## Repositorio y rama\n\nEstado de Git y artefactos que soportan este paquete."),
        cd("import subprocess\nsubprocess.run(['git', 'log', '--oneline', '-8'], cwd=REPO)"),
        cd("print('artifacts:')\n"
           "for p in sorted((REPO / 'ml' / 'artifacts').glob('exp-*')):\n"
           "    if p.is_dir():\n"
           "        files = sorted(f.name for f in p.glob('*'))\n"
           "        print(' ', p.name, '->', files[:5])"),
        md("## Nota\n\nLos CSV originales no se incluyen en el paquete (datos privados); "
           "se referencian por hash (ver manifiesto)."),
    ],
)

# ---------------------------------------------------------------- 01
nb(
    "01 | Carga y auditoría de datos",
    TIPO_CARGA,
    [
        md("## Fuentes\n\nCarga de los dos CSV crudos y resumen de calidad."),
        cd("import pandas as pd\n"
           "inter = pd.read_csv(REPO / 'data/raw/interseccion_terrenos_zhg_r1_yacopi.csv', low_memory=False)\n"
           "zhf = pd.read_csv(REPO / 'data/raw/zhf_yacopi.csv', low_memory=False)\n"
           "print('intersecciones:', inter.shape, '| predios unicos:', inter.numero_predial.nunique())\n"
           "print('zhf:', zhf.shape, '| codpred unicos:', zhf.CODPRED.nunique())\n"
           "print('sha256 interseccion:', '" + SHA_INT + "')\n"
           "print('sha256 zhf:', '" + SHA_ZHF + "')"),
        cd("cols = ['valor_avaluo','area_terreno_m2','area_construida_m2']\n"
           "resumen = inter[cols].agg(['count', lambda s: s.isna().sum(),"
           " lambda s: (s==0).sum(), lambda s: (s<0).sum(), 'min','median','max'])\n"
           "resumen.index = ['n','nulos','ceros','negativos','min','mediana','max']\n"
           "resumen"),
        md("## Lectura\n\nSin nulos ni negativos en avalúo y áreas; 5.793 filas con "
           "construcción = 0. La construcción faltante NO se interpreta como ausencia "
           "comprobada de edificaciones."),
    ],
)

# ---------------------------------------------------------------- 02
nb(
    "02 | Estadística descriptiva",
    TIPO_CARGA,
    [
        md("## Descriptivos y distribuciones"),
        cd("import pandas as pd\n"
           "inter = pd.read_csv(REPO / 'data/raw/interseccion_terrenos_zhg_r1_yacopi.csv', low_memory=False)\n"
           "print('destinos:')\n"
           "print(inter.destino_economico.value_counts().head(6))\n"
           "print('\\nzonas ZHG:', inter.codigo_zona_geoeconomica.nunique())\n"
           "print('valor zonal COP/ha: min', inter.valor_hectarea_agropecuario.min(),\n"
           "      'mediana', inter.valor_hectarea_agropecuario.median(),\n"
           "      'max', inter.valor_hectarea_agropecuario.max())"),
        cd("import matplotlib.pyplot as plt\n"
           "plt.rcParams['figure.dpi'] = 100\n"
           "fig, axs = plt.subplots(1, 3, figsize=(12, 3))\n"
           "axs[0].hist(inter.valor_avaluo / 1e6, bins=40); axs[0].set_title('Avalúo (M COP)')\n"
           "axs[1].hist(inter.area_terreno_m2, bins=40); axs[1].set_title('Área terreno (m²)')\n"
           "axs[2].hist(inter.area_construida_m2, bins=40); axs[2].set_title('Área construida (m²)')\n"
           "plt.tight_layout(); plt.show()"),
    ],
)

# ---------------------------------------------------------------- 03
nb(
    "03 | Variable respuesta ZHG",
    TIPO_CONSULTA,
    [
        md("## Objetivo ZHG (Fase 5)\n\n`valor_zona_dominante_cop_ha`: referencia zonal; "
           "solo 11 valores posibles (uno por zona)."),
        cd("import json\n"
           "m = json.loads((REPO / 'ml/artifacts/exp-zhg-001/metrics.json').read_text(encoding='utf-8'))\n"
           "print('predios:', m['n_predios'], '| zonas:', m['n_zonas'], "
           "'| valores unicos del objetivo:', m['valores_objetivo_unicos'])\n"
           "print('cobertura:', m['cobertura'])"),
        cd("print('Resultados de los 5 modelos en el test con zonas completas fuera:')\n"
           "for nombre, res in m['scenarios'].items():\n"
           "    z = res['zona']\n"
           "    print(f\"  {nombre:9s} n={z['n']} MAE={z['mae_cop_ha']:>10.0f} "
           "R2={z['r2']:>8.2f}\")"),
        md("## Interpretación\n\nCon zonas enteras fuera del entrenamiento, todos los "
           "modelos colapsan (R² negativos): identificar la zona era la vía de "
           "memorización. Por eso ningún modelo de Fase 5 fue aprobado."),
    ],
)

# ---------------------------------------------------------------- 04
nb(
    "04 | Variable respuesta avalúo",
    TIPO_CARGA,
    [
        md("## VALOR_TERRENO_Ha = VALOR_AVALUO × 10000 / AREA_TERRENO_M2\n\n"
           "Nueva variable comunicada por el profesor. El avalúo es catastral TOTAL; "
           "no hay campo de valor exclusivo de terreno."),
        cd("import sys\nsys.path.insert(0, str(REPO / 'ml' / 'src'))\n"
           "from yacopi_ml.valor.dataset import cargar_intersecciones\n"
           "df = cargar_intersecciones()\n"
           "df['valor_terreno_ha'] = df['valor_avaluo'] * 10000 / df['area_terreno_m2']\n"
           "print('valores unicos:', df['valor_terreno_ha'].nunique())\n"
           "print(df['valor_terreno_ha'].describe().round(0).to_string())"),
        cd("import numpy as np\n"
           "print('Igualdad exacta con zonal x area: %: ',\n"
           "      np.isclose(df['valor_avaluo'],\n"
           "                 df['area_terreno_m2']*df['valor_hectarea_agropecuario']/10000,\n"
           "                 rtol=1e-6).mean()*100)\n"
           "print('corr(avaluo, zonal x area) =',\n"
           "      df[['valor_avaluo','valor_hectarea_agropecuario']].corr().iloc[0,1].round(3))"),
        md("## Lectura\n\nLa variable NO es copia del valor zonal (0 % de igualdad "
           "exacta; 5.654 valores únicos), pero está fuertemente asociada a él "
           "(corr 0,73). No es valor comercial."),
    ],
)

# ---------------------------------------------------------------- 05
nb(
    "05 | Filtros y decisiones",
    TIPO_CARGA,
    [
        md("## Escenarios de construcción\n\nA: construcción == 0 · B: 0 < construcción ≤ 32 m².\n"
           "El umbral se aplica sobre CONSTRUCCIÓN, no sobre el terreno."),
        cd("import sys\nsys.path.insert(0, str(REPO / 'ml' / 'src'))\n"
           "from yacopi_ml.valor.dataset import cargar_intersecciones\n"
           "df = cargar_intersecciones()\n"
           "a = df[df.area_construida_m2 == 0]\n"
           "b = df[(df.area_construida_m2 > 0) & (df.area_construida_m2 <= 32)]\n"
           "print('A: filas', len(a), '| predios', a.numero_predial.nunique())\n"
           "print('B: filas', len(b), '| predios', b.numero_predial.nunique())\n"
           "print('excluidos (>32 m2):', (df.area_construida_m2 > 32).sum(), 'filas')\n"
           "print('nulos construccion:', df.area_construida_m2.isna().sum())"),
        md("## Decisiones documentadas\n\n- Nada se elimina silenciosamente: los "
           "extremos se reportan con análisis de sensibilidad.\n"
           "- La ausencia de dato de construcción no se asume como cero."),
    ],
)

# ---------------------------------------------------------------- 06
nb(
    "06 | Variables predictoras",
    TIPO_CONSULTA,
    [
        md("## Features permitidas y excluidas\n\nSin fuga: se excluyen avalúo, "
           "valores y códigos zonales."),
        cd("import sys\nsys.path.insert(0, str(REPO / 'ml' / 'src'))\n"
           "from yacopi_ml.valor.dataset import (FEATURES_EXCLUIDAS, CATEGORICAS, NUMERICAS)\n"
           "print('excluidas (fuga):', sorted(FEATURES_EXCLUIDAS))\n"
           "print('numericas:', NUMERICAS)\n"
           "print('categoricas (%d):' % len(CATEGORICAS), CATEGORICAS)"),
        cd("import json\n"
           "d = json.loads((REPO / 'ml/artifacts/exp-valor-terreno-001/desgloses_esc_A.json').read_text(encoding='utf-8'))\n"
           "print('correlaciones feature-y (top 8):')\n"
           "for k, v in d['correlaciones_top'][:8]:\n"
           "    print(f'  {k:22s} {v:+.3f}')"),
        md("## Lectura\n\nCorrelaciones lineales débiles: la señal predictiva está en "
           "interacciones (principalmente geográficas), no en una sola variable."),
    ],
)

# ---------------------------------------------------------------- 07
nb(
    "07 | Construcción de los modelos",
    TIPO_CONSULTA,
    [
        md("## Código real del protocolo v2 (actual)\n\n"
           "`ml/src/yacopi_ml/valor/modelos.py` define `preprocesador`, "
           "`entrenar_modelos` (Dummy, Ridge log, Árbol, RandomForest, CatBoost) y "
           "`predecir`. Es el módulo ejecutado por train.py y audit_r2.py."),
        cd("src = (REPO / 'ml/src/yacopi_ml/valor/modelos.py').read_text(encoding='utf-8')\n"
           "print(src)"),
        md("## Código histórico de Fase 2 (NO es el protocolo actual)\n\n"
           "`ml/src/yacopi_ml/models.py` pertenece al experimento proxy histórico con "
           "búsqueda de hiperparámetros (seed 42). Se conserva como evidencia, no se "
           "usa en el protocolo v2 (que usa hiperparámetros fijos y semilla 20261023)."),
        cd("src = (REPO / 'ml/src/yacopi_ml/models.py').read_text(encoding='utf-8')\n"
           "print(src[:2600])"),
    ],
)

# ---------------------------------------------------------------- 08
nb(
    "08 | Entrenamiento y validación",
    TIPO_ENTRENA,
    [
        md("## Entrenamiento real (escenario A)\n\n"
           "Se ajustan los 5 modelos con el módulo del protocolo v2. Primero el "
           "protocolo por predios; luego el protocolo espacial independiente."),
        cd("import sys\nsys.path.insert(0, str(REPO / 'ml' / 'src'))\n"
           "from yacopi_ml.valor.dataset import construir_dataset, seleccionar_features\n"
           "from yacopi_ml.valor.splits import dividir_predios, dividir_espacial\n"
           "from yacopi_ml.valor.modelos import entrenar_modelos, predecir\n"
           "ds = construir_dataset('A')\n"
           "X, y, _, _ = seleccionar_features(ds)\n"
           "ds = ds.assign(**{c: X[c] for c in X.columns})\n"
           "tr, te = dividir_predios(ds)\n"
           "tr_esp, te_esp = dividir_espacial(ds)\n"
           "print('train/test predio:', len(tr), '/', len(te))\n"
           "print('train/test espacial:', len(tr_esp), '/', len(te_esp))\n"
           "print('solape tr_predio vs te_esp:', len(set(tr.numero_predial) & set(te_esp.numero_predial)))\n"
           "print('solape tr_esp vs te_esp:', len(set(tr_esp.numero_predial) & set(te_esp.numero_predial)))"),
        cd("modelos = entrenar_modelos(tr[X.columns], tr['valor_terreno_ha'])\n"
           "preds = predecir(modelos, te[X.columns])\n"
           "from sklearn.metrics import r2_score\n"
           "print('PROTOCOLO PREDIO (entrena con tr, evalua con te):')\n"
           "for nombre, p in preds.items():\n"
           "    print(f'  {nombre:14s} R2={r2_score(te.valor_terreno_ha, p):+.3f}')"),
        md("## Evidencia de la contaminación v1 (ya corregida en v2)\n\n"
           "En la versión v1, el modelo entrenado con `tr` (partición aleatoria) se "
           "evaluaba sobre `te_esp`: **560 de 689 predios del test espacial (81,3 %) "
           "ya estaban en el entrenamiento**. En v2 el protocolo espacial entrena una "
           "instancia NUEVA con `tr_esp` y solo entonces evalúa `te_esp` (solape 0)."),
        cd("modelos_esp = entrenar_modelos(tr_esp[X.columns], tr_esp['valor_terreno_ha'])\n"
           "preds_esp = predecir(modelos_esp, te_esp[X.columns])\n"
           "print('PROTOCOLO ESPACIAL INDEPENDIENTE (entrena con tr_esp, evalua con te_esp):')\n"
           "for nombre, p in preds_esp.items():\n"
           "    print(f'  {nombre:14s} R2={r2_score(te_esp.valor_terreno_ha, p):+.3f}')"),
        cd("import json\n"
           "r = json.loads((REPO / 'ml/artifacts/exp-valor-terreno-001/resumen.json').read_text(encoding='utf-8'))\n"
           "for esc in ['A','B']:\n"
           "    print('== escenario', esc, '==')\n"
           "    for proto in ['predio','espacial']:\n"
           "        p = r[esc]['protocolos'][proto]\n"
           "        print(' --', proto, 'train/test:', p['n_train'], '/', p['n_test'])\n"
           "        for nombre, res in p['resultados'].items():\n"
           "            if nombre.startswith('_') or isinstance(res, list): continue\n"
           "            print(f\"    {nombre:16s} MAE={res['mae_cop_ha']:>11.0f} R2={res['r2']:+.3f}\")"),
    ],
)

# ---------------------------------------------------------------- 09
nb(
    "09 | Métricas y comparación",
    "RECÁLCULO — calcula métricas desde predicciones guardadas (y_true/y_pred); NO entrena.",
    [
        md("## Recálculo desde pares y_true/y_pred\n\n"
           "Se leen las predicciones guardadas por `audit_r2.py` (protocolo v2) y se "
           "recalculan MAE, RMSE y R² con sklearn para los 5 modelos del escenario A "
           "en ambos protocolos, contrastando con `resumen.json`."),
        cd("import pandas as pd\n"
           "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\n"
           "import numpy as np, json\n"
           "modelos = ['dummy_media','arbol','random_forest','ridge_log','catboost']\n"
           "base = REPO / 'ml/artifacts/exp-valor-terreno-001/audit_r2'\n"
           "resumen = json.loads((REPO / 'ml/artifacts/exp-valor-terreno-001/resumen.json').read_text(encoding='utf-8'))\n"
           "filas = []\n"
           "for particion in ['test_predio','test_espacial']:\n"
           "    for modelo in modelos:\n"
           "        d = pd.read_csv(base / f'preds_A_{modelo}_{particion}.csv')\n"
           "        y, yp = d.y_true.to_numpy(), d.y_pred.to_numpy()\n"
           "        m = {'modelo': modelo, 'particion': particion, 'n': len(d),\n"
           "             'mae': mean_absolute_error(y, yp),\n"
           "             'rmse': float(np.sqrt(mean_squared_error(y, yp))),\n"
           "             'r2': r2_score(y, yp)}\n"
           "        filas.append(m)\n"
           "tabla = pd.DataFrame(filas)\n"
           "print(tabla.round(3).to_string(index=False))"),
        cd("print('Contraste con resumen.json (deben coincidir):')\n"
           "for _, f in tabla.iterrows():\n"
           "    r = resumen['A']['protocolos'][{'test_predio':'predio','test_espacial':'espacial'}[f.particion]]['resultados'][f.modelo]\n"
           "    ok = (abs(r['mae_cop_ha'] - f.mae) < 1) and (abs(r['r2'] - f.r2) < 1e-6)\n"
           "    print(f\"  {f.modelo:14s} {f.particion:14s} coincide={ok}\")"),
        md("## Lectura\n\nLas métricas recalculadas aquí provienen de predicciones "
           "generadas previamente por `audit_r2.py`; este cuaderno NO reentrena."),
    ],
)

# ---------------------------------------------------------------- 10
nb(
    "10 | Investigación de R² negativos",
    "ENTRENA ejemplo didáctico — regresión lineal de juguete (NO es un experimento del proyecto).",
    [
        md("## Fórmula\n\n`R² = 1 − Σ(y−ŷ)² / Σ(y−ȳ)²`\n\n"
           "R² < 0 ⇒ el modelo tiene más error cuadrático que predecir la media "
           "del conjunto evaluado. No es un porcentaje de aciertos."),
        cd("import numpy as np\n"
           "from sklearn.linear_model import LinearRegression\n"
           "from sklearn.metrics import r2_score\n"
           "rng = np.random.default_rng(7)\n"
           "x_tr = np.linspace(0, 2, 60)\n"
           "y_tr = (x_tr - 3)**2 + rng.normal(0, 0.2, size=60)\n"
           "x_te = np.linspace(6, 10, 60)\n"
           "y_te = (x_te - 3)**2 + rng.normal(0, 0.2, size=60)\n"
           "m = LinearRegression().fit(x_tr.reshape(-1, 1), y_tr)\n"
           "pred = m.predict(x_te.reshape(-1, 1))\n"
           "print('R2 en prueba (entrenamiento y prueba separados) =', round(r2_score(y_te, pred), 3))\n"
           "print('=> R2 negativo SIN error de programacion: la recta no extrapola la parabola')"),
        cd("import matplotlib.pyplot as plt\n"
           "plt.figure(figsize=(6,4))\n"
           "plt.scatter(x_tr, y_tr, s=8, label='entrenamiento')\n"
           "plt.scatter(x_te, y_te, s=8, label='prueba')\n"
           "xs = np.linspace(0, 10, 50)\n"
           "plt.plot(xs, m.predict(xs.reshape(-1,1)), 'r', label='recta')\n"
           "plt.title('Ejemplo didáctico (no es un resultado del proyecto)')\n"
           "plt.legend(); plt.show()"),
        md("## Casos negativos reales de Atlas Vivo\n\n"
           "Ver `AUDITORIA_R2_ATLAS_VIVO.md`. Resumen:\n"
           "- Baseline ≈ 0 (por construcción).\n"
           "- ZHG con zonas fuera: −1,70 (RF) y −2,18 (CatBoost).\n"
           "- LOZO con varianza casi nula: −1e30 / NaN (R² indefinido).\n"
           "- Escenario B: extremos por áreas mínimas dominan el error.\n"
           "- v2 espacial A (CatBoost −0,075): bloques geográficos no vistos."),
    ],
)

# ---------------------------------------------------------------- 11
nb(
    "11 | Generalización espacial",
    TIPO_CONSULTA,
    [
        md("## LOZO (leave-one-zone-out)\n\n"
           "Generado por `ml/src/yacopi_ml/valor/evaluate.py` y guardado en "
           "`desgloses_esc_A.json`. Cada zona se evalúa con un CatBoost entrenado "
           "sobre TODAS las demás zonas (la zona evaluada nunca aparece en su "
           "entrenamiento)."),
        cd("import json\n"
           "d = json.loads((REPO / 'ml/artifacts/exp-valor-terreno-001/desgloses_esc_A.json').read_text(encoding='utf-8'))\n"
           "print('MAE CatBoost dejando cada zona completa fuera (LOZO):')\n"
           "for k, v in sorted(d['lozo_por_zona'].items()):\n"
           "    print(f\"  zona {k:>3s} n={v['n']:>4d} MAE={v['mae_cop_ha']:>10.0f} R2={v['r2']:+.3f}\")\n"
           "print('suma de n:', d['lozo_suma_n'])"),
        md("## Por qué antes aparecían 4.668 registros (y no 4.676)\n\n"
           "El LOZO original excluía zonas con menos de 30 predios: la zona 1 tiene "
           "**8 predios** y quedaba fuera (4.676 − 8 = 4.668). En la revisión de "
           "cierre se eliminó ese umbral: ahora se evalúan las 11 zonas y la suma "
           "coincide con los 4.676 predios del escenario A."),
        cd("import sys\nsys.path.insert(0, str(REPO / 'ml' / 'src'))\n"
           "from yacopi_ml.valor.dataset import construir_dataset\n"
           "ds = construir_dataset('A')\n"
           "print('zona 1 en escenario A:', int((ds.codigo_zona_dominante == '1').sum()), 'predios')\n"
           "print('zonas en A:', ds.codigo_zona_dominante.unique().tolist())"),
        cd("print('Verificacion de independencia LOZO (por construccion, evalua evaluate.py):')\n"
           "for zona, g in ds.groupby('codigo_zona_dominante'):\n"
           "    tr_z = ds[ds.codigo_zona_dominante != zona]\n"
           "    assert not set(tr_z.numero_predial) & set(g.numero_predial)\n"
           "print('  OK: en ninguna zona hay solapamiento con su entrenamiento')"),
        md("## Lectura\n\nEl desempeño depende de la partición: test predio (aleatorio) "
           "vs test espacial (bloques) vs LOZO (zonas fuera). La buena métrica en test "
           "predio NO garantiza generalización a zonas no vistas."),
    ],
)

# ---------------------------------------------------------------- 12
nb(
    "12 | Conclusiones y decisiones",
    TIPO_CONSULTA,
    [
        md("## Síntesis para la revisión docente"),
        cd("print('\\n'.join([\n"
           " '1. Datos: 9.447 filas interseccion + 7.968 ZHF -> 7.709 predios consolidados.',\n"
           " '2. Variables objetivo distintas por experimento (proxy, ZHG, VALOR_TERRENO_Ha, demo).',\n"
           " '3. Fase 5 ZHG: rechazado (no generaliza a zonas nuevas; R2 negativos).',\n"
           " '4. VALOR_TERRENO_Ha v2: protocolos independientes; espacial A RF R2 0,171 / CatBoost -0,075.',\n"
           " '5. R2 negativos: baselines, zonas/bloques no vistos, extremos, varianza casi nula.',\n"
           " '6. NO existe modelo definitivo aprobado; la prediccion oficial sigue 503.',\n"
           "]))"),
        cd("print('Preguntas al profesor (ver PREGUNTAS_PARA_EL_PROFESOR.md):')\n"
           "print(' - fecha/procedencia del avaluo')\n"
           "print(' - avaluo total vs exclusivo de terreno')\n"
           "print(' - criterio para areas minimas')\n"
           "print(' - alcance interpretativo (refinar la referencia zonal)')"),
    ],
)

print("cuadernos generados y ejecutados en", OUT)
