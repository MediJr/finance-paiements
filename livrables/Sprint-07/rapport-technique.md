# Rapport technique — Sprint 7 — Security by Design



**Application** : 11-finance  

**Prototype** : 3  

**Date** : 6 août 2026  

**Statut** : Terminé — en attente de validation



---



## 1. Résumé technique



Le Sprint 7 renforce la sécurité de toutes les fonctionnalités existantes (Security by Design), sans ajouter de nouvelle fonctionnalité métier financière.



Principaux apports :



- scoping propriétaire (IDOR corrigé sur utilisateurs, wallets, historique)

- application réelle des paramètres Sprint 6 (plafonds, maintenance, session, devise)

- validations centralisées

- journal simple des actions d'administration

- filet HTTP complementary (middleware maintenance)



---



## 2. Mécanismes de sécurité implémentés



| Mécanisme | Détail |

|-----------|--------|

| Contrôle d'accès | Non-admin = données propres ; staff = vision globale |

| Permissions | Vérifiées côté serveur (services + décorateurs / DRF) |

| Plafonds | `montant_virement_max` / `montant_paiement_max` dans les services |

| Maintenance | Blocage services + middleware sur écritures financières |

| Session | `delai_session_minutes` via middleware |

| Validation | `securite_service` + `parse_montant` |

| Protection soldes | Uniquement via `mouvement_service` |

| Journal admin | `JournalAdministration` |



---



## 3. Services modifiés / créés



| Service | Changement |

|---------|------------|

| `utilisateur_service` | Scoping `demandeur` / `vue_admin` |

| `wallet_service` | Scoping + devise depuis paramètres |

| `historique_service` | Scoping `proprietaire` / `vue_admin` |

| `virement_service` | Maintenance + plafond |

| `paiement_service` | Maintenance + plafond |

| `remboursement_service` | Maintenance |

| `administration_service` | Journalisation des actions |

| `securite_service` | **Créé** |

| `journal_service` | **Créé** |



---



## 4. API modifiées



Endpoints existants uniquement :



- `/api/utilisateurs/`, `/api/wallets/…`, `/api/historique/…` — scoping

- `/api/virements|paiements|remboursements/` — héritent des contrôles services

- `/api/administration/parametres/` — journal + IP



Aucun nouvel endpoint métier.



---



## 5. Modèles / migrations



| Élément | Détail |

|---------|--------|

| Modèle | `JournalAdministration` |

| Migration | `administration/migrations/0002_journaladministration.py` |



`ParametresApplication` inchangé (déjà présent Sprint 6).



---



## 6. Templates



- Adaptations vues existantes (scoping)

- Nouveau template admin (non métier) : `administration/journal.html`

- Lien journal sur l'index administration



---



## 7. Tests réalisés



Nouveau fichier `tests/test_securite.py` :



- IDOR API / web (utilisateurs, wallets, historique)

- Vision globale admin

- Plafonds virement / paiement

- Mode maintenance (service + middleware)

- Journal (paramètres, activation, accès admin)

- Virement sous plafond OK



---



## 8. Résultats des tests



```text

92 passed

```



---



## 9. Difficultés rencontrées



Aucune majeure. Distinction 403 (profil refusé) vs 404 (objet hors scope) conservée selon le domaine.



---



## 10. Recommandations pour le Sprint 8



1. Authentification métier dédiée (hors `/admin/login/`) si demandée

2. Rate limiting / anti-bruteforce sur opérations financières

3. Renforcement CSRF / headers de sécurité HTTP en durcissement prod

4. Dépôt / approvisionnement Wallet (si sprint métier)

5. Pagination des listes API volumineuses



---



## 11. Proposition de commit



```text

feat(finance): renforcement Security by Design — Prototype 3 Sprint 7

```



Aucun commit créé.



---



**Fin du rapport — Sprint 7**


