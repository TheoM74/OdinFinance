"""Thèmes de l'application : jetons de couleur, polices et règles de typographie.

Deux thèmes :
- « cyberpunk » : repris du portfolio (palette du thème VS Code « Cyberpunk 2077 », polices Cyberpunk,
  Oxanium et Blender Pro, coins coupés, trame de fond) ;
- « classique » : thème clair sobre, police système, accent bleu du bilan Excel.

Le fichier resources/style.qss est un gabarit (string.Template) : chaque jeton y est remplacé par la valeur du thème.
La casse et l'interlettrage (impossibles en QSS) sont appliqués en Python par `appliquer_typographie`.
"""
import os
import sys
from dataclasses import dataclass, replace
from string import Template

from PyQt6.QtCore import QEvent, QObject, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PyQt6.QtWidgets import QAbstractButton, QApplication, QHeaderView, QLabel, QPushButton, QTabBar, QWidget


def chemin_ressource(*parties: str) -> str:
    """Chemin d'un fichier de resources/, en développement comme dans l'exécutable PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "resources", *parties)


@dataclass(frozen=True)
class Theme:
    id: str
    nom: str
    couleurs: dict[str, str]
    police_texte: str
    police_titre: str
    police_logo: str
    taille_texte: int
    rayon: int
    majuscules: bool  # titres, boutons et légendes en capitales espacées
    coins_coupes: bool
    trame: bool  # lignes de balayage et grille en fond de fenêtre

    def couleur(self, nom: str) -> QColor:
        valeur = self.couleurs[nom]
        # QColor lit « #AARRGGBB » ; le QSS aussi : les jetons sont écrits dans ce format.
        return QColor(valeur)


CYBERPUNK = Theme(
    id="cyberpunk",
    nom="Cyberpunk",
    couleurs={
        "fond": "#160000",
        "surface": "#200404",
        "surface_alt": "#250606",
        "surface_2": "#2a0909",
        "survol": "#340d0d",
        "champ": "#160000",
        "texte": "#ecdede",
        "texte_doux": "#c4a9a9",
        "texte_desactive": "#8a6f6f",
        "titre": "#ff9393",
        "accent": "#5aedf4",
        "accent_survol": "#9df6fa",
        "accent_doux": "#245aedf4",
        "sur_accent": "#160000",
        "danger": "#ff5c5c",
        "danger_doux": "#24ff5c5c",
        "positif": "#98c379",
        "attention": "#e5c07b",
        "trait": "#33ff9393",
        "trait_fort": "#80ff9393",
        "focus": "#ff5c5c",
        "selection": "#21545a",  # opaque : une sélection translucide laisse des liserés entre cellules
        "texte_selection": "#ffffff",
        "ombre_logo": "#995aedf4",
    },
    police_texte="Blender Pro",
    police_titre="Oxanium",
    police_logo="Cyberpunk",
    taille_texte=16,
    rayon=0,
    majuscules=True,
    coins_coupes=True,
    trame=True,
)

CLASSIQUE = Theme(
    id="classique",
    nom="Classique",
    couleurs={
        "fond": "#f3f5f8",
        "surface": "#ffffff",
        "surface_alt": "#f8fafc",
        "surface_2": "#f7f9fb",
        "survol": "#edf1f6",
        "champ": "#ffffff",
        "texte": "#18212c",
        "texte_doux": "#556170",
        "texte_desactive": "#97a1ad",
        "titre": "#18212c",
        "accent": "#0070c0",
        "accent_survol": "#005a9e",
        "accent_doux": "#e5f0fa",
        "sur_accent": "#ffffff",
        "danger": "#c42b1c",
        "danger_doux": "#fbeae8",
        "positif": "#107c41",
        "attention": "#9d5d00",
        "trait": "#dfe4ea",
        "trait_fort": "#b9c3ce",
        "focus": "#0070c0",
        "selection": "#cfe3f6",
        "texte_selection": "#0b1a2a",
        "ombre_logo": "#00000000",
    },
    police_texte="",  # police système, résolue au chargement
    police_titre="",
    police_logo="",
    taille_texte=14,
    rayon=6,
    majuscules=False,
    coins_coupes=False,
    trame=False,
)

THEMES = {t.id: t for t in (CYBERPUNK, CLASSIQUE)}
_theme_actuel: Theme = CYBERPUNK


def theme_actuel() -> Theme:
    return _theme_actuel


def charger_polices():
    dossier = chemin_ressource("fonts")
    if os.path.isdir(dossier):
        for fichier in sorted(os.listdir(dossier)):
            if fichier.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(dossier, fichier))


def _avec_police_systeme(theme: Theme) -> Theme:
    if theme.police_texte:
        return theme
    systeme = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()
    return replace(theme, police_texte=systeme, police_titre=systeme, police_logo=systeme)


# Rôles (propriété Qt « role ») qui passent en capitales espacées dans le thème Cyberpunk
ROLES_MAJUSCULES = {"legende", "titre-section"}


def appliquer_typographie(widget: QWidget, theme: Theme):
    """Casse et interlettrage selon le thème (le QSS ne sait pas faire text-transform ni letter-spacing)."""
    if widget.property("casse_libre"):
        return
    if isinstance(widget, QHeaderView):
        capitales = True  # intitulés de colonnes en petites capitales dans les deux thèmes
    elif isinstance(widget, (QPushButton, QTabBar)) or (
            isinstance(widget, QLabel) and widget.property("role") in ROLES_MAJUSCULES):
        capitales = theme.majuscules
    else:
        return
    police = QFont(widget.font())
    police.setCapitalization(QFont.Capitalization.AllUppercase if capitales else QFont.Capitalization.MixedCase)
    police.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 106 if capitales else 100)
    widget.setFont(police)
    if isinstance(widget, QAbstractButton):
        # Pas d'anneau de focus après un clic souris : il reste visible à la navigation clavier.
        widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)


def rafraichir_style(widget: QWidget):
    """À appeler après avoir changé une propriété dynamique utilisée par le QSS (ex. erreur, variante)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class GestionnaireTheme(QObject):
    """Applique un thème à toute l'application et mémorise le choix de l'utilisateur."""

    theme_change = pyqtSignal(object)

    def __init__(self, app: QApplication, settings: QSettings):
        super().__init__(app)
        self.app = app
        self.settings = settings
        charger_polices()
        identifiant = settings.value("theme", CYBERPUNK.id)
        self.theme = THEMES.get(identifiant, CYBERPUNK)
        app.installEventFilter(self)

    def eventFilter(self, objet, evenement):
        # Chaque widget (y compris ceux des boîtes de dialogue créées plus tard) reçoit la typographie du thème
        if evenement.type() == QEvent.Type.Polish and isinstance(objet, QWidget):
            appliquer_typographie(objet, self.theme)
        return False

    def appliquer(self, theme: Theme | None = None):
        global _theme_actuel
        self.theme = _avec_police_systeme(theme or self.theme)
        _theme_actuel = self.theme
        self.settings.setValue("theme", self.theme.id)

        from views.icones import ecrire_images_qss, recolorer  # import tardif : icones dépend de ce module
        jetons = {
            **self.theme.couleurs,
            **ecrire_images_qss(self.theme),
            "police_texte": self.theme.police_texte,
            "police_titre": self.theme.police_titre,
            "taille_texte": str(self.theme.taille_texte),
            # légendes et boutons : plus petits en Cyberpunk, où ils sont en capitales espacées
            "taille_petite": str(self.theme.taille_texte - (3 if self.theme.majuscules else 2)),
            "taille_bouton": str(self.theme.taille_texte - (3 if self.theme.majuscules else 0)),
            "taille_titre": str(self.theme.taille_texte + 8),
            "rayon": str(self.theme.rayon),
            "rayon_petit": str(max(0, self.theme.rayon - 2)),
        }
        # La typographie est posée avant ET après la feuille de style : Qt fige la police des en-têtes
        # de tableau au moment où il applique le QSS.
        self._typographier_tout()
        with open(chemin_ressource("style.qss"), encoding="utf-8") as fichier:
            self.app.setStyleSheet(Template(fichier.read()).substitute(jetons))

        palette = QPalette(self.app.palette())
        for role, jeton in (
            (QPalette.ColorRole.Window, "fond"), (QPalette.ColorRole.Base, "champ"),
            (QPalette.ColorRole.AlternateBase, "surface_alt"), (QPalette.ColorRole.Text, "texte"),
            (QPalette.ColorRole.WindowText, "texte"), (QPalette.ColorRole.ButtonText, "texte"),
            (QPalette.ColorRole.PlaceholderText, "texte_doux"), (QPalette.ColorRole.Highlight, "selection"),
            (QPalette.ColorRole.HighlightedText, "texte_selection"), (QPalette.ColorRole.ToolTipBase, "surface"),
            (QPalette.ColorRole.ToolTipText, "texte"), (QPalette.ColorRole.Link, "accent"),
        ):
            palette.setColor(role, self.theme.couleur(jeton))
        self.app.setPalette(palette)

        police = QFont(self.theme.police_texte)
        police.setPixelSize(self.theme.taille_texte)
        self.app.setFont(police)
        self._typographier_tout()
        recolorer(self.theme)
        self.theme_change.emit(self.theme)

    def _typographier_tout(self):
        for widget in self.app.allWidgets():
            appliquer_typographie(widget, self.theme)
            widget.update()

    def basculer(self):
        self.appliquer(CLASSIQUE if self.theme.id == CYBERPUNK.id else CYBERPUNK)
