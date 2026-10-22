# API REST

Préfixe `/api/`. Authentification par **session Django** (cookie). Les requêtes
`POST`, `PUT`, `PATCH` et `DELETE` exigent l'en-tête `X-CSRFToken` (jeton fourni
par `GET /api/auth/csrf/`). Réponses JSON ; erreurs de validation en `400`,
accès refusé en `403`, ressource d'un autre client en `404`.

**Idempotence** : pour `POST /api/virements/`, `/api/paiements/` et
`/api/alimentations/`, envoyer un en-tête `Idempotency-Key` unique par opération.
Un renvoi avec la même clé renvoie l'opération existante (`200`) sans nouveau
mouvement de fonds.

## Authentification

| Endpoint | Description |
|----------|-------------|
| `GET /api/auth/csrf/` | Jeton CSRF |
| `POST /api/auth/inscription/` | Création de compte (portefeuille ouvert à 0 EUR) |
| `POST /api/auth/connexion/` | Ouverture de session (blocage après échecs répétés) |
| `POST /api/auth/deconnexion/` | Fermeture de session |

## Client (données du client connecté uniquement)

| Endpoint | Description |
|----------|-------------|
| `GET, POST /api/alimentations/` | Alimentations par carte `{montant, numero_carte}` — `201` acceptée, `402` refusée |
| `GET /api/utilisateurs/`, `GET /api/utilisateurs/<id>/` | Son profil |
| `GET /api/utilisateurs/<id>/wallet/`, `GET /api/wallets/<id>/` | Son portefeuille |
| `GET /api/historique/`, `GET /api/historique/<id>/` | Historique (filtres `type`, `statut`, `date_debut`, `date_fin`, `reference`) |
| `GET /api/wallets/<id>/historique/` | Historique d'un portefeuille |
| `GET, POST /api/beneficiaires/` | Bénéficiaires — création `{email, alias?}` |
| `GET, PUT, PATCH, DELETE /api/beneficiaires/<id>/` | Détail, modification, désactivation logique |
| `GET, POST /api/virements/` | Virements — `{beneficiaire_id, montant, motif?}` |
| `GET /api/virements/<id>/` | Détail |
| `GET, POST /api/paiements/` | Paiements — `{beneficiaire_id, montant, motif?}` |
| `GET /api/paiements/<id>/` | Détail |
| `GET, POST /api/remboursements/` | Remboursements — `{paiement_id, montant?}` |
| `GET /api/remboursements/<id>/` | Détail |

## Administration (personnel uniquement)

| Endpoint | Description |
|----------|-------------|
| `GET, PUT, PATCH /api/administration/parametres/` | Paramètres (plafonds, maintenance, devise, session) |
| `GET /api/administration/utilisateurs/` | Utilisateurs |
| `GET /api/administration/wallets/` | Portefeuilles |
| `GET /api/administration/operations/` | Opérations |
| `GET /api/administration/dashboard/` | Indicateurs |
| `GET /api/administration/statistiques/` | Statistiques filtrables |
| `GET /api/administration/rapports/` | Rapports |
| `GET /api/administration/evenements/`, `GET /api/administration/evenements/<id>/` | Journal d'événements |
| `GET /api/administration/exports/?type=…&export_format=json\|csv` | Exports |
