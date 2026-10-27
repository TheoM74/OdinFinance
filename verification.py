"""Vérification de fumée : `OdinFinance --autotest`.

Lancée par la CI après la compilation, sur Windows, macOS et Linux : construit l'interface dans les deux thèmes,
saisit une recette, une dépense et un virement, puis exporte un bilan. Tout se passe dans un dossier temporaire :
les données et les réglages de l'utilisateur ne sont pas touchés. Code de sortie 0 si tout fonctionne.
"""
import os
import sys
import tempfile
import traceback
from datetime import date

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from controllers.main_controller import MainController
from database.db_manager import DBManager
from database.modeles import DEPENSE, RECETTE
from database.queries import TresoQueries
from services.export_excel import exporter_bilan
from views.main_window import MainWindow
from views.theme import CLASSIQUE, CYBERPUNK, GestionnaireTheme

JOURNAL = "odinfinance-autotest.log"


def _rapporter(message: str):
    """L'exécutable fenêtré n'a pas de console : le résultat est aussi écrit dans un fichier lu par la CI."""
    if sys.stdout:
        print(message)
    with open(JOURNAL, "a", encoding="utf-8") as fichier:
        fichier.write(message + "\n")


def verifier(app: QApplication) -> int:
    try:
        with tempfile.TemporaryDirectory() as dossier:
            settings = QSettings(os.path.join(dossier, "reglages.ini"), QSettings.Format.IniFormat)
            themes = GestionnaireTheme(app, settings)
            themes.appliquer(CYBERPUNK)
            # Ressources embarquées (un mauvais chemin dans l'exécutable passerait sinon inaperçu)
            polices = set(QFontDatabase.families())
            manquantes = {"Cyberpunk", "Oxanium", "Blender Pro"} - polices
            if manquantes:
                raise RuntimeError(f"Polices non chargées : {', '.join(sorted(manquantes))}")
            if "QPushButton" not in app.styleSheet():
                raise RuntimeError("Feuille de style non chargée")

            chemin_base = os.path.join(dossier, "tresorerie.db")
            queries = TresoQueries(DBManager(chemin_base))
            comptes = queries.get_tous_comptes()
            categories = queries.get_toutes_categories()
            recette = next(c for c in categories if c.type_flux == RECETTE)
            depense = next(c for c in categories if c.type_flux == DEPENSE)
            jour = date.today()
            queries.enregistrer_operation(None, jour, "Vente de test", 12345, None, comptes[0].id, recette.id, None, None)
            queries.enregistrer_operation(None, jour, "Achat de test", 2390, "F-TEST", comptes[0].id, depense.id, None, None)
            queries.enregistrer_operation(None, jour, "Virement de test", 5000, None, comptes[0].id, None, comptes[1].id, None)

            view = MainWindow()
            controleur = MainController(view, queries, themes, settings, chemin_base)
            for theme in (CLASSIQUE, CYBERPUNK):
                themes.appliquer(theme)
                for page in range(view.pages.count()):
                    view.afficher_page(page)
                    app.processEvents()
                    if view.grab().isNull():
                        raise RuntimeError(f"Rendu vide : thème {theme.id}, page {page}")

            d = controleur.donnees
            if len(d.operations) != 3:
                raise RuntimeError(f"{len(d.operations)} opérations relues au lieu de 3")
            classeur = os.path.join(dossier, "bilan.xlsx")
            exporter_bilan(classeur, d.nom_association, d.exercice, d.comptes, d.categories, d.operations)
            if os.path.getsize(classeur) == 0:
                raise RuntimeError("Le bilan exporté est vide")
            view.close()

        _rapporter(f"OdinFinance {app.applicationVersion()} : autotest réussi.")
        return 0
    except Exception:
        _rapporter("OdinFinance : autotest échoué.\n" + traceback.format_exc())
        return 1
