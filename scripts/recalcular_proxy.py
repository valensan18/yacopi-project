import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

p = pd.read_csv("ml/artifacts/exp-proxy-001/predictions_test.csv")
for part, g in p.groupby("particion"):
    print(
        f"{part}: n={len(g)} "
        f"R2={r2_score(g.y_true_cop_ha, g.y_pred_cop_ha):+.4f} "
        f"MAE={mean_absolute_error(g.y_true_cop_ha, g.y_pred_cop_ha):,.0f}"
    )
