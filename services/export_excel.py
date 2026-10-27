"""Export du bilan financier au format du classeur de l'association (« Bilan financier.xlsx »).

Feuille 1 « Bilan financier » : un journal par compte, côte à côte (Débit à gauche, Crédit à droite),
avec sous-totaux et solde à chaque fin de mois.
Feuille 2 « Résumé financier » : soldes de clôture, compte de résultat par catégorie et cadres de signature.

Les sous-totaux, soldes et résultats sont écrits en formules Excel : le trésorier peut corriger une ligne
dans le classeur et tout se recalcule.
"""
from dataclasses import dataclass

import openpyxl
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.worksheet import Worksheet

from database.modeles import Categorie, Compte, Operation
from services.bilan import CompteResultat, Exercice, compte_resultat, fin_de_mois, journal_compte
from services.montants import nom_mois

POLICE = "Aptos Narrow"
BLEU = "0070C0"
VERT = "00B050"
ROUGE = "FF0000"

FORMAT_EUROS = '#,##0.00\\ "€";[Red]\\-#,##0.00\\ "€"'
FORMAT_VARIATION = '[Color10]+#,##0.00\\ "€";[Red]\\-#,##0.00\\ "€";0.00\\ "€"'
FORMAT_DATE = "dd/mm/yyyy"

_FIN = Side(style="thin")
CADRE = Border(left=_FIN, right=_FIN, top=_FIN, bottom=_FIN)
CADRE_BAS_EPAIS = Border(left=_FIN, right=_FIN, top=_FIN, bottom=Side(style="medium"))
CENTRE = Alignment(horizontal="center", vertical="center")
CENTRE_HAUT = Alignment(horizontal="center", vertical="top", wrap_text=True)
ENTETE = Alignment(vertical="center", wrap_text=True)


@dataclass(frozen=True)
class Style:
    gras: bool = False
    couleur: str | None = None
    taille: int = 11
    italique: bool = False
    format: str | None = None
    cadre: Border | None = CADRE
    alignement: Alignment | None = None

    def appliquer(self, cellule):
        cellule.font = Font(name=POLICE, size=self.taille, bold=self.gras, italic=self.italique, color=self.couleur)
        if self.format:
            cellule.number_format = self.format
        if self.cadre:
            cellule.border = self.cadre
        if self.alignement:
            cellule.alignment = self.alignement


NORMAL = Style()
GRAS = Style(gras=True)
SOLDE = Style(gras=True, couleur=BLEU)
TITRE = Style(gras=True, couleur=BLEU, taille=18, cadre=None, alignement=CENTRE)
SOUS_TITRE = Style(italique=True, couleur="595959", cadre=None, alignement=CENTRE)


def _ecrire(ws: Worksheet, ligne: int, col: int, valeur, style: Style = NORMAL, format: str | None = None):
    cellule = ws.cell(row=ligne, column=col, value=valeur)
    style.appliquer(cellule)
    if format:
        cellule.number_format = format
    return cellule


def _fusionner(ws: Worksheet, ligne: int, col_debut: int, col_fin: int, valeur, style: Style, ligne_fin: int | None = None):
    ligne_fin = ligne_fin or ligne
    for l in range(ligne, ligne_fin + 1):
        for c in range(col_debut, col_fin + 1):
            style.appliquer(ws.cell(row=l, column=c))  # les bordures d'une plage fusionnée se posent case par case
    ws.merge_cells(start_row=ligne, start_column=col_debut, end_row=ligne_fin, end_column=col_fin)
    ws.cell(row=ligne, column=col_debut, value=valeur)


def _ref(col: int, ligne: int) -> str:
    return f"{get_column_letter(col)}{ligne}"


def _mise_en_page(ws: Worksheet, pages_en_largeur: int = 1, pages_en_hauteur: int = 0, lignes_titres: str | None = None):
    """A4 paysage, ajusté à `pages_en_largeur` pages de large (0 en hauteur = autant que nécessaire)."""
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = pages_en_largeur
    ws.page_setup.fitToHeight = pages_en_hauteur
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    if lignes_titres:
        ws.print_title_rows = lignes_titres


# --- Feuille 1 : journaux par compte ---
LARGEUR_BLOC = 6  # Date, Libellé, Somme (débit) + Date, Libellé, Somme (crédit)
LIGNE_COMPTES, LIGNE_SENS, LIGNE_ENTETES, PREMIERE_LIGNE = 6, 7, 8, 9


def _feuille_journaux(ws: Worksheet, nom_association: str, exercice: Exercice,
                      comptes: list[Compte], operations: list[Operation]) -> dict[int, str]:
    """Écrit les journaux et renvoie, pour chaque compte, la référence de la cellule du solde de clôture."""
    ws.title = "Bilan financier"
    # Titre au-dessus du premier compte, comme dans le classeur d'origine (B2:G2)
    _fusionner(ws, 2, 2, 1 + LARGEUR_BLOC, f"Bilan financier {exercice.annee} · {nom_association}", TITRE)
    ws.row_dimensions[2].height = 24
    _fusionner(ws, 3, 2, 1 + LARGEUR_BLOC,
               f"Exercice du {exercice.debut:%d/%m/%Y} au {exercice.fin:%d/%m/%Y}", SOUS_TITRE)

    soldes_cloture = {}
    for index, compte in enumerate(comptes):
        col = 2 + index * (LARGEUR_BLOC + 1)
        soldes_cloture[compte.id] = _bloc_compte(ws, col, compte, operations, exercice)
        for decalage, largeur in enumerate([11, 34, 13, 11, 34, 13]):
            ws.column_dimensions[get_column_letter(col + decalage)].width = largeur
        ws.column_dimensions[get_column_letter(col + LARGEUR_BLOC)].width = 3
        if index < len(comptes) - 1:
            ws.col_breaks.append(Break(id=col + LARGEUR_BLOC))  # à l'impression : un compte par page

    ws.column_dimensions["A"].width = 3
    ws.freeze_panes = _ref(1, PREMIERE_LIGNE)
    _mise_en_page(ws, max(1, len(comptes)), 0, f"{LIGNE_COMPTES}:{LIGNE_ENTETES}")
    return soldes_cloture


def _encadrer_ligne(ws: Worksheet, ligne: int, col: int):
    """Encadre les six cases d'une ligne de journal, y compris le côté laissé vide."""
    for c in range(col, col + LARGEUR_BLOC):
        NORMAL.appliquer(ws.cell(row=ligne, column=c))


def _bloc_compte(ws: Worksheet, col: int, compte: Compte, operations: list[Operation], exercice: Exercice) -> str:
    journal = journal_compte(compte, operations, exercice)
    debit, credit = col, col + 3  # première colonne de chaque côté

    titre = f"{compte.code} - {compte.nom}" if compte.code else compte.nom
    _fusionner(ws, LIGNE_COMPTES, col, col + LARGEUR_BLOC - 1, titre, Style(gras=True, alignement=CENTRE))
    _fusionner(ws, LIGNE_SENS, debit, debit + 2, "↘ Débit", Style(gras=True, alignement=CENTRE, cadre=CADRE_BAS_EPAIS))
    _fusionner(ws, LIGNE_SENS, credit, credit + 2, "↗ Crédit", Style(gras=True, alignement=CENTRE, cadre=CADRE_BAS_EPAIS))
    for cote in (debit, credit):
        for decalage, entete in enumerate(["Date", "Libellé", "Somme"]):
            _ecrire(ws, LIGNE_ENTETES, cote + decalage, entete, GRAS)

    # Solde reporté de la fin du mois précédant l'exercice
    ligne = PREMIERE_LIGNE
    _encadrer_ligne(ws, ligne, debit)
    ouverture = journal.date_ouverture
    _ecrire(ws, ligne, debit, ouverture, SOLDE, FORMAT_DATE)
    _ecrire(ws, ligne, debit + 1, f"Solde de {nom_mois(ouverture.year, ouverture.month)}", SOLDE)
    _ecrire(ws, ligne, debit + 2, journal.solde_ouverture / 100, SOLDE, FORMAT_EUROS)
    ref_solde = _ref(debit + 2, ligne)
    ligne += 1

    if not journal.mois:
        _fusionner(ws, ligne, debit, credit + 2, "Aucun mouvement sur l'exercice",
                   Style(italique=True, couleur="595959", alignement=CENTRE))
        return ref_solde

    sous_totaux_debit, sous_totaux_credit = [], []
    for mois in journal.mois:
        premiere = ligne
        for l in mois.lignes:
            cote = debit if l.debit else credit
            _encadrer_ligne(ws, ligne, debit)
            _ecrire(ws, ligne, cote, l.date, format=FORMAT_DATE)
            _ecrire(ws, ligne, cote + 1, l.libelle)
            _ecrire(ws, ligne, cote + 2, l.montant / 100, format=FORMAT_EUROS)
            ligne += 1
        derniere = ligne - 1
        cloture_mois = fin_de_mois(mois.annee, mois.mois)

        # Sous-totaux du mois, des deux côtés
        for cote, liste in ((debit, sous_totaux_debit), (credit, sous_totaux_credit)):
            _ecrire(ws, ligne, cote, cloture_mois, GRAS, FORMAT_DATE)
            _ecrire(ws, ligne, cote + 1, "Sous-total", GRAS)
            somme = f"=SUM({_ref(cote + 2, premiere)}:{_ref(cote + 2, derniere)})"
            _ecrire(ws, ligne, cote + 2, somme, GRAS, FORMAT_EUROS)
            liste.append(_ref(cote + 2, ligne))
        ref_debit, ref_credit = sous_totaux_debit[-1], sous_totaux_credit[-1]
        ligne += 1

        # Solde de fin de mois (côté débit) et variation du mois (côté crédit)
        _ecrire(ws, ligne, debit, cloture_mois, SOLDE, FORMAT_DATE)
        _ecrire(ws, ligne, debit + 1, f"Solde de {nom_mois(mois.annee, mois.mois)}", SOLDE)
        _ecrire(ws, ligne, debit + 2, f"={ref_solde}+{ref_debit}-{ref_credit}", SOLDE, FORMAT_EUROS)
        _ecrire(ws, ligne, credit, cloture_mois, GRAS, FORMAT_DATE)
        _ecrire(ws, ligne, credit + 1, "Variation du mois", GRAS)
        _ecrire(ws, ligne, credit + 2, f"={ref_debit}-{ref_credit}", GRAS, FORMAT_VARIATION)
        ref_solde = _ref(debit + 2, ligne)
        ligne += 1

    # Totaux de l'exercice
    for cote, liste in ((debit, sous_totaux_debit), (credit, sous_totaux_credit)):
        _ecrire(ws, ligne, cote, exercice.fin, GRAS, FORMAT_DATE)
        _ecrire(ws, ligne, cote + 1, "Total de l'exercice", GRAS)
        _ecrire(ws, ligne, cote + 2, "=" + "+".join(liste), GRAS, FORMAT_EUROS)
    return ref_solde


# --- Feuille 2 : résumé ---
def _feuille_resume(ws: Worksheet, nom_association: str, exercice: Exercice, comptes: list[Compte],
                    resultat: CompteResultat, soldes_cloture: dict[int, str], feuille_journaux: str):
    ws.title = "Résumé financier"
    entetes_categories = []  # (libellé, montant, est_produit, est_racine)
    for ligne in resultat.produits:
        entetes_categories.append((ligne.categorie.nom, ligne.total, True, True))
        entetes_categories += [(f"dont {c.nom.lower()}", m, True, False) for c, m in ligne.sous_lignes]
    for ligne in resultat.charges:
        entetes_categories.append((ligne.categorie.nom, ligne.total, False, True))
        entetes_categories += [(f"dont {c.nom.lower()}", m, False, False) for c, m in ligne.sous_lignes]

    derniere_col = max(8, 1 + len(comptes) + 1, 1 + len(entetes_categories) + 1)
    _fusionner(ws, 2, 2, derniere_col, f"Résumé financier · {exercice.annee}", Style(gras=True, couleur=BLEU, taille=16, cadre=None, alignement=CENTRE))
    ws.row_dimensions[2].height = 22
    _fusionner(ws, 3, 2, derniere_col,
               f"{nom_association} · exercice du {exercice.debut:%d/%m/%Y} au {exercice.fin:%d/%m/%Y}", SOUS_TITRE)

    # Soldes de clôture par compte (formules liées aux journaux)
    _ecrire(ws, 5, 2, f"Soldes au {exercice.fin:%d/%m/%Y}", Style(gras=True, cadre=None))
    for i, compte in enumerate(comptes):
        _ecrire(ws, 6, 2 + i, compte.nom).alignment = ENTETE
        _ecrire(ws, 7, 2 + i, f"='{feuille_journaux}'!{soldes_cloture[compte.id]}", NORMAL, FORMAT_EUROS)
    col_total = 2 + len(comptes)
    _ecrire(ws, 6, col_total, "Total", GRAS).alignment = ENTETE
    somme = f"=SUM({_ref(2, 7)}:{_ref(col_total - 1, 7)})" if comptes else 0
    _ecrire(ws, 7, col_total, somme, Style(gras=True, couleur=VERT), FORMAT_EUROS)

    # Compte de résultat : catégories racines puis lignes « dont »
    _ecrire(ws, 9, 2, "Compte de résultat de l'exercice", Style(gras=True, cadre=None))
    refs_produits, refs_charges = [], []
    for i, (libelle, montant, est_produit, est_racine) in enumerate(entetes_categories):
        col = 2 + i
        _ecrire(ws, 10, col, libelle, Style(italique=not est_racine)).alignment = ENTETE
        _ecrire(ws, 11, col, montant / 100, Style(couleur=VERT if est_produit else ROUGE, italique=not est_racine), FORMAT_EUROS)
        if est_racine:
            (refs_produits if est_produit else refs_charges).append(_ref(col, 11))
    col_resultat = 2 + len(entetes_categories)
    produits = "+".join(refs_produits) or "0"
    charges = "+".join(refs_charges) or "0"
    _ecrire(ws, 10, col_resultat, "Résultat", GRAS).alignment = ENTETE
    _ecrire(ws, 11, col_resultat, f"=({produits})-({charges})", GRAS, FORMAT_VARIATION)

    # Totaux, alignés sous la colonne Résultat
    col_gains = max(2, col_resultat - 2)
    for decalage, (libelle, formule, couleur) in enumerate([
        ("Gains totaux", f"={produits}", VERT),
        ("Dépenses totales", f"={charges}", ROUGE),
    ]):
        _ecrire(ws, 13, col_gains + decalage, libelle, Style(gras=True, couleur=BLEU))
        _ecrire(ws, 14, col_gains + decalage, formule, Style(gras=True, couleur=couleur), FORMAT_EUROS)
    _ecrire(ws, 13, col_gains + 2, "Résultat", GRAS)
    _ecrire(ws, 14, col_gains + 2, f"={_ref(col_gains, 14)}-{_ref(col_gains + 1, 14)}", GRAS, FORMAT_VARIATION)

    # Cadres de signature
    milieu = 2 + max(2, (derniere_col - 1) // 2)
    for ligne, role in ((17, "président"), (20, "trésorier")):
        _fusionner(ws, ligne, 2, milieu - 1, f"Signature du {role} sortant", Style(alignement=CENTRE))
        _fusionner(ws, ligne, milieu, derniere_col, f"Signature du {role} entrant", Style(alignement=CENTRE))
        _fusionner(ws, ligne + 1, 2, milieu - 1, None, Style(alignement=CENTRE_HAUT))
        _fusionner(ws, ligne + 1, milieu, derniere_col, None, Style(alignement=CENTRE_HAUT))
        ws.row_dimensions[ligne + 1].height = 60

    ws.column_dimensions["A"].width = 3
    for col in range(2, derniere_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18
    for ligne in (6, 10):
        ws.row_dimensions[ligne].height = 30
    _mise_en_page(ws, 1, 1)


def exporter_bilan(chemin: str, nom_association: str, exercice: Exercice, comptes: list[Compte],
                   categories: list[Categorie], operations: list[Operation]):
    """Écrit le classeur complet de l'exercice dans `chemin`."""
    operations_exercice = [op for op in operations if exercice.contient(op.date)]
    wb = openpyxl.Workbook()
    journaux = wb.active
    soldes_cloture = _feuille_journaux(journaux, nom_association, exercice, comptes, operations)
    _feuille_resume(wb.create_sheet(), nom_association, exercice, comptes,
                    compte_resultat(categories, operations_exercice), soldes_cloture, journaux.title)
    wb.calculation.fullCalcOnLoad = True  # les formules sont calculées à l'ouverture
    wb.save(chemin)
