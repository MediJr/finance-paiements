# État du projet

**Version** : 1.1.0 — 22 octobre 2026
**Statut** : terminé, audité et durci (prototypes 1 à 5, sprints 0 à 11).

## Indicateurs

| Indicateur | Valeur |
|------------|--------|
| Modules Django | 9 (+ utilitaires `commun`) |
| Modèles ORM | 11 |
| Routes API REST | 31 |
| Pages web (gabarits) | 35 |
| Tests automatisés | 169 |
| Couverture du code applicatif | 86 % |
| `check --deploy` (production) | 0 avertissement |

## Feuille de route

| Prototype | Sprints | Thème | Statut |
|-----------|:-------:|-------|:------:|
| 1 — Fondation | 0–2 | Initialisation, utilisateurs et portefeuilles, historique | ✅ |
| 2 — Opérations | 3–5 | Bénéficiaires, virements, paiements et remboursements | ✅ |
| 3 — Administration et sécurité | 6–8 | Paramètres, Security by Design, pilotage | ✅ |
| 4 — Exploitation | 9–10 | Observabilité, exports | ✅ |
| 5 — Durcissement | 11 | Audit, espace client, alimentation, idempotence, CI, production | ✅ |

Détail : [cycle-de-vie.md](cycle-de-vie.md) ; rapports : [livrables](../livrables/README.md).

## Limites connues

| Limite | Commentaire |
|--------|-------------|
| Carte bancaire simulée | Passerelle serveur réaliste ; remplaçable par un prestataire réel. |
| Pas de double authentification | Indispensable avant une mise en service réelle. |
| Cache des tentatives de connexion | Mémoire locale : utiliser Redis en multi-instance. |
| Mono-devise | Les portefeuilles sont en EUR ; un virement entre devises différentes est refusé. |
