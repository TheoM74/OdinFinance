from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from services.bilan import LigneResultat
from services.montants import formater_montant
from views.theme import theme_actuel
from views.widgets import ChampFormulaire, Panneau, TitreSection, bouton, etiquette, poser_signe

DROITE = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class TableResultat(QTableWidget):
    """Liste « Catégorie / Montant » d'un côté du compte de résultat, lignes « dont » en retrait."""

    def __init__(self, vide: str):
        super().__init__(0, 2)
        self.vide = vide
        self.setHorizontalHeaderLabels(["Catégorie", "Montant"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.horizontalHeaderItem(1).setTextAlignment(DROITE)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def afficher(self, lignes: list[LigneResultat], total: int):
        theme = theme_actuel()
        contenu = []
        for ligne in lignes:
            contenu.append((ligne.categorie.nom, ligne.total, "racine"))
            contenu += [(f"dont {c.nom.lower()}", m, "dont") for c, m in ligne.sous_lignes]
        self.setRowCount(len(contenu) + 1)
        if not contenu:
            self.setRowCount(1)
            item = QTableWidgetItem(self.vide)
            item.setForeground(theme.couleur("texte_doux"))
            self.setItem(0, 0, item)
            self.setItem(0, 1, QTableWidgetItem(""))
            return

        for i, (nom, montant, genre) in enumerate(contenu):
            nom_item = QTableWidgetItem(("      " if genre == "dont" else "") + nom)
            montant_item = QTableWidgetItem(formater_montant(montant))
            montant_item.setTextAlignment(DROITE)
            if genre == "dont":
                for item in (nom_item, montant_item):
                    item.setForeground(theme.couleur("texte_doux"))
                    police = item.font()
                    police.setItalic(True)
                    item.setFont(police)
            self.setItem(i, 0, nom_item)
            self.setItem(i, 1, montant_item)

        total_nom, total_montant = QTableWidgetItem("Total"), QTableWidgetItem(formater_montant(total))
        total_montant.setTextAlignment(DROITE)
        for item in (total_nom, total_montant):
            police = item.font()
            police.setWeight(QFont.Weight.DemiBold)
            item.setFont(police)
        self.setItem(len(contenu), 0, total_nom)
        self.setItem(len(contenu), 1, total_montant)


class PageSynthese(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        entete = QHBoxLayout()
        titre = etiquette("Synthèse de l'exercice", "titre-page")
        self.label_periode = etiquette("", "aide")
        entete.addWidget(titre)
        entete.addSpacing(12)
        entete.addWidget(self.label_periode, 0, Qt.AlignmentFlag.AlignBottom)
        entete.addStretch()
        layout.addLayout(entete)

        # Trésorerie : solde de chaque compte
        self.panneau_tresorerie = Panneau()
        tete = QHBoxLayout()
        tete.addWidget(TitreSection("Trésorerie"))
        tete.addStretch()
        self.label_date_soldes = etiquette("", "aide")
        tete.addWidget(self.label_date_soldes, 0, Qt.AlignmentFlag.AlignTop)
        self.panneau_tresorerie.contenu.addLayout(tete)
        self.grille_soldes = QGridLayout()
        self.grille_soldes.setHorizontalSpacing(32)
        self.grille_soldes.setVerticalSpacing(4)
        self.panneau_tresorerie.contenu.addLayout(self.grille_soldes)
        layout.addWidget(self.panneau_tresorerie)

        # Filtres
        filtres = QHBoxLayout()
        filtres.setSpacing(12)
        self.filtre_periode = QComboBox()
        self.filtre_compte = QComboBox()
        self.filtre_categorie = QComboBox()
        self.filtre_tiers = QComboBox()
        for legende, combo in (("Période", self.filtre_periode), ("Compte", self.filtre_compte),
                               ("Catégorie", self.filtre_categorie), ("Tiers", self.filtre_tiers)):
            combo.setMinimumWidth(170)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            filtres.addWidget(ChampFormulaire(legende, combo), 1)
        self.btn_reinitialiser = bouton("Réinitialiser", "discret", "fermer", "Retirer tous les filtres")
        filtres.addWidget(self.btn_reinitialiser, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(filtres)

        # Compte de résultat en T : produits à gauche, charges à droite
        colonnes = QHBoxLayout()
        colonnes.setSpacing(18)
        self.table_produits = TableResultat("Aucune catégorie de recettes : ajoutez-en dans Paramètres.")
        self.table_charges = TableResultat("Aucune catégorie de dépenses : ajoutez-en dans Paramètres.")
        for titre_colonne, table in (("Produits", self.table_produits), ("Charges", self.table_charges)):
            panneau = Panneau()
            panneau.contenu.addWidget(TitreSection(titre_colonne))
            panneau.contenu.addWidget(table, 1)
            colonnes.addWidget(panneau, 1)
        layout.addLayout(colonnes, 1)

        # Résultat
        self.panneau_resultat = Panneau(marges=(20, 14, 20, 14))
        ligne = QHBoxLayout()
        ligne.setSpacing(28)
        self.label_total_produits = etiquette("", "montant")
        self.label_total_charges = etiquette("", "montant")
        self.label_resultat = etiquette("", "montant-fort")
        self.label_nature_resultat = etiquette("", "legende")
        for legende, valeur in (("Total des produits", self.label_total_produits),
                                ("Total des charges", self.label_total_charges)):
            bloc = QVBoxLayout()
            bloc.setSpacing(2)
            bloc.addWidget(etiquette(legende, "legende"))
            bloc.addWidget(valeur)
            ligne.addLayout(bloc)
        ligne.addStretch()
        bloc = QVBoxLayout()
        bloc.setSpacing(0)
        bloc.addWidget(self.label_nature_resultat, 0, Qt.AlignmentFlag.AlignRight)
        bloc.addWidget(self.label_resultat, 0, Qt.AlignmentFlag.AlignRight)
        ligne.addLayout(bloc)
        self.panneau_resultat.contenu.addLayout(ligne)
        layout.addWidget(self.panneau_resultat)

    def afficher_soldes(self, soldes: list[tuple[str, int]], total: int, date_texte: str):
        while self.grille_soldes.count():
            ancien = self.grille_soldes.takeAt(0).widget()
            ancien.setParent(None)  # retiré tout de suite de l'écran, détruit ensuite
            ancien.deleteLater()
        self.label_date_soldes.setText(date_texte)
        if not soldes:
            self.grille_soldes.addWidget(etiquette("Aucun compte : créez vos comptes dans Paramètres.", "aide"), 0, 0)
            return
        for col, (nom, montant) in enumerate(soldes + [("Total", total)]):
            est_total = col == len(soldes)
            legende = etiquette(nom, "legende")
            valeur = etiquette(formater_montant(montant), "montant-fort" if est_total else "montant")
            if montant < 0 or est_total:
                poser_signe(valeur, montant)
            self.grille_soldes.addWidget(legende, 0, col, Qt.AlignmentFlag.AlignBottom)
            self.grille_soldes.addWidget(valeur, 1, col, Qt.AlignmentFlag.AlignTop)
        self.grille_soldes.setColumnStretch(len(soldes), 1)

    def afficher_resultat(self, total_produits: int, total_charges: int, resultat: int):
        self.label_total_produits.setText(formater_montant(total_produits))
        self.label_total_charges.setText(formater_montant(total_charges))
        self.label_resultat.setText(formater_montant(resultat, signe=True))
        nature = "Excédent" if resultat > 0 else "Déficit" if resultat < 0 else "Équilibre"
        self.label_nature_resultat.setText(f"Résultat · {nature}")
        poser_signe(self.label_resultat, resultat)
