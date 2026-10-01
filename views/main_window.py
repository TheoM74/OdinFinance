from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QFormLayout, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import QDate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OdinFinance - Gestion de Trésorerie")
        self.resize(1000, 650)

        # Widget central principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- TITRE ---
        title_label = QLabel("📊 Tableau de Bord - Trésorerie ODIN")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # --- SECTION CENTRALE (Formulaire à gauche, Tableau à droite) ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # 1. Formulaire d'ajout de transaction (Côté gauche)
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

        # Layout Catégorie avec bouton "+"
        cat_layout = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.btn_add_cat = QPushButton("+")
        self.btn_add_cat.setFixedWidth(30)
        cat_layout.addWidget(self.cat_combo)
        cat_layout.addWidget(self.btn_add_cat)

        # Layout Tier avec bouton "+"
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
        content_layout.addWidget(form_group)

        # 2. Tableau des transactions (Côté droit)
        table_layout = QVBoxLayout()
        
        self.table_transactions = QTableWidget()
        self.table_transactions.setColumnCount(6)
        self.table_transactions.setHorizontalHeaderLabels([
            "Date", "Description", "Montant", "Catégorie", "Tier", "Facture"
        ])
        self.table_transactions.horizontalHeader().setStretchLastSection(True)
        
        table_layout.addWidget(self.table_transactions)
        content_layout.addLayout(table_layout)

    def afficher_message(self, titre: str, message: str, is_erreur: bool = False):
        """Affiche une boîte de dialogue (succès ou erreur)."""
        msg = QMessageBox(self)
        msg.setWindowTitle(titre)
        msg.setText(message)
        if is_erreur:
            msg.setIcon(QMessageBox.Icon.Warning)
        else:
            msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def demander_texte_et_type(self, titre: str, options_type: list[str]):
        """Ouvre une popup simple pour créer un élément avec un nom et un type."""
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