import json
from pathlib import Path

h = json.loads(Path("ml/artifacts/exp-zhg-001/metrics.json").read_text(encoding="utf-8"))
r = json.loads(Path("ml/artifacts/exp-zhg-rerun/metrics.json").read_text(encoding="utf-8"))
print("ZHG dominante — historico vs rerun (particiones actuales)")
print(
    f"{'modelo':9s} {'hist predio':>12s} {'rerun predio':>12s} "
    f"{'hist zona':>12s} {'rerun zona':>12s}"
)
for k in h["scenarios"]:
    print(
        f"{k:9s} {h['scenarios'][k]['predio']['r2']:>+12.3f} "
        f"{r['scenarios'][k]['predio']['r2']:>+12.3f} "
        f"{h['scenarios'][k]['zona']['r2']:>+12.3f} "
        f"{r['scenarios'][k]['zona']['r2']:>+12.3f}"
    )
print("criterio rerun:", r.get("criterio_aceptacion"))
print("n rerun:", r.get("n_predios"))
