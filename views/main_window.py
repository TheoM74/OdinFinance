from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QFormLayout, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox, QTabWidget
)
from PyQt6.QtCore import QDate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OdinFinance - Gestion de Trésorerie")
        self.resize(1050, 700)

        # Widget central contenant les onglets
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

        # 1. Formulaire d'ajout (Côté gauche)
        form_group = QGroupBox("Ajouter une transaction")
        form_layout = QFormLayout(form_group)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ex: Achat boissons soirée")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Numéro de facture optionnel")

        cat_layout = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.btn_add_cat = QPushButton("+")
        self.btn_add_cat.setFixedWidth(30)
        cat_layout.addWidget(self.cat_combo)
        cat_layout.addWidget(self.btn_add_cat)

        tier_layout = QHBoxLayout()
        self.tier_combo = QComboBox()
        self.btn_add_tier = QPushButton("+")
        self.btn_add_tier.setFixedWidth(30)
        tier_layout.addWidget(self.tier_combo)
        tier_layout.addWidget(self.btn_add_tier)

        self.btn_ajouter = QPushButton("Enregistrer la transaction")
        self.btn_ajouter.setStyleSheet("background-color: #2b5b84; color: white; font-weight: bold; padding: 6px;")

        form_layout.addRow("Date :", self.date_input)
        form_layout.addRow("Description :", self.desc_input)
        form_layout.addRow("Montant (€) :", self.amount_input)
        form_layout.addRow("Réf. Facture :", self.ref_input)
        form_layout.addRow("Catégorie :", cat_layout)
        form_layout.addRow("Tier :", tier_layout)
        form_layout.addRow(self.btn_ajouter)

        form_group.setFixedWidth(380)
        layout_principal.addWidget(form_group)

        # 2. Tableau des transactions (Côté droit)
        table_layout = QVBoxLayout()
        self.table_transactions = QTableWidget()
        self.table_transactions.setColumnCount(6)
        self.table_transactions.setHorizontalHeaderLabels([
            "Date", "Description", "Montant", "Catégorie", "Tier", "Facture"
        ])
        self.table_transactions.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.table_transactions)
        layout_principal.addLayout(table_layout)

    def init_tab_bilan(self):
        layout = QVBoxLayout(self.tab_bilan)

        title = QLabel("Bilan Financier Synthétique (Présentation AG)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tableau récapitulatif par catégorie
        self.table_bilan = QTableWidget()
        self.table_bilan.setColumnCount(3)
        self.table_bilan.setHorizontalHeaderLabels(["Catégorie", "Type de Flux", "Total Cumulé (€)"])
        self.table_bilan.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_bilan)

        # Indicateurs globaux (Solde)
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