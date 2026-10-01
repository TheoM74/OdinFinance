# OdinFinance - Gestion de Trésorerie Associative

Logiciel de bureau multiplateforme (Windows et macOS) conçu pour la gestion comptable et la préparation des bilans financiers d'assemblées générales (AG) d'associations.

## Description du Projet

OdinFinance a été développé pour répondre aux exigences comptables et de gestion financière des associations. L'application centralise les flux financiers, garantit l'intégrité stricte des données via une base de données relationnelle, et automatise la génération de rapports financiers conformes aux normes des assemblées générales.

Pour les utilisateurs finaux, des exécutables autonomes pour Windows et macOS sont compilés et publiés automatiquement pour chaque version officielle via les GitHub Releases.

## Architecture Technique et Choix de Conception

* **Langage :** Python 3.10+
* **Interface graphique :** PyQt6, personnalisée via des feuilles de style QSS (Flat Design, design system isolé dans `resources/style.qss`).
* **Base de données :** SQLite3 avec gestion des contraintes d'intégrité et des clés étrangères.
* **Génération de rapports :** `openpyxl` pour l'exportation de comptes de résultat officiels en tableau en T (charges à gauche, produits à droite, équilibrage par le résultat de l'exercice).
* **Architecture :** Modèle-Vue-Contrôleur (MVC) strict assurant la séparation entre la logique métier, l'accès aux données et l'interface utilisateur.

```
OdinFinance/
│
├── .github/workflows/ # Automatisation CI/CD pour les builds multiplateformes
├── controllers/       # Logique de contrôle et gestion des signaux I/O
├── database/          # Connexion SQLite et requêtes SQL optimisées
├── resources/         # Feuilles de style QSS globales (Flat Design)
├── views/             # Composants d'interface graphique (PyQt6)
├── main.py            # Point d'entrée de l'application (multi-OS safe)
└── requirements.txt   # Dépendances du projet
```

## Fonctionnalités Principales

1. **Tableau de Bord & Synthèse Analytique :**
   * Page d'accueil centrée sur les indicateurs clés (Total Produits, Total Charges, Résultat Net).
   * Filtres multicritères en temps réel par mois, par catégorie de flux et par tiers.
2. **Gestion des Transactions (CRUD Complet) :**
   * Enregistrement, modification interactive (chargement automatique du formulaire par sélection de ligne) et suppression sécurisée des flux financiers.
   * Gestion dynamique des catégories (recettes/dépenses) et des tiers (moraux/physiques) avec protection relationnelle contre les données orphelines.
3. **Gestion des Erreurs Inline :**
   * Validation des formulaires en temps réel avec feedback visuel ciblé (surbrillance rouge des champs incorrects et messages contextuels associés), évitant les interruptions par popups bloquantes.
4. **Exportation Comptable Officielle :**
   * Génération automatisée de tableurs Excel `.xlsx` structurés selon les exigences légales des comptes de résultat d'association.

## Automatisation et Déploiement

Le projet intègre un pipeline d'intégration continue via GitHub Actions (`.github/workflows/build.yml`). Lors de la publication d'un tag de version (`v*`), les serveurs de build compilent simultanément l'application pour Windows et macOS afin de générer les paquets de distribution autonomes.

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

---

*Projet développé par Théo Mauhin (B.U.T. Informatique, IUT d'Annecy) en collaboration avec l'assistant IA Gemini (Gemini 3 Flash, Paid tier).*