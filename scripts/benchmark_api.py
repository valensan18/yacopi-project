"""Benchmark de latencia de la API (mediciones reales, no umbrales inventados).

Uso:
  python scripts/benchmark_api.py [--base http://127.0.0.1:8000] [--n 100]

Mide p50/p95/p99 de consulta, estadísticas, mapa y predicción experimental
(si está habilitada). Solo lectura; no modifica datos.
"""

import argparse
import statistics
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"

EXPERIMENTAL_PAYLOAD = {
    "features": {
        "area_terreno_catastral_m2": 50000,
        "area_construida_m2": 0,
        "tr_latitud": 5.55,
        "tr_longitud": -74.35,
        "destino_economico": "Agropecuario",
        "zhf_codigo": "05",
        "zhf_dispon": "4",
        "zhf_influe": "3",
        "zhf_uso_ac": "16",
        "aht_vpoten": "23",
        "vus_vocaci": "ASPp",
        "ups": "Zonas de desarrollo agropecuario sin restricciones",
    },
}


def measure(client, method, url, n, **kwargs) -> dict:
    latencies = []
    statuses = []
    for _ in range(n):
        start = time.perf_counter()
        response = client.request(method, url, **kwargs)
        latencies.append((time.perf_counter() - start) * 1000)
        statuses.append(response.status_code)
    latencies.sort()
    return {
        "n": n,
        "p50_ms": round(statistics.median(latencies), 1),
        "p95_ms": round(latencies[int(n * 0.95) - 1], 1),
        "p99_ms": round(latencies[int(n * 0.99) - 1], 1),
        "ok": statuses.count(200),
        "errores": n - statuses.count(200),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--n", type=int, default=100)
    args = parser.parse_args()

    results = {}
    with httpx.Client(base_url=args.base, timeout=30) as client:
        results["health_live"] = measure(client, "GET", "/health/live", args.n)
        results["system_status"] = measure(client, "GET", "/system/status", args.n)
        results["properties_l20"] = measure(
            client, "GET", "/properties", args.n, params={"limit": 20}
        )
        results["properties_filtradas"] = measure(
            client, "GET", "/properties", args.n,
            params={"destino": "Agropecuario", "limit": 20},
        )
        results["statistics_overview"] = measure(
            client, "GET", "/statistics/overview", args.n
        )
        results["maps_points_1000"] = measure(
            client, "GET", "/maps/points", args.n, params={"limit": 1000}
        )
        exp = client.get("/system/status").json()["experimental_model"]
        if exp.get("habilitado") and exp.get("disponible"):
            results["prediccion_experimental"] = measure(
                client, "POST", "/predictions/experimental", args.n,
                json=EXPERIMENTAL_PAYLOAD,
            )
        else:
            results["prediccion_experimental"] = "inferencia desactivada"

    for name, metrics in results.items():
        if isinstance(metrics, str):
            print(f"{name}: {metrics}")
            continue
        print(
            f"{name}: n={metrics['n']} p50={metrics['p50_ms']} ms "
            f"p95={metrics['p95_ms']} ms p99={metrics['p99_ms']} ms "
            f"ok={metrics['ok']} errores={metrics['errores']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
