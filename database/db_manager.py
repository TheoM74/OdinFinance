import os
import sqlite3
import sys
from contextlib import contextmanager

# Version du schéma, stockée dans PRAGMA user_version.
# 0 = base créée par OdinFinance 1.x (montants REAL, pas de comptes), 2 = schéma actuel.
VERSION_SCHEMA = 2

SCHEMA = """
    CREATE TABLE IF NOT EXISTS comptes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL DEFAULT '',
        nom TEXT NOT NULL UNIQUE,
        solde_initial INTEGER NOT NULL DEFAULT 0,  -- en centimes
        ordre INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE,
        type_flux TEXT NOT NULL CHECK(type_flux IN ('RECETTE', 'DEPENSE')),
        parent_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS tiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE,
        type_tier TEXT NOT NULL CHECK(type_tier IN ('PHYSIQUE', 'MORAL'))
    );

    -- Une opération est soit une recette/dépense (categorie_id renseigné),
    -- soit un virement interne entre deux comptes (compte_destination_id renseigné).
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_transaction TEXT NOT NULL,
        description TEXT NOT NULL,
        montant_centimes INTEGER NOT NULL CHECK(montant_centimes >= 0),
        reference_facture TEXT,
        compte_id INTEGER NOT NULL REFERENCES comptes(id) ON DELETE RESTRICT,
        categorie_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
        compte_destination_id INTEGER REFERENCES comptes(id) ON DELETE RESTRICT,
        tier_id INTEGER REFERENCES tiers(id) ON DELETE SET NULL,
        CHECK ((categorie_id IS NULL) <> (compte_destination_id IS NULL)),
        CHECK (compte_destination_id IS NULL OR compte_destination_id <> compte_id)
    );

    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date_transaction);

    CREATE TABLE IF NOT EXISTS parametres (
        cle TEXT PRIMARY KEY,
        valeur TEXT NOT NULL
    );
"""

# Plan de départ d'une base neuve, repris du bilan financier du BDE (modifiable dans Paramètres)
COMPTES_DEPART = [
    ("512", "Compte courant"),
    ("507", "Livret A"),
    ("530 001", "Caisse rouge"),
    ("530 002", "Caisse noire"),
    ("530 003", "SumUp"),
]
CATEGORIES_DEPART = [
    ("Ventes", "RECETTE", None),
    ("Adhésions", "RECETTE", "Ventes"),
    ("Versements divers", "RECETTE", None),
    ("Achats", "DEPENSE", None),
    ("Sorties", "DEPENSE", "Achats"),
    ("Frais divers", "DEPENSE", None),
]


def _executer_schema(conn):
    """Exécute SCHEMA instruction par instruction (executescript() validerait la transaction en cours)."""
    for instruction in SCHEMA.split(";"):
        code = "\n".join(ligne for ligne in instruction.splitlines() if not ligne.strip().startswith("--")).strip()
        if code:
            conn.execute(code)


def chemin_base_historique(nom_fichier="tresorerie.db"):
    """Emplacement utilisé par OdinFinance 1.x : à côté du code (ou dans _internal une fois compilé)."""
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, nom_fichier)


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        dossier = os.path.dirname(db_path)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
        self.init_db()

    @contextmanager
    def connexion(self):
        """Ouvre une connexion, valide en sortie (ou annule sur exception) puis la ferme.

        sqlite3.connect() utilisé seul comme gestionnaire de contexte valide la transaction
        mais ne ferme pas la connexion : d'où cette enveloppe.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # SQLite désactive les clés étrangères par défaut : il faut les activer à chaque connexion.
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """Crée le schéma d'une base neuve ou migre une base 1.x."""
        with self.connexion() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            base_existante = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'transactions'"
            ).fetchone() is not None

        if base_existante and version < 2:
            self._migrer_v1_vers_v2()
        elif not base_existante:
            with self.connexion() as conn:
                _executer_schema(conn)
                self._inserer_plan_depart(conn)
                conn.execute(f"PRAGMA user_version = {VERSION_SCHEMA}")

    @staticmethod
    def _inserer_plan_depart(conn):
        for ordre, (code, nom) in enumerate(COMPTES_DEPART):
            conn.execute("INSERT INTO comptes (code, nom, ordre) VALUES (?, ?, ?)", (code, nom, ordre))
        ids = {}
        for nom, type_flux, parent in CATEGORIES_DEPART:
            cur = conn.execute(
                "INSERT INTO categories (nom, type_flux, parent_id) VALUES (?, ?, ?)",
                (nom, type_flux, ids.get(parent)),
            )
            ids[nom] = cur.lastrowid

    def _migrer_v1_vers_v2(self):
        """Montants REAL -> centimes, ajout des comptes, des virements et des sous-catégories.

        Les opérations existantes sont rattachées à un compte « Compte courant » créé pour l'occasion.
        """
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            # La reconstruction d'une table impose de couper les clés étrangères (hors transaction).
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("BEGIN")
            colonnes_cat = [r[1] for r in conn.execute("PRAGMA table_info(categories)")]
            if "parent_id" not in colonnes_cat:
                conn.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT")
            conn.execute("ALTER TABLE transactions RENAME TO transactions_v1")
            _executer_schema(conn)  # comptes, nouvelle table transactions, parametres
            conn.execute("INSERT INTO comptes (id, code, nom, ordre) VALUES (1, '512', 'Compte courant', 0)")
            conn.execute("""
                INSERT INTO transactions (id, date_transaction, description, montant_centimes, reference_facture,
                                          compte_id, categorie_id, tier_id)
                SELECT id, date_transaction, description, CAST(ROUND(montant * 100) AS INTEGER), reference_facture,
                       1, categorie_id, tier_id
                FROM transactions_v1
            """)
            conn.execute("DROP TABLE transactions_v1")
            conn.execute(f"PRAGMA user_version = {VERSION_SCHEMA}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
