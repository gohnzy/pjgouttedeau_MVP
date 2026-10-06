"""Rend les exports PNG des diagrammes documentaires."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
WIDTH, HEIGHT = 1600, 900
BACKGROUND = "#F5F7F2"
INK = "#172A32"
MUTED = "#52646A"
GREEN = "#28745B"
BLUE = "#376B80"
CORAL = "#BA5B42"
GOLD = "#B68A3A"
PALE_GREEN = "#E3F0E9"
PALE_BLUE = "#E6EFF2"
PALE_CORAL = "#F6E9E4"
PALE_GOLD = "#F3EEDF"

FONT_PATH = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD_PATH = Path("C:/Windows/Fonts/segoeuib.ttf")


def fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    return (
        ImageFont.truetype(str(BOLD_PATH), 36),
        ImageFont.truetype(str(BOLD_PATH), 23),
        ImageFont.truetype(str(FONT_PATH), 19),
    )


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw, tuple]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font, heading_font, body_font = fonts()
    draw.text((80, 54), title, font=title_font, fill=INK)
    draw.text((82, 111), subtitle, font=body_font, fill=MUTED)
    draw.line((80, 160, WIDTH - 80, 160), fill="#CDD7D2", width=2)
    draw.text((82, HEIGHT - 55), "Goutte d'eau  |  MVP logiciel", font=body_font, fill=MUTED)
    return image, draw, (title_font, heading_font, body_font)


def centered_text(draw: ImageDraw.ImageDraw, box: tuple, text: str, font, fill: str) -> None:
    left, top, right, bottom = box
    bounds = draw.multiline_textbbox((0, 0), text, font=font, align="center", spacing=8)
    text_width, text_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.multiline_text(
        ((left + right - text_width) / 2, (top + bottom - text_height) / 2),
        text,
        font=font,
        fill=fill,
        align="center",
        spacing=8,
    )


def node(draw: ImageDraw.ImageDraw, box: tuple, title: str, detail: str, fill: str, edge: str) -> None:
    draw.rounded_rectangle(box, radius=14, fill=fill, outline=edge, width=3)
    left, top, right, bottom = box
    centered_text(draw, (left + 12, top + 18, right - 12, top + 66), title, fonts()[1], edge)
    centered_text(draw, (left + 10, top + 70, right - 10, bottom - 12), detail, fonts()[2], INK)


def arrow(draw: ImageDraw.ImageDraw, start: tuple, end: tuple, color: str = MUTED, dashed: bool = False) -> None:
    x1, y1 = start
    x2, y2 = end
    if dashed:
        distance = max(abs(x2 - x1), abs(y2 - y1))
        for offset in range(0, distance, 18):
            t0, t1 = offset / distance, min((offset + 9) / distance, 1)
            draw.line((x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                       x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1), fill=color, width=4)
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=4)
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    base = (x2 - 15 * dx / length, y2 - 15 * dy / length)
    perpendicular = (-dy / length * 8, dx / length * 8)
    draw.polygon([
        (x2, y2),
        (base[0] + perpendicular[0], base[1] + perpendicular[1]),
        (base[0] - perpendicular[0], base[1] - perpendicular[1]),
    ], fill=color)


def render_architecture() -> None:
    image, draw, _ = canvas(
        "Architecture du MVP",
        "Chaîne actuellement livrée : données historiques, entraînement local et prédiction par API.",
    )
    boxes = [
        (65, 360, 285, 535),
        (325, 360, 545, 535),
        (585, 360, 805, 535),
        (845, 360, 1065, 535),
        (1105, 360, 1325, 535),
        (1365, 360, 1535, 535),
    ]
    items = [
        ("SYNOP", "Archives\nMétéo-France", PALE_BLUE, BLUE),
        ("Collecte", "Python / pandas\nmensuelle", PALE_GREEN, GREEN),
        ("SQLite", "observations\n+ daily", PALE_GOLD, GOLD),
        ("Modèle", "features J+1\nscikit-learn", PALE_GREEN, GREEN),
        ("FastAPI", "/predict\n/predict/batch", PALE_CORAL, CORAL),
        ("Streamlit", "démo", PALE_BLUE, BLUE),
    ]
    for box, (title, detail, fill, edge) in zip(boxes, items):
        node(draw, box, title, detail, fill, edge)
    for index in range(len(boxes) - 1):
        arrow(draw, (boxes[index][2] + 7, 447), (boxes[index + 1][0] - 7, 447))
    draw.text((90, 610), "Artefacts locaux", font=fonts()[1], fill=INK)
    node(draw, (365, 590, 680, 730), "rain_model.joblib", "classifieur + médianes", PALE_GREEN, GREEN)
    node(draw, (790, 590, 1105, 730), "metrics.json", "scores test + baselines", PALE_GOLD, GOLD)
    arrow(draw, (920, 580), (1210, 542), BLUE, dashed=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / "architecture.png", optimize=True)


def render_components() -> None:
    image, draw, _ = canvas(
        "Composants logiciels",
        "Responsabilités et échanges entre modules du dépôt.",
    )
    draw.text((95, 225), "Données", font=fonts()[1], fill=GREEN)
    draw.text((600, 225), "Modèle", font=fonts()[1], fill=BLUE)
    draw.text((1105, 225), "Restitution", font=fonts()[1], fill=CORAL)

    collection = (95, 300, 495, 420)
    database = (95, 565, 495, 685)
    features = (600, 300, 1000, 420)
    training = (600, 470, 1000, 590)
    evaluation = (600, 640, 1000, 760)
    api = (1105, 300, 1505, 420)
    ui = (1105, 565, 1505, 685)
    node(draw, collection, "data_collection.py", "download / parse\nagrégation", PALE_GREEN, GREEN)
    node(draw, database, "database.py", "SQLite\nupsert + daily", PALE_GREEN, GREEN)
    node(draw, features, "features.py", "variables\nretards météo", PALE_BLUE, BLUE)
    node(draw, training, "train.py", "fit + calibration\nartefact", PALE_BLUE, BLUE)
    node(draw, evaluation, "evaluate.py", "scores et\nbaselines", PALE_BLUE, BLUE)
    node(draw, api, "api.py", "FastAPI\nPydantic", PALE_CORAL, CORAL)
    node(draw, ui, "streamlit_app.py", "écran de démo\n1 appel batch", PALE_CORAL, CORAL)

    arrow(draw, (295, 430), (295, 550), GREEN)
    arrow(draw, (505, 625), (590, 390), GREEN)
    arrow(draw, (800, 430), (800, 455), BLUE)
    arrow(draw, (800, 600), (800, 625), BLUE)
    arrow(draw, (1010, 535), (1095, 390), BLUE)
    arrow(draw, (1305, 430), (1305, 550), CORAL)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / "composants.png", optimize=True)


def render_deployment() -> None:
    image, draw, _ = canvas(
        "Déploiement",
        "Seul le parcours local est déployé. Le cloud reste une cible à arbitrer.",
    )
    node(draw, (90, 305, 465, 470), "Fichiers du dépôt", "SQLite\nmodèle\nmétriques", PALE_GOLD, GOLD)
    node(draw, (625, 345, 990, 510), "API locale", "Uvicorn\nFastAPI", PALE_CORAL, CORAL)
    node(draw, (1160, 345, 1505, 510), "Interface", "Streamlit\nnavigateur local", PALE_BLUE, BLUE)
    arrow(draw, (475, 390), (610, 410), GOLD)
    arrow(draw, (1000, 430), (1145, 430), CORAL)
    node(draw, (625, 625, 990, 780), "Cible à étudier", "AWS Paris / Stockholm\nOVHcloud / Scaleway", "#F1EEE7", MUTED)
    arrow(draw, (810, 520), (810, 610), MUTED, dashed=True)
    draw.text((1050, 665), "Pas de compte cloud ni de coût\nréel engagés par le MVP.",
              font=fonts()[2], fill=MUTED, spacing=7)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / "deploiement.png", optimize=True)


def render_gantt() -> None:
    image, draw, _ = canvas(
        "Planning du MVP — 10 semaines",
        "Plan relatif : la date réelle de lancement n'est pas fournie.",
    )
    left, top, cell = 440, 265, 100
    week_font = fonts()[2]
    for week in range(10):
        x = left + week * cell
        draw.text((x + 30, 205), f"S{week + 1}", font=week_font, fill=MUTED)
        draw.line((x, 245, x, 795), fill="#D8E0DA", width=1)
    draw.line((left + 10 * cell, 245, left + 10 * cell, 795), fill="#D8E0DA", width=1)
    rows = [
        ("P0  Cadrage et socle", 0, 1, GREEN),
        ("P1  Données et qualité", 1, 2, BLUE),
        ("P2  Modèle et services", 3, 4, CORAL),
        ("P3  Recette et transfert", 7, 3, GOLD),
    ]
    for index, (label, start, duration, color) in enumerate(rows):
        y = 300 + index * 120
        draw.text((80, y + 17), label, font=fonts()[2], fill=INK)
        x1, x2 = left + start * cell + 8, left + (start + duration) * cell - 8
        draw.rounded_rectangle((x1, y, x2, y + 60), radius=10, fill=color)
        for week in range(start, start + duration):
            draw.text((left + week * cell + 30, y + 18), f"S{week + 1}",
                      font=week_font, fill="white")
    draw.text((80, 795), "10 sprints hebdomadaires; détail des tâches dans le Gantt Mermaid.",
              font=week_font, fill=MUTED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / "planning-gantt.png", optimize=True)


def main() -> None:
    render_architecture()
    render_components()
    render_deployment()
    render_gantt()
    print(f"PNG générés dans {OUTPUT_DIR}")


if __name__ == "__main__":
    main()