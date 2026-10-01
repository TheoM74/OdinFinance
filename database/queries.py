from database.db_manager import DBManager

class TresoQueries:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    # --- CATEGORIES ---
    def ajouter_categorie(self, nom: str, type_flux: str):
        """Ajoute une nouvelle catégorie (RECETTE ou DEPENSE)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO categories (nom, type_flux) VALUES (?, ?)",
                (nom, type_flux)
            )
            conn.commit()

    def get_toutes_categories(self):
        """Récupère toutes les catégories de la base."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, type_flux FROM categories ORDER BY nom")
            return cursor.fetchall()

    # --- TIERS ---
    def ajouter_tier(self, nom: str, type_tier: str):
        """Ajoute un tier (PHYSIQUE ou MORAL)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO tiers (nom, type_tier) VALUES (?, ?)",
                (nom, type_tier)
            )
            conn.commit()

    def get_tous_tiers(self):
        """Récupère tous les tiers."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, type_tier FROM tiers ORDER BY nom")
            return cursor.fetchall()

    # --- TRANSACTIONS ---
    def ajouter_transaction(self, date: str, description: str, montant: float, 
                            ref_facture: str, categorie_id: int, tier_id: int = None):
        """Enregistre une nouvelle transaction financière."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (date_transaction, description, montant, reference_facture, categorie_id, tier_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, description, montant, ref_facture, categorie_id, tier_id))
            conn.commit()

    def get_toutes_transactions(self):
        """Récupère l'historique complet des transactions avec les noms des catégories et tiers (via JOIN)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.date_transaction, t.description, t.montant, t.reference_facture,
                       c.nom AS categorie_nom, c.type_flux,
                       ti.nom AS tier_nom
                FROM transactions t
                JOIN categories c ON t.categorie_id = c.id
                LEFT JOIN tiers ti ON t.tier_id = ti.id
                ORDER BY t.date_transaction DESC, t.id DESC
            """)
            return cursor.fetchall()