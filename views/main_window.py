from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QFormLayout, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox, QTabWidget, QHeaderView
)
from PyQt6.QtCore import QDate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OdinFinance - Gestion de Trésorerie")
        self.resize(1100, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- ONGLET 1 : TRANSACTIONS & SAISIE ---
        self.tab_transactions = QWidget()
        self.init_tab_transactions()
        self.tabs.addTab(self.tab_transactions, "📋 Gestion des Transactions")

        # --- ONGLET 2 : BILAN & SYNTHÈSE ---
        self.tab_bilan = QWidget()
        self.init_tab_bilan()
        self.tabs.addTab(self.tab_bilan, "📈 Bilan & Synthèse AG")

    def init_tab_transactions(self):
        layout_principal = QHBoxLayout(self.tab_transactions)

        # 1. Formulaire d'ajout / modification (Côté gauche)
        self.form_group = QGroupBox("Ajouter une transaction")
        form_layout = QFormLayout(self.form_group)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ex: Achat boissons")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Réf. optionnelle")

        # Layout Catégorie [+ / -]
        cat_layout = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.btn_add_cat = QPushButton("+")
        self.btn_add_cat.setFixedWidth(25)
        self.btn_del_cat = QPushButton("-")
        self.btn_del_cat.setFixedWidth(25)
        self.btn_del_cat.setStyleSheet("color: red; font-weight: bold;")
        cat_layout.addWidget(self.cat_combo)
        cat_layout.addWidget(self.btn_add_cat)
        cat_layout.addWidget(self.btn_del_cat)

        # Layout Tier [+ / -]
        tier_layout = QHBoxLayout()
        self.tier_combo = QComboBox()
        self.btn_add_tier = QPushButton("+")
        self.btn_add_tier.setFixedWidth(25)
        self.btn_del_tier = QPushButton("-")
        self.btn_del_tier.setFixedWidth(25)
        self.btn_del_tier.setStyleSheet("color: red; font-weight: bold;")
        tier_layout.addWidget(self.tier_combo)
        tier_layout.addWidget(self.btn_add_tier)
        tier_layout.addWidget(self.btn_del_tier)

        # Boutons d'action du formulaire
        self.btn_ajouter = QPushButton("Enregistrer la transaction")
        self.btn_ajouter.setStyleSheet("background-color: #2b5b84; color: white; font-weight: bold; padding: 6px;")

        self.btn_annuler_edition = QPushButton("Annuler la modification")
        self.btn_annuler_edition.setVisible(False) # Caché par défaut
        self.btn_annuler_edition.setStyleSheet("background-color: #6c757d; color: white; padding: 4px;")

        form_layout.addRow("Date :", self.date_input)
        form_layout.addRow("Description :", self.desc_input)
        form_layout.addRow("Montant (€) :", self.amount_input)
        form_layout.addRow("Réf. Facture :", self.ref_input)
        form_layout.addRow("Catégorie :", cat_layout)
        form_layout.addRow("Tier :", tier_layout)
        form_layout.addRow(self.btn_ajouter)
        form_layout.addRow(self.btn_annuler_edition)

        self.form_group.setFixedWidth(400)
        layout_principal.addWidget(self.form_group)

        # 2. Tableau des transactions (Côté droit)
        right_layout = QVBoxLayout()
        
        self.table_transactions = QTableWidget()
        self.table_transactions.setColumnCount(6)
        self.table_transactions.setHorizontalHeaderLabels([
            "Date", "Description", "Montant", "Catégorie", "Tier", "Facture"
        ])
        self.table_transactions.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_transactions.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_transactions.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.table_transactions)

        # Bouton Supprimer en bas du tableau
        actions_table_layout = QHBoxLayout()
        self.btn_supprimer_trans = QPushButton("🗑️ Supprimer la transaction sélectionnée")
        self.btn_supprimer_trans.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 6px;")
        actions_table_layout.addWidget(self.btn_supprimer_trans)
        
        right_layout.addLayout(actions_table_layout)
        layout_principal.addLayout(right_layout)

    def init_tab_bilan(self):
        layout = QVBoxLayout(self.tab_bilan)

        header_layout = QHBoxLayout()
        title = QLabel("Bilan Financier Synthétique (Présentation AG)")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.btn_export_excel = QPushButton("📥 Exporter le Bilan AG (Excel)")
        self.btn_export_excel.setStyleSheet("background-color: #2b8450; color: white; font-weight: bold; padding: 6px;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_export_excel)
        layout.addLayout(header_layout)

        self.table_bilan = QTableWidget()
        self.table_bilan.setColumnCount(3)
        self.table_bilan.setHorizontalHeaderLabels(["Catégorie", "Type de Flux", "Total Cumulé (€)"])
        self.table_bilan.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_bilan)

        self.label_solde = QLabel("Solde Actuel de la Trésorerie : -- €")
        self.label_solde.setStyleSheet("font-size: 14px; font-weight: bold; color: #2b5b84; margin-top: 10px;")
        layout.addWidget(self.label_solde)

    def afficher_message(self, titre: str, message: str, is_erreur: bool = False):
        msg = QMessageBox(self)
        msg.setWindowTitle(titre)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning if is_erreur else QMessageBox.Icon.Information)
        msg.exec()

    def demander_texte_et_type(self, titre: str, options_type: list[str]):
        dialog = QDialog(self)
        dialog.setWindowTitle(titre)
        dialog.resize(300, 150)
        
        layout = QVBoxLayout(dialog)
        input_nom = QLineEdit()
        input_nom.setPlaceholderText("Nom...")
        layout.addWidget(input_nom)
        
        combo_type = QComboBox()
        combo_type.addItems(options_type)
        layout.addWidget(combo_type)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return input_nom.text().strip(), combo_type.currentText()
        return None, None