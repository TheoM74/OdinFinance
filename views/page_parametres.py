from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLineEdit, QScrollArea,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QWidget,
)

from database.modeles import DEPENSE, LIBELLES_TIERS, RECETTE, Categorie, Compte, Tiers
from services.montants import formater_montant
from views.theme import theme_actuel
from views.widgets import ChampFormulaire, Panneau, TitreSection, bouton, etiquette

ROLE_ID = Qt.ItemDataRole.UserRole


def _tableau(entetes: list[str], colonne_extensible: int) -> QTableWidget:
    table = QTableWidget(0, len(entetes))
    table.setHorizontalHeaderLabels(entetes)
    table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    table.horizontalHeader().setHighlightSections(False)
    for col in range(len(entetes)):
        mode = QHeaderView.ResizeMode.Stretch if col == colonne_extensible else QHeaderView.ResizeMode.ResizeToContents
        table.horizontalHeader().setSectionResizeMode(col, mode)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(34)
    table.setShowGrid(False)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setMinimumHeight(190)
    return table


def _barre_actions(element: str) -> tuple[QHBoxLayout, object, object, object]:
    ligne = QHBoxLayout()
    ajouter = bouton("Ajouter", None, "plus", f"Ajouter {element}")
    modifier = bouton("Modifier", None, "modifier", f"Modifier {element} sélectionné(e)")
    supprimer = bouton("Supprimer", "danger", "supprimer", f"Supprimer {element} sélectionné(e)")
    ligne.addWidget(ajouter)
    ligne.addStretch()
    ligne.addWidget(modifier)
    ligne.addWidget(supprimer)
    return ligne, ajouter, modifier, supprimer


class PageParametres(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        contenu = QWidget()
        contenu.setObjectName("page")
        self.setWidget(contenu)

        grille = QGridLayout(contenu)
        grille.setContentsMargins(28, 24, 28, 24)
        grille.setHorizontalSpacing(20)
        grille.setVerticalSpacing(20)
        grille.addWidget(etiquette("Paramètres", "titre-page"), 0, 0, 1, 2)
        grille.addWidget(self._panneau_association(), 1, 0)
        grille.addWidget(self._panneau_comptes(), 2, 0)
        grille.addWidget(self._panneau_donnees(), 3, 0)
        grille.addWidget(self._panneau_categories(), 1, 1, 2, 1)
        grille.addWidget(self._panneau_tiers(), 3, 1)
        grille.setColumnStretch(0, 1)
        grille.setColumnStretch(1, 1)
        grille.setRowStretch(4, 1)

    def _panneau_association(self) -> Panneau:
        p = Panneau()
        p.contenu.addWidget(TitreSection("Association et exercice"))
        self.nom_association_input = QLineEdit()
        self.nom_association_input.setMaxLength(80)
        self.champ_nom_association = ChampFormulaire("Nom de l'association", self.nom_association_input)
        p.contenu.addWidget(self.champ_nom_association)

        dates = QHBoxLayout()
        dates.setSpacing(12)
        self.debut_input, self.fin_input = QDateEdit(), QDateEdit()
        for champ in (self.debut_input, self.fin_input):
            champ.setCalendarPopup(True)
            champ.setDisplayFormat("dd/MM/yyyy")
        self.champ_fin = ChampFormulaire("Fin de l'exercice", self.fin_input)
        dates.addWidget(ChampFormulaire("Début de l'exercice", self.debut_input), 1)
        dates.addWidget(self.champ_fin, 1)
        p.contenu.addLayout(dates)
        aide = etiquette("La synthèse et le bilan exporté couvrent cette période. "
                         "Le titre du bilan reprend l'année de clôture.", "aide")
        aide.setWordWrap(True)
        p.contenu.addWidget(aide)

        ligne = QHBoxLayout()
        ligne.addStretch()
        self.btn_enregistrer_association = bouton("Enregistrer", "primaire")
        ligne.addWidget(self.btn_enregistrer_association)
        p.contenu.addLayout(ligne)
        return p

    def _panneau_comptes(self) -> Panneau:
        p = Panneau()
        p.contenu.addWidget(TitreSection("Comptes de trésorerie"))
        aide = etiquette("Le solde initial est le solde du compte avant la première opération saisie.", "aide")
        aide.setWordWrap(True)
        p.contenu.addWidget(aide)
        self.table_comptes = _tableau(["Code", "Nom", "Solde initial"], 1)
        self.table_comptes.setMinimumHeight(250)
        p.contenu.addWidget(self.table_comptes)
        ligne, self.btn_ajouter_compte, self.btn_modifier_compte, self.btn_supprimer_compte = _barre_actions("un compte")
        p.contenu.addLayout(ligne)
        return p

    def _panneau_donnees(self) -> Panneau:
        p = Panneau()
        p.contenu.addWidget(TitreSection("Données"))
        self.label_chemin_base = etiquette("", "aide")
        self.label_chemin_base.setWordWrap(True)
        self.label_chemin_base.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        p.contenu.addWidget(self.label_chemin_base)
        ligne = QHBoxLayout()
        self.btn_ouvrir_dossier = bouton("Ouvrir le dossier", None, "dossier",
                                         "Ouvrir le dossier de la base de données, pour la sauvegarder")
        ligne.addWidget(self.btn_ouvrir_dossier)
        ligne.addStretch()
        p.contenu.addLayout(ligne)
        return p

    def _panneau_categories(self) -> Panneau:
        p = Panneau()
        p.contenu.addWidget(TitreSection("Catégories"))
        aide = etiquette("Une sous-catégorie apparaît dans le bilan en ligne « dont … » sous sa catégorie.", "aide")
        aide.setWordWrap(True)
        p.contenu.addWidget(aide)
        self.arbre_categories = QTreeWidget()
        self.arbre_categories.setHeaderHidden(True)
        self.arbre_categories.setRootIsDecorated(False)
        self.arbre_categories.setItemsExpandable(False)
        self.arbre_categories.setIndentation(22)
        self.arbre_categories.setMinimumHeight(320)
        p.contenu.addWidget(self.arbre_categories, 1)
        ligne, self.btn_ajouter_categorie, self.btn_modifier_categorie, self.btn_supprimer_categorie = _barre_actions("une catégorie")
        p.contenu.addLayout(ligne)
        return p

    def _panneau_tiers(self) -> Panneau:
        p = Panneau()
        p.contenu.addWidget(TitreSection("Tiers"))
        self.table_tiers = _tableau(["Nom", "Type"], 0)
        p.contenu.addWidget(self.table_tiers)
        ligne, self.btn_ajouter_tier, self.btn_modifier_tier, self.btn_supprimer_tier = _barre_actions("un tiers")
        p.contenu.addLayout(ligne)
        return p

    # --- Affichage ---
    @staticmethod
    def _remplir(table: QTableWidget, lignes: list[tuple[int, list[str]]], colonnes_droite=()):
        table.setRowCount(len(lignes))
        for i, (identifiant, valeurs) in enumerate(lignes):
            for col, valeur in enumerate(valeurs):
                item = QTableWidgetItem(valeur)
                item.setData(ROLE_ID, identifiant)
                if col in colonnes_droite:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(i, col, item)

    def afficher_comptes(self, comptes: list[Compte]):
        self._remplir(self.table_comptes, [(c.id, [c.code, c.nom, formater_montant(c.solde_initial)]) for c in comptes], (2,))

    def afficher_tiers(self, tiers: list[Tiers]):
        self._remplir(self.table_tiers, [(t.id, [t.nom, LIBELLES_TIERS[t.type_tier]]) for t in tiers])

    def afficher_categories(self, categories: list[Categorie]):
        self.arbre_categories.clear()
        theme = theme_actuel()
        for type_flux, titre in ((RECETTE, "Recettes"), (DEPENSE, "Dépenses")):
            groupe = QTreeWidgetItem([titre])
            groupe.setFlags(Qt.ItemFlag.ItemIsEnabled)
            police = groupe.font(0)
            police.setWeight(QFont.Weight.DemiBold)
            groupe.setFont(0, police)
            groupe.setForeground(0, theme.couleur("texte_doux"))
            self.arbre_categories.addTopLevelItem(groupe)
            for racine in (c for c in categories if c.type_flux == type_flux and c.parent_id is None):
                item = QTreeWidgetItem([racine.nom])
                item.setData(0, ROLE_ID, racine.id)
                groupe.addChild(item)
                for enfant in (c for c in categories if c.parent_id == racine.id):
                    sous_item = QTreeWidgetItem([enfant.nom])
                    sous_item.setData(0, ROLE_ID, enfant.id)
                    item.addChild(sous_item)
        self.arbre_categories.expandAll()

    @staticmethod
    def id_selectionne(vue: QTableWidget | QTreeWidget) -> int | None:
        items = vue.selectedItems()
        if not items:
            return None
        return items[0].data(0, ROLE_ID) if isinstance(vue, QTreeWidget) else items[0].data(ROLE_ID)

    def afficher_association(self, nom: str, debut: QDate, fin: QDate):
        self.nom_association_input.setText(nom)
        self.debut_input.setDate(debut)
        self.fin_input.setDate(fin)
