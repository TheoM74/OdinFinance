"""Composants communs aux écrans. Les éléments propres au thème Cyberpunk (coins coupés, encoche sous
les titres, trame de fond, ombre du logo) sont peints ici, le QSS ne sachant pas les dessiner."""
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from views.icones import poser_icone
from views.theme import rafraichir_style, theme_actuel

COUPE = 14  # taille des coins coupés (comme --cut sur le portfolio)


def bouton(texte: str, variante: str | None = None, icone: str | None = None, infobulle: str | None = None) -> QPushButton:
    b = QPushButton(texte)
    if variante:
        b.setProperty("variante", variante)
    if icone:
        poser_icone(b, icone)
    if infobulle:
        b.setToolTip(infobulle)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def etiquette(texte: str, role: str | None = None) -> QLabel:
    label = QLabel(texte)
    if role:
        label.setProperty("role", role)
    return label


def poser_signe(label: QLabel, centimes: int):
    """Colore un montant selon son signe (positif = vert, négatif = rouge)."""
    label.setProperty("signe", "negatif" if centimes < 0 else "positif" if centimes > 0 else "")
    rafraichir_style(label)


class FondApplication(QWidget):
    """Fond de fenêtre : couleur du thème, et pour Cyberpunk lignes de balayage + grille de 64 px."""

    def paintEvent(self, _):
        theme = theme_actuel()
        p = QPainter(self)
        p.fillRect(self.rect(), theme.couleur("fond"))
        if theme.trame:
            ligne_balayage = theme.couleur("texte")
            ligne_balayage.setAlpha(5)
            for y in range(0, self.height(), 3):
                p.fillRect(0, y, self.width(), 1, ligne_balayage)
            grille = theme.couleur("titre")
            grille.setAlpha(12)
            for x in range(0, self.width(), 64):
                p.fillRect(x, 0, 1, self.height(), grille)
            for y in range(0, self.height(), 64):
                p.fillRect(0, y, self.width(), 1, grille)


class Panneau(QFrame):
    """Conteneur de section : coin supérieur droit coupé (Cyberpunk) ou coins arrondis (Classique)."""

    def __init__(self, parent=None, marges=(20, 18, 20, 20)):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.contenu = QVBoxLayout(self)
        self.contenu.setContentsMargins(*marges)
        self.contenu.setSpacing(12)

    def paintEvent(self, _):
        theme = theme_actuel()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        chemin = QPainterPath()
        if theme.coins_coupes:
            chemin.addPolygon(QPolygonF([
                r.topLeft(), QPointF(r.right() - COUPE, r.top()), QPointF(r.right(), r.top() + COUPE),
                r.bottomRight(), r.bottomLeft(),
            ]))
            chemin.closeSubpath()
        else:
            chemin.addRoundedRect(r, theme.rayon + 2, theme.rayon + 2)
        p.fillPath(chemin, theme.couleur("surface"))
        p.setPen(QPen(theme.couleur("trait"), 1))
        p.drawPath(chemin)


class TitreSection(QLabel):
    """Titre de panneau. En Cyberpunk, souligné d'un trait avec encoche (repris du portfolio)."""

    HAUTEUR_TRAIT = 5

    def __init__(self, texte: str, parent=None):
        super().__init__(texte, parent)
        self.setProperty("role", "titre-section")

    def _avec_trait(self) -> bool:
        return theme_actuel().coins_coupes

    def sizeHint(self) -> QSize:
        taille = super().sizeHint()
        return QSize(taille.width(), taille.height() + (self.HAUTEUR_TRAIT + 8 if self._avec_trait() else 0))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, evenement):
        if not self._avec_trait():
            return super().paintEvent(evenement)
        p = QPainter(self)
        p.setFont(self.font())
        p.setPen(theme_actuel().couleur("titre"))
        hauteur_texte = QFontMetrics(self.font()).height()
        p.drawText(QRectF(0, 0, self.width(), hauteur_texte), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
        # Trait : pleine hauteur sur 18 % puis biseau vers un filet de 2 px
        largeur, y, h = min(self.width(), 360), hauteur_texte + 6, self.HAUTEUR_TRAIT
        cran = largeur * 0.18
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme_actuel().couleur("titre"))
        p.drawPolygon(QPolygonF([
            QPointF(0, y), QPointF(0, y + h), QPointF(cran, y + h), QPointF(cran + 4, y + 2),
            QPointF(largeur, y + 2), QPointF(largeur, y),
        ]))


class Logo(QWidget):
    """« ODINFINANCE » en police Cyberpunk avec l'ombre cyan décalée du portfolio, ou sobre en Classique."""

    def _police(self) -> QFont:
        theme = theme_actuel()
        police = QFont(theme.police_logo)
        if theme.trame:
            police.setPixelSize(22)
            police.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 104)
        else:
            police.setPixelSize(19)
            police.setWeight(QFont.Weight.DemiBold)
        return police

    def _texte(self) -> str:
        return "ODINFINANCE" if theme_actuel().trame else "OdinFinance"

    def sizeHint(self) -> QSize:
        m = QFontMetrics(self._police())
        return QSize(m.horizontalAdvance(self._texte()) + 6, m.height() + 6)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, _):
        theme = theme_actuel()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setFont(self._police())
        zone = QRectF(self.rect()).adjusted(0, 0, -3, -3)
        alignement = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        if theme.trame:
            p.setPen(theme.couleur("ombre_logo"))
            p.drawText(zone.translated(3, 3), alignement, self._texte())
        p.setPen(theme.couleur("titre"))
        p.drawText(zone, alignement, self._texte())


class ChampFormulaire(QWidget):
    """Légende + champ + message d'erreur en ligne (remplace _creer_champ_avec_erreur de la v1)."""

    def __init__(self, legende: str, champ: QWidget, facultatif: bool = False, accessoire: QWidget | None = None):
        super().__init__()
        self.champ = champ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        texte = f"{legende} · facultatif" if facultatif else legende
        self.legende = etiquette(texte, "legende")
        self.legende.setBuddy(champ)
        layout.addWidget(self.legende)

        if accessoire:
            ligne = QHBoxLayout()
            ligne.setSpacing(6)
            ligne.addWidget(champ, 1)
            ligne.addWidget(accessoire)
            layout.addLayout(ligne)
        else:
            layout.addWidget(champ)

        self.erreur = etiquette("", "erreur")
        self.erreur.setWordWrap(True)
        self.erreur.setVisible(False)
        layout.addWidget(self.erreur)

    def changer_legende(self, texte: str):
        self.legende.setText(texte)

    def afficher_erreur(self, message: str):
        self.erreur.setText(message)
        self.erreur.setVisible(True)
        self.champ.setProperty("erreur", True)
        rafraichir_style(self.champ)

    def effacer_erreur(self):
        self.erreur.setVisible(False)
        self.champ.setProperty("erreur", False)
        rafraichir_style(self.champ)


class BarreSegmentee(QWidget):
    """Choix exclusif sous forme de boutons accolés (ex. Recette / Dépense / Virement)."""

    change = pyqtSignal(str)

    def __init__(self, options: list[tuple[str, str]]):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.groupe = QButtonGroup(self)
        self.boutons: dict[str, QPushButton] = {}
        for i, (valeur, texte) in enumerate(options):
            b = bouton(texte, "segment")
            b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setProperty("position", "gauche" if i == 0 else "droite" if i == len(options) - 1 else "milieu")
            b.toggled.connect(lambda coche, v=valeur: coche and self.change.emit(v))
            self.groupe.addButton(b)
            self.boutons[valeur] = b
            layout.addWidget(b)

    def valeur(self) -> str:
        return next(v for v, b in self.boutons.items() if b.isChecked())

    def choisir(self, valeur: str):
        self.boutons[valeur].setChecked(True)
