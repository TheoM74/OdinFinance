from PyQt6.QtCore import QDate

from controllers.commun import editer_avec_dialogue, options_categories, remplir_combo
from database.modeles import DEPENSE, RECETTE, VIREMENT, Operation
from services.montants import formater_montant, formater_saisie, parser_montant
from views.dialogues import DialogueCategorie, DialogueTiers, confirmer


class JournalController:
    def __init__(self, principal):
        self.principal = principal
        self.queries = principal.queries
        self.vue = v = principal.view.page_journal
        self.donnees = None
        self.operation_en_cours: Operation | None = None

        v.btn_enregistrer.clicked.connect(self.enregistrer)
        for champ in (v.libelle_input, v.montant_input, v.reference_input):
            champ.returnPressed.connect(self.enregistrer)
        v.btn_annuler.clicked.connect(self.reinitialiser_formulaire)
        v.raccourci_echap.activated.connect(self.reinitialiser_formulaire)
        v.type_operation.change.connect(self._remplir_categories)
        v.btn_ajout_categorie.clicked.connect(self.ajouter_categorie)
        v.btn_ajout_tier.clicked.connect(self.ajouter_tier)

        v.table.doubleClicked.connect(self.modifier_selection)
        v.btn_modifier.clicked.connect(self.modifier_selection)
        v.raccourci_modifier.activated.connect(self.modifier_selection)
        v.btn_supprimer.clicked.connect(self.supprimer_selection)
        v.raccourci_suppr.activated.connect(self.supprimer_selection)
        v.table.selectionModel().selectionChanged.connect(self._etat_boutons)
        v.recherche_input.textChanged.connect(self._filtrer)
        v.filtre_compte.currentIndexChanged.connect(self._filtrer)

        self.reinitialiser_formulaire()

    # --- Affichage ---
    def rafraichir(self, donnees):
        self.donnees = d = donnees
        v = self.vue
        comptes = [(c.libelle, c.id) for c in d.comptes]
        remplir_combo(v.compte_combo, comptes)
        remplir_combo(v.destination_combo, comptes)
        if v.destination_combo.currentData() == v.compte_combo.currentData() and v.destination_combo.count() > 1:
            v.destination_combo.setCurrentIndex(1)
        remplir_combo(v.tier_combo, [(t.nom, t.id) for t in d.tiers], "Aucun")
        remplir_combo(v.filtre_compte, [(c.nom, c.id) for c in d.comptes], "Tous les comptes")
        self._remplir_categories(v.type_operation.valeur())
        v.afficher_operations(d.operations)
        self._filtrer()
        if self.operation_en_cours and all(op.id != self.operation_en_cours.id for op in d.operations):
            self.reinitialiser_formulaire()

    def _remplir_categories(self, type_operation: str):
        if self.donnees and type_operation != VIREMENT:
            remplir_combo(self.vue.cat_combo, options_categories(self.donnees.categories, type_operation))

    def _filtrer(self):
        v = self.vue
        v.filtre.setFilterFixedString(v.recherche_input.text().strip())
        v.filtre.filtrer_compte(v.filtre_compte.currentData())
        total, visibles = v.modele.rowCount(), v.filtre.rowCount()
        if total == 0:
            v.etat_vide.setText("Aucune opération pour l'instant.\n"
                                "Saisissez la première avec le formulaire : elle apparaîtra ici.")
        elif visibles == 0:
            v.etat_vide.setText("Aucune opération ne correspond à cette recherche.")
        v.pile_liste.setCurrentWidget(v.table if visibles else v.etat_vide)
        v.label_compteur.setText(f"{visibles} opération{'s' if visibles > 1 else ''}" if visibles == total
                                 else f"{visibles} sur {total}")
        self._etat_boutons()

    def _etat_boutons(self):
        selection = self.vue.id_selectionne() is not None and self.vue.pile_liste.currentWidget() is self.vue.table
        self.vue.btn_modifier.setEnabled(selection)
        self.vue.btn_supprimer.setEnabled(selection)

    # --- Formulaire ---
    def reinitialiser_formulaire(self, garder_contexte: bool = False):
        """Vide le formulaire. garder_contexte conserve type, date et compte pour enchaîner les saisies."""
        v = self.vue
        self.operation_en_cours = None
        for champ in (v.champ_libelle, v.champ_montant, v.champ_compte, v.champ_destination, v.champ_categorie):
            champ.effacer_erreur()
        v.libelle_input.clear()
        v.montant_input.clear()
        v.reference_input.clear()
        v.tier_combo.setCurrentIndex(0)
        if not garder_contexte:
            v.date_input.setDate(QDate.currentDate())
            v.type_operation.choisir(DEPENSE)
        v.titre_formulaire.setText("Nouvelle opération")
        v.btn_enregistrer.setText("Enregistrer")
        v.btn_annuler.setVisible(False)

    def _charger(self, op: Operation):
        v = self.vue
        self.reinitialiser_formulaire()
        self.operation_en_cours = op
        v.type_operation.choisir(op.type_operation)
        v.date_input.setDate(QDate(op.date.year, op.date.month, op.date.day))
        v.compte_combo.setCurrentIndex(max(0, v.compte_combo.findData(op.compte_id)))
        if op.est_virement:
            v.destination_combo.setCurrentIndex(max(0, v.destination_combo.findData(op.compte_destination_id)))
        else:
            v.cat_combo.setCurrentIndex(max(0, v.cat_combo.findData(op.categorie_id)))
            v.tier_combo.setCurrentIndex(max(0, v.tier_combo.findData(op.tier_id)))
            v.reference_input.setText(op.reference or "")
        v.libelle_input.setText(op.libelle)
        v.montant_input.setText(formater_saisie(op.montant))
        v.titre_formulaire.setText("Modifier l'opération")
        v.btn_enregistrer.setText("Mettre à jour")
        v.btn_annuler.setVisible(True)
        v.libelle_input.setFocus()

    def enregistrer(self):
        v = self.vue
        for champ in (v.champ_libelle, v.champ_montant, v.champ_compte, v.champ_destination, v.champ_categorie):
            champ.effacer_erreur()
        type_operation = v.type_operation.valeur()
        virement = type_operation == VIREMENT
        libelle = v.libelle_input.text().strip()
        compte_id = v.compte_combo.currentData()
        destination_id = v.destination_combo.currentData() if virement else None
        categorie_id = None if virement else v.cat_combo.currentData()

        erreurs = []
        if compte_id is None:
            erreurs.append((v.champ_compte, "Créez d'abord un compte dans Paramètres."))
        if virement and destination_id is None:
            erreurs.append((v.champ_destination, "Choisissez le compte qui reçoit le virement."))
        elif virement and destination_id == compte_id:
            erreurs.append((v.champ_destination, "Choisissez un compte différent du compte de départ."))
        if not virement and categorie_id is None:
            erreurs.append((v.champ_categorie, "Créez une catégorie avec le bouton + pour classer l'opération."))
        if not libelle:
            erreurs.append((v.champ_libelle, "Décrivez l'opération, par exemple « Achat Métro »."))
        try:
            montant = parser_montant(v.montant_input.text())
        except ValueError as e:
            erreurs.append((v.champ_montant, str(e)))
        if erreurs:
            for champ, message in erreurs:
                champ.afficher_erreur(message)
            erreurs[0][0].champ.setFocus()
            return

        jour = v.date_input.date().toPyDate()
        modification = self.operation_en_cours is not None
        operation_id = self.queries.enregistrer_operation(
            self.operation_en_cours.id if modification else None, jour, libelle, montant,
            None if virement else (v.reference_input.text().strip() or None),
            compte_id, categorie_id, destination_id, None if virement else v.tier_combo.currentData(),
        )
        message = f"« {libelle} » ({formater_montant(montant)}) {'mise à jour' if modification else 'enregistrée'}."
        if not self.donnees.exercice.contient(jour):
            message += " Attention : sa date est hors de l'exercice en cours, elle n'apparaît pas dans la synthèse."
        self.reinitialiser_formulaire(garder_contexte=True)
        self.principal.recharger()
        self.principal.message(message)
        v.selectionner(operation_id)
        v.libelle_input.setFocus()

    # --- Liste ---
    def _operation_selectionnee(self) -> Operation | None:
        operation_id = self.vue.id_selectionne()
        return next((op for op in self.donnees.operations if op.id == operation_id), None)

    def modifier_selection(self, *_):
        op = self._operation_selectionnee()
        if op:
            self._charger(op)

    def supprimer_selection(self):
        op = self._operation_selectionnee()
        if not op:
            return
        question = (f"Supprimer « {op.libelle} » du {op.date:%d/%m/%Y} ({formater_montant(op.montant)}) ?\n"
                    "Cette suppression est définitive.")
        if not confirmer(self.vue, "Supprimer l'opération", question, "Supprimer"):
            return
        self.queries.supprimer_operation(op.id)
        if self.operation_en_cours and self.operation_en_cours.id == op.id:
            self.reinitialiser_formulaire()
        self.principal.recharger()
        self.principal.message(f"« {op.libelle} » supprimée.")

    # --- Ajouts rapides depuis le formulaire ---
    def ajouter_categorie(self):
        type_operation = self.vue.type_operation.valeur()
        dialogue = DialogueCategorie(self.vue, self.donnees.categories,
                                     type_flux=type_operation if type_operation in (RECETTE, DEPENSE) else None)
        nouvel_id = editer_avec_dialogue(dialogue, self.queries.ajouter_categorie)
        if nouvel_id:
            self.principal.recharger()
            self.vue.cat_combo.setCurrentIndex(max(0, self.vue.cat_combo.findData(nouvel_id)))

    def ajouter_tier(self):
        nouvel_id = editer_avec_dialogue(DialogueTiers(self.vue), self.queries.ajouter_tier)
        if nouvel_id:
            self.principal.recharger()
            self.vue.tier_combo.setCurrentIndex(max(0, self.vue.tier_combo.findData(nouvel_id)))
