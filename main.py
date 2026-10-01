import sys
import os

from PyQt6.QtWidgets import QApplication
from database.db_manager import DBManager
from database.queries import TresoQueries
from views.main_window import MainWindow
from controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)

    # --- CHARGEMENT DYNAMIQUE DU FICHIER DE STYLE ---
    chemin_style = os.path.join(os.path.dirname(__file__), "resources", "style.qss")
    if os.path.exists(chemin_style):
        with open(chemin_style, "r", encoding="utf-8") as fichier_qss:
            app.setStyleSheet(fichier_qss.read())
    else:
        print("Attention : Fichier de style (resources/style.qss) introuvable.")
    # -------------------------------------------------

    # Initialisation de la base de données (tables vides)
    db = DBManager()
    queries = TresoQueries(db)

    view = MainWindow()
    controller = MainController(view, queries)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

    #fin