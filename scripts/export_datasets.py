"""Export local de la table quotidienne et du jeu utilisé pour le modèle."""
from __future__ import annotations

import pandas as pd

import config
from src import database
from src.features import build_feature_frame, feature_row_mask


def main() -> None:
    database.init_db()
    conn = database.get_connection()
    try:
        daily = pd.read_sql_query(
            "SELECT * FROM daily WHERE station_id = ? ORDER BY obs_date",
            conn,
            params=(config.STATION_ID,),
        )
    finally:
        conn.close()
    if daily.empty:
        raise RuntimeError("Table 'daily' vide : lancez d'abord la collecte.")

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    daily.to_csv(config.DATA_DIR / "daily.csv", index=False)

    features, target = build_feature_frame(daily)
    ordered = daily.sort_values("obs_date").reset_index(drop=True)
    eligible = feature_row_mask(ordered)
    dates = ordered.loc[eligible, "obs_date"].reset_index(drop=True)
    if len(dates) != len(features):
        raise RuntimeError("Les dates exportees ne sont pas alignees avec les features.")

    model_dataset = pd.concat(
        [dates.rename("obs_date"), features, target.rename("is_rainy")], axis=1
    )
    model_dataset.to_csv(config.DATA_DIR / "model_dataset.csv", index=False)
    print(f"Export quotidien : {config.DATA_DIR / 'daily.csv'} ({len(daily)} lignes)")
    print(
        f"Jeu de modele : {config.DATA_DIR / 'model_dataset.csv'} "
        f"({len(model_dataset)} lignes, {len(features.columns)} variables)"
    )


if __name__ == "__main__":
    main()