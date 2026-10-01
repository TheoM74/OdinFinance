from views.main_window import MainWindow
from database.queries import TresoQueries
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import QDate

class MainController:
    def __init__(self, view: MainWindow, queries: TresoQueries):
        self.view = view
        self.queries = queries
        self.transaction_en_cours_id = None

        self.charger_combobox()
        self.charger_donnees_completes()

        # Signaux
        self.view.btn_ajouter.clicked.connect(self.enregistrer_transaction)
        self.view.btn_annuler_edition.clicked.connect(self.reinitialiser_formulaire)
        self.view.btn_add_cat.clicked.connect(self.ouvrir_ajout_categorie)
        self.view.btn_del_cat.clicked.connect(self.supprimer_categorie)
        self.view.btn_add_tier.clicked.connect(self.ouvrir_ajout_tier)
        self.view.btn_del_tier.clicked.connect(self.supprimer_tier)
        self.view.btn_supprimer_trans.clicked.connect(self.supprimer_transaction_selectionnee)
        self.view.table_transactions.cellClicked.connect(self.charger_transaction_dans_formulaire)
        self.view.btn_export_excel.clicked.connect(self.exporter_compte_resultat_excel)

    def charger_combobox(self):
        self.view.cat_combo.clear()
        self.categories_data = self.queries.get_toutes_categories()
        for cat_id, nom, type_flux in self.categories_data:
            self.view.cat_combo.addItem(f"{nom} ({type_flux})", cat_id)

        self.view.tier_combo.clear()
        self.view.tier_combo.addItem("-- Non spécifié --", None)
        self.tiers_data = self.queries.get_tous_tiers()
        for tier_id, nom, type_tier in self.tiers_data:
            self.view.tier_combo.addItem(f"{nom}", tier_id)

    def charger_donnees_completes(self):
        self.charger_tableau_transactions()
        self.charger_tableau_bilan()

    def charger_tableau_transactions(self):
        transactions = self.queries.get_toutes_transactions()
        self.view.table_transactions.setRowCount(len(transactions))
        self.transactions_cache = transactions

        for row_idx, trans in enumerate(transactions):
            date_str = trans[1]
            desc = trans[2]
            montant = f"{trans[3]:.2f} €"
            cat = f"{trans[5]}"
            tier = trans[7] if trans[7] else "-"
            ref = trans[4] if trans[4] else "-"

            for col_idx, val in enumerate([date_str, desc, montant, cat, tier, ref]):
                self.view.table_transactions.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def charger_tableau_bilan(self):
        totaux = self.queries.get_totaux_par_categorie()
        self.view.table_bilan.setRowCount(len(totaux))

        total_recettes = 0.0
        total_depenses = 0.0

        for row_idx, (nom_cat, type_flux, somme) in enumerate(totaux):
            if type_flux == "RECETTE": total_recettes += somme
            else: total_depenses += somme

            self.view.table_bilan.setItem(row_idx, 0, QTableWidgetItem(nom_cat))
            self.view.table_bilan.setItem(row_idx, 1, QTableWidgetItem("Produit" if type_flux == "RECETTE" else "Charge"))
            self.view.table_bilan.setItem(row_idx, 2, QTableWidgetItem(f"{somme:.2f} €"))

        solde_net = total_recettes - total_depenses
        self.view.label_solde.setText(
            f"📈 Total Produits : {total_recettes:.2f} €   |   "
            f"📉 Total Charges : {total_depenses:.2f} €   ||   "
            f"💰 Résultat : {solde_net:.2f} €"
        )

    def charger_transaction_dans_formulaire(self, row, col):
        if row >= len(self.transactions_cache): return
        trans = self.transactions_cache[row]
        self.transaction_en_cours_id = trans[0]
        self._reset_erreurs_ui()

        date_parts = list(map(int, trans[1].split("-")))
        self.view.date_input.setDate(QDate(date_parts[0], date_parts[1], date_parts[2]))
        self.view.desc_input.setText(trans[2])
        self.view.amount_input.setText(str(trans[3]))
        self.view.ref_input.setText(trans[4] if trans[4] else "")

        idx_cat = self.view.cat_combo.findData(trans[8])
        if idx_cat >= 0: self.view.cat_combo.setCurrentIndex(idx_cat)

        idx_tier = self.view.tier_combo.findData(trans[9]) if trans[9] else 0
        if idx_tier >= 0: self.view.tier_combo.setCurrentIndex(idx_tier)

        self.view.form_group.setTitle("Modifier l'opération sélectionnée")
        self.view.btn_ajouter.setText("Mettre à jour")
        self.view.btn_ajouter.setStyleSheet("background-color: #f59e0b; color: white;")
        self.view.btn_annuler_edition.setVisible(True)

    def reinitialiser_formulaire(self):
        self.transaction_en_cours_id = None
        self._reset_erreurs_ui()
        self.view.date_input.setDate(QDate.currentDate())
        self.view.desc_input.clear()
        self.view.amount_input.clear()
        self.view.ref_input.clear()
        self.view.tier_combo.setCurrentIndex(0)
        
        self.view.form_group.setTitle("Enregistrer un flux financier")
        self.view.btn_ajouter.setText("Enregistrer")
        self.view.btn_ajouter.setStyleSheet("")
        self.view.btn_annuler_edition.setVisible(False)

    def _reset_erreurs_ui(self):
        """Efface les messages d'erreur et remet les bordures normales."""
        self.view.err_desc.setVisible(False)
        self.view.desc_input.setStyleSheet("")
        self.view.err_amount.setVisible(False)
        self.view.amount_input.setStyleSheet("")

    def _afficher_erreur_inline(self, champ_input, label_erreur, message):
        """Applique le style rouge d'erreur directement sur le widget."""
        label_erreur.setText(message)
        label_erreur.setVisible(True)
        champ_input.setStyleSheet("border: 2px solid #ef4444; background-color: #fef2f2;")

    def enregistrer_transaction(self):
        self._reset_erreurs_ui()
        has_error = False

        date_str = self.view.date_input.date().toString("yyyy-MM-dd")
        description = self.view.desc_input.text().strip()
        montant_str = self.view.amount_input.text().strip().replace(",", ".")
        ref_facture = self.view.ref_input.text().strip()
        
        categorie_id = self.view.cat_combo.currentData()
        tier_id = self.view.tier_combo.currentData()

        # Validation Libellé
        if not description:
            self._afficher_erreur_inline(
                self.view.desc_input, 
                self.view.err_desc, 
                "Le libellé de l'opération est obligatoire."
            )
            has_error = True

        # Validation Montant (Doit être un nombre positif strict)
        montant = 0.0
        if not montant_str:
            self._afficher_erreur_inline(
                self.view.amount_input, 
                self.view.err_amount, 
                "Le montant est obligatoire."
            )
            has_error = True
        else:
            try:
                montant = float(montant_str)
                if montant <= 0:
                    raise ValueError("Le montant doit être supérieur à zéro.")
            except ValueError:
                self._afficher_erreur_inline(
                    self.view.amount_input, 
                    self.view.err_amount, 
                    "Format invalide : veuillez saisir un nombre positif (ex: 45.00)."
                )
                has_error = True

        if has_error:
            return # Stoppe l'enregistrement, l'utilisateur voit directement l'erreur en rouge

        try:
            if self.transaction_en_cours_id is None:
                self.queries.ajouter_transaction(
                    date_str, description, montant,
                    ref_facture if ref_facture else None, categorie_id, tier_id
                )
            else:
                self.queries.modifier_transaction(
                    self.transaction_en_cours_id, date_str, description, montant,
                    ref_facture if ref_facture else None, categorie_id, tier_id
                )
            self.reinitialiser_formulaire()
            self.charger_donnees_completes()
        except Exception as e:
            QMessageBox.critical(self.view, "Erreur Base de Données", str(e))

    def supprimer_transaction_selectionnee(self):
        selected_rows = self.view.table_transactions.selectionModel().selectedRows()
        if not selected_rows: return

        row = selected_rows[0].row()
        trans = self.transactions_cache[row]
        
        confirm = QMessageBox.question(self.view, "Suppression", 
            f"Confirmez-vous la suppression du flux : {trans[2]} ({trans[3]}€) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            self.queries.supprimer_transaction(trans[0])
            self.charger_donnees_completes()
            self.reinitialiser_formulaire()

    def ouvrir_ajout_categorie(self):
        nom, type_flux = self.view.demander_texte_et_type("Nouvelle Catégorie", ["RECETTE", "DEPENSE"])
        if nom:
            self.queries.ajouter_categorie(nom, type_flux)
            self.charger_combobox()

    def supprimer_categorie(self):
        cat_id = self.view.cat_combo.currentData()
        if not cat_id: return
        if QMessageBox.question(self.view, "Suppression", "Supprimer cette catégorie ? (Impossible si utilisée)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                self.queries.supprimer_categorie(cat_id)
                self.charger_combobox()
            except:
                QMessageBox.warning(self.view, "Erreur", "Cette catégorie est liée à des transactions.")

    def ouvrir_ajout_tier(self):
        nom, type_tier = self.view.demander_texte_et_type("Nouveau Tier", ["MORAL", "PHYSIQUE"])
        if nom:
            self.queries.ajouter_tier(nom, type_tier)
            self.charger_combobox()

    def supprimer_tier(self):
        tier_id = self.view.tier_combo.currentData()
        if not tier_id: return
        if QMessageBox.question(self.view, "Suppression", "Supprimer ce tier ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                self.queries.supprimer_tier(tier_id)
                self.charger_combobox()
            except:
                QMessageBox.warning(self.view, "Erreur", "Ce tier est lié à des transactions.")

    def exporter_compte_resultat_excel(self):
        from PyQt6.QtWidgets import QFileDialog
        from importlib import import_module
        from datetime import datetime

        try:
            openpyxl = import_module("openpyxl")
            styles = import_module("openpyxl.styles")
            Font = styles.Font
            PatternFill = styles.PatternFill
            Alignment = styles.Alignment
            Border = styles.Border
            Side = styles.Side
        except ImportError:
            QMessageBox.warning(
                self.view,
                "Erreur",
                "L'export Excel nécessite l'installation du module openpyxl."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Enregistrer Compte de Résultat", 
            f"Compte_Resultat_ODIN_{datetime.now().year}.xlsx", 
            "Fichiers Excel (*.xlsx)"
        )
        if not file_path: return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Compte de Résultat"
            ws.views.sheetView[0].showGridLines = False

            f_titre = Font(name="Calibri", size=16, bold=True, color="1e293b")
            f_head_charge = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
            f_head_prod = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
            
            fill_charge = PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid")
            fill_prod = PatternFill(start_color="10b981", end_color="10b981", fill_type="solid")
            
            align_c = Alignment(horizontal="center", vertical="center")
            
            bordure_legere = Border(
                left=Side(style='thin', color='d1d5db'), right=Side(style='thin', color='d1d5db'),
                top=Side(style='thin', color='d1d5db'), bottom=Side(style='thin', color='d1d5db')
            )
            bordure_totaux = Border(top=Side(style='double', color='000000'), bottom=Side(style='double', color='000000'))

            ws.merge_cells('A1:E1')
            ws['A1'] = "COMPTE DE RÉSULTAT - ASSOCIATION ODIN"
            ws['A1'].font = f_titre
            ws['A1'].alignment = align_c
            ws['A2'] = f"Exercice clos / Généré le : {datetime.now().strftime('%d/%m/%Y')}"
            ws['A2'].alignment = align_c
            ws.merge_cells('A2:E2')
            ws.append([])

            ws.append(["CHARGES (Dépenses / Emplois)", "Montant (€)", "", "PRODUITS (Recettes / Ressources)", "Montant (€)"])
            
            for col, fill in zip([1, 2], [fill_charge, fill_charge]):
                ws.cell(row=4, column=col).font = f_head_charge
                ws.cell(row=4, column=col).fill = fill
                ws.cell(row=4, column=col).alignment = align_c
                
            for col, fill in zip([4, 5], [fill_prod, fill_prod]):
                ws.cell(row=4, column=col).font = f_head_prod
                ws.cell(row=4, column=col).fill = fill
                ws.cell(row=4, column=col).alignment = align_c

            ws.column_dimensions['C'].width = 3

            totaux = self.queries.get_totaux_par_categorie()
            charges = [(nom, somme) for nom, type_flux, somme in totaux if type_flux == "DEPENSE"]
            produits = [(nom, somme) for nom, type_flux, somme in totaux if type_flux == "RECETTE"]
            
            total_charges = sum(s for n, s in charges)
            total_produits = sum(s for n, s in produits)
            resultat = total_produits - total_charges

            max_lignes = max(len(charges), len(produits))
            current_row = 5

            for i in range(max_lignes):
                charge_nom = charges[i][0] if i < len(charges) else ""
                charge_montant = charges[i][1] if i < len(charges) else ""
                prod_nom = produits[i][0] if i < len(produits) else ""
                prod_montant = produits[i][1] if i < len(produits) else ""

                ws.append([charge_nom, charge_montant, "", prod_nom, prod_montant])
                
                for c in [1, 2, 4, 5]:
                    ws.cell(row=current_row, column=c).border = bordure_legere
                if charge_montant != "": ws.cell(row=current_row, column=2).number_format = '#,##0.00 "€"'
                if prod_montant != "": ws.cell(row=current_row, column=5).number_format = '#,##0.00 "€"'
                
                current_row += 1

            if resultat > 0:
                ws.append(["RÉSULTAT (Excédent)", resultat, "", "", ""])
            elif resultat < 0:
                ws.append(["", "", "", "RÉSULTAT (Déficit)", abs(resultat)])
            else:
                ws.append(["RÉSULTAT (Équilibre)", 0, "", "", ""])

            for c in [1, 2, 4, 5]: ws.cell(row=current_row, column=c).border = bordure_legere
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=4).font = Font(bold=True)
            if resultat > 0: ws.cell(row=current_row, column=2).number_format = '#,##0.00 "€"'
            if resultat < 0: ws.cell(row=current_row, column=5).number_format = '#,##0.00 "€"'
            current_row += 1

            total_general = max(total_charges, total_produits)
            ws.append(["TOTAL GÉNÉRAL", total_general, "", "TOTAL GÉNÉRAL", total_general])
            
            for c in [1, 2, 4, 5]:
                cell = ws.cell(row=current_row, column=c)
                cell.font = Font(bold=True)
                cell.border = bordure_totaux
                if c in [2, 5]: cell.number_format = '#,##0.00 "€"'

            ws.column_dimensions['A'].width = 35
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['D'].width = 35
            ws.column_dimensions['E'].width = 15

            wb.save(file_path)
            QMessageBox.information(self.view, "Succès", "Le Compte de Résultat officiel a été généré avec succès.")

        except Exception as e:
            QMessageBox.critical(self.view, "Erreur Excel", str(e))