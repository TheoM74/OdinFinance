# OdinFinance - Gestion de Trésorerie Associative

Logiciel de bureau multiplateforme (Windows, macOS et Linux) conçu pour la gestion comptable et la préparation des bilans financiers d'assemblées générales (AG) d'associations.

## Description du Projet

OdinFinance a été développé pour répondre aux exigences comptables et de gestion financière des associations. L'application centralise les flux financiers de chaque compte de trésorerie (compte courant, livret, caisses), garantit l'intégrité stricte des données via une base de données relationnelle, et génère le bilan financier présenté en AG au format du classeur Excel de l'association.

Pour les utilisateurs finaux, des exécutables autonomes pour Windows, macOS et Linux sont compilés et publiés automatiquement pour chaque version officielle via les GitHub Releases.

## Téléchargement et installation

Télécharger l'archive de son système dans la [dernière Release](https://github.com/TheoM74/OdinFinance/releases/latest). Python n'est pas nécessaire.

* **Windows** (`OdinFinance-Windows.zip`) : extraire l'archive, puis lancer `OdinFinance\OdinFinance.exe`. Au premier lancement, Windows SmartScreen peut afficher « Windows a protégé votre ordinateur » : cliquer sur « Informations complémentaires » puis « Exécuter quand même » (l'application n'est pas signée).
* **macOS** (`OdinFinance-macOS.zip`, Mac à puce Apple M1 ou plus récent) : extraire l'archive et glisser `OdinFinance.app` dans Applications. L'application n'étant pas signée, faire au premier lancement un clic droit sur l'application puis « Ouvrir », ou autoriser l'ouverture dans Réglages Système > Confidentialité et sécurité.
* **Linux** (`OdinFinance-Linux.tar.gz`, distributions récentes en x86_64 : Ubuntu 22.04 ou plus récent, Debian 12, Fedora…) :
  ```bash
  mkdir OdinFinance && tar -xzf OdinFinance-Linux.tar.gz -C OdinFinance
  ./OdinFinance/OdinFinance/OdinFinance
  ```
  Si le message « could not load the Qt platform plugin "xcb" » apparaît, installer la bibliothèque manquante (Ubuntu / Debian : `sudo apt install libxcb-cursor0`).

Les données d'une version précédente sont reprises automatiquement (voir [Données](#données)).

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
* Linux : `~/.local/share/OdinFinance/OdinFinance/tresorerie.db`

Le chemin exact et un bouton « Ouvrir le dossier » se trouvent dans Paramètres : copier ce fichier suffit à sauvegarder la trésorerie.

**Reprendre les données de la version 1 :** la version 1 enregistrait sa base dans le dossier de l'application (sous Windows : `OdinFinance\_internal\tresorerie.db`). Dans Paramètres > Données, « Importer une base… » permet de choisir ce fichier : il est converti automatiquement (montants en centimes, opérations rattachées à un compte « Compte courant ») et les données présentes avant l'import sont sauvegardées à côté. Si la version 2 est extraite par-dessus le dossier de la version 1, la reprise est automatique au premier lancement.

## Automatisation et Déploiement

Le projet intègre un pipeline d'intégration continue via GitHub Actions (`.github/workflows/build.yml`). À chaque envoi sur `main`, l'application est compilée avec PyInstaller sous Windows, macOS et Linux, les tests unitaires sont lancés, puis chaque exécutable compilé est vérifié par `OdinFinance --autotest` (interface construite dans les deux thèmes, saisie d'opérations et export d'un bilan, dans un dossier temporaire). Lors de la publication d'un tag de version (`v*`), une seule Release est créée avec les trois archives et les notes de version du dossier `notes-de-version/`. Le dossier `resources/` (style et polices) est embarqué dans l'exécutable.

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

## Collaborateurs

* **Théo Mauhin** (B.U.T. Informatique, IUT d'Annecy) : auteur du projet, conception et besoins de la trésorerie du BDE ODIN.
* **Gemini** (Google, Gemini 3 Flash) : assistant IA, collaboration sur la version 1 (application initiale, base de données, export et pipeline de build).
* **Claude** (Anthropic, Claude Opus 5.5) : assistant IA, collaboration sur la version 2 (comptes et virements, export au format du bilan de l'association, thèmes Cyberpunk et classique, refonte de l'interface, tests et build Linux).
