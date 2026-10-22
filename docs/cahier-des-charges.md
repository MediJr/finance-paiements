# Cahier des charges — Finance Paiements

> Phase du cycle de vie : **Analyse des besoins**.
> Les exigences sont numérotées pour être reliées au code et aux tests
> (voir la [matrice de traçabilité](tests.md#5-matrice-de-traçabilité)).

## 1. Contexte et objectifs

Un établissement fictif souhaite proposer à ses clients un **portefeuille
électronique** (wallet), à la manière des applications de paiement entre
particuliers. Le client doit pouvoir :

1. ouvrir un compte et disposer d'un portefeuille en euros ;
2. l'approvisionner par carte bancaire ;
3. envoyer de l'argent à des proches (virements) et payer des commerçants (paiements) ;
4. être remboursé, et consulter l'historique complet de ses opérations.

L'établissement doit de son côté **superviser** l'activité, **fixer des plafonds**,
pouvoir **suspendre** les opérations (maintenance), **tracer** toute action sensible
et **exporter** les données.

Le traitement de la carte bancaire est **simulé** : une passerelle côté serveur
reproduit le comportement d'un prestataire (validation, autorisation, refus,
masquage du numéro).

## 2. Acteurs

| Acteur | Description |
|--------|-------------|
| Visiteur | Peut créer un compte et se connecter. |
| Client | Possède un portefeuille ; alimente, vire, paie, rembourse, consulte son historique. |
| Administrateur | Membre du personnel (`is_staff`) ; supervise, paramètre, active / désactive des comptes, consulte journaux, statistiques et exports. |

## 3. Exigences fonctionnelles (EF)

Priorité selon **MoSCoW** : *M* = Must (indispensable), *S* = Should, *C* = Could.

### Comptes et portefeuilles

| ID | Exigence | Priorité | Sprint |
|----|----------|:--------:|:------:|
| EF-01 | Un visiteur crée un compte client ; un portefeuille en euros à solde nul est ouvert automatiquement. | M | 1, 11 |
| EF-02 | Un client se connecte et se déconnecte depuis un espace dédié (distinct du site d'administration). | M | 11 |
| EF-03 | Un client consulte son solde, son profil et ses dernières opérations. | M | 1, 11 |
| EF-04 | Un client alimente son portefeuille par carte bancaire ; la passerelle accepte ou refuse. | M | 11 |

### Opérations

| ID | Exigence | Priorité | Sprint |
|----|----------|:--------:|:------:|
| EF-05 | Chaque opération est inscrite dans un historique consultable et filtrable (type, statut, dates, référence). | M | 2 |
| EF-06 | Un client gère ses bénéficiaires (ajout par adresse e-mail, alias, désactivation). | M | 3, 11 |
| EF-07 | Un client vire de l'argent à un bénéficiaire actif ; débit et crédit sont atomiques. | M | 4 |
| EF-08 | Un client paie un bénéficiaire ; le bénéficiaire peut le rembourser totalement ou partiellement. | M | 5 |
| EF-09 | Une même demande envoyée deux fois (double clic, réseau) n'est exécutée qu'une fois. | M | 11 |

### Administration et pilotage

| ID | Exigence | Priorité | Sprint |
|----|----------|:--------:|:------:|
| EF-10 | L'administrateur supervise utilisateurs, portefeuilles et opérations ; il active / désactive un compte. | M | 6 |
| EF-11 | L'administrateur règle les paramètres : plafonds par opération, plafond journalier, plafond d'alimentation, devise, durée de session, mode maintenance. | M | 6, 7, 11 |
| EF-12 | Les actions d'administration sont journalisées. | M | 7 |
| EF-13 | Tableau de bord, statistiques et rapports filtrables par période, statut et utilisateur. | S | 8 |
| EF-14 | Journal d'événements centralisé et consultable. | S | 9 |
| EF-15 | Export CSV / JSON des utilisateurs, portefeuilles, bénéficiaires, opérations et événements. | C | 10 |

## 4. Exigences non fonctionnelles (ENF)

| ID | Catégorie | Exigence | Mise en œuvre |
|----|-----------|----------|---------------|
| ENF-01 | Sécurité | Mots de passe hachés et validés ; messages d'échec identiques que le compte existe ou non. | Validateurs Django, PBKDF2 |
| ENF-02 | Sécurité | Un client n'accède qu'à ses propres données ; l'administration est réservée au personnel. | Filtrage par propriétaire dans les services |
| ENF-03 | Sécurité | Aucun annuaire de clients exposé : un destinataire est désigné par son e-mail exact. | `ajouter_beneficiaire_par_email` |
| ENF-04 | Sécurité | Blocage temporaire après 5 échecs de connexion (compte) ou 20 (IP). | `auth_service` + cache |
| ENF-05 | Sécurité | CSRF, XSS, clickjacking, redirections ouvertes, injection de formules CSV. | Middleware Django, `commun/`, `export_service` |
| ENF-06 | Sécurité | Aucune donnée de carte complète conservée. | `Alimentation.carte_masquee` |
| ENF-07 | Intégrité | Aucun solde négatif ni double débit : transactions atomiques, verrous de ligne, clés d'idempotence. | `transaction.atomic`, `select_for_update`, contraintes d'unicité |
| ENF-08 | Intégrité | Montants en décimal exact, 2 décimales maximum, sans arrondi silencieux. | `parse_montant` |
| ENF-09 | Conformité | Plafond par opération et plafond journalier cumulé des sorties. | `securite_service` |
| ENF-10 | Traçabilité | Événements immuables pour toute action sensible (connexion, alimentation, virement, administration). | `observabilite.journal_service` |
| ENF-11 | Qualité | Couverture de tests ≥ 80 % ; tests exécutés automatiquement à chaque push. | pytest-cov, GitHub Actions |
| ENF-12 | Déploiement | Configuration par environnement ; démarrage refusé sans clé secrète ; HTTPS imposé en production. | `settings/production.py` |
| ENF-13 | Maintenabilité | Toute modification de solde passe par un module unique ; la logique métier est dans les services. | `mouvement_service`, `*/services/` |

## 5. Contraintes

- Python 3.12, Django 6, Django REST Framework, PostgreSQL 16.
- Développement par une seule personne (rôle de développeur et de Product Owner).
- Données de démonstration uniquement ; aucune transaction bancaire réelle.

## 6. Hors périmètre

- Prestataire de paiement réel, virement vers un compte bancaire externe (SEPA).
- Multi-devise avec conversion, KYC (vérification d'identité), lutte anti-blanchiment.
- Notifications par e-mail ou SMS, double authentification.
