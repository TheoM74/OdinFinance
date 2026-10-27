import os
from dataclasses import dataclass
from datetime import date

from PyQt6.QtCore import QSettings, QStandardPaths, QUrl
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from controllers.journal_controller import JournalController
from controllers.parametres_controller import ParametresController
from controllers.synthese_controller import SyntheseController
from database.modeles import Categorie, Compte, Operation, Tiers
from database.queries import TresoQueries
from services.bilan import Exercice
from services.export_excel import exporter_bilan
from views.dialogues import bouton_message, signaler_erreur
from views.main_window import MainWindow
from views.theme import CYBERPUNK, GestionnaireTheme, Theme


@dataclass(frozen=True)
class Donnees:
    """Instantané de la base, partagé par les trois écrans après chaque modification."""
    nom_association: str
    exercice: Exercice
    comptes: list[Compte]
    categories: list[Categorie]
    tiers: list[Tiers]
    operations: list[Operation]


class MainController:
    def __init__(self, view: MainWindow, queries: TresoQueries, themes: GestionnaireTheme,
                 settings: QSettings, chemin_base: str):
        self.view = view
        self.queries = queries
        self.themes = themes
        self.settings = settings
        self.chemin_base = chemin_base
        self.donnees: Donnees | None = None

        self.synthese = SyntheseController(self)
        self.journal = JournalController(self)
        self.parametres = ParametresController(self)

        view.btn_theme.clicked.connect(themes.basculer)
        view.btn_exporter.clicked.connect(self.exporter_bilan)
        QShortcut(QKeySequence("Ctrl+T"), view, activated=themes.basculer)
        QShortcut(QKeySequence("Ctrl+E"), view, activated=self.exporter_bilan)
        themes.theme_change.connect(self._sur_changement_theme)

        page = int(settings.value("page", 0))
        view.afficher_page(page if 0 <= page < view.pages.count() else 0)
        view.navigation.currentChanged.connect(lambda i: settings.setValue("page", i))

        self.recharger()
        self._libeller_bouton_theme(themes.theme)

    # --- Données ---
    def exercice(self) -> Exercice:
        debut, fin = self.queries.get_parametre("exercice_debut"), self.queries.get_parametre("exercice_fin")
        if debut and fin:
            return Exercice(date.fromisoformat(debut), date.fromisoformat(fin))
        return Exercice.par_defaut(date.today())

    def recharger(self):
        """Relit la base et met à jour les trois écrans."""
        self.donnees = Donnees(
            nom_association=self.queries.get_parametre("nom_association"),
            exercice=self.exercice(),
            comptes=self.queries.get_tous_comptes(),
            categories=self.queries.get_toutes_categories(),
            tiers=self.queries.get_tous_tiers(),
            operations=self.queries.get_toutes_operations(),
        )
        ex = self.donnees.exercice
        annees = str(ex.debut.year) if ex.debut.year == ex.fin.year else f"{ex.debut.year}-{ex.fin.year}"
        self.view.label_exercice.setText(f"{self.donnees.nom_association} · exercice {annees}")
        self.view.label_exercice.setToolTip(f"Exercice du {ex.debut:%d/%m/%Y} au {ex.fin:%d/%m/%Y} (modifiable dans Paramètres)")
        self._afficher()

    def _afficher(self):
        for ecran in (self.synthese, self.journal, self.parametres):
            ecran.rafraichir(self.donnees)

    def message(self, texte: str):
        self.view.afficher_message(texte)

    # --- Thème ---
    def _libeller_bouton_theme(self, theme: Theme):
        self.view.btn_theme.setText("Thème classique" if theme.id == CYBERPUNK.id else "Thème Cyberpunk")

    def _sur_changement_theme(self, theme: Theme):
        self._libeller_bouton_theme(theme)
        if self.donnees:
            self._afficher()  # les couleurs des montants dans les tableaux dépendent du thème

    # --- Export ---
    def exporter_bilan(self):
        d = self.donnees
        dossier = self.settings.value("dossier_export") or QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation)
        chemin, _ = QFileDialog.getSaveFileName(
            self.view, "Exporter le bilan financier",
            os.path.join(dossier, f"Bilan_financier_{d.exercice.annee}.xlsx"), "Classeur Excel (*.xlsx)")
        if not chemin:
            return
        if not chemin.lower().endswith(".xlsx"):
            chemin += ".xlsx"
        try:
            exporter_bilan(chemin, d.nom_association, d.exercice, d.comptes, d.categories, d.operations)
        except PermissionError:
            signaler_erreur(self.view, "Export impossible",
                            "Le fichier est sans doute ouvert dans Excel. Fermez-le puis relancez l'export.")
            return
        except OSError as e:
            signaler_erreur(self.view, "Export impossible", f"Le fichier n'a pas pu être écrit : {e.strerror}.")
            return

        self.settings.setValue("dossier_export", os.path.dirname(chemin))
        self.message(f"Bilan {d.exercice.annee} exporté : {chemin}")
        boite = QMessageBox(QMessageBox.Icon.Information, "Bilan exporté",
                            f"Le bilan financier {d.exercice.annee} a été enregistré.", parent=self.view)
        ouvrir = bouton_message(boite, "Ouvrir le fichier", QMessageBox.ButtonRole.AcceptRole, "primaire")
        bouton_message(boite, "Fermer", QMessageBox.ButtonRole.RejectRole)
        boite.exec()
        if boite.clickedButton() is ouvrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(chemin))
