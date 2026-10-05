"""Interface de demonstration du MVP Projet Goutte d'eau (Streamlit).

Objectif : prouver le fonctionnement du modele de facon accessible.
L'interface interroge l'API REST et restitue :
- le risque de pluie pour une date choisie (jauge + libelle) ;
- la courbe de risque sur une periode ;
- les indicateurs qualite du modele.

Accessibilite (RGAA/WCAG) : libelles explicites, contrastes eleves,
information jamais portee par la seule couleur (texte + valeur + icone).

Lancement :
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.environ.get("GOUTTE_API_URL", "http://127.0.0.1:8000")

# Palette accessible (contraste AA) + icone pour ne pas dependre de la couleur.
RISK_STYLE = {
    "faible": ("#1a7f37", "✅"),
    "modere": ("#9a6700", "🟡"),
    "eleve": ("#bc4c00", "🟠"),
    "tres eleve": ("#b35900", "🔴"),
}

session = requests.Session()
session.trust_env = False  # ignore le proxy pour l'appel localhost


@st.cache_data(ttl=60)
def get_json(path: str) -> dict:
    resp = session.get(f"{API_URL}{path}", timeout=20)
    resp.raise_for_status()
    return resp.json()


def gauge(probability: float, level: str) -> go.Figure:
    color = RISK_STYLE.get(level, ("#1f77b4", ""))[0]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": " %", "font": {"size": 44}},
        title={"text": "Probabilite de pluie"},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": " %"},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 25], "color": "#e6f4ea"},
                {"range": [25, 50], "color": "#fff8e1"},
                {"range": [50, 75], "color": "#fde7d6"},
                {"range": [75, 100], "color": "#fbe0e0"},
            ],
        },
    ))
    fig.update_layout(height=320, margin=dict(t=60, b=10))
    return fig


def main() -> None:
    st.set_page_config(page_title="Goutte d'eau - Risque de pluie", page_icon="🌧️")
    st.title("🌧️ Projet Goutte d'eau — Risque de pluie")
    st.caption("Estimation du risque de pluie par date, a destination des agriculteurs.")

    # Etat du service.
    try:
        health = get_json("/health")
    except Exception as exc:
        st.error(f"API injoignable sur {API_URL}. Lancez l'API puis rechargez. ({exc})")
        st.stop()

    rng = health.get("data_range", {})
    st.sidebar.header("Parametres")
    st.sidebar.write(f"**Station :** {get_json('/model-info').get('station_name', '-')}")
    st.sidebar.write(f"**Donnees :** {rng.get('from')} → {rng.get('to')}")

    default_day = date.fromisoformat(rng["to"]) if rng.get("to") else date.today()
    chosen = st.date_input("Choisissez une date", value=default_day,
                           help="Date pour laquelle estimer le risque de pluie.")

    if st.button("Estimer le risque", type="primary"):
        data = get_json(f"/predict?date={chosen.isoformat()}")
        proba = data["rain_probability"]
        level = data["risk_level"]
        color, icon = RISK_STYLE.get(level, ("#1f77b4", "ℹ️"))

        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(gauge(proba, level), use_container_width=True)
        with col2:
            st.metric("Risque de pluie", f"{proba:.0%}")
            st.markdown(
                f"### {icon} Niveau de risque : **{level.upper()}**",
            )
            st.write(data["note"])
        st.divider()

        # Courbe de risque sur 14 jours autour de la date choisie.
        st.subheader("Evolution du risque sur 14 jours")
        days = [chosen + timedelta(days=i) for i in range(-3, 11)]
        probs = []
        for d in days:
            try:
                probs.append(get_json(f"/predict?date={d.isoformat()}")["rain_probability"])
            except Exception:
                probs.append(None)
        serie = pd.DataFrame({"date": days, "probabilite_%": [p * 100 if p is not None else None for p in probs]})
        st.line_chart(serie, x="date", y="probabilite_%")

    # Indicateurs qualite du modele.
    st.divider()
    with st.expander("📊 Indicateurs qualite du modele"):
        info = get_json("/model-info")
        m = info["test_metrics"]["at_0.5"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROC-AUC", m["roc_auc"])
        c2.metric("PR-AUC", m["pr_auc"])
        c3.metric("Brier score", m["brier"], help="Plus bas = mieux calibre")
        c4.metric("Taux de base", f"{m['base_rate']:.0%}")
        st.caption(
            f"Modele : {info['selected_model']} — entraine sur {info['n_train']} jours, "
            f"teste sur {info['n_test']} jours (a partir de {info['test_from_year']}). "
            f"Seuil de pluie : {info['rain_threshold_mm']} mm/jour."
        )


if __name__ == "__main__":
    main()
