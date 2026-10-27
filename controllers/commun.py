"""Outils partagés par les contrôleurs d'écran."""
from PyQt6.QtWidgets import QComboBox

from database.modeles import ErreurMetier, Categorie


def remplir_combo(combo: QComboBox, options: list[tuple[str, object]], premier: str | None = None):
    """Remplit une liste déroulante en conservant la sélection courante si elle existe encore."""
    actuel = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if premier is not None:
        combo.addItem(premier, None)
    for texte, valeur in options:
        combo.addItem(texte, valeur)
    index = combo.findData(actuel)
    combo.setCurrentIndex(index if index >= 0 else 0)
    combo.blockSignals(False)


def options_categories(categories: list[Categorie], type_flux: str | None = None) -> list[tuple[str, int]]:
    """Catégories principales suivies de leurs sous-catégories (« Ventes › Adhésions »), recettes d'abord."""
    options = []
    for type_courant in ("RECETTE", "DEPENSE"):
        if type_flux and type_courant != type_flux:
            continue
        for racine in (c for c in categories if c.type_flux == type_courant and c.parent_id is None):
            options.append((racine.nom, racine.id))
            options += [(f"{racine.nom} › {e.nom}", e.id) for e in categories if e.parent_id == racine.id]
    return options


def editer_avec_dialogue(dialogue, enregistrer):
    """Ouvre `dialogue` et appelle enregistrer(*dialogue.valeurs()). Une ErreurMetier (nom en double…)
    s'affiche sous le champ Nom et la boîte reste ouverte pour corriger.

    Renvoie ce que renvoie `enregistrer` (l'id créé pour un ajout), True s'il ne renvoie rien, False si annulé."""
    while dialogue.exec():
        try:
            resultat = enregistrer(*dialogue.valeurs())
            return True if resultat is None else resultat
        except ErreurMetier as e:
            dialogue.champ_nom.afficher_erreur(str(e))
    return False
