# Documentation

Organisée selon les phases du cycle de vie du développement logiciel.

**Rapport de synthèse (LaTeX → PDF) :** [rapport/Rapport-Finance-Paiements.pdf](rapport/Rapport-Finance-Paiements.pdf)
— source : [rapport/rapport.tex](rapport/rapport.tex) (`latexmk -pdf rapport.tex`).

| Phase | Document | Contenu |
|-------|----------|---------|
| Méthode | [cycle-de-vie.md](cycle-de-vie.md) | Prototypage évolutif + Scrum, Definition of Done, déroulé des sprints |
| 1. Analyse | [cahier-des-charges.md](cahier-des-charges.md) | Contexte, acteurs, exigences fonctionnelles (EF) et non fonctionnelles (ENF) |
| | [backlog.md](backlog.md) | Récits utilisateurs par prototype |
| 2. Conception | [architecture.md](architecture.md) | Couches, modules, modèle de données, flux d'un virement |
| 3. Réalisation | Documents par module (ci-dessous) | Règles métier de chaque domaine |
| 4. Tests | [tests.md](tests.md) | Stratégie, couverture, matrice de traçabilité |
| 5. Audit | [securite.md](securite.md), [security-by-design.md](security-by-design.md) | Modèle de menace, mesures, défauts corrigés |
| 6. Déploiement | [installation.md](installation.md) | Local, Docker, production, variables d'environnement |
| 7. Maintenance | [../CHANGELOG.md](../CHANGELOG.md), [versions.md](versions.md), [ETAT_DU_PROJET.md](ETAT_DU_PROJET.md) | Historique, dépendances, état actuel |
| Démonstration | [guide-demo.md](guide-demo.md) | Scénario de présentation en 5 minutes |

## Documents par module

| Module | Document |
|--------|----------|
| Utilisateurs et portefeuilles | [utilisateurs-wallets.md](utilisateurs-wallets.md) |
| Alimentation par carte | [alimentation.md](alimentation.md) |
| Historique | [historique-operations.md](historique-operations.md) |
| Bénéficiaires | [beneficiaires.md](beneficiaires.md) |
| Virements | [virements.md](virements.md) |
| Paiements et remboursements | [paiements-remboursements.md](paiements-remboursements.md) |
| Administration | [administration.md](administration.md) |
| Pilotage | [pilotage.md](pilotage.md) |
| Observabilité | [observabilite.md](observabilite.md) |
| Exports | [exports.md](exports.md) |
| API REST | [../api/README.md](../api/README.md) |

Rapports de sprint et audits : [../livrables/README.md](../livrables/README.md).
