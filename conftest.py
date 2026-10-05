import sys
from pathlib import Path

# Garantit que la racine du projet est importable (import config, import src).
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
