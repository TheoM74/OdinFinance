import os

from PyQt6.QtCore import QDate, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QFileDialog

from controllers.commun import editer_avec_dialogue
from database.modeles import ErreurMetier
from views.dialogues import DialogueCategorie, DialogueCompte, DialogueTiers, confirmer, signaler_erreur

DUREE_MAX_EXERCICE = 731  # jours : un exercice dure au plus deux ans (premier exercice allongé)


class ParametresController:
    def __init__(self, principal):
        self.principal = principal
        self.queries = principal.queries
        self.vue = v = principal.view.page_parametres
        self.donnees = None

        v.btn_enregistrer_association.clicked.connect(self.enregistrer_association)
        v.nom_association_input.returnPressed.connect(self.enregistrer_association)
        v.btn_ouvrir_dossier.clicked.connect(self.ouvrir_dossier)
        v.btn_importer_base.clicked.connect(self.importer_base)

        # Chaque liste : (vue, ajouter, modifier, supprimer, actions)
        for vue, ajouter, modifier, supprimer, actions in (
            (v.table_comptes, v.btn_ajouter_compte, v.btn_modifier_compte, v.btn_supprimer_compte,
             (self.ajouter_compte, self.modifier_compte, self.supprimer_compte)),
            (v.arbre_categories, v.btn_ajouter_categorie, v.btn_modifier_categorie, v.btn_supprimer_categorie,
             (self.ajouter_categorie, self.modifier_categorie, self.supprimer_categorie)),
            (v.table_tiers, v.btn_ajouter_tier, v.btn_modifier_tier, v.btn_supprimer_tier,
             (self.ajouter_tier, self.modifier_tier, self.supprimer_tier)),
        ):
            ajouter.clicked.connect(actions[0])
            modifier.clicked.connect(actions[1])
            supprimer.clicked.connect(actions[2])
            vue.doubleClicked.connect(lambda _, action=actions[1]: action())
            vue.itemSelectionChanged.connect(lambda vue=vue, b=(modifier, supprimer): self._activer(vue, b))
            self._activer(vue, (modifier, supprimer))

    def _activer(self, vue, boutons):
        """Modifier et Supprimer ne sont utilisables qu'avec un élément sélectionné."""
        actif = self.vue.id_selectionne(vue) is not None
        for b in boutons:
            b.setEnabled(actif)

    def rafraichir(self, donnees):
        self.donnees = d = donnees
        v = self.vue
        v.afficher_comptes(d.comptes)
        v.afficher_categories(d.categories)
        v.afficher_tiers(d.tiers)
        ex = d.exercice
        v.afficher_association(d.nom_association, QDate(ex.debut.year, ex.debut.month, ex.debut.day),
                               QDate(ex.fin.year, ex.fin.month, ex.fin.day))
        v.label_chemin_base.setText(f"OdinFinance {QApplication.applicationVersion()}\n"
                                    f"Base de données : {self.principal.chemin_base}\n"
                                    "Copiez ce fichier pour sauvegarder la trésorerie.")

    def _apres_modification(self, message: str):
        self.principal.recharger()
        self.principal.message(message)

    # --- Association et exercice ---
    def enregistrer_association(self):
        v = self.vue
        v.champ_nom_association.effacer_erreur()
        v.champ_fin.effacer_erreur()
        nom = v.nom_association_input.text().strip()
        debut, fin = v.debut_input.date().toPyDate(), v.fin_input.date().toPyDate()
        valide = True
        if not nom:
            v.champ_nom_association.afficher_erreur("Indiquez le nom de l'association : il figure sur le bilan.")
            valide = False
        if fin <= debut:
            v.champ_fin.afficher_erreur("La fin de l'exercice doit être après son début.")
            valide = False
        elif (fin - debut).days > DUREE_MAX_EXERCICE:
            v.champ_fin.afficher_erreur("Un exercice dure au plus deux ans.")
            valide = False
        if not valide:
            return
        self.queries.set_parametre("nom_association", nom)
        self.queries.set_parametre("exercice_debut", debut.isoformat())
        self.queries.set_parametre("exercice_fin", fin.isoformat())
        self._apres_modification(f"Exercice enregistré : du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}.")

    def ouvrir_dossier(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.principal.chemin_base)))

    def importer_base(self):
        source, _ = QFileDialog.getOpenFileName(self.vue, "Importer une base OdinFinance", "",
                                                "Base OdinFinance (*.db);;Tous les fichiers (*)")
        if not source or not confirmer(
                self.vue, "Importer une base",
                f"Remplacer les données actuelles par celles de « {os.path.basename(source)} » ?\n"
                "Les données actuelles sont d'abord sauvegardées dans le dossier de la base.", "Importer"):
            return
        try:
            sauvegarde = self.queries.db.importer(source)
        except ErreurMetier as e:
            signaler_erreur(self.vue, "Import impossible", str(e))
            return
        self._apres_modification(f"Base importée. Les données précédentes sont sauvegardées : {sauvegarde}")

    # --- Comptes ---
    def _compte(self):
        identifiant = self.vue.id_selectionne(self.vue.table_comptes)
        return next((c for c in self.donnees.comptes if c.id == identifiant), None)

    def ajouter_compte(self):
        if editer_avec_dialogue(DialogueCompte(self.vue), self.queries.ajouter_compte):
            self._apres_modification("Compte ajouté.")

    def modifier_compte(self):
        compte = self._compte()
        if compte and editer_avec_dialogue(DialogueCompte(self.vue, compte),
                                           lambda *valeurs: self.queries.modifier_compte(compte.id, *valeurs)):
            self._apres_modification("Compte mis à jour.")

    def supprimer_compte(self):
        compte = self._compte()
        if compte and confirmer(self.vue, "Supprimer le compte", f"Supprimer le compte « {compte.nom} » ?", "Supprimer"):
            self._supprimer(lambda: self.queries.supprimer_compte(compte.id), f"Compte « {compte.nom} » supprimé.")

    # --- Catégories ---
    def _categorie(self):
        identifiant = self.vue.id_selectionne(self.vue.arbre_categories)
        return next((c for c in self.donnees.categories if c.id == identifiant), None)

    def ajouter_categorie(self):
        selection = self._categorie()
        dialogue = DialogueCategorie(self.vue, self.donnees.categories,
                                     type_flux=selection.type_flux if selection else None)
        if editer_avec_dialogue(dialogue, self.queries.ajouter_categorie):
            self._apres_modification("Catégorie ajoutée.")

    def modifier_categorie(self):
        categorie = self._categorie()
        if categorie and editer_avec_dialogue(
                DialogueCategorie(self.vue, self.donnees.categories, categorie),
                lambda *valeurs: self.queries.modifier_categorie(categorie.id, *valeurs)):
            self._apres_modification("Catégorie mise à jour.")

    def supprimer_categorie(self):
        categorie = self._categorie()
        if categorie and confirmer(self.vue, "Supprimer la catégorie",
                                   f"Supprimer la catégorie « {categorie.nom} » ?", "Supprimer"):
            self._supprimer(lambda: self.queries.supprimer_categorie(categorie.id),
                            f"Catégorie « {categorie.nom} » supprimée.")

    # --- Tiers ---
    def _tier(self):
        identifiant = self.vue.id_selectionne(self.vue.table_tiers)
        return next((t for t in self.donnees.tiers if t.id == identifiant), None)

    def ajouter_tier(self):
        if editer_avec_dialogue(DialogueTiers(self.vue), self.queries.ajouter_tier):
            self._apres_modification("Tiers ajouté.")

    def modifier_tier(self):
        tier = self._tier()
        if tier and editer_avec_dialogue(DialogueTiers(self.vue, tier),
                                         lambda *valeurs: self.queries.modifier_tier(tier.id, *valeurs)):
            self._apres_modification("Tiers mis à jour.")

    def supprimer_tier(self):
        tier = self._tier()
        if not tier:
            return
        utilisations = self.queries.compter_operations_tier(tier.id)
        question = f"Supprimer le tiers « {tier.nom} » ?"
        if utilisations:
            question += f"\n{utilisations} opération(s) le mentionnent : elles seront conservées, sans tiers."
        if confirmer(self.vue, "Supprimer le tiers", question, "Supprimer"):
            self._supprimer(lambda: self.queries.supprimer_tier(tier.id), f"Tiers « {tier.nom} » supprimé.")

    def _supprimer(self, action, message: str):
        try:
            action()
        except ErreurMetier as e:
            signaler_erreur(self.vue, "Suppression impossible", str(e))
            return
        self._apres_modification(message)
