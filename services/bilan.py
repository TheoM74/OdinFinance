"""Calculs du bilan, sans dépendance à Qt ni à la base : utilisés par l'écran Synthèse et l'export Excel."""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta

from database.modeles import DEPENSE, RECETTE, Categorie, Compte, Operation


@dataclass(frozen=True)
class Exercice:
    debut: date
    fin: date

    @property
    def annee(self) -> int:
        """Année affichée dans le titre : celle de la clôture (« Bilan financier 2026 » pour avril 2025 → mars 2026)."""
        return self.fin.year

    def contient(self, jour: date) -> bool:
        return self.debut <= jour <= self.fin

    def mois(self) -> list[tuple[int, int]]:
        """Liste des (année, mois) couverts, dans l'ordre."""
        resultat, annee, mois = [], self.debut.year, self.debut.month
        while (annee, mois) <= (self.fin.year, self.fin.month):
            resultat.append((annee, mois))
            annee, mois = (annee + 1, 1) if mois == 12 else (annee, mois + 1)
        return resultat

    @staticmethod
    def par_defaut(aujourd_hui: date) -> "Exercice":
        """Exercice d'avril à mars, comme le bilan du BDE, contenant la date du jour."""
        annee = aujourd_hui.year if aujourd_hui.month >= 4 else aujourd_hui.year - 1
        return Exercice(date(annee, 4, 1), date(annee + 1, 3, 31))


def fin_de_mois(annee: int, mois: int) -> date:
    return date(annee, mois, monthrange(annee, mois)[1])


# --- Soldes ---
def solde_compte(compte: Compte, operations: list[Operation], jusqu_au: date | None = None, avant: date | None = None) -> int:
    """Solde en centimes : jusqu_au (inclus) ou avant (exclu) une date ; sans borne = solde actuel."""
    total = compte.solde_initial
    for op in operations:
        if (jusqu_au and op.date > jusqu_au) or (avant and op.date >= avant):
            continue
        total += op.mouvement(compte.id)
    return total


def soldes_par_compte(comptes: list[Compte], operations: list[Operation], jusqu_au: date | None = None) -> list[tuple[Compte, int]]:
    return [(c, solde_compte(c, operations, jusqu_au=jusqu_au)) for c in comptes]


# --- Compte de résultat ---
@dataclass
class LigneResultat:
    categorie: Categorie
    total: int  # inclut les sous-catégories
    sous_lignes: list[tuple[Categorie, int]] = field(default_factory=list)  # lignes « dont … »


@dataclass
class CompteResultat:
    produits: list[LigneResultat]
    charges: list[LigneResultat]

    @property
    def total_produits(self) -> int:
        return sum(l.total for l in self.produits)

    @property
    def total_charges(self) -> int:
        return sum(l.total for l in self.charges)

    @property
    def resultat(self) -> int:
        return self.total_produits - self.total_charges


def compte_resultat(categories: list[Categorie], operations: list[Operation], garder_vides: bool = True) -> CompteResultat:
    """Totaux par catégorie racine, avec le détail « dont » des sous-catégories. Les virements sont ignorés."""
    par_categorie: dict[int, int] = {}
    for op in operations:
        if op.categorie_id is not None:
            par_categorie[op.categorie_id] = par_categorie.get(op.categorie_id, 0) + op.montant

    racines = [c for c in categories if c.parent_id is None]
    enfants: dict[int, list[Categorie]] = {}
    for c in categories:
        if c.parent_id is not None:
            enfants.setdefault(c.parent_id, []).append(c)

    def lignes(type_flux: str) -> list[LigneResultat]:
        resultat = []
        for racine in (c for c in racines if c.type_flux == type_flux):
            sous = [(e, par_categorie.get(e.id, 0)) for e in sorted(enfants.get(racine.id, []), key=lambda c: c.nom)]
            total = par_categorie.get(racine.id, 0) + sum(m for _, m in sous)
            if garder_vides or total:
                resultat.append(LigneResultat(racine, total, [(e, m) for e, m in sous if garder_vides or m]))
        return resultat

    return CompteResultat(lignes(RECETTE), lignes(DEPENSE))


# --- Journal d'un compte (feuille 1 de l'export) ---
@dataclass(frozen=True)
class LigneJournal:
    date: date
    libelle: str
    montant: int
    debit: bool  # True = entrée d'argent sur le compte (colonne Débit du bilan)


@dataclass
class MoisJournal:
    annee: int
    mois: int
    lignes: list[LigneJournal]
    solde_fin: int

    @property
    def total_debit(self) -> int:
        return sum(l.montant for l in self.lignes if l.debit)

    @property
    def total_credit(self) -> int:
        return sum(l.montant for l in self.lignes if not l.debit)


@dataclass
class JournalCompte:
    compte: Compte
    date_ouverture: date
    solde_ouverture: int
    mois: list[MoisJournal]


def journal_compte(compte: Compte, operations: list[Operation], exercice: Exercice) -> JournalCompte:
    """Mouvements d'un compte sur l'exercice, regroupés par mois (seuls les mois avec mouvements sont gardés)."""
    ouverture = solde_compte(compte, operations, avant=exercice.debut)
    mouvements = sorted(
        (op for op in operations if exercice.contient(op.date) and op.mouvement(compte.id)),
        key=lambda op: (op.date, op.id),
    )
    mois_journal, solde = [], ouverture
    for annee, mois in exercice.mois():
        lignes = [
            LigneJournal(op.date, op.libelle, op.montant, op.mouvement(compte.id) > 0)
            for op in mouvements if (op.date.year, op.date.month) == (annee, mois)
        ]
        if lignes:
            solde += sum(l.montant if l.debit else -l.montant for l in lignes)
            mois_journal.append(MoisJournal(annee, mois, lignes, solde))
    return JournalCompte(compte, exercice.debut - timedelta(days=1), ouverture, mois_journal)
