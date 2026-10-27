"""Objets métier renvoyés par TresoQueries (à la place des tuples indexés par position)."""
from dataclasses import dataclass
from datetime import date

RECETTE = "RECETTE"
DEPENSE = "DEPENSE"
VIREMENT = "VIREMENT"  # pas une catégorie : type d'opération entre deux comptes

LIBELLES_FLUX = {RECETTE: "Recette", DEPENSE: "Dépense", VIREMENT: "Virement interne"}
LIBELLES_TIERS = {"PHYSIQUE": "Personne physique", "MORAL": "Personne morale"}


class ErreurMetier(Exception):
    """Erreur prévue, affichable telle quelle à l'utilisateur."""


@dataclass(frozen=True)
class Compte:
    id: int
    code: str
    nom: str
    solde_initial: int  # centimes, avant toute opération enregistrée
    ordre: int = 0

    @property
    def libelle(self) -> str:
        return f"{self.code} · {self.nom}" if self.code else self.nom


@dataclass(frozen=True)
class Categorie:
    id: int
    nom: str
    type_flux: str
    parent_id: int | None = None


@dataclass(frozen=True)
class Tiers:
    id: int
    nom: str
    type_tier: str


@dataclass(frozen=True)
class Operation:
    id: int
    date: date
    libelle: str
    montant: int  # centimes, toujours positif : le sens vient du type
    reference: str | None
    compte_id: int
    compte_nom: str
    categorie_id: int | None = None
    categorie_nom: str | None = None
    type_flux: str | None = None  # RECETTE / DEPENSE, None pour un virement
    compte_destination_id: int | None = None
    compte_destination_nom: str | None = None
    tier_id: int | None = None
    tier_nom: str | None = None

    @property
    def est_virement(self) -> bool:
        return self.compte_destination_id is not None

    @property
    def type_operation(self) -> str:
        return VIREMENT if self.est_virement else self.type_flux

    def mouvement(self, compte_id: int) -> int:
        """Effet de l'opération sur le solde d'un compte, en centimes (positif = entrée d'argent)."""
        if self.est_virement:
            if compte_id == self.compte_destination_id:
                return self.montant
            if compte_id == self.compte_id:
                return -self.montant
            return 0
        if compte_id != self.compte_id:
            return 0
        return self.montant if self.type_flux == RECETTE else -self.montant
