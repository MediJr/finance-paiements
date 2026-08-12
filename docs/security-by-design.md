# Security by Design — Sprint 7

Mécanismes de sécurité réellement implémentés sur `11-finance`.

## Principes

- Moindre privilège
- Contrôle d'autorisation côté serveur
- Validation centralisée des entrées
- Scoping propriétaire (IDOR empêché)
- Vision globale réservée aux administrateurs (`is_staff`)
- Mouvements de fonds exclusivement via les services métier

## Contrôle d'accès (scoping)

| Domaine | Non-admin | Admin (`is_staff`) |
|---------|-----------|--------------------|
| Utilisateurs | Profil propre uniquement | Liste / détail globaux |
| Wallets | Wallet propre uniquement | Tous |
| Historique | Opérations de ses wallets | Toutes |
| Bénéficiaires / virements / paiements / remboursements | Déjà scoped propriétaire | Via module administration |

Implémentation : paramètres `demandeur` / `proprietaire` / `vue_admin` dans les services + `_scope_acteur` / `_scope_web` dans les vues.

## Paramètres de sécurité (effectifs)

| Paramètre | Application |
|-----------|-------------|
| `mode_maintenance` | Bloque virements / paiements / remboursements (services + middleware HTTP) |
| `montant_virement_max` | Contrôlé dans `executer_virement` |
| `montant_paiement_max` | Contrôlé dans `executer_paiement` |
| `delai_session_minutes` | Appliqué via `SecurityParametresMiddleware` (`session.set_expiry`) |
| `devise_par_defaut` | Utilisée à la création d'un Wallet |

Module : `administration.services.securite_service`.

## Validation centralisée

- `parse_montant` (`mouvement_service`)
- `parse_identifiant` / `parse_reference` / plafonds / maintenance (`securite_service`)

Aucune confiance accordée aux données client : les vues délèguent aux services.

## Protection métier

- Aucune API ne modifie directement un solde
- Seul `wallets.services.mouvement_service.transferer_fonds` débite/crédite
- Appelé uniquement par `virement_service`, `paiement_service`, `remboursement_service`

## Journal d'administration

Modèle `JournalAdministration` :

- modification des paramètres
- activation / désactivation utilisateur
- accès à l'accueil administration

Consultation : `/administration/journal/` (+ Django Admin lecture seule).

Pas de SIEM / pas d'observabilité avancée.
