"""Icônes vectorielles dessinées pour l'application (grille 24 px, trait de 2 px, extrémités arrondies).

Elles remplacent les émojis de la version 1 et prennent la couleur du thème actif.
"""
import os
import tempfile

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QAbstractButton, QApplication

from views.theme import Theme, theme_actuel

TRACES = {
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "modifier": '<path d="M16.5 3.5l4 4L8 20H4v-4z"/><path d="M14 6l4 4"/>',
    "supprimer": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',
    "exporter": '<path d="M12 3v12M7 10l5 5 5-5M4 19h16"/>',
    "rechercher": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
    "theme": '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="{couleur}"/>',
    "dossier": '<path d="M3 6.5h6l2 2.5h10v10.5H3z"/>',
    "fermer": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "calendrier": '<path d="M4 6h16v14H4zM4 10h16M8 3v5M16 3v5"/>',
}


def _svg(nom: str, couleur: str) -> bytes:
    trace = TRACES[nom].replace("{couleur}", couleur)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{couleur}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{trace}</svg>'
    ).encode()


def _couleur_svg(valeur: str) -> str:
    """Le SVG ne lit pas le format Qt « #AARRGGBB » : on garde la couleur sans son opacité."""
    return "#" + valeur[-6:]


def pixmap(nom: str, couleur: str, taille: int = 18) -> QPixmap:
    ratio = QApplication.primaryScreen().devicePixelRatio() if QApplication.primaryScreen() else 1.0
    image = QPixmap(int(taille * ratio), int(taille * ratio))
    image.fill(Qt.GlobalColor.transparent)
    peintre = QPainter(image)
    QSvgRenderer(QByteArray(_svg(nom, _couleur_svg(couleur)))).render(peintre, QRectF(0, 0, image.width(), image.height()))
    peintre.end()
    image.setDevicePixelRatio(ratio)
    return image


def icone(nom: str, couleur: str, couleur_desactivee: str | None = None, taille: int = 18) -> QIcon:
    resultat = QIcon(pixmap(nom, couleur, taille))
    if couleur_desactivee:
        resultat.addPixmap(pixmap(nom, couleur_desactivee, taille), QIcon.Mode.Disabled)
    return resultat


def poser_icone(bouton: QAbstractButton, nom: str):
    """Associe une icône à un bouton ; elle est recolorée à chaque changement de thème (voir recolorer)."""
    bouton.setProperty("icone", nom)
    _colorer(bouton, theme_actuel())


def _colorer(bouton: QAbstractButton, theme: Theme):
    nom = bouton.property("icone")
    variante = bouton.property("variante")
    couleur = {
        "primaire": theme.couleurs["sur_accent"],
        "danger": theme.couleurs["danger"],
    }.get(variante, theme.couleurs["texte"])
    bouton.setIcon(icone(nom, couleur, theme.couleurs["texte_desactive"]))


def recolorer(theme: Theme):
    for widget in QApplication.allWidgets():
        if isinstance(widget, QAbstractButton) and widget.property("icone"):
            _colorer(widget, theme)


def ecrire_images_qss(theme: Theme) -> dict[str, str]:
    """Le QSS ne lit les images que depuis des fichiers : écrit les flèches des listes déroulantes du thème."""
    dossier = os.path.join(tempfile.gettempdir(), "odinfinance-icones", theme.id)
    os.makedirs(dossier, exist_ok=True)
    images = {}
    for jeton, nom, couleur in (
        ("image_chevron", "chevron", theme.couleurs["texte_doux"]),
        ("image_chevron_desactive", "chevron", theme.couleurs["texte_desactive"]),
        ("image_calendrier", "calendrier", theme.couleurs["texte_doux"]),
    ):
        chemin = os.path.join(dossier, f"{jeton}.svg")
        with open(chemin, "wb") as fichier:
            fichier.write(_svg(nom, _couleur_svg(couleur)))
        images[jeton] = chemin.replace("\\", "/")
    return images
