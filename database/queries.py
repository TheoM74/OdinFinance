import sqlite3
from datetime import date

from database.db_manager import DBManager
from database.modeles import Categorie, Compte, ErreurMetier, Operation, Tiers

PARAMETRES_DEFAUT = {
    "nom_association": "BDE ODIN",
}


class TresoQueries:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    # --- Outils communs ---
    def _lire(self, sql: str, params=()):
        with self.db.connexion() as conn:
            return conn.execute(sql, params).fetchall()

    def _ecrire(self, sql: str, params=(), doublon: str | None = None) -> int:
        """Exécute une écriture et renvoie l'id inséré. `doublon` = message si une contrainte UNIQUE saute."""
        try:
            with self.db.connexion() as conn:
                return conn.execute(sql, params).lastrowid
        except sqlite3.IntegrityError as e:
            if doublon and "UNIQUE" in str(e):
                raise ErreurMetier(doublon) from e
            raise

    def _compter(self, sql: str, params=()) -> int:
        return self._lire(sql, params)[0][0]

    # --- PARAMÈTRES ---
    def get_parametre(self, cle: str, defaut: str | None = None) -> str | None:
        lignes = self._lire("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
        return lignes[0]["valeur"] if lignes else PARAMETRES_DEFAUT.get(cle, defaut)

    def set_parametre(self, cle: str, valeur: str):
        self._ecrire(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?) ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
            (cle, valeur),
        )

    # --- COMPTES ---
    def get_tous_comptes(self) -> list[Compte]:
        return [Compte(**dict(r)) for r in self._lire(
            "SELECT id, code, nom, solde_initial, ordre FROM comptes ORDER BY ordre, code, nom")]

    def ajouter_compte(self, code: str, nom: str, solde_initial: int) -> int:
        ordre = self._compter("SELECT COALESCE(MAX(ordre) + 1, 0) FROM comptes")
        return self._ecrire(
            "INSERT INTO comptes (code, nom, solde_initial, ordre) VALUES (?, ?, ?, ?)",
            (code, nom, solde_initial, ordre), doublon=f"Un compte « {nom} » existe déjà.")

    def modifier_compte(self, compte_id: int, code: str, nom: str, solde_initial: int):
        self._ecrire(
            "UPDATE comptes SET code = ?, nom = ?, solde_initial = ? WHERE id = ?",
            (code, nom, solde_initial, compte_id), doublon=f"Un compte « {nom} » existe déjà.")

    def supprimer_compte(self, compte_id: int):
        utilisations = self._compter(
            "SELECT COUNT(*) FROM transactions WHERE compte_id = ? OR compte_destination_id = ?", (compte_id, compte_id))
        if utilisations:
            raise ErreurMetier(
                f"Ce compte porte {utilisations} opération(s). Supprimez-les ou modifiez-les avant de supprimer le compte.")
        self._ecrire("DELETE FROM comptes WHERE id = ?", (compte_id,))

    # --- CATÉGORIES ---
    def get_toutes_categories(self) -> list[Categorie]:
        return [Categorie(**dict(r)) for r in self._lire(
            "SELECT id, nom, type_flux, parent_id FROM categories ORDER BY type_flux DESC, nom")]

    def ajouter_categorie(self, nom: str, type_flux: str, parent_id: int | None = None) -> int:
        self._verifier_parent(None, type_flux, parent_id)
        return self._ecrire(
            "INSERT INTO categories (nom, type_flux, parent_id) VALUES (?, ?, ?)",
            (nom, type_flux, parent_id), doublon=f"Une catégorie « {nom} » existe déjà.")

    def modifier_categorie(self, categorie_id: int, nom: str, type_flux: str, parent_id: int | None):
        self._verifier_parent(categorie_id, type_flux, parent_id)
        ancien_type = self._lire("SELECT type_flux FROM categories WHERE id = ?", (categorie_id,))[0]["type_flux"]
        if ancien_type != type_flux:
            if self._compter("SELECT COUNT(*) FROM transactions WHERE categorie_id = ?", (categorie_id,)):
                raise ErreurMetier("Impossible de changer le type d'une catégorie déjà utilisée par des opérations.")
            if self._compter("SELECT COUNT(*) FROM categories WHERE parent_id = ?", (categorie_id,)):
                raise ErreurMetier("Impossible de changer le type d'une catégorie qui a des sous-catégories.")
        self._ecrire(
            "UPDATE categories SET nom = ?, type_flux = ?, parent_id = ? WHERE id = ?",
            (nom, type_flux, parent_id, categorie_id), doublon=f"Une catégorie « {nom} » existe déjà.")

    def _verifier_parent(self, categorie_id: int | None, type_flux: str, parent_id: int | None):
        """Un seul niveau de sous-catégorie, et le parent est du même type (recette ou dépense)."""
        if parent_id is None:
            return
        if parent_id == categorie_id:
            raise ErreurMetier("Une catégorie ne peut pas être sa propre catégorie parente.")
        parent = self._lire("SELECT type_flux, parent_id FROM categories WHERE id = ?", (parent_id,))
        if not parent:
            raise ErreurMetier("La catégorie parente n'existe plus.")
        if parent[0]["parent_id"] is not None:
            raise ErreurMetier("La catégorie parente est déjà une sous-catégorie : un seul niveau est possible.")
        if parent[0]["type_flux"] != type_flux:
            raise ErreurMetier("La catégorie parente doit être du même type (recette ou dépense).")
        if categorie_id is not None and self._compter(
                "SELECT COUNT(*) FROM categories WHERE parent_id = ?", (categorie_id,)):
            raise ErreurMetier("Cette catégorie a déjà des sous-catégories : elle ne peut pas devenir une sous-catégorie.")

    def supprimer_categorie(self, categorie_id: int):
        utilisations = self._compter("SELECT COUNT(*) FROM transactions WHERE categorie_id = ?", (categorie_id,))
        if utilisations:
            raise ErreurMetier(
                f"Cette catégorie est utilisée par {utilisations} opération(s). Changez leur catégorie avant de la supprimer.")
        if self._compter("SELECT COUNT(*) FROM categories WHERE parent_id = ?", (categorie_id,)):
            raise ErreurMetier("Cette catégorie a des sous-catégories. Supprimez-les ou déplacez-les d'abord.")
        self._ecrire("DELETE FROM categories WHERE id = ?", (categorie_id,))

    # --- TIERS ---
    def get_tous_tiers(self) -> list[Tiers]:
        return [Tiers(**dict(r)) for r in self._lire("SELECT id, nom, type_tier FROM tiers ORDER BY nom")]

    def ajouter_tier(self, nom: str, type_tier: str) -> int:
        return self._ecrire("INSERT INTO tiers (nom, type_tier) VALUES (?, ?)", (nom, type_tier),
                            doublon=f"Un tiers « {nom} » existe déjà.")

    def modifier_tier(self, tier_id: int, nom: str, type_tier: str):
        self._ecrire("UPDATE tiers SET nom = ?, type_tier = ? WHERE id = ?", (nom, type_tier, tier_id),
                     doublon=f"Un tiers « {nom} » existe déjà.")

    def compter_operations_tier(self, tier_id: int) -> int:
        return self._compter("SELECT COUNT(*) FROM transactions WHERE tier_id = ?", (tier_id,))

    def supprimer_tier(self, tier_id: int):
        """Les opérations liées sont conservées, sans tiers (ON DELETE SET NULL)."""
        self._ecrire("DELETE FROM tiers WHERE id = ?", (tier_id,))

    # --- OPÉRATIONS ---
    def get_toutes_operations(self) -> list[Operation]:
        lignes = self._lire("""
            SELECT t.id, t.date_transaction, t.description, t.montant_centimes, t.reference_facture,
                   t.compte_id, co.nom AS compte_nom,
                   t.categorie_id, ca.nom AS categorie_nom, ca.type_flux,
                   t.compte_destination_id, cd.nom AS compte_destination_nom,
                   t.tier_id, ti.nom AS tier_nom
            FROM transactions t
            JOIN comptes co ON co.id = t.compte_id
            LEFT JOIN categories ca ON ca.id = t.categorie_id
            LEFT JOIN comptes cd ON cd.id = t.compte_destination_id
            LEFT JOIN tiers ti ON ti.id = t.tier_id
            ORDER BY t.date_transaction DESC, t.id DESC
        """)
        return [Operation(
            id=r["id"], date=date.fromisoformat(r["date_transaction"]), libelle=r["description"],
            montant=r["montant_centimes"], reference=r["reference_facture"],
            compte_id=r["compte_id"], compte_nom=r["compte_nom"],
            categorie_id=r["categorie_id"], categorie_nom=r["categorie_nom"], type_flux=r["type_flux"],
            compte_destination_id=r["compte_destination_id"], compte_destination_nom=r["compte_destination_nom"],
            tier_id=r["tier_id"], tier_nom=r["tier_nom"],
        ) for r in lignes]

    def enregistrer_operation(self, operation_id: int | None, jour: date, libelle: str, montant: int,
                              reference: str | None, compte_id: int, categorie_id: int | None,
                              compte_destination_id: int | None, tier_id: int | None) -> int:
        """Ajoute (operation_id=None) ou met à jour une opération. Renvoie son id."""
        valeurs = (jour.isoformat(), libelle, montant, reference, compte_id, categorie_id, compte_destination_id, tier_id)
        if operation_id is None:
            return self._ecrire("""
                INSERT INTO transactions (date_transaction, description, montant_centimes, reference_facture,
                                          compte_id, categorie_id, compte_destination_id, tier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, valeurs)
        self._ecrire("""
            UPDATE transactions
            SET date_transaction = ?, description = ?, montant_centimes = ?, reference_facture = ?,
                compte_id = ?, categorie_id = ?, compte_destination_id = ?, tier_id = ?
            WHERE id = ?
        """, valeurs + (operation_id,))
        return operation_id

    def supprimer_operation(self, operation_id: int):
        self._ecrire("DELETE FROM transactions WHERE id = ?", (operation_id,))
