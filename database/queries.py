from database.db_manager import DBManager

class TresoQueries:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    # --- CATEGORIES ---
    def ajouter_categorie(self, nom: str, type_flux: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO categories (nom, type_flux) VALUES (?, ?)",
                (nom, type_flux)
            )
            conn.commit()

    def get_toutes_categories(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, type_flux FROM categories ORDER BY nom")
            return cursor.fetchall()

    def supprimer_categorie(self, categorie_id: int):
        """Supprime une catégorie (échouera si des transactions y sont liées grâce aux Foreign Keys)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (categorie_id,))
            conn.commit()

    # --- TIERS ---
    def ajouter_tier(self, nom: str, type_tier: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO tiers (nom, type_tier) VALUES (?, ?)",
                (nom, type_tier)
            )
            conn.commit()

    def get_tous_tiers(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, type_tier FROM tiers ORDER BY nom")
            return cursor.fetchall()

    def supprimer_tier(self, tier_id: int):
        """Supprime un tier."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tiers WHERE id = ?", (tier_id,))
            conn.commit()

    # --- TRANSACTIONS ---
    def ajouter_transaction(self, date: str, description: str, montant: float, 
                            ref_facture: str, categorie_id: int, tier_id: int = None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (date_transaction, description, montant, reference_facture, categorie_id, tier_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, description, montant, ref_facture, categorie_id, tier_id))
            conn.commit()

    def modifier_transaction(self, trans_id: int, date: str, description: str, montant: float, 
                             ref_facture: str, categorie_id: int, tier_id: int = None):
        """Met à jour une transaction existante."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions 
                SET date_transaction = ?, description = ?, montant = ?, reference_facture = ?, categorie_id = ?, tier_id = ?
                WHERE id = ?
            """, (date, description, montant, ref_facture, categorie_id, tier_id, trans_id))
            conn.commit()

    def supprimer_transaction(self, trans_id: int):
        """Supprime une transaction par son ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            conn.commit()

    def get_toutes_transactions(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.date_transaction, t.description, t.montant, t.reference_facture,
                       c.nom AS categorie_nom, c.type_flux,
                       ti.nom AS tier_nom, t.categorie_id, t.tier_id
                FROM transactions t
                JOIN categories c ON t.categorie_id = c.id
                LEFT JOIN tiers ti ON t.tier_id = ti.id
                ORDER BY t.date_transaction DESC, t.id DESC
            """)
            return cursor.fetchall()

    def get_totaux_par_categorie(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.nom, c.type_flux, COALESCE(SUM(t.montant), 0.0) as total
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.categorie_id
                GROUP BY c.id, c.nom, c.type_flux
                ORDER BY c.type_flux DESC, c.nom ASC
            """)
            return cursor.fetchall()