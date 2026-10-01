from views.main_window import MainWindow
from database.queries import TresoQueries
from PyQt6.QtWidgets import QTableWidgetItem

class MainController:
    def __init__(self, view: MainWindow, queries: TresoQueries):
        self.view = view
        self.queries = queries

        # Chargement initial des données dans l'interface
        self.charger_combobox()
        self.charger_tableau_transactions()

        # Connexion des signaux (clics de boutons)
        self.view.btn_ajouter.clicked.connect(self.ajouter_transaction)
        self.view.btn_add_cat.clicked.connect(self.ouvrir_ajout_categorie)
        self.view.btn_add_tier.clicked.connect(self.ouvrir_ajout_tier)

    def charger_combobox(self):
        """Remplit les menus déroulants (Catégories et Tiers) depuis la BDD."""
        # Catégories
        self.view.cat_combo.clear()
        self.categories_data = self.queries.get_toutes_categories()
        for cat_id, nom, type_flux in self.categories_data:
            self.view.cat_combo.addItem(f"[{type_flux}] {nom}", cat_id)

        # Tiers
        self.view.tier_combo.clear()
        self.view.tier_combo.addItem("-- Aucun --", None)
        self.tiers_data = self.queries.get_tous_tiers()
        for tier_id, nom, type_tier in self.tiers_data:
            self.view.tier_combo.addItem(f"{nom} ({type_tier})", tier_id)

    def charger_tableau_transactions(self):
        """Charge l'historique des transactions dans le tableau de droite."""
        transactions = self.queries.get_toutes_transactions()
        self.view.table_transactions.setRowCount(len(transactions))

        for row_idx, trans in enumerate(transactions):
            date_str = trans[1]
            desc = trans[2]
            montant = f"{trans[3]:.2f} €"
            ref = trans[4] if trans[4] else "-"
            cat = f"{trans[5]} ({trans[6]})"
            tier = trans[7] if trans[7] else "-"

            values = [date_str, desc, montant, cat, tier, ref]
            for col_idx, val in enumerate(values):
                self.view.table_transactions.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def ajouter_transaction(self):
        """Récupère les données du formulaire et les insère en BDD."""
        date_str = self.view.date_input.date().toString("yyyy-MM-dd")
        description = self.view.desc_input.text().strip()
        montant_str = self.view.amount_input.text().strip().replace(",", ".")
        ref_facture = self.view.ref_input.text().strip()
        
        categorie_id = self.view.cat_combo.currentData()
        tier_id = self.view.tier_combo.currentData()

        if not description:
            self.view.afficher_message("Erreur", "Veuillez saisir une description.", is_erreur=True)
            return

        try:
            montant = float(montant_str)
            if montant < 0:
                raise ValueError()
        except ValueError:
            self.view.afficher_message("Erreur", "Le montant doit être un nombre positif valide.", is_erreur=True)
            return

        try:
            self.queries.ajouter_transaction(
                date=date_str,
                description=description,
                montant=montant,
                ref_facture=ref_facture if ref_facture else None,
                categorie_id=categorie_id,
                tier_id=tier_id
            )

            self.view.desc_input.clear()
            self.view.amount_input.clear()
            self.view.ref_input.clear()
            self.charger_tableau_transactions()

            self.view.afficher_message("Succès", "Transaction enregistrée avec succès !")
        except Exception as e:
            self.view.afficher_message("Erreur BDD", f"Erreur lors de l'enregistrement : {str(e)}", is_erreur=True)

    def ouvrir_ajout_categorie(self):
        nom, type_flux = self.view.demander_texte_et_type("Ajouter une catégorie", ["RECETTE", "DEPENSE"])
        if nom:
            try:
                self.queries.ajouter_categorie(nom, type_flux)
                self.charger_combobox()
                self.view.afficher_message("Succès", f"Catégorie '{nom}' ajoutée !")
            except Exception as e:
                self.view.afficher_message("Erreur", f"Impossible d'ajouter la catégorie : {str(e)}", is_erreur=True)

    def ouvrir_ajout_tier(self):
        nom, type_tier = self.view.demander_texte_et_type("Ajouter un tier", ["MORAL", "PHYSIQUE"])
        if nom:
            try:
                self.queries.ajouter_tier(nom, type_tier)
                self.charger_combobox()
                self.view.afficher_message("Succès", f"Tier '{nom}' ajouté !")
            except Exception as e:
                self.view.afficher_message("Erreur", f"Impossible d'ajouter le tier : {str(e)}", is_erreur=True)