import sqlite3
import os

class DBManager:
    def __init__(self, db_name="tresorerie.db"):
        # On s'assure que le fichier de base de données sera stocké à la racine du projet
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        self.init_db()

    def get_connection(self):
        """Retourne une connexion à la base de données avec les clés étrangères activées."""
        conn = sqlite3.connect(self.db_path)
        # Contrairement à PostgreSQL, SQLite désactive les clés étrangères par défaut pour des raisons historiques.
        # Il faut les activer manuellement à chaque connexion.
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Crée les tables si elles n'existent pas encore."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Table des catégories (dynamiques)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL UNIQUE,
                    type_flux TEXT NOT NULL CHECK(type_flux IN ('RECETTE', 'DEPENSE'))
                )
            """)

            # 2. Table des tiers (personnes physiques ou morales)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL UNIQUE,
                    type_tier TEXT NOT NULL CHECK(type_tier IN ('PHYSIQUE', 'MORAL'))
                )
            """)

            # 3. Table des transactions (avec Foreign Keys)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_transaction TEXT NOT NULL,
                    description TEXT NOT NULL,
                    montant REAL NOT NULL CHECK(montant >= 0),
                    reference_facture TEXT,
                    categorie_id INTEGER NOT NULL,
                    tier_id INTEGER,
                    FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE RESTRICT,
                    FOREIGN KEY (tier_id) REFERENCES tiers(id) ON DELETE SET NULL
                )
            """)
            
            conn.commit()

# Petit bloc de test rapide
if __name__ == "__main__":
    db = DBManager()
    print(f"Base de données initialisée avec succès : {db.db_path}")