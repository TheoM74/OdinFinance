from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QFormLayout, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox, QTabWidget, QHeaderView
)
from PyQt6.QtCore import QDate, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OdinFinance - Trésorerie Officielle")
        self.resize(1200, 750)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- ONGLET 1 : COMPTE DE RÉSULTAT (PRINCIPAL) ---
        self.tab_bilan = QWidget()
        self.init_tab_bilan()
        self.tabs.addTab(self.tab_bilan, "📈 Compte de Résultat & Synthèse")

        # --- ONGLET 2 : SAISIE & MOUVEMENTS ---
        self.tab_transactions = QWidget()
        self.init_tab_transactions()
        self.tabs.addTab(self.tab_transactions, "📋 Saisie & Mouvements")

    def _creer_champ_avec_erreur(self, widget_saisie):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(widget_saisie)
        
        label_erreur = QLabel("")
        label_erreur.setStyleSheet("color: #ef4444; font-size: 11px; font-style: italic;")
        label_erreur.setVisible(False)
        layout.addWidget(label_erreur)
        
        container = QWidget()
        container.setLayout(layout)
        return container, label_erreur

    def init_tab_bilan(self):
        layout = QVBoxLayout(self.tab_bilan)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # En-tête
        header_layout = QHBoxLayout()
        title = QLabel("Tableau de Bord & Compte de Résultat Officiel")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1f2937;")
        
        self.btn_export_excel = QPushButton("📥 Exporter le Compte de Résultat (AG)")
        self.btn_export_excel.setObjectName("btn_succes")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_export_excel)
        layout.addLayout(header_layout)

        # --- BARRE DE FILTRES ---
        filtres_group = QGroupBox("Filtres d'analyse")
        filtres_layout = QHBoxLayout(filtres_group)
        filtres_layout.setContentsMargins(15, 15, 15, 15)

        self.filtre_mois_combo = QComboBox()
        self.filtre_cat_combo = QComboBox()
        self.filtre_tier_combo = QComboBox()
        self.btn_reset_filtres = QPushButton("Réinitialiser")
        self.btn_reset_filtres.setObjectName("btn_secondaire")

        filtres_layout.addWidget(QLabel("Mois :"))
        filtres_layout.addWidget(self.filtre_mois_combo)
        filtres_layout.addWidget(QLabel("Catégorie :"))
        filtres_layout.addWidget(self.filtre_cat_combo)
        filtres_layout.addWidget(QLabel("Tier :"))
        filtres_layout.addWidget(self.filtre_tier_combo)
        filtres_layout.addWidget(self.btn_reset_filtres)

        layout.addWidget(filtres_group)

        # Tableau de synthèse
        self.table_bilan = QTableWidget()
        self.table_bilan.setColumnCount(3)
        self.table_bilan.setHorizontalHeaderLabels(["Catégorie Comptable", "Type de Flux", "Solde Cumulé (€)"])
        self.table_bilan.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_bilan.verticalHeader().setVisible(False)
        self.table_bilan.setAlternatingRowColors(True)
        layout.addWidget(self.table_bilan)

        # Bloc Solde
        solde_widget = QWidget()
        solde_widget.setStyleSheet("background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px;")
        solde_layout = QHBoxLayout(solde_widget)
        
        self.label_solde = QLabel("Solde Actuel : -- €")
        self.label_solde.setStyleSheet("font-size: 16px; font-weight: bold; color: #166534;")
        solde_layout.addWidget(self.label_solde, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(solde_widget)

    def init_tab_transactions(self):
        layout_principal = QHBoxLayout(self.tab_transactions)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        self.form_group = QGroupBox("Enregistrer un flux financier")
        form_layout = QFormLayout(self.form_group)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 20, 15, 15)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ex: Achat boissons soirée")
        desc_container, self.err_desc = self._creer_champ_avec_erreur(self.desc_input)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        amount_container, self.err_amount = self._creer_champ_avec_erreur(self.amount_input)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("N° Facture (Optionnel)")

        cat_layout = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.btn_add_cat = QPushButton("+")
        self.btn_add_cat.setObjectName("btn_icon")
        self.btn_del_cat = QPushButton("−")
        self.btn_del_cat.setStyleSheet("color: #ef4444;")
        self.btn_del_cat.setObjectName("btn_icon")
        for w in [self.cat_combo, self.btn_add_cat, self.btn_del_cat]: cat_layout.addWidget(w)

        tier_layout = QHBoxLayout()
        self.tier_combo = QComboBox()
        self.btn_add_tier = QPushButton("+")
        self.btn_add_tier.setObjectName("btn_icon")
        self.btn_del_tier = QPushButton("−")
        self.btn_del_tier.setStyleSheet("color: #ef4444;")
        self.btn_del_tier.setObjectName("btn_icon")
        for w in [self.tier_combo, self.btn_add_tier, self.btn_del_tier]: tier_layout.addWidget(w)

        self.btn_ajouter = QPushButton("Enregistrer")
        self.btn_ajouter.setObjectName("btn_primaire")

        self.btn_annuler_edition = QPushButton("Annuler la modification")
        self.btn_annuler_edition.setObjectName("btn_secondaire")
        self.btn_annuler_edition.setVisible(False)

        form_layout.addRow("Date :", self.date_input)
        form_layout.addRow("Catégorie :", cat_layout)
        form_layout.addRow("Libellé :", desc_container)
        form_layout.addRow("Montant (€) :", amount_container)
        form_layout.addRow("Tiers :", tier_layout)
        form_layout.addRow("Réf. :", self.ref_input)
        
        btns_layout = QVBoxLayout()
        btns_layout.addWidget(self.btn_ajouter)
        btns_layout.addWidget(self.btn_annuler_edition)
        form_layout.addRow("", btns_layout)

        self.form_group.setFixedWidth(400)
        layout_principal.addWidget(self.form_group)

        right_layout = QVBoxLayout()
        
        self.table_transactions = QTableWidget()
        self.table_transactions.setColumnCount(6)
        self.table_transactions.setHorizontalHeaderLabels(["Date", "Libellé", "Montant", "Catégorie", "Tier", "Facture"])
        self.table_transactions.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_transactions.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_transactions.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_transactions.verticalHeader().setVisible(False)
        self.table_transactions.setAlternatingRowColors(True)
        right_layout.addWidget(self.table_transactions)

        self.btn_supprimer_trans = QPushButton("Supprimer le flux sélectionné")
        self.btn_supprimer_trans.setObjectName("btn_danger")
        right_layout.addWidget(self.btn_supprimer_trans, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_principal.addLayout(right_layout)

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