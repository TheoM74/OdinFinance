import unittest
from datetime import date

from database.modeles import DEPENSE, RECETTE, Categorie, Compte, Operation
from services.bilan import Exercice, compte_resultat, journal_compte, solde_compte
from services.montants import formater_montant, formater_saisie, parser_montant, parser_montant_signe

NBSP = "\u00a0"


def operation(id, jour, montant, compte_id=1, categorie_id=None, type_flux=None, destination=None):
    return Operation(id=id, date=date.fromisoformat(jour), libelle=f"op {id}", montant=montant, reference=None,
                     compte_id=compte_id, compte_nom="", categorie_id=categorie_id, type_flux=type_flux,
                     compte_destination_id=destination)


class TestMontants(unittest.TestCase):
    def test_parser_formats_francais(self):
        self.assertEqual(parser_montant("45"), 4500)
        self.assertEqual(parser_montant("45,9"), 4590)
        self.assertEqual(parser_montant("1 234,56 €"), 123456)
        self.assertEqual(parser_montant("0.01"), 1)

    def test_parser_refuse_les_saisies_invalides(self):
        for saisie in ("", "abc", "0", "-5", "1,234", "1e3x"):
            with self.subTest(saisie=saisie), self.assertRaises(ValueError):
                parser_montant(saisie)

    def test_parser_signe_accepte_zero_et_negatif(self):
        self.assertEqual(parser_montant_signe(""), 0)
        self.assertEqual(parser_montant_signe("0"), 0)
        self.assertEqual(parser_montant_signe("-12,50"), -1250)

    def test_formater(self):
        self.assertEqual(formater_montant(123456), f"1{NBSP}234,56{NBSP}€")
        self.assertEqual(formater_montant(-970), f"−9,70{NBSP}€")
        self.assertEqual(formater_montant(500, signe=True), f"+5,00{NBSP}€")
        self.assertEqual(formater_saisie(123456), "1234,56")


class TestBilan(unittest.TestCase):
    def setUp(self):
        self.exercice = Exercice(date(2025, 4, 1), date(2026, 3, 31))
        self.courant = Compte(1, "512", "Compte courant", 179093)
        self.livret = Compte(2, "507", "Livret A", 0)
        self.categories = [
            Categorie(10, "Ventes", RECETTE), Categorie(11, "Adhésions", RECETTE, 10),
            Categorie(20, "Achats", DEPENSE), Categorie(21, "Sorties", DEPENSE, 20),
        ]
        self.operations = [
            operation(1, "2025-03-15", 1000, categorie_id=10, type_flux=RECETTE),  # avant l'exercice
            operation(2, "2025-05-07", 1300, categorie_id=10, type_flux=RECETTE),
            operation(3, "2025-05-09", 3700, categorie_id=20, type_flux=DEPENSE),
            operation(4, "2025-09-20", 63000, categorie_id=11, type_flux=RECETTE),
            operation(5, "2026-02-02", 100000, destination=2),  # virement vers le livret
            operation(6, "2026-03-09", 64980, categorie_id=21, type_flux=DEPENSE),
        ]

    def test_exercice(self):
        self.assertEqual(self.exercice.annee, 2026)
        self.assertEqual(len(self.exercice.mois()), 12)
        self.assertEqual(Exercice.par_defaut(date(2026, 2, 1)), self.exercice)
        self.assertEqual(Exercice.par_defaut(date(2026, 4, 1)).debut, date(2026, 4, 1))

    def test_virement_deplace_l_argent_sans_resultat(self):
        self.assertEqual(solde_compte(self.livret, self.operations), 100000)
        resultat = compte_resultat(self.categories, [op for op in self.operations if self.exercice.contient(op.date)])
        self.assertEqual(resultat.total_produits, 1300 + 63000)
        self.assertEqual(resultat.total_charges, 3700 + 64980)

    def test_soldes(self):
        total = 179093 + 1000 + 1300 - 3700 + 63000 - 100000 - 64980
        self.assertEqual(solde_compte(self.courant, self.operations), total)
        self.assertEqual(solde_compte(self.courant, self.operations, avant=date(2025, 4, 1)), 180093)
        self.assertEqual(solde_compte(self.courant, self.operations, jusqu_au=date(2025, 5, 7)), 181393)

    def test_compte_resultat_avec_lignes_dont(self):
        resultat = compte_resultat(self.categories, self.operations[1:])
        ventes = resultat.produits[0]
        self.assertEqual((ventes.categorie.nom, ventes.total), ("Ventes", 64300))
        self.assertEqual([(c.nom, m) for c, m in ventes.sous_lignes], [("Adhésions", 63000)])
        self.assertEqual(resultat.resultat, 64300 - 68680)

    def test_journal_par_mois(self):
        journal = journal_compte(self.courant, self.operations, self.exercice)
        self.assertEqual(journal.solde_ouverture, 180093)
        self.assertEqual(journal.date_ouverture, date(2025, 3, 31))
        self.assertEqual([(m.annee, m.mois) for m in journal.mois], [(2025, 5), (2025, 9), (2026, 2), (2026, 3)])
        mai = journal.mois[0]
        self.assertEqual((mai.total_debit, mai.total_credit, mai.solde_fin), (1300, 3700, 177693))
        self.assertEqual(journal.mois[-1].solde_fin, solde_compte(self.courant, self.operations))
        livret = journal_compte(self.livret, self.operations, self.exercice)
        self.assertTrue(livret.mois[0].lignes[0].debit)


if __name__ == "__main__":
    unittest.main()
