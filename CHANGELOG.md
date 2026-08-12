# Changelog — Finance (11-finance)

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [Non publié]

### Prototype 4 — Sprint 10 — Export des données (clôture)

- Service `export_service` (CSV / JSON, format `finance-export-v1`)
- Exports : utilisateurs, wallets, bénéficiaires, virements, paiements, remboursements, historique, événements
- Pages `/administration/exports/` + téléchargement
- API `GET /api/administration/exports/`
- 121 tests pytest
- **Clôture de l'application 11-finance**

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
