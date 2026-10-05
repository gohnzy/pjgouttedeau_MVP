# -*- coding: utf-8 -*-
"""Rendu local (matplotlib) des 2 diagrammes d'API de l'EdC-02.
Pas de service en ligne, pas de Chromium : dessin vectoriel -> PNG."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTDIR = r"c:\Users\gnuzzoad\OneDrive - BOUYGUES TELECOM\Bureau\ISCOD\Exos\goutte-deau-mvp\docs\diagrams"

C_SRC = "#E3F2FD"; C_ING = "#FFF3E0"; C_DATA = "#EDE7F6"
C_ML = "#E8F5E9"; C_SRV = "#FCE4EC"; C_UI = "#E0F7FA"; C_USER = "#F5F5F5"
C_FUT = "#FAFAFA"; EDGE = "#555555"


def box(ax, x, y, w, h, text, fc, future=False, fs=10):
    ls = (0, (4, 3)) if future else "solid"
    ec = "#9E9E9E" if future else "#37474F"
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.02,rounding_size=0.12",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, linestyle=ls)
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color="#263238", zorder=5, linespacing=1.25)
    return (x, y, w, h)


def cluster(ax, x0, y0, x1, y1, label, fc):
    p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                       boxstyle="round,pad=0.02,rounding_size=0.15",
                       linewidth=1.2, edgecolor="#B0BEC5", facecolor=fc, alpha=0.55)
    ax.add_patch(p)
    ax.text(x0 + 0.15, y1 - 0.22, label, ha="left", va="top", fontsize=10,
            fontweight="bold", color="#455A64")


def arrow(ax, a, b, label=None, dashed=False, color=EDGE, rad=0.0, lx=0, ly=0):
    x1, y1 = anchor(a, b); x2, y2 = anchor(b, a)
    st = "dashed" if dashed else "solid"
    ar = FancyArrowPatch((x1, y1), (x2, y2),
                         arrowstyle="-|>", mutation_scale=14,
                         linewidth=1.4, color=color, linestyle=st,
                         connectionstyle=f"arc3,rad={rad}", zorder=3)
    ax.add_patch(ar)
    if label:
        mx, my = (x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly
        ax.text(mx, my, label, ha="center", va="center", fontsize=8.5,
                color="#37474F", zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))


def anchor(a, towards):
    """Point sur le bord de la boite a, cote la boite towards."""
    ax0, ay0, aw, ah = a; tx, ty = towards[0], towards[1]
    dx, dy = tx - ax0, ty - ay0
    if dx == 0 and dy == 0:
        return ax0, ay0
    hw, hh = aw / 2, ah / 2
    sx = hw / abs(dx) if dx != 0 else 1e9
    sy = hh / abs(dy) if dy != 0 else 1e9
    s = min(sx, sy)
    return ax0 + dx * s, ay0 + dy * s


# ---------------------------------------------------------------- Diagramme 1
fig, ax = plt.subplots(figsize=(12.5, 15))
ax.set_xlim(0, 13); ax.set_ylim(0, 15.5); ax.axis("off")
ax.set_title("Projet Goutte d'eau \u2014 Diagramme d'architecture (MVP \u2192 cible)",
             fontsize=15, fontweight="bold", color="#263238", pad=14)

cluster(ax, 0.4, 13.6, 12.6, 15.0, "Sources de donnees", C_SRC)
cluster(ax, 0.4, 11.5, 12.6, 13.2, "Couche d'ingestion", C_ING)
cluster(ax, 0.4, 9.6, 12.6, 11.1, "Couche de donnees", C_DATA)
cluster(ax, 0.4, 7.2, 12.6, 9.2, "Couche IA / Modele", C_ML)
cluster(ax, 0.4, 4.8, 12.6, 6.8, "Couche de service", C_SRV)
cluster(ax, 0.4, 2.9, 12.6, 4.4, "Couche presentation", C_UI)
cluster(ax, 0.4, 0.6, 12.6, 2.5, "Utilisateurs", C_USER)

MF = box(ax, 3.4, 14.25, 4.2, 1.0, "Meteo-France SYNOP\n(Licence Ouverte)\nsource du MVP", C_SRC)
IOT = box(ax, 9.3, 14.25, 4.2, 1.0, "Reseau capteurs IoT\n(50 km2, temps reel)\ncible EdC-01", C_FUT, future=True)
COL = box(ax, 3.4, 12.35, 3.6, 0.9, "Service de collecte\n(Python / requests)", C_ING)
SCHED = box(ax, 9.3, 12.35, 4.0, 0.9, "Ordonnanceur\nrafraichissement < 5 min", C_ING)
DB = box(ax, 6.5, 10.35, 4.4, 0.9, "Base de donnees\nSQLite (MVP) / PostgreSQL+PostGIS (cible)", C_DATA)
TRAIN = box(ax, 2.6, 8.15, 3.0, 0.9, "Entrainement\n(scikit-learn)", C_ML)
MODEL = box(ax, 6.5, 8.15, 3.0, 0.9, "Modele entraine\n(artefact .joblib)", C_ML)
EVAL = box(ax, 10.3, 8.15, 2.8, 0.9, "Evaluation\n(metriques)", C_ML)
API = box(ax, 2.6, 5.75, 3.0, 0.9, "API REST\n(FastAPI + Uvicorn)", C_SRV)
AUTH = box(ax, 6.5, 5.75, 3.0, 0.9, "Authentification\n(cible, backlog #4)", C_FUT, future=True)
NOTIF = box(ax, 10.3, 5.75, 3.2, 0.9, "Notifications multicanal\nSMS / mail / push (cible)", C_FUT, future=True)
UI = box(ax, 6.5, 3.6, 4.4, 0.85, "Dashboard & interface demo (Streamlit)", C_UI)
AGRI = box(ax, 2.6, 1.5, 3.0, 0.85, "Agriculteurs", C_USER)
SDIS = box(ax, 6.5, 1.5, 3.2, 0.85, "SDIS / gestion des risques", C_USER)
COLL = box(ax, 10.3, 1.5, 3.2, 0.85, "Collectivites / urbanisme", C_USER)

arrow(ax, MF, COL)
arrow(ax, IOT, COL, dashed=True, label="cible")
arrow(ax, SCHED, COL)
arrow(ax, COL, DB)
arrow(ax, DB, TRAIN)
arrow(ax, TRAIN, MODEL)
arrow(ax, TRAIN, EVAL)
arrow(ax, MODEL, API)
arrow(ax, API, UI)
arrow(ax, API, NOTIF, rad=-0.1)
arrow(ax, AUTH, API, dashed=True, label="protege")
arrow(ax, UI, AGRI)
arrow(ax, UI, SDIS)
arrow(ax, UI, COLL)
arrow(ax, NOTIF, SDIS, dashed=True, rad=0.15, color="#B0558A")

fig.savefig(OUTDIR + r"\01-architecture.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- Diagramme 2
fig, ax = plt.subplots(figsize=(11, 14))
ax.set_xlim(0, 11); ax.set_ylim(0, 14); ax.axis("off")
ax.set_title("Projet Goutte d'eau \u2014 Diagramme de composants (MVP)",
             fontsize=15, fontweight="bold", color="#263238", pad=14)

cluster(ax, 0.6, 1.0, 8.6, 11.8, "Application Goutte d'eau (MVP)", "#FBFBFD")
cluster(ax, 1.0, 10.2, 8.2, 11.4, "Composant Collecte", C_ING)
cluster(ax, 1.0, 7.5, 8.2, 9.9, "Composant Persistance", C_DATA)
cluster(ax, 1.0, 6.0, 8.2, 7.2, "Composant Features", C_SRC)
cluster(ax, 1.0, 3.0, 8.2, 5.7, "Composant Modele", C_ML)
cluster(ax, 1.0, 1.9, 8.2, 2.9, "Composant API", C_SRV)
cluster(ax, 1.0, 0.7, 8.2, 1.7, "Composant Interface", C_UI)

EXT = box(ax, 4.6, 12.9, 4.0, 0.9, "API Meteo-France\n(HTTP / CSV.gz)", "#FFFDE7")
DC = box(ax, 4.6, 10.75, 4.6, 0.75, "data_collection.py\ndownload_month / collect / build_daily", C_ING, fs=9)
DBM = box(ax, 4.6, 9.2, 4.2, 0.72, "database.py\ninit_db / upsert / replace_daily", C_DATA, fs=9)
SQL = box(ax, 4.6, 8.0, 3.4, 0.72, "SQLite\n(observations, daily)", "#D1C4E9", fs=9)
FE = box(ax, 4.6, 6.55, 3.6, 0.72, "features.py\nbuild_features()", C_SRC, fs=9)
TR = box(ax, 2.9, 4.95, 3.0, 0.75, "train.py\nPipeline scikit-learn", C_ML, fs=9)
EV = box(ax, 6.5, 4.95, 2.8, 0.75, "evaluate.py\nmetriques & courbes", C_ML, fs=9)
ART = box(ax, 2.9, 3.65, 3.0, 0.75, "rain_model.joblib\nmetrics.json", "#C8E6C9", fs=9)
API2 = box(ax, 4.6, 2.4, 4.6, 0.72, "api.py\nGET /health, /predict, /model-info", C_SRV, fs=9)
ST = box(ax, 4.6, 1.2, 4.2, 0.72, "streamlit_app.py\ndemo & indicateurs", C_UI, fs=9)

arrow(ax, EXT, DC, label="HTTP GET")
arrow(ax, DC, DBM, label="upsert")
arrow(ax, DBM, SQL)
arrow(ax, SQL, FE, label="lecture")
arrow(ax, FE, TR)
arrow(ax, TR, ART, label="serialise")
arrow(ax, TR, EV)
arrow(ax, ART, API2, label="charge au demarrage")
arrow(ax, API2, ST, label="HTTP JSON")
arrow(ax, FE, API2, dashed=True, rad=-0.45, label="reutilise", lx=2.4)

fig.savefig(OUTDIR + r"\02-composants.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("OK")
