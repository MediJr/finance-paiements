# Rapport technique — Sprint 2 — Historique des opérations

**Application** : 11-finance (Plateforme de paiements numériques)  
**Prototype** : 1  
**Date** : 6 août 2026  
**Statut** : Terminé — en attente de validation

---

## 1. Résumé technique

Le Sprint 2 prépare le socle d'historique des opérations financières futures.

Un modèle générique `HistoriqueOperation` enregistre les événements liés à un Wallet. Les services centralisent la consultation et le filtrage. Aucune transaction financière n'est exécutée et aucun solde n'est modifié.

---

## 2. Fonctionnalités développées

- Enregistrement d'événements d'historique (service interne)
- Consultation web et API (liste, détail, filtres)
- Historique par Wallet
- Administration Django en lecture seule

Hors périmètre respecté : paiements, virements, remboursements, bénéficiaires, analytics, SIEM.

---

## 3. Architecture retenue

```text
Vue / API  →  historique_service  →  HistoriqueOperation
                                      └── FK Wallet (PROTECT)
```

---

## 4. Modèles créés

### `historique.HistoriqueOperation`

- `wallet` (FK)
- `type_operation` (credit, debit, virement, paiement, remboursement, autre)
- `statut` (enregistree, en_cours, reussie, echouee, annulee)
- `description`, `montant` (optionnel), `devise`
- `reference` (unique)
- `date_creation`, `date_mise_a_jour`

---

## 5. Services créés

| Service | Fonctions |
|---------|-----------|
| `historique.services.historique_service` | `create_historique_operation`, `list_historique_operations`, `get_historique_operation` |

Filtres : wallet, type, statut, période, référence.

---

## 6. Vues créées

| Vue | URL |
|-----|-----|
| Liste historique | `/historique/` |
| Détail opération | `/historique/<id>/` |

---

## 7. API créées

| Méthode | Endpoint |
|---------|----------|
| GET | `/api/historique/` |
| GET | `/api/historique/<id>/` |
| GET | `/api/wallets/<id>/historique/` |

Aucune création via l'API (`POST` → 405).

---

## 8. Templates créés

- `frontend/templates/historique/historique_list.html`
- `frontend/templates/historique/historique_detail.html`
- styles filtres dans `frontend/static/css/base.css`

---

## 9. Migrations

| Migration | Contenu |
|-----------|---------|
| `historique/migrations/0001_initial.py` | Modèle HistoriqueOperation |

---

## 10. Tests réalisés

- création d'enregistrement sans impact sur le solde
- unicité de la référence
- consultation par Wallet
- filtres type / statut / période
- API lecture + refus POST
- pages web
- admin consultation (add/delete interdits)

### Résultats

```
32 passed in 1.72s
```

**Résultat** : OK — 32/32 tests passés

---

## 11. Difficultés rencontrées

1. **Filtre période / fuseaux** — Django 6 parse une date `YYYY-MM-DD` via `parse_datetime` (minuit). Traitement explicite des dates calendaires + bornes locales pour garantir une journée inclusive.

---

## 12. Recommandations pour le Prototype 2 — Sprint 3

1. Brancher la création d'historique sur les premières opérations financières réelles
2. Garantir l'atomicité opération + historique + solde
3. Renforcer les contrôles d'autorisation (propriétaire du Wallet)
4. Introduire une pagination sur les listes d'historique

---

## 13. Proposition de message de commit Git

```
feat(finance): historique des opérations et API de consultation — Prototype 1 Sprint 2
```

**Note** : aucun commit n'a été créé. En attente de validation.

---

**Fin du rapport — Sprint 2**
