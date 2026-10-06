"""Interface de démonstration Streamlit pour le risque de pluie."""
from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.environ.get("GOUTTE_API_URL", "http://127.0.0.1:8000")
RISK_COLORS = {
    "faible": "#1a7f37",
    "modéré": "#9a6700",
    "élevé": "#bc4c00",
    "très élevé": "#b35900",
}

session = requests.Session()
session.trust_env = False


@st.cache_data(ttl=60)
def get_json(path: str) -> dict:
    response = session.get(f"{API_URL}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict) -> list[dict]:
    response = session.post(f"{API_URL}{path}", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def gauge(probability: float, level: str, alert_threshold: float) -> go.Figure:
    cutoff = min(alert_threshold * 100, 50)
    figure = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": " %", "font": {"size": 44}},
        title={"text": "Probabilité de pluie"},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": " %"},
            "bar": {"color": RISK_COLORS.get(level, "#376b80")},
            "steps": [
                {"range": [0, cutoff], "color": "#e6f4ea"},
                {"range": [cutoff, 50], "color": "#fff8e1"},
                {"range": [50, 75], "color": "#fde7d6"},
                {"range": [75, 100], "color": "#fbe0e0"},
            ],
        },
    ))
    figure.update_layout(height=320, margin=dict(t=60, b=10))
    return figure


def main() -> None:
    st.set_page_config(page_title="Goutte d'eau - Risque de pluie")
    st.title("Projet Goutte d'eau — Risque de pluie")
    st.caption("Estimation du risque de pluie par date, à destination des agriculteurs.")

    try:
        health = get_json("/health")
        model_info = get_json("/model-info")
    except Exception as exc:
        st.error(f"API injoignable sur {API_URL}. Lancez l'API puis rechargez. ({exc})")
        st.stop()

    data_range = health.get("data_range", {})
    st.sidebar.header("Paramètres")
    st.sidebar.write(f"**Station :** {model_info.get('station_name', '-')}")
    st.sidebar.write(f"**Données :** {data_range.get('from')} → {data_range.get('to')}")

    default_day = date.fromisoformat(data_range["to"]) if data_range.get("to") else date.today()
    chosen = st.date_input(
        "Choisissez une date",
        value=default_day,
        help="Date pour laquelle estimer le risque de pluie.",
    )

    if st.button("Estimer le risque", type="primary"):
        try:
            data = get_json(f"/predict?date={chosen.isoformat()}")
            first_column, second_column = st.columns([1, 1])
            with first_column:
                st.plotly_chart(
                    gauge(
                        data["rain_probability"],
                        data["risk_level"],
                        data["alert_probability_threshold"],
                    ),
                    use_container_width=True,
                )
            with second_column:
                st.metric("Risque de pluie", f"{data['rain_probability']:.0%}")
                st.markdown(f"### Niveau de risque : **{data['risk_level'].upper()}**")
                st.write(data["note"])

            days = [chosen + timedelta(days=offset) for offset in range(-3, 11)]
            predictions = post_json(
                "/predict/batch", {"dates": [day.isoformat() for day in days]}
            )
            probabilities = [item["rain_probability"] for item in predictions]
            series = pd.DataFrame({
                "date": days,
                "probabilité (%)": [value * 100 for value in probabilities],
            })
            st.subheader("Évolution du risque sur 14 jours")
            st.line_chart(series, x="date", y="probabilité (%)")
        except requests.RequestException as exc:
            st.error(f"La prédiction n'a pas abouti : {exc}")

    st.divider()
    with st.expander("Indicateurs qualité du modèle"):
        selected = model_info["test_metrics"]["at_selected"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROC-AUC", model_info["test_metrics"]["at_0.5"]["roc_auc"])
        c2.metric("PR-AUC", model_info["test_metrics"]["at_0.5"]["pr_auc"])
        c3.metric("Brier score", model_info["test_metrics"]["at_0.5"]["brier"])
        c4.metric("Précision au seuil validé", selected["precision"])
        st.caption(
            f"Modèle : {model_info['selected_model']} — seuil de validation : "
            f"{model_info['test_metrics']['selected_threshold']:.4f}. "
            f"Test : {model_info['n_test']} jours à partir de {model_info['test_from_year']}."
        )


if __name__ == "__main__":
    main()
