# Changelog — Finance Paiements

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versionnement [sémantique](https://semver.org/lang/fr/).

## [1.1.0] — Prototype 5 / Sprint 11 — Audit de sécurité et durcissement — 22 octobre 2026

### Sécurité

- **F1** Bénéficiaire ajouté par e-mail exact : l'API n'accepte plus d'identifiant
  séquentiel et le formulaire web ne liste plus les clients (annuaire non énumérable).
- **F4** Clés d'idempotence sur virements, paiements et alimentations (champ caché,
  en-tête `Idempotency-Key`, contrainte d'unicité) : plus de double débit.
- **F5** Plafond journalier cumulé des sorties (`plafond_journalier`).
- **F6** Montants : 2 décimales maximum, valeurs finies, borne technique.
- **F7** Neutralisation des formules dans les exports CSV.
- **F8** Blocage temporaire après échecs de connexion ; CSRF imposé à l'API
  d'authentification ; redirection `next` validée ; déconnexion en POST.
- **F9** `X-Forwarded-For` ignoré sauf `TRUST_X_FORWARDED_FOR=True`.
- **F10** `DEBUG=False` par défaut, `settings/production.py` (HTTPS, HSTS, cookies
  sécurisés, clé secrète obligatoire), en-têtes de sécurité, Dockerfile non-root,
  Gunicorn, WhiteNoise.

### Ajouté

- **F2** Espace client : inscription, connexion, déconnexion (web + API), page
  « Mon espace » ; le site `/admin/` reste réservé au personnel.
- **F3** Alimentation du portefeuille par carte via une passerelle simulée côté
  serveur (modèle `Alimentation`, paramètre `montant_alimentation_max`).
- `config.settings.local` (SQLite), `config.settings.test_postgres`, commande
  `creer_comptes_demo`, `docker-compose.prod.yml`.
- Intégration continue GitHub Actions (tests, couverture ≥ 80 %, migrations,
  `check --deploy`, suite complète sur PostgreSQL).
- 48 tests (`tests/test_durcissement.py`) — **169** au total, couverture 86 %.
- Documentation : cahier des charges, cycle de vie, backlog, architecture,
  sécurité, stratégie de test, alimentation, guide de démonstration, rapport LaTeX.

### Modifié

- **F11** Produit renommé « Finance Paiements » ; fichiers source en double
  interligne normalisés.

### Migrations

- `administration.0003_plafonds_journalier_alimentation`
- `wallets.0002_alimentation`
- `virements.0002_cle_idempotence`, `paiements.0002_cle_idempotence`

## [1.0.0] — Prototypes 1 à 4 / Sprints 0 à 10 — août 2026

### Prototype 4 — Sprint 10 — Export des données (clôture)

- Service `export_service` (CSV / JSON, format `finance-export-v1`)
- Exports : utilisateurs, wallets, bénéficiaires, virements, paiements, remboursements, historique, événements
- Pages `/administration/exports/` + téléchargement
- API `GET /api/administration/exports/`
- 121 tests pytest
- Clôture de la feuille de route initiale

### Prototype 4 — Sprint 9 — Observabilité

- App `observabilite` + modèle `Evenement` (immuable)
- `journal_service` : unique point d'écriture
- Instrumentation métier (utilisateurs, wallets, bénéficiaires, virements, paiements, remboursements, admin)
- Middleware erreurs HTTP 500
- API/web admin lecture seule + filtres
- Migration `observabilite.0001_evenement`
- 112 tests pytest

### Prototype 3 — Sprint 8 — Tableaux de bord, statistiques et rapports

- Services `dashboard_service`, `statistiques_service`, `rapport_service`
- Pages web `/administration/dashboard|statistiques|rapports/`
- API `GET /api/administration/dashboard|statistiques|rapports/`
- Filtres période / statut / utilisateur (admin)
- Accès exclusivement administrateur
- 103 tests pytest

### Prototype 3 — Sprint 7 — Security by Design

- Scoping propriétaire utilisateurs / wallets / historique (API + web)
- Vision globale réservée aux administrateurs (`is_staff`)
- Application réelle des paramètres : plafonds, maintenance, session, devise
- Service `securite_service` (validations centralisées)
- Middleware `SecurityParametresMiddleware`
- Journal `JournalAdministration` + page `/administration/journal/`
- Migration `administration.0002_journaladministration`
- 92 tests pytest

### Prototype 3 — Sprint 6 — Administration et paramètres

- Module `administration` + modèle `ParametresApplication`
- Services de supervision (utilisateurs, wallets, opérations)
- Activation / désactivation utilisateurs (sans édition métier)
- Pages web `/administration/…`
- API `/api/administration/…` (staff only)
- Migration `administration.0001_initial`
- 80 tests pytest

### Prototype 2 — Sprint 5 — Paiements et remboursements

- Modèles `Paiement` et `Remboursement`
- Services `paiement_service` / `remboursement_service`
- Factorisation `wallets.services.mouvement_service` (réutilisé par virements)
- Historique automatique (`paiement` / `remboursement`)
- Pages web + API POST/GET
- Admin consultation seule
- Migration `paiements.0001_initial`
- 72 tests pytest

### Prototype 2 — Sprint 4 — Virements

- Modèle `Virement` (référence unique, wallets, montant, statut)
- Service `virement_service.executer_virement` (transaction atomique)
- Débit / crédit des Wallets + historique automatique
- Validations : solde, bénéficiaire, wallets actifs, auto-virement
- Pages web : liste, détail, formulaire
- API : POST/GET `/api/virements/`
- Admin : consultation seule
- Migration `virements.0001_initial`
- 59 tests pytest

### Prototype 2 — Sprint 3 — Gestion des bénéficiaires

- Modèle `Beneficiaire` (propriétaire → destinataire, alias, statut)
- Service `beneficiaire_service` (création, consultation, modification, désactivation)
- Contrôle d'accès : un utilisateur ne gère que ses propres bénéficiaires
- Pages web : liste, détail, création, modification
- API REST : GET/POST/PUT/PATCH/DELETE (DELETE = désactivation logique)
- Admin Django : consultation, recherche, filtrage, activation/désactivation
- Migration `beneficiaires.0001_initial`
- 44 tests pytest
- Aucune opération financière, aucun impact sur les soldes

### Prototype 1 — Sprint 2 — Historique des opérations

- Modèle `HistoriqueOperation` (lié à un Wallet, référence unique)
- Service `historique_service` (création interne, consultation, filtres)
- Pages web : liste filtrable et détail
- API REST lecture seule : `/api/historique/`, `/api/wallets/<id>/historique/`
- Admin Django : consultation uniquement (pas d'ajout / modification / suppression)
- Migration `historique.0001_initial`
- 32 tests pytest
- Aucune modification de solde, aucune opération financière réelle

### Prototype 1 — Sprint 1 — Utilisateurs + Wallet

- Modèle métier `Utilisateur` (OneToOne avec `User` Django)
- Modèle `Wallet` (OneToOne, solde initial 0, devise EUR)
- Services `utilisateur_service` et `wallet_service`
- Création automatique du Wallet à la création d'un utilisateur
- Pages web : liste / détail utilisateurs, consultation Wallet
- API REST lecture seule : utilisateurs et wallets
- Admin Django : consultation utilisateurs et Wallets
- Migrations `accounts.0001_initial`, `wallets.0001_initial`
- 21 tests pytest

### Prototype 1 — Sprint 0 — Initialisation

- Structure Django MTV (`backend/config`, `api`, `frontend`)
- Configuration PostgreSQL via variables d'environnement
- Docker Compose (PostgreSQL 16 + Django)
- Django REST Framework configuré (aucun endpoint métier)
- Authentification Django standard (pas de modèle utilisateur personnalisé)
- Logging de base
- Suite pytest (tests de configuration)
- Documentation technique initiale (`docs/`)
