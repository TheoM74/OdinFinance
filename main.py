import sys
import os

# --- CORRECTION COCOA ULTRA-FORCÉE POUR MAC ---
if sys.platform == "darwin":
    try:
        import PyQt6
        pyqt_path = os.path.dirname(PyQt6.__file__)
        platforms_dir = os.path.join(pyqt_path, "Qt6", "plugins", "platforms")
        if not os.path.exists(platforms_dir):
            platforms_dir = os.path.join(pyqt_path, "Qt", "plugins", "platforms")
        
        if os.path.exists(platforms_dir):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
    except Exception:
        pass
# ---------------------------------------------

from PyQt6.QtWidgets import QApplication
from database.db_manager import DBManager
from database.queries import TresoQueries
from views.main_window import MainWindow
from controllers.main_controller import MainController

def initialiser_donnees_test(queries: TresoQueries):
    """Insère les catégories et tiers de base pour l'association ODIN si elles n'existent pas."""
    categories_init = [
        ("Évènements / Soirées", "RECETTE"),
        ("Subventions", "RECETTE"),
        ("Ventes Courses (Épicerie)", "RECETTE"),
        ("Commissions préventes", "RECETTE"),
        ("Frais bancaires", "DEPENSE"),
        ("Matériel", "DEPENSE"),
        ("Courses METRO (Épicerie)", "DEPENSE")
    ]
    for nom, type_flux in categories_init:
        queries.ajouter_categorie(nom, type_flux)

    tiers_init = [
        ("METRO", "MORAL"),
        ("BDE", "MORAL"),
        ("Université Savoie Mont Blanc", "MORAL"),
        ("Rémy (Membre)", "PHYSIQUE")
    ]
    for nom, type_tier in tiers_init:
        queries.ajouter_tier(nom, type_tier)

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

    db = DBManager()
    queries = TresoQueries(db)
    initialiser_donnees_test(queries)

    view = MainWindow()
    controller = MainController(view, queries)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()