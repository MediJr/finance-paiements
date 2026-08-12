# Rapport technique — Sprint 1 — Utilisateurs + Wallet

**Application** : 11-finance (Plateforme de paiements numériques)  
**Prototype** : 1  
**Date** : 6 août 2026  
**Statut** : Terminé — en attente de validation

---

## 1. Résumé technique

Le Sprint 1 introduit les premiers objets métier : l'utilisateur de plateforme et son Wallet.

L'authentification Django du Sprint 0 est conservée. Un modèle `Utilisateur` (OneToOne) porte l'identité métier. Chaque utilisateur reçoit automatiquement un unique Wallet au solde initial `0.00`, sans aucune opération financière.

---

## 2. Fonctionnalités développées

- Création / consultation des utilisateurs métier
- Création automatique d'un Wallet par utilisateur
- Consultation web des utilisateurs et du Wallet
- API REST en lecture seule
- Administration Django (consultation)

Hors périmètre respecté : paiements, virements, bénéficiaires, historique, analytics, SIEM.

---

## 3. Architecture retenue

```text
Vue / API  →  services métier  →  modèles ORM
                │
                ├── utilisateur_service
                └── wallet_service (+ signal post_save)
```

---

## 4. Modèles créés

### `accounts.Utilisateur`

- `user` (OneToOne → User)
- `prenom`, `nom`, `email`, `telephone`
- `est_actif`
- `date_creation`, `date_mise_a_jour`

### `wallets.Wallet`

- `utilisateur` (OneToOne)
- `solde` (≥ 0, défaut 0.00)
- `devise` (défaut EUR)
- `statut` (actif / inactif)
- `date_creation`, `date_mise_a_jour`

---

## 5. Services créés

| Service | Fonctions |
|---------|-----------|
| `accounts.services.utilisateur_service` | `create_utilisateur`, `list_utilisateurs`, `get_utilisateur` |
| `wallets.services.wallet_service` | `create_wallet_for_utilisateur`, `get_wallet`, `get_wallet_for_utilisateur` |

---

## 6. Vues créées

| Vue | URL |
|-----|-----|
| Liste utilisateurs | `/utilisateurs/` |
| Détail utilisateur | `/utilisateurs/<id>/` |
| Détail Wallet | `/wallets/<id>/` |

---

## 7. API créées

| Méthode | Endpoint |
|---------|----------|
| GET | `/api/utilisateurs/` |
| GET | `/api/utilisateurs/<id>/` |
| GET | `/api/utilisateurs/<id>/wallet/` |
| GET | `/api/wallets/<id>/` |

---

## 8. Templates créés

- `frontend/templates/base.html`
- `frontend/templates/accounts/utilisateur_list.html`
- `frontend/templates/accounts/utilisateur_detail.html`
- `frontend/templates/wallets/wallet_detail.html`
- `frontend/static/css/base.css`

---

## 9. Migrations

| Migration | Contenu |
|-----------|---------|
| `accounts/migrations/0001_initial.py` | Modèle Utilisateur |
| `wallets/migrations/0001_initial.py` | Modèle Wallet |

---

## 10. Fichiers créés / modifiés

### Créés

- `accounts/` (models, services, views, urls, admin, signals, migrations)
- `wallets/` (models, services, views, urls, admin, migrations)
- `api/serializers.py`
- templates + CSS
- `tests/test_utilisateurs_wallets.py`
- `docs/utilisateurs-wallets.md`
- `livrables/Sprint-01/rapport-technique.md`

### Modifiés

- `backend/config/settings/base.py`
- `backend/config/urls.py`
- `api/views.py`, `api/urls.py`
- `tests/conftest.py`, `tests/test_configuration.py`
- `README.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/README.md`

---

## 11. Tests réalisés

Couverture principale :

- création utilisateur + Wallet automatique
- unicité Wallet / solde initial
- refus Wallet sans utilisateur
- API authentifiée
- pages web
- admin consultation

### Résultats

```
21 passed in 6.11s
```

**Résultat** : OK — 21/21 tests passés  
`manage.py check` : OK

---

## 12. Difficultés rencontrées

1. **Double déclenchement** (service + signal) — résolu par `get_or_create` idempotent dans `wallet_service`.
2. **Locale fr-fr** — affichage du solde `0,00` dans les templates (tests adaptés).
3. **PostgreSQL local indisponible** — migrations générées malgré l'absence du démon Docker ; tests exécutés sur SQLite mémoire.

---

## 13. Recommandations pour le Sprint 2

1. Introduire les premières opérations financières uniquement si demandées (crédit/débit contrôlés)
2. Ajouter une authentification web dédiée (hors admin) si le sprint le prévoit
3. Renforcer les contrôles d'autorisation (propriétaire vs administrateur)
4. Prévoir un journal d'audit des mouvements de solde dès qu'ils existeront

---

## 14. Proposition de message de commit Git

```
feat(finance): utilisateurs et wallet — Prototype 1 Sprint 1
```

**Note** : aucun commit n'a été créé. En attente de validation.

---

**Fin du rapport — Sprint 1**
