# Product backlog

Récits utilisateurs au format **« En tant que… je veux… afin de… »**, reliés aux
exigences du [cahier des charges](cahier-des-charges.md). Tous les récits
ci-dessous sont **livrés** ; les idées non réalisées sont en fin de document.

## Prototype 1 — Fondation

| ID | Récit utilisateur | Exigence | Sprint |
|----|-------------------|----------|:------:|
| US-01 | En tant que développeur, je veux un projet configuré (PostgreSQL, Docker, tests) afin de livrer chaque incrément sur une base saine. | ENF-11, ENF-12 | 0 |
| US-02 | En tant que client, je veux disposer d'un portefeuille en euros dès la création de mon compte. | EF-01 | 1 |
| US-03 | En tant que client, je veux consulter l'historique de mes opérations avec des filtres. | EF-05 | 2 |

## Prototype 2 — Opérations

| ID | Récit utilisateur | Exigence | Sprint |
|----|-------------------|----------|:------:|
| US-04 | En tant que client, je veux enregistrer des bénéficiaires afin de ne virer de l'argent qu'à des personnes choisies. | EF-06 | 3 |
| US-05 | En tant que client, je veux virer de l'argent à un bénéficiaire, sans risque de débit sans crédit. | EF-07, ENF-07 | 4 |
| US-06 | En tant que client, je veux payer un commerçant et pouvoir être remboursé. | EF-08 | 5 |

## Prototype 3 — Administration et sécurité

| ID | Récit utilisateur | Exigence | Sprint |
|----|-------------------|----------|:------:|
| US-07 | En tant qu'administrateur, je veux superviser les comptes et désactiver un compte suspect. | EF-10 | 6 |
| US-08 | En tant qu'administrateur, je veux fixer des plafonds et suspendre les opérations en cas d'incident. | EF-11, ENF-09 | 6, 7 |
| US-09 | En tant que client, je veux être certain qu'aucun autre client ne voit mes données. | ENF-02 | 7 |
| US-10 | En tant que responsable, je veux que les actions d'administration soient tracées. | EF-12 | 7 |
| US-11 | En tant que responsable, je veux un tableau de bord et des rapports par période. | EF-13 | 8 |

## Prototype 4 — Exploitation

| ID | Récit utilisateur | Exigence | Sprint |
|----|-------------------|----------|:------:|
| US-12 | En tant qu'exploitant, je veux un journal d'événements centralisé afin de diagnostiquer un incident. | EF-14, ENF-10 | 9 |
| US-13 | En tant qu'analyste, je veux exporter les données en CSV / JSON. | EF-15 | 10 |

## Prototype 5 — Durcissement

| ID | Récit utilisateur | Exigence | Sprint |
|----|-------------------|----------|:------:|
| US-14 | En tant que visiteur, je veux m'inscrire et me connecter depuis un espace client, sans passer par l'administration. | EF-01, EF-02 | 11 |
| US-15 | En tant que client, je veux alimenter mon portefeuille par carte afin de pouvoir l'utiliser. | EF-04, ENF-06 | 11 |
| US-16 | En tant que client, je veux qu'un double clic ne me débite jamais deux fois. | EF-09, ENF-07 | 11 |
| US-17 | En tant que client, je veux que personne ne puisse obtenir la liste des clients de la plateforme. | EF-06, ENF-03 | 11 |
| US-18 | En tant que responsable conformité, je veux un plafond journalier cumulé. | EF-11, ENF-09 | 11 |
| US-19 | En tant que client, je veux que mon compte soit protégé contre les tentatives de mot de passe répétées. | ENF-04 | 11 |
| US-20 | En tant qu'exploitant, je veux une configuration de production sûre et une CI qui bloque toute régression. | ENF-11, ENF-12 | 11 |

## Idées non réalisées (backlog restant)

| Idée | Priorité | Remarque |
|------|:--------:|----------|
| Double authentification (TOTP) pour les opérations sensibles | S | Indispensable avant une mise en service réelle. |
| Prestataire de paiement réel en mode test | S | La passerelle simulée a la même interface : seul `passerelle_carte.py` serait remplacé. |
| Retrait vers un compte bancaire (IBAN) | C | Nécessite un prestataire SEPA. |
| Notifications e-mail des opérations | C | |
| Cache Redis pour les compteurs de connexion en multi-serveur | S | Le cache mémoire suffit pour une instance unique. |
