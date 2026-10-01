from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QFormLayout, QGroupBox, QMessageBox
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

        self.cat_combo = QComboBox()
        self.tier_combo = QComboBox()

        self.btn_ajouter = QPushButton("Enregistrer la transaction")
        self.btn_ajouter.setStyleSheet("background-color: #2b5b84; color: white; font-weight: bold; padding: 6px;")

        form_layout.addRow("Date :", self.date_input)
        form_layout.addRow("Description :", self.desc_input)
        form_layout.addRow("Montant (€) :", self.amount_input)
        form_layout.addRow("Réf. Facture :", self.ref_input)
        form_layout.addRow("Catégorie :", self.cat_combo)
        form_layout.addRow("Tier :", self.tier_combo)
        form_layout.addRow(self.btn_ajouter)

        form_group.setFixedWidth(350)
        content_layout.addWidget(form_group)

        # 2. Tableau des transactions (Côté droit)
        table_layout = QVBoxLayout()
        
        self.table_transactions = QTableWidget()
        self.table_transactions.setColumnCount(6)
        self.table_transactions.setHorizontalHeaderLabels([
            "Date", "Description", "Montant", "Catégorie", "Tier", "Facture"
        ])
        # Ajustement des colonnes
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