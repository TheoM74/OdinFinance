import sys
from database.db_manager import DBManager
from database.queries import TresoQueries

def initialiser_donnees_test(queries: TresoQueries):
    """Insère les catégories et tiers de base pour l'association ODIN."""
    # Catégories basées sur tes besoins
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

    # Tiers de test
    tiers_init = [
        ("METRO", "MORAL"),
        ("BDE", "MORAL"),
        ("Université Savoie Mont Blanc", "MORAL"),
        ("Rémy (Membre)", "PHYSIQUE")
    ]
    for nom, type_tier in tiers_init:
        queries.ajouter_tier(nom, type_tier)

def main():
    print("Démarrage de l'application de trésorerie OdinFinance...")
    
    # 1. Initialisation de la BDD et des requêtes
    db = DBManager()
    queries = TresoQueries(db)
    
    # 2. Ajout des données par défaut
    initialiser_donnees_test(queries)
    
    # 3. Vérification en affichant les catégories en console
    print("\n--- Catégories enregistrées en BDD ---")
    for cat in queries.get_toutes_categories():
        print(f"[{cat[2]}] {cat[1]}")

    print("\n[OK] Base de données prête pour l'interface graphique !")

if __name__ == "__main__":
    main()