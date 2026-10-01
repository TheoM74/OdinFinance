import sys
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
    # 1. Initialisation de l'application Qt
    app = QApplication(sys.argv)

    # 2. Initialisation de la BDD et des requêtes
    db = DBManager()
    queries = TresoQueries(db)
    initialiser_donnees_test(queries)

    # 3. Création de la Vue et du Contrôleur (Architecture MVC)
    view = MainWindow()
    controller = MainController(view, queries)

    # 4. Affichage de la fenêtre et lancement de la boucle événementielle
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()