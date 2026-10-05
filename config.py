"""Configuration centrale du projet Goutte d'eau (MVP).

Toutes les constantes parametrables du MVP sont regroupees ici afin de
faciliter la reproductibilite et l'adaptation a une autre region.
"""
from pathlib import Path

# --- Arborescence ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DB_PATH = DATA_DIR / "goutte_deau.db"
MODEL_PATH = MODELS_DIR / "rain_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

# --- Source de donnees (Meteo-France, Licence Ouverte 2.0) ----------------
# Archive SYNOP essentielles OMM : un fichier CSV compresse par mois.
SYNOP_ARCHIVE_URL = (
    "https://donneespubliques.meteofrance.fr/donnees_libres/Txt/Synop/Archive/"
    "synop.{year}{month:02d}.csv.gz"
)
STATIONS_URL = (
    "https://donneespubliques.meteofrance.fr/donnees_libres/Txt/Synop/postesSynop.csv"
)

# --- Perimetre (une seule region, cf. enonce) -----------------------------
# Station SYNOP retenue : Montpellier-Frejorgues (Occitanie, arc mediterraneen).
# Zone a la fois agricole (vignes, maraichage) et a fort enjeu inondation
# (episodes mediterraneens / cevenols), coherente avec les cas d'usage
# "planification agricole" et "gestion des inondations" de l'EdC-01.
STATION_ID = "07643"
STATION_NAME = "Montpellier-Frejorgues"
REGION = "Occitanie (arc mediterraneen)"

# Periode d'historique a collecter (annees incluses).
YEAR_START = 2015
YEAR_END = 2024

# --- Definition de la cible ----------------------------------------------
# Jour "pluvieux" si le cumul quotidien de precipitations (mm) depasse ce seuil.
RAIN_THRESHOLD_MM = 1.0

# --- Divers ---------------------------------------------------------------
RANDOM_STATE = 42
REQUEST_TIMEOUT = 60
USER_AGENT = "GoutteDeau-MVP/1.0 (projet pedagogique)"
