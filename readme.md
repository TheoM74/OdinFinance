# OdinFinance - Gestion de Trésorerie Associative

Logiciel de bureau multiplateforme (Windows et macOS) conçu pour la gestion comptable et la préparation des bilans financiers d'assemblées générales (AG) d'associations.

## Description du Projet

OdinFinance a été développé pour répondre aux exigences comptables et de gestion financière des associations. L'application centralise les flux financiers de chaque compte de trésorerie (compte courant, livret, caisses), garantit l'intégrité stricte des données via une base de données relationnelle, et génère le bilan financier présenté en AG au format du classeur Excel de l'association.

Pour les utilisateurs finaux, des exécutables autonomes pour Windows et macOS sont compilés et publiés automatiquement pour chaque version officielle via les GitHub Releases.

## Architecture Technique et Choix de Conception

* **Langage :** Python 3.10+
* **Interface graphique :** PyQt6, personnalisée par une feuille de style QSS commune (`resources/style.qss`) dont les jetons de couleur, de police et d'arrondi sont fournis par le thème actif (`views/theme.py`).
* **Base de données :** SQLite3 avec clés étrangères, contraintes de cohérence et migration automatique du schéma (`PRAGMA user_version`). Les montants sont stockés en centimes (entiers) pour éviter les erreurs d'arrondi.
* **Génération de rapports :** `openpyxl` pour l'export du bilan financier (journaux par compte + résumé signé), avec formules Excel recalculées à l'ouverture.
* **Architecture :** Modèle-Vue-Contrôleur (MVC). Les calculs (soldes, compte de résultat, journaux mensuels) sont isolés dans `services/`, sans dépendance à Qt, et couverts par des tests.

```
OdinFinance/
│
├── .github/workflows/ # Automatisation CI/CD pour les builds multiplateformes
├── controllers/       # Un contrôleur par écran (synthèse, journal, paramètres) + contrôleur principal
├── database/          # Connexion SQLite, schéma et migrations, requêtes, objets métier
├── services/          # Calculs du bilan, montants en centimes, export Excel
├── resources/         # Feuille de style QSS (gabarit) et polices embarquées
├── tests/             # Tests unitaires (unittest)
├── views/             # Écrans, composants, thèmes et icônes (PyQt6)
├── main.py            # Point d'entrée de l'application (multi-OS safe)
└── requirements.txt   # Dépendances du projet
```

## Fonctionnalités Principales

1. **Synthèse de l'exercice :**
   * Solde de chaque compte de trésorerie et total, à la date du jour (ou à la clôture d'un exercice terminé).
   * Compte de résultat en T : produits à gauche, charges à droite, avec le détail « dont … » des sous-catégories.
   * Filtres par mois, compte, catégorie et tiers.
2. **Journal des opérations :**
   * Trois types d'opération : recette, dépense et virement interne entre deux comptes (qui ne compte ni en produit ni en charge).
   * Saisie enchaînée (la date et le compte restent remplis), modification par double-clic ou touche Entrée, suppression confirmée (touche Suppr).
   * Recherche plein texte (Ctrl+F), filtre par compte, tri sur chaque colonne, montants signés et colorés.
3. **Paramètres :**
   * Nom de l'association et dates de l'exercice (par exemple d'avril à mars).
   * Comptes de trésorerie (numéro, nom, solde initial), catégories et sous-catégories, tiers.
   * Suppressions protégées : un compte ou une catégorie utilisés ne peuvent pas être supprimés, avec un message qui explique quoi faire.
4. **Erreurs en ligne :**
   * Chaque champ invalide est signalé sous le champ, avec la correction attendue, sans fenêtre bloquante.
5. **Export du bilan financier (Ctrl+E) :**
   * Feuille « Bilan financier » : un journal par compte (Débit / Crédit), sous-totaux, solde et variation de chaque mois, total de l'exercice ; un compte par page à l'impression.
   * Feuille « Résumé financier » : soldes de clôture, compte de résultat par catégorie, gains, dépenses et résultat, cadres de signature des présidents et trésoriers sortants et entrants.
6. **Deux thèmes (Ctrl+T) :**
   * **Cyberpunk** : identité du portfolio (palette du thème VS Code « Cyberpunk 2077 », polices Cyberpunk, Oxanium et Blender Pro, coins coupés, trame de fond).
   * **Classique** : thème clair et sobre, police du système, accent bleu du bilan Excel.
   * Le choix est mémorisé, comme la taille de la fenêtre et le dernier écran ouvert.

Raccourcis : Ctrl+1 / Ctrl+2 / Ctrl+3 pour changer d'écran, Échap pour annuler une modification.

## Données

La base `tresorerie.db` est enregistrée dans le dossier de données de l'utilisateur (et plus dans le dossier de l'application, qui est remplacé à chaque mise à jour) :

* Windows : `%APPDATA%\OdinFinance\OdinFinance\tresorerie.db`
* macOS : `~/Library/Application Support/OdinFinance/OdinFinance/tresorerie.db`

Au premier lancement, une base 1.x trouvée à l'ancien emplacement y est copiée puis migrée (montants en centimes, opérations rattachées à un compte « Compte courant »). Le chemin exact et un bouton « Ouvrir le dossier » se trouvent dans Paramètres : copier ce fichier suffit à sauvegarder la trésorerie.

## Automatisation et Déploiement

Le projet intègre un pipeline d'intégration continue via GitHub Actions (`.github/workflows/build.yml`). Lors de la publication d'un tag de version (`v*`), les serveurs de build compilent simultanément l'application pour Windows et macOS afin de générer les paquets de distribution autonomes. Le dossier `resources/` (style et polices) est embarqué dans l'exécutable.

## Instructions de Développement

Pour configurer l'environnement de développement local et lancer l'application :

### 1. Cloner le dépôt et se placer dans le répertoire
```bash
git clone https://github.com/votre-nom-utilisateur/OdinFinance.git
cd OdinFinance
```

### 2. Créer l'environnement virtuel et installer les dépendances

* **Sous macOS / Linux :**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

* **Sous Windows (PowerShell) :**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate
  pip install -r requirements.txt
  ```

### 3. Lancer l'application
```bash
python main.py
```

### 4. Lancer les tests
```bash
python -m unittest discover -s tests -t .
```

## Polices

Les polices du thème Cyberpunk sont celles du portfolio : Oxanium (licence SIL Open Font), Cyberpunk et Blender Pro. Oxanium a été converti en trois graisses statiques (Regular, SemiBold, Bold) dont l'ascendante a été relevée pour que Qt n'écrête pas les capitales accentuées. Vérifier les licences de Cyberpunk et Blender Pro avant toute redistribution publique.

---

*Projet développé par Théo Mauhin (B.U.T. Informatique, IUT d'Annecy) en collaboration avec l'assistant IA Gemini (Gemini 3 Flash, Paid tier).*
