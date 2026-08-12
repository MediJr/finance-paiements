# Rapport technique — Sprint 5 — Paiements et remboursements

**Application** : 11-finance  
**Prototype** : 2  
**Date** : 6 août 2026  
**Statut** : Terminé — en attente de validation

---

## 1. Résumé technique

Le Sprint 5 ajoute les paiements et remboursements atomiques, en factorisant les mouvements de fonds dans `wallets.services.mouvement_service` pour éviter toute duplication avec les virements.

---

## 2. Fonctionnalités développées

- Paiement vers un bénéficiaire actif
- Remboursement (partiel ou total) d'un paiement existant
- Historique automatique (`paiement` / `remboursement`)
- Interface web et API
- Admin consultation

---

## 3. Architecture retenue

```text
paiement_service / remboursement_service / virement_service
        └── mouvement_service.transferer_fonds + journaliser_transfert
```

---

## 4. Modèles créés

- `Paiement` (référence, wallets, montants, statut, motif)
- `Remboursement` (lié à un paiement, wallets, montant, référence)

---

## 5. Services créés

| Service | Rôle |
|---------|------|
| `mouvement_service` | Transfert de fonds + journalisation (partagé) |
| `paiement_service` | Exécution / consultation paiements |
| `remboursement_service` | Exécution / consultation remboursements |

---

## 6. Vues / API / Templates

**Web** : listes, détails, formulaires paiements et remboursements  

**API** :

- `POST/GET /api/paiements/`, `GET /api/paiements/<id>/`
- `POST/GET /api/remboursements/`, `GET /api/remboursements/<id>/`

---

## 7. Migrations

`paiements/migrations/0001_initial.py`

---

## 8. Règles métier

- validations Wallets / bénéficiaire / solde / montant
- remboursement uniquement par le bénéficiaire d'origine
- pas de remboursement au-delà du reste
- refus si paiement inexistant ou déjà totalement remboursé
- atomicité complète

---

## 9. Résultats des tests

```
72 passed in 5.97s
```

---

## 10. Difficultés rencontrées

1. **Anti-duplication** — extraction de `mouvement_service` et adaptation des tests virements (types d'historique `virement`).

---

## 11. Recommandations pour le Prototype 3

1. Tableaux de bord et rapports financiers
2. Mécanisme de dépôt / approvisionnement Wallet
3. Pagination et exports
4. Observabilité / audit avancé si demandé

---

## 12. Proposition de commit

```
feat(finance): paiements et remboursements sécurisés — Prototype 2 Sprint 5
```

Aucun commit créé. En attente de validation.

---

**Fin du rapport — Sprint 5**
