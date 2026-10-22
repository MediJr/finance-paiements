# Rapport technique — Sprint 11 — Audit de sécurité et durcissement

**Prototype** : 5 — Durcissement
**Date** : 22 octobre 2026
**Statut** : Terminé — validé
**Version livrée** : 1.1.0

---

## 1. Objectif du sprint

Faire passer l'application d'un prototype fonctionnel à un produit
**utilisable, présentable et déployable** : auditer le code, rendre le parcours
client complet (connexion, approvisionnement), corriger chaque défaut avec des
tests, préparer la production et compléter la documentation du cycle de vie.

## 2. Démarche

1. **Audit** : lecture des services (mouvements de fonds, bénéficiaires,
   paramètres, exports), des vues et des routes API ; parcours manuel complet.
2. **Constat majeur** : le parcours client était impossible (connexion réservée
   au personnel, portefeuilles bloqués à 0 EUR) — invisible dans les tests,
   qui appelaient directement les services.
3. **Correction** dans la couche service, puis adaptation des vues et de l'API.
4. **Tests** : 48 tests dans `tests/test_durcissement.py`.
5. **Vérification** : suite complète, `makemigrations --check`, `check --deploy`,
   parcours manuel dans le navigateur (client puis administrateur).

## 3. Défauts corrigés

| ID | Gravité | Défaut | Correction |
|----|:-------:|--------|------------|
| F1 | Critique | Annuaire des clients énumérable (API par identifiant, liste déroulante) | Ajout de bénéficiaire par e-mail exact |
| F2 | Bloquant | Aucun espace client | Inscription, connexion, déconnexion, espace client |
| F3 | Bloquant | Aucun approvisionnement possible | Alimentation par carte (passerelle simulée) |
| F4 | Élevée | Double débit sur double soumission | Clés d'idempotence + contrainte d'unicité |
| F5 | Élevée | Plafond par opération contournable | Plafond journalier cumulé |
| F6 | Moyenne | Arrondi silencieux des montants, erreur 500 sur valeurs extrêmes | Validation stricte |
| F7 | Moyenne | Injection de formules dans les exports CSV | Neutralisation |
| F8 | Moyenne | Force brute et login CSRF | Blocage temporaire, CSRF imposé, redirections sûres |
| F9 | Moyenne | IP falsifiable | `X-Forwarded-For` ignoré par défaut |
| F10 | Moyenne | Configuration non sûre par défaut | `settings/production.py`, Docker non-root |
| F11 | Qualité | Fichiers en double interligne, nom de laboratoire | Normalisation, renommage |

## 4. Migrations

| Migration | Contenu |
|-----------|---------|
| `administration.0003_plafonds_journalier_alimentation` | Paramètres `plafond_journalier`, `montant_alimentation_max` |
| `wallets.0002_alimentation` | Modèle `Alimentation` |
| `virements.0002_cle_idempotence` | Champ et contrainte d'idempotence |
| `paiements.0002_cle_idempotence` | Champ et contrainte d'idempotence |

## 5. Tests

| Mesure | Avant | Après |
|--------|------:|------:|
| Tests | 121 | **169** |
| Couverture du code applicatif | — | **86 %** |

```text
pytest                                         → 169 passed
manage.py makemigrations --check --dry-run     → No changes detected
manage.py check --deploy (production)          → no issues (0 silenced)
```

## 6. Rétrospective

| Ce qui a bien fonctionné | À améliorer |
|--------------------------|-------------|
| Le module unique de mouvements de fonds a rendu l'idempotence et le plafond journalier simples à ajouter. | Les tests appelaient les services directement : aucun ne jouait le parcours réel d'un client, d'où deux défauts bloquants non détectés. Un test de bout en bout par parcours devient obligatoire. |
| Les 121 tests existants ont validé qu'aucune règle financière n'avait régressé. | L'audit de sécurité doit être planifié à la fin de chaque prototype. |
