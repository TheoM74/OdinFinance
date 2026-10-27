from PyQt6.QtCore import QDate, QSortFilterProxyModel, Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QFrame, QHBoxLayout, QHeaderView, QLineEdit, QScrollArea,
    QStackedWidget, QTableView, QVBoxLayout, QWidget,
)

from database.modeles import DEPENSE, RECETTE, VIREMENT, Operation
from services.montants import formater_montant
from views.icones import icone
from views.theme import theme_actuel
from views.widgets import BarreSegmentee, ChampFormulaire, Panneau, TitreSection, bouton, etiquette

ROLE_TRI = Qt.ItemDataRole.UserRole + 1
ROLE_ID = Qt.ItemDataRole.UserRole + 2
ROLE_COMPTES = Qt.ItemDataRole.UserRole + 3
COLONNES = ["Date", "Libellé", "Compte", "Catégorie", "Tiers", "Réf.", "Montant"]
COL_MONTANT = 6


class FiltreOperations(QSortFilterProxyModel):
    """Recherche plein texte sur toutes les colonnes + filtre par compte (source ou destination)."""

    def __init__(self):
        super().__init__()
        self.compte_id = None
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterKeyColumn(-1)
        self.setSortRole(ROLE_TRI)

    def filtrer_compte(self, compte_id):
        self.compte_id = compte_id
        self.invalidateFilter()

    def filterAcceptsRow(self, ligne, parent):
        if self.compte_id is not None:
            comptes = self.sourceModel().index(ligne, 0, parent).data(ROLE_COMPTES)
            if self.compte_id not in comptes:
                return False
        return super().filterAcceptsRow(ligne, parent)


class PageJournal(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)
        layout.addWidget(self._creer_formulaire())
        layout.addLayout(self._creer_liste(), 1)

    # --- Formulaire de saisie ---
    def _creer_formulaire(self) -> QWidget:
        panneau = Panneau()
        panneau.setFixedWidth(400)
        panneau.contenu.setSpacing(14)
        self.titre_formulaire = TitreSection("Nouvelle opération")
        panneau.contenu.addWidget(self.titre_formulaire)

        # Les champs défilent si la fenêtre est trop basse ; titre et boutons restent visibles.
        zone = QScrollArea()
        zone.setObjectName("zone_formulaire")
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.Shape.NoFrame)
        zone.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        champs = QWidget()
        champs.setObjectName("page")
        zone.setWidget(champs)
        panneau.contenu.addWidget(zone, 1)
        f = QVBoxLayout(champs)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(14)

        self.type_operation = BarreSegmentee([(RECETTE, "Recette"), (DEPENSE, "Dépense"), (VIREMENT, "Virement")])
        self.type_operation.setToolTip("Un virement déplace de l'argent entre deux comptes de l'association : "
                                       "il ne compte ni en produit ni en charge.")
        f.addWidget(self.type_operation)

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.champ_date = ChampFormulaire("Date", self.date_input)

        self.compte_combo = QComboBox()
        self.champ_compte = ChampFormulaire("Compte", self.compte_combo)
        self.destination_combo = QComboBox()
        self.champ_destination = ChampFormulaire("Vers le compte", self.destination_combo)

        self.cat_combo = QComboBox()
        self.btn_ajout_categorie = bouton("", "icone", "plus", "Nouvelle catégorie")
        self.champ_categorie = ChampFormulaire("Catégorie", self.cat_combo, accessoire=self.btn_ajout_categorie)

        self.libelle_input = QLineEdit()
        self.libelle_input.setPlaceholderText("Ex. Achat boissons soirée d'intégration")
        self.libelle_input.setMaxLength(120)
        self.champ_libelle = ChampFormulaire("Libellé", self.libelle_input)

        self.montant_input = QLineEdit()
        self.montant_input.setPlaceholderText("0,00")
        self.montant_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.champ_montant = ChampFormulaire("Montant (€)", self.montant_input)

        self.tier_combo = QComboBox()
        self.btn_ajout_tier = bouton("", "icone", "plus", "Nouveau tiers")
        self.champ_tiers = ChampFormulaire("Tiers", self.tier_combo, facultatif=True, accessoire=self.btn_ajout_tier)

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Ex. F2026-014")
        self.reference_input.setMaxLength(60)
        self.champ_reference = ChampFormulaire("Référence de facture", self.reference_input, facultatif=True)

        ligne_date_montant = QHBoxLayout()
        ligne_date_montant.setSpacing(12)
        ligne_date_montant.addWidget(self.champ_date, 1, Qt.AlignmentFlag.AlignTop)
        ligne_date_montant.addWidget(self.champ_montant, 1, Qt.AlignmentFlag.AlignTop)
        f.addLayout(ligne_date_montant)
        for champ in (self.champ_compte, self.champ_destination, self.champ_categorie, self.champ_libelle,
                      self.champ_tiers, self.champ_reference):
            f.addWidget(champ)
        f.addStretch()

        boutons = QHBoxLayout()
        self.btn_annuler = bouton("Annuler", "discret", infobulle="Abandonner la modification (Échap)")
        self.btn_enregistrer = bouton("Enregistrer", "primaire", infobulle="Enregistrer l'opération (Entrée)")
        self.btn_enregistrer.setDefault(True)
        boutons.addWidget(self.btn_annuler)
        boutons.addStretch()
        boutons.addWidget(self.btn_enregistrer)
        panneau.contenu.addLayout(boutons)

        self.type_operation.change.connect(self._adapter_au_type)
        self.type_operation.choisir(DEPENSE)
        return panneau

    def _adapter_au_type(self, type_operation: str):
        virement = type_operation == VIREMENT
        self.champ_destination.setVisible(virement)
        self.champ_categorie.setVisible(not virement)
        self.champ_tiers.setVisible(not virement)
        self.champ_reference.setVisible(not virement)
        self.champ_compte.changer_legende("Depuis le compte" if virement else "Compte")

    # --- Liste des opérations ---
    def _creer_liste(self):
        colonne = QVBoxLayout()
        colonne.setSpacing(12)

        outils = QHBoxLayout()
        outils.setSpacing(10)
        self.recherche_input = QLineEdit()
        self.recherche_input.setPlaceholderText("Rechercher un libellé, un tiers, une référence…")
        self.recherche_input.setClearButtonEnabled(True)
        self.action_recherche = self.recherche_input.addAction(
            icone("rechercher", theme_actuel().couleurs["texte_doux"]), QLineEdit.ActionPosition.LeadingPosition)
        self.filtre_compte = QComboBox()
        self.filtre_compte.setMinimumWidth(200)
        self.label_compteur = etiquette("", "aide")
        outils.addWidget(self.recherche_input, 2)
        outils.addWidget(self.filtre_compte, 1)
        outils.addWidget(self.label_compteur)
        colonne.addLayout(outils)

        self.modele = QStandardItemModel(0, len(COLONNES))
        self.modele.setHorizontalHeaderLabels(COLONNES)
        self.filtre = FiltreOperations()
        self.filtre.setSourceModel(self.modele)

        self.table = QTableView()
        self.table.setModel(self.filtre)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        entete = self.table.horizontalHeader()
        entete.setHighlightSections(False)
        entete.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col, mode in enumerate([QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.Stretch,
                                    QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents,
                                    QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents,
                                    QHeaderView.ResizeMode.ResizeToContents]):
            entete.setSectionResizeMode(col, mode)

        self.etat_vide = etiquette("", "etat-vide")
        self.etat_vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etat_vide.setWordWrap(True)
        self.pile_liste = QStackedWidget()
        self.pile_liste.addWidget(self.table)
        self.pile_liste.addWidget(self.etat_vide)
        colonne.addWidget(self.pile_liste, 1)

        actions = QHBoxLayout()
        actions.addWidget(etiquette("Double-cliquez sur une ligne pour la modifier.", "aide"))
        actions.addStretch()
        self.btn_modifier = bouton("Modifier", None, "modifier", "Charger l'opération dans le formulaire (Entrée)")
        self.btn_supprimer = bouton("Supprimer", "danger", "supprimer", "Supprimer l'opération sélectionnée (Suppr)")
        actions.addWidget(self.btn_modifier)
        actions.addWidget(self.btn_supprimer)
        colonne.addLayout(actions)

        self.raccourci_suppr = QShortcut(QKeySequence.StandardKey.Delete, self.table)
        self.raccourci_modifier = QShortcut(QKeySequence(Qt.Key.Key_Return), self.table)
        self.raccourci_echap = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.raccourci_recherche = QShortcut(QKeySequence.StandardKey.Find, self)
        self.raccourci_recherche.activated.connect(lambda: self.recherche_input.setFocus())
        return colonne

    def afficher_operations(self, operations: list[Operation]):
        theme = theme_actuel()
        self.action_recherche.setIcon(icone("rechercher", theme.couleurs["texte_doux"]))
        self.modele.removeRows(0, self.modele.rowCount())
        for op in operations:
            if op.est_virement:
                compte, categorie, signe = f"{op.compte_nom} → {op.compte_destination_nom}", "Virement interne", 0
            else:
                compte, categorie = op.compte_nom, op.categorie_nom
                signe = 1 if op.type_flux == RECETTE else -1
            valeurs = [
                (op.date.strftime("%d/%m/%Y"), f"{op.date.isoformat()}-{op.id:08d}"),
                (op.libelle, op.libelle.lower()),
                (compte, compte.lower()),
                (categorie, categorie.lower()),
                (op.tier_nom or "", (op.tier_nom or "").lower()),
                (op.reference or "", (op.reference or "").lower()),
                (formater_montant(op.montant * (signe or 1), signe=signe > 0), op.montant * (signe or 1)),
            ]
            items = []
            for texte, cle_tri in valeurs:
                item = QStandardItem(texte)
                item.setData(cle_tri, ROLE_TRI)
                items.append(item)
            items[0].setData(op.id, ROLE_ID)
            items[0].setData({op.compte_id, op.compte_destination_id}, ROLE_COMPTES)
            montant = items[COL_MONTANT]
            montant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            montant.setForeground(theme.couleur("positif" if signe > 0 else "danger" if signe < 0 else "texte_doux"))
            if op.est_virement:
                items[3].setForeground(theme.couleur("texte_doux"))
            self.modele.appendRow(items)
        self.table.sortByColumn(self.table.horizontalHeader().sortIndicatorSection(),
                                self.table.horizontalHeader().sortIndicatorOrder())

    def id_selectionne(self) -> int | None:
        lignes = self.table.selectionModel().selectedRows()
        return lignes[0].data(ROLE_ID) if lignes else None

    def selectionner(self, operation_id: int):
        for ligne in range(self.filtre.rowCount()):
            index = self.filtre.index(ligne, 0)
            if index.data(ROLE_ID) == operation_id:
                self.table.selectRow(ligne)
                self.table.scrollTo(index)
                return
