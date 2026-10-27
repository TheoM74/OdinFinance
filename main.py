import os
import shutil
import sys

from PyQt6.QtCore import QLocale, QSettings, QStandardPaths
from PyQt6.QtWidgets import QApplication

from controllers.main_controller import MainController
from database.db_manager import DBManager, chemin_base_historique
from database.queries import TresoQueries
from views.main_window import MainWindow
from views.theme import GestionnaireTheme

VERSION = "2.0.0"
NOM_BASE = "tresorerie.db"


def chemin_base_donnees() -> str:
    """La base vit dans le dossier de données de l'utilisateur (et non plus dans le dossier de l'application,
    effacé à chaque mise à jour et en lecture seule sur macOS). Une base 1.x existante y est copiée."""
    dossier = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    chemin = os.path.join(dossier, NOM_BASE)
    ancienne = chemin_base_historique(NOM_BASE)
    if not os.path.exists(chemin) and os.path.exists(ancienne):
        os.makedirs(dossier, exist_ok=True)
        shutil.copy2(ancienne, chemin)
    return chemin


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("OdinFinance")
    app.setApplicationName("OdinFinance")
    app.setApplicationVersion(VERSION)
    QLocale.setDefault(QLocale(QLocale.Language.French, QLocale.Country.France))

    if "--autotest" in sys.argv:
        from verification import verifier
        sys.exit(verifier(app))

    settings = QSettings()
    themes = GestionnaireTheme(app, settings)
    themes.appliquer()

    chemin_base = chemin_base_donnees()
    queries = TresoQueries(DBManager(chemin_base))

    view = MainWindow()
    if settings.value("geometrie"):
        view.restoreGeometry(settings.value("geometrie"))
    app.aboutToQuit.connect(lambda: settings.setValue("geometrie", view.saveGeometry()))
    controller = MainController(view, queries, themes, settings, chemin_base)  # référence gardée jusqu'à la fin

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
