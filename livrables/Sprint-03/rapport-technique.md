# Rapport technique — Sprint 3 — Gestion des bénéficiaires

**Application** : 11-finance (Plateforme de paiements numériques)  
**Prototype** : 2  
**Date** : 6 août 2026  
**Statut** : Terminé — en attente de validation

---

## 1. Résumé technique

Le Sprint 3 introduit la gestion des bénéficiaires : chaque utilisateur métier peut constituer une liste de destinataires autorisés pour de futures opérations.

La logique (création, unicité, auto-ajout interdit, désactivation, contrôle d'appartenance) est centralisée dans `beneficiaire_service`. Aucune opération financière n'est exécutée.

---

## 2. Fonctionnalités développées

- Création / consultation / modification de bénéficiaires
- Désactivation logique et réactivation
- Interface web et API REST scoped au propriétaire
- Administration Django (consultation, recherche, filtrage, statut)

Hors périmètre respecté : virements, paiements, remboursements, soldes.

---

## 3. Architecture retenue

```text
Vue / API  →  beneficiaire_service  →  Beneficiaire
                                         ├── FK proprietaire (Utilisateur)
                                         └── FK utilisateur_beneficiaire (Utilisateur)
```

Suppression métier = désactivation (`statut=inactif`), pas de delete physique via l'API.

---

## 4. Modèles créés

### `beneficiaires.Beneficiaire`

- `proprietaire`, `utilisateur_beneficiaire`
- `alias` (optionnel)
- `statut` (actif / inactif)
- `date_creation`, `date_mise_a_jour`
- contrainte unique `(proprietaire, utilisateur_beneficiaire)`

---

## 5. Services créés

| Service | Fonctions |
|---------|-----------|
| `beneficiaire_service` | `create_beneficiaire`, `list_beneficiaires`, `list_beneficiaires_selectionnables`, `get_beneficiaire_pour_proprietaire`, `update_beneficiaire`, `desactiver_beneficiaire`, `reactiver_beneficiaire`, `get_utilisateur_connecte` |

---

## 6. Vues créées

| Vue | URL |
|-----|-----|
| Liste | `/beneficiaires/` |
| Création | `/beneficiaires/nouveau/` |
| Détail | `/beneficiaires/<id>/` |
| Modification | `/beneficiaires/<id>/modifier/` |

---

## 7. API créées

| Méthode | Endpoint |
|---------|----------|
| GET | `/api/beneficiaires/` |
| POST | `/api/beneficiaires/` |
| GET | `/api/beneficiaires/<id>/` |
| PUT/PATCH | `/api/beneficiaires/<id>/` |
| DELETE | `/api/beneficiaires/<id>/` (désactivation) |

---

## 8. Templates créés

- `frontend/templates/beneficiaires/beneficiaire_list.html`
- `frontend/templates/beneficiaires/beneficiaire_detail.html`
- `frontend/templates/beneficiaires/beneficiaire_form.html`

---

## 9. Migrations

| Migration | Contenu |
|-----------|---------|
| `beneficiaires/migrations/0001_initial.py` | Modèle Beneficiaire |

---

## 10. Tests réalisés

- création, auto-ajout interdit, unicité
- consultation / modification
- désactivation / réactivation / sélectionnables
- contrôle d'accès inter-utilisateurs
- API CRUD + refus d'accès
- pages web
- admin

### Résultats

```
44 passed in 2.27s
```

**Résultat** : OK — 44/44 tests passés

---

## 11. Difficultés rencontrées

1. **Profil métier requis** — l'API bénéficiaires exige un `Utilisateur` lié au `User` Django (`get_utilisateur_connecte`), cohérent avec le modèle métier du Sprint 1.

---

## 12. Recommandations pour le Sprint 4

1. Introduire les virements en s'appuyant uniquement sur `list_beneficiaires_selectionnables`
2. Enregistrer chaque virement dans `HistoriqueOperation`
3. Mettre à jour les soldes de façon atomique (transaction)
4. Renforcer les permissions (propriétaire du Wallet source)

---

## 13. Proposition de message de commit Git

```
feat(finance): gestion des bénéficiaires — Prototype 2 Sprint 3
```

**Note** : aucun commit n'a été créé. En attente de validation.

---

**Fin du rapport — Sprint 3**
