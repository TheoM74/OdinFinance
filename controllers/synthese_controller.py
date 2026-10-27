from datetime import date

from controllers.commun import options_categories, remplir_combo
from services.bilan import compte_resultat, soldes_par_compte
from services.montants import nom_mois


class SyntheseController:
    def __init__(self, principal):
        self.principal = principal
        self.vue = principal.view.page_synthese
        self.donnees = None
        self.filtres = (self.vue.filtre_periode, self.vue.filtre_compte, self.vue.filtre_categorie, self.vue.filtre_tiers)
        for combo in self.filtres:
            combo.currentIndexChanged.connect(self.actualiser)
        self.vue.btn_reinitialiser.clicked.connect(self.reinitialiser_filtres)

    def rafraichir(self, donnees):
        self.donnees = donnees
        d, v = donnees, self.vue
        remplir_combo(v.filtre_periode, [(nom_mois(a, m).capitalize(), (a, m)) for a, m in d.exercice.mois()],
                      "Tout l'exercice")
        remplir_combo(v.filtre_compte, [(c.nom, c.id) for c in d.comptes], "Tous les comptes")
        remplir_combo(v.filtre_categorie, options_categories(d.categories), "Toutes les catégories")
        remplir_combo(v.filtre_tiers, [(t.nom, t.id) for t in d.tiers], "Tous les tiers")
        self.actualiser()

    def reinitialiser_filtres(self):
        for combo in self.filtres:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.actualiser()

    def actualiser(self):
        d, v = self.donnees, self.vue
        ex = d.exercice
        periode, compte_id, categorie_id, tier_id = (c.currentData() for c in self.filtres)
        filtre_actif = any(x is not None for x in (periode, compte_id, categorie_id, tier_id))

        sous_categories = {c.id for c in d.categories if c.parent_id == categorie_id}
        operations = [
            op for op in d.operations
            if ex.contient(op.date)
            and (periode is None or (op.date.year, op.date.month) == periode)
            and (compte_id is None or op.compte_id == compte_id)
            and (categorie_id is None or op.categorie_id == categorie_id or op.categorie_id in sous_categories)
            and (tier_id is None or op.tier_id == tier_id)
        ]
        resultat = compte_resultat(d.categories, operations, garder_vides=not filtre_actif)
        v.table_produits.afficher(resultat.produits, resultat.total_produits)
        v.table_charges.afficher(resultat.charges, resultat.total_charges)
        v.afficher_resultat(resultat.total_produits, resultat.total_charges, resultat.resultat)
        v.btn_reinitialiser.setEnabled(filtre_actif)
        v.label_periode.setText(f"du {ex.debut:%d/%m/%Y} au {ex.fin:%d/%m/%Y}")

        # Soldes : à la date du jour pendant l'exercice, sinon à sa clôture
        aujourd_hui = date.today()
        date_soldes = ex.fin if aujourd_hui > ex.fin else aujourd_hui
        soldes = soldes_par_compte(d.comptes, d.operations, jusqu_au=date_soldes)
        v.afficher_soldes([(c.nom, s) for c, s in soldes], sum(s for _, s in soldes),
                          f"Soldes au {date_soldes:%d/%m/%Y}")
