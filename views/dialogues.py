"""Boîtes de dialogue de création / modification (compte, catégorie, tiers) et confirmations."""
from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from database.modeles import DEPENSE, LIBELLES_FLUX, LIBELLES_TIERS, RECETTE, Categorie, Compte, Tiers
from services.montants import formater_saisie, parser_montant_signe
from views.theme import rafraichir_style
from views.widgets import ChampFormulaire, TitreSection


class DialogueFormulaire(QDialog):
    """Squelette commun : titre, champs, boutons Annuler / Enregistrer, validation avant fermeture."""

    def __init__(self, parent: QWidget, titre: str, texte_validation: str):
        super().__init__(parent)
        self.setWindowTitle(titre)
        self.setMinimumWidth(380)
        self.layout_champs = QVBoxLayout(self)
        self.layout_champs.setContentsMargins(24, 20, 24, 20)
        self.layout_champs.setSpacing(14)
        self.layout_champs.addWidget(TitreSection(titre))
        self.boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.boutons.button(QDialogButtonBox.StandardButton.Save).setText(texte_validation)
        self.boutons.button(QDialogButtonBox.StandardButton.Save).setProperty("variante", "primaire")
        self.boutons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.boutons.button(QDialogButtonBox.StandardButton.Cancel).setProperty("variante", "discret")
        self.boutons.accepted.connect(self._valider)
        self.boutons.rejected.connect(self.reject)

    def ajouter(self, champ: ChampFormulaire):
        self.layout_champs.addWidget(champ)

    def terminer(self):
        self.layout_champs.addSpacing(6)
        self.layout_champs.addWidget(self.boutons)

    def _valider(self):
        if self.verifier():
            self.accept()

    def verifier(self) -> bool:
        return True

    @staticmethod
    def _exiger_texte(champ: ChampFormulaire, message: str) -> bool:
        champ.effacer_erreur()
        if not champ.champ.text().strip():
            champ.afficher_erreur(message)
            champ.champ.setFocus()
            return False
        return True


class DialogueCompte(DialogueFormulaire):
    def __init__(self, parent: QWidget, compte: Compte | None = None):
        super().__init__(parent, "Modifier le compte" if compte else "Nouveau compte",
                         "Enregistrer" if compte else "Ajouter")
        self.code = QLineEdit(compte.code if compte else "")
        self.code.setPlaceholderText("Ex. 512")
        self.code.setMaxLength(12)
        self.nom = QLineEdit(compte.nom if compte else "")
        self.nom.setPlaceholderText("Ex. Compte courant")
        self.nom.setMaxLength(60)
        self.solde = QLineEdit(formater_saisie(compte.solde_initial) if compte else "")
        self.solde.setPlaceholderText("0,00")
        self.champ_nom = ChampFormulaire("Nom", self.nom)
        self.champ_solde = ChampFormulaire("Solde initial (€)", self.solde)
        self.ajouter(ChampFormulaire("Numéro de compte", self.code, facultatif=True))
        self.ajouter(self.champ_nom)
        self.ajouter(self.champ_solde)
        self.terminer()

    def verifier(self) -> bool:
        ok = self._exiger_texte(self.champ_nom, "Donnez un nom au compte.")
        self.champ_solde.effacer_erreur()
        try:
            parser_montant_signe(self.solde.text())
        except ValueError as e:
            self.champ_solde.afficher_erreur(str(e))
            ok = False
        return ok

    def valeurs(self) -> tuple[str, str, int]:
        return self.code.text().strip(), self.nom.text().strip(), parser_montant_signe(self.solde.text())


class DialogueCategorie(DialogueFormulaire):
    def __init__(self, parent: QWidget, categories: list[Categorie], categorie: Categorie | None = None,
                 type_flux: str | None = None):
        super().__init__(parent, "Modifier la catégorie" if categorie else "Nouvelle catégorie",
                         "Enregistrer" if categorie else "Ajouter")
        self.categories = categories
        self.categorie = categorie
        self.nom = QLineEdit(categorie.nom if categorie else "")
        self.nom.setPlaceholderText("Ex. Billetterie")
        self.nom.setMaxLength(60)
        self.type = QComboBox()
        for valeur in (RECETTE, DEPENSE):
            self.type.addItem(LIBELLES_FLUX[valeur], valeur)
        self.type.setCurrentIndex(self.type.findData(categorie.type_flux if categorie else type_flux or RECETTE))
        self.parent_combo = QComboBox()
        self.champ_nom = ChampFormulaire("Nom", self.nom)
        self.ajouter(self.champ_nom)
        self.ajouter(ChampFormulaire("Type", self.type))
        self.ajouter(ChampFormulaire("Sous-catégorie de", self.parent_combo, facultatif=True))
        self.terminer()
        self.type.currentIndexChanged.connect(self._remplir_parents)
        self._remplir_parents()
        if categorie and categorie.parent_id:
            self.parent_combo.setCurrentIndex(self.parent_combo.findData(categorie.parent_id))

    def _remplir_parents(self):
        type_flux = self.type.currentData()
        self.parent_combo.clear()
        self.parent_combo.addItem("Aucune (catégorie principale)", None)
        for c in self.categories:
            if c.parent_id is None and c.type_flux == type_flux and (not self.categorie or c.id != self.categorie.id):
                self.parent_combo.addItem(c.nom, c.id)

    def verifier(self) -> bool:
        return self._exiger_texte(self.champ_nom, "Donnez un nom à la catégorie.")

    def valeurs(self) -> tuple[str, str, int | None]:
        return self.nom.text().strip(), self.type.currentData(), self.parent_combo.currentData()


class DialogueTiers(DialogueFormulaire):
    def __init__(self, parent: QWidget, tiers: Tiers | None = None):
        super().__init__(parent, "Modifier le tiers" if tiers else "Nouveau tiers", "Enregistrer" if tiers else "Ajouter")
        self.nom = QLineEdit(tiers.nom if tiers else "")
        self.nom.setPlaceholderText("Ex. Métro Annecy")
        self.nom.setMaxLength(80)
        self.type = QComboBox()
        for valeur, libelle in LIBELLES_TIERS.items():
            self.type.addItem(libelle, valeur)
        self.type.setCurrentIndex(self.type.findData(tiers.type_tier if tiers else "MORAL"))
        self.champ_nom = ChampFormulaire("Nom", self.nom)
        self.ajouter(self.champ_nom)
        self.ajouter(ChampFormulaire("Type", self.type))
        self.terminer()

    def verifier(self) -> bool:
        return self._exiger_texte(self.champ_nom, "Donnez un nom au tiers.")

    def valeurs(self) -> tuple[str, str]:
        return self.nom.text().strip(), self.type.currentData()


def bouton_message(boite: QMessageBox, texte: str, role: QMessageBox.ButtonRole, variante: str | None = None):
    """Ajoute un bouton à une QMessageBox ; QMessageBox le stylise dès l'ajout, d'où le rafraîchissement."""
    b = boite.addButton(texte, role)
    if variante:
        b.setProperty("variante", variante)
        rafraichir_style(b)
    return b


def confirmer(parent: QWidget, titre: str, question: str, action: str) -> bool:
    """Confirmation d'une action destructrice, avec un bouton qui nomme l'action plutôt que « Oui »."""
    boite = QMessageBox(QMessageBox.Icon.Warning, titre, question, parent=parent)
    bouton_action = bouton_message(boite, action, QMessageBox.ButtonRole.DestructiveRole, "danger")
    annuler = bouton_message(boite, "Annuler", QMessageBox.ButtonRole.RejectRole)
    boite.setDefaultButton(annuler)
    boite.exec()
    return boite.clickedButton() is bouton_action


def signaler_erreur(parent: QWidget, titre: str, message: str):
    QMessageBox.warning(parent, titre, message)
