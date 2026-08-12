# Audit technique — Application Finance (11-finance)

**Date** : 6 août 2026  
**Périmètre** : `applications/11-finance`  
**Nature** : Audit read-only — aucun code métier modifié  
**Dernier sprint documenté / attendu** : Prototype 3 — Sprint 6 (Administration et paramètres)  
**Branche Git** : `main`

**Contrôles exécutés** :

| Contrôle | Résultat |
|----------|----------|
| `python backend/manage.py check` | **0 issue** |
| `pytest -q` | **80 passed** in ~14 s |
| `pytest --collect-only` | **80 tests** collectés |
| `docker compose -f docker/docker-compose.yml config` | **OK** (fichier valide) |
| Connexion PostgreSQL `localhost:5433` | **Échec** (serveur arrêté / non joignable) |
| Modifications de code | **Aucune** (hors ce rapport) |
| Commit Git | **Aucun** |

---

## 1. État général

| Domaine | État | Commentaire |
|---------|------|-------------|
| Architecture MTV + services | 🟢 | Cohérente, logique métier hors vues |
| Modèles / migrations | 🟢 | 8 modèles, 7 migrations initiales alignées |
| Services | 🟢 | Factorisation `mouvement_service` solide |
| API REST | 🟡 | Fonctionnelle ; scoping inégal selon domaines |
| Templates web | 🟢 | Couverture métier + administration |
| Administration Django | 🟢 | Consultation / garde-fous sur opérations financières |
| Docker / Compose | 🟢 | Config valide ; runtime DB non vérifié ici |
| PostgreSQL | 🟡 | Configuré ; instance locale non démarrée au moment de l’audit |
| Tests | 🟢 | 80/80 |
| Documentation | 🟡 | Complète par sprint ; pas d’`ETAT_DU_PROJET` |
| Livrables sprint | 🟢 | Sprint-00 → Sprint-06 présents |
| Git | 🔴 | Quasi-totalité non versionnée |
| Qualité générale | 🟢 | Projet cohérent avec le Sprint 6 |

**Verdict** : le dépôt `11-finance` est **techniquement cohérent avec le dernier sprint validé (Prototype 3 — Sprint 6)**. Les tests et le check Django sont verts. Les principaux écarts concernent le **versionnement Git**, l’**absence d’`ETAT_DU_PROJET`**, la **non-application métier des paramètres** (plafonds / maintenance), et un **scoping API encore large** sur utilisateurs / wallets / historique.

**Reprise du développement** : possible après validation de cet audit ; aucun bloqueur technique majeur côté code.

---

## 2. Statistiques consolidées

| Indicateur | Valeur |
|------------|--------|
| Application | `11-finance` |
| Prototype courant | **3** |
| Dernier sprint | **6** |
| Apps Django métier / API | **8** (`accounts`, `wallets`, `historique`, `beneficiaires`, `virements`, `paiements`, `administration`, `api`) |
| Modèles ORM métier | **8** |
| Migrations applicatives | **7** (`*.0001_initial`) |
| Modules services (fichiers) | **9** (+ `__init__`) |
| Vues web (fonctions métier) | **~25** |
| Classes vues API | **~18** |
| Endpoints API (`path` sous `/api/`) | **16** (+ racine) |
| Templates HTML | **22** |
| Fichiers `admin.py` | **8** |
| Fichiers de tests | **7** |
| Tests automatisés | **80** (100 % réussis) |
| Documents Markdown (app) | **~34** |
| Dossiers livrables sprint | **7** (Sprint-00 … Sprint-06) |
| Fichiers projet (hors `.venv`) | **~177** |
| Fichiers Python (hors `.venv`) | **~107** |
| Fichiers suivis Git sous `11-finance` | **1** (essentiellement `README.md` modifié) |
| Port Django (doc / Docker) | **8001** |
| Port PostgreSQL hôte | **5433** → 5432 conteneur |

### Répartition des modèles

| App | Modèles |
|-----|---------|
| accounts | `Utilisateur` |
| wallets | `Wallet` |
| historique | `HistoriqueOperation` |
| beneficiaires | `Beneficiaire` |
| virements | `Virement` |
| paiements | `Paiement`, `Remboursement` |
| administration | `ParametresApplication` |

### Répartition des tests

| Fichier | Tests (approx.) |
|---------|----------------:|
| `test_administration.py` | 8 |
| `test_beneficiaires.py` | 12 |
| `test_historique.py` | 11 |
| `test_paiements.py` | 13 |
| `test_utilisateurs_wallets.py` | 14 |
| `test_virements.py` | 15 |
| `test_configuration.py` | 7 |
| **Total** | **80** |

---

## 3. Architecture

### 3.1 Vue d’ensemble

```text
frontend/templates  →  vues Django (login_required)
api/                →  DRF (SessionAuth + IsAuthenticated par défaut)
        ↓
services métier (accounts … administration)
        ↓
modèles ORM  →  PostgreSQL (finance)
```

Principes observés et respectés :

- Architecture **MTV** Django
- Logique métier dans des **services** (pas dans serializers / modèles lourds)
- Mouvements de fonds centralisés dans `wallets/services/mouvement_service.py`
- Administration fonctionnelle découplée (`administration`) sans modification de soldes

### 3.2 Arborescence (principale)

```text
11-finance/
├── accounts/ wallets/ historique/ beneficiaires/
├── virements/ paiements/ administration/
├── api/
├── backend/config/          # settings, urls, wsgi
├── frontend/templates|static
├── tests/
├── docs/
├── livrables/Sprint-00 … Sprint-06/
├── docker/                  # compose + Dockerfile
├── database/init/
├── requirements.txt, pytest.ini, .env.example
└── README.md, CHANGELOG.md
```

### 3.3 Cohérence prototypes / sprints

| Prototype | Sprints | Contenu | Cohérence doc ↔ code |
|-----------|---------|---------|----------------------|
| 1 | 0–2 | Fondations, utilisateurs/wallets, historique | 🟢 |
| 2 | 3–5 | Bénéficiaires, virements, paiements/remboursements | 🟢 |
| 3 | 6 | Administration + paramètres | 🟢 |

- README, CHANGELOG et `docs/README.md` annoncent bien **Prototype 3 — Sprint 6**.
- Livrables : un dossier par sprint (0–6), indexé dans `livrables/README.md`.
- Pas de dossiers `Prototype-*` (contrairement à d’autres apps du labo) : le suivi se fait par **sprints** — acceptable si assumé, mais à documenter.
- Pas de fichier `docs/ETAT_DU_PROJET.md` ni équivalent.

---

## 4. Modèles

| Modèle | Rôle | Remarques |
|--------|------|-----------|
| `Utilisateur` | Profil métier (OneToOne `User`) | Création liée au Wallet |
| `Wallet` | Solde / devise / statut | Solde initial 0 |
| `HistoriqueOperation` | Journal des mouvements | Référence unique |
| `Beneficiaire` | Lien propriétaire → destinataire | Désactivation logique |
| `Virement` | Transfert atomique | Statuts + référence |
| `Paiement` | Paiement | Historique auto |
| `Remboursement` | Remboursement | Lié au paiement |
| `ParametresApplication` | Singleton paramètres | pk=1 |

Aucun modèle orphelin détecté. Les relations financières passent par les wallets et l’historique.

---

## 5. Migrations

| App | Migration | État attendu |
|-----|-----------|--------------|
| accounts | `0001_initial` | Présente |
| wallets | `0001_initial` | Présente |
| historique | `0001_initial` | Présente |
| beneficiaires | `0001_initial` | Présente |
| virements | `0001_initial` | Présente |
| paiements | `0001_initial` | Présente |
| administration | `0001_initial` | Présente |

- Une migration initiale par app métier : schéma simple, lisible.
- `manage.py showmigrations` n’a **pas** pu lister l’état appliqué en base : PostgreSQL local **non joignable** (port 5433).
- Les tests (`config.settings.test`) valident le schéma via la base de test (80 tests OK).

---

## 6. Services

| Service | Responsabilité |
|---------|----------------|
| `utilisateur_service` | CRUD / consultation utilisateurs métier |
| `wallet_service` | Consultation wallets |
| `mouvement_service` | Transfert de fonds + journalisation |
| `historique_service` | Création interne / consultation filtrée |
| `beneficiaire_service` | Gestion scoped propriétaire |
| `virement_service` | Exécution atomique de virement |
| `paiement_service` / `remboursement_service` | Paiements / remboursements |
| `administration_service` | Paramètres + supervision staff |

Points forts :

- Factorisation des mouvements (virements / paiements / remboursements)
- Validations métier (solde, statut, auto-virement, propriété bénéficiaire, etc.)

Écart fonctionnel notable :

- `montant_virement_max`, `montant_paiement_max`, `mode_maintenance` sont **stockés et éditables** (admin + API) mais **non appliqués** dans les services financiers au moment de l’audit.

---

## 7. API

### Endpoints

| Groupe | Chemins |
|--------|---------|
| Racine | `GET /api/` |
| Utilisateurs / wallets | `GET /api/utilisateurs/`, `…/<id>/`, `…/<id>/wallet/`, `GET /api/wallets/<id>/`, historique wallet |
| Historique | `GET /api/historique/`, `…/<id>/` |
| Bénéficiaires | liste/création/détail (CRUD logique) |
| Virements | liste/création/détail |
| Paiements / remboursements | liste/création/détail |
| Administration | `/api/administration/parametres|utilisateurs|wallets|operations/` |

### Sécurité API (constat)

| Zone | Auth | Scoping |
|------|------|---------|
| Défaut DRF | Session + `IsAuthenticated` | — |
| Racine API | Publique (`permission_classes = []`) | Intentionnel |
| Administration | `IsAdministrateur` (`is_staff`) | 🟢 |
| Bénéficiaires / virements / paiements | Utilisateur connecté | 🟢 (scoped) |
| Utilisateurs / wallets / historique | Authentifié seulement | 🟡 (liste / détail **sans** filtre propriétaire) |

Les pages web métier sont protégées par `@login_required`. Le login web pointe vers `/admin/login/` (pas d’écran de login métier dédié).

---

## 8. Templates

22 templates sous `frontend/templates/` :

- `base.html`
- accounts (liste / détail)
- wallets (détail)
- historique (liste / détail)
- beneficiaires (liste / détail / formulaire)
- virements (liste / détail / formulaire)
- paiements + remboursements (liste / détail / formulaires)
- administration (index, paramètres, utilisateurs, wallets, opérations)

Couverture alignée avec les vues web du Sprint 6. Pas de template orphelin évident.

---

## 9. Administration Django

- Enregistrements admin pour les apps métier.
- Opérations financières (`Historique`, `Virement`, `Paiement`, `Remboursement`) : consultation limitée (`has_add` / `has_change` / `has_delete` restreints selon les modules).
- `ParametresApplication` : pas d’ajout / suppression multiples (singleton).
- Administration **fonctionnelle** distincte sous `/administration/` (staff), documentée.

---

## 10. Docker / PostgreSQL / configuration

### Docker

- Compose : `docker/docker-compose.yml` (services `db` + `web`).
- Image PostgreSQL : `postgres:16-alpine`.
- Ports : DB hôte **5433**, web **8001**.
- Healthcheck `pg_isready`, volume persisté, init SQL en lecture seule.
- `docker compose config` : **valide**.

### PostgreSQL

- Settings : moteur PostgreSQL, variables `.env` / `.env.example`.
- Au moment de l’audit : **connexion refusée** sur `localhost:5433` → instance non démarrée (Docker Desktop / conteneur arrêté).
- Les tests ne dépendent pas de cette instance (settings test).

### Configuration

- Django **6.0.7**, DRF **3.17.1**, pytest / pytest-django.
- Settings découpés (`base` / environnements dont `test`).
- `SECRET_KEY` / `DEBUG` via env (valeur insecure par défaut en dev — attendu en labo).
- Locale `fr-fr`, fuseau `Europe/Paris`.

---

## 11. Couverture fonctionnelle

| Domaine | Web | API | Admin Django | Tests | Statut |
|---------|-----|-----|--------------|-------|--------|
| Utilisateurs / wallets | ✅ | ✅ lecture | ✅ | ✅ | Livré P1 |
| Historique | ✅ | ✅ lecture | ✅ lecture | ✅ | Livré P1 |
| Bénéficiaires | ✅ | ✅ | ✅ | ✅ | Livré P2 |
| Virements | ✅ | ✅ | ✅ lecture | ✅ | Livré P2 |
| Paiements / remboursements | ✅ | ✅ | ✅ lecture | ✅ | Livré P2 |
| Administration / paramètres | ✅ | ✅ staff | ✅ | ✅ | Livré P3 S6 |
| Dépôt / crédit métier | ❌ | ❌ | ❌ | — | Hors scope actuel |
| Application des plafonds / maintenance | Stockage ✅ | — | — | partiel | **Non appliqué** aux flux |
| Auth métier dédiée (UI login) | Via admin login | Session | — | partiel | Minimal labo |

---

## 12. Documentation

| Artefact | Présent | Aligné Sprint 6 |
|----------|---------|-----------------|
| `README.md` | ✅ | ✅ |
| `CHANGELOG.md` | ✅ | ✅ (80 tests) |
| `docs/architecture.md` | ✅ | ✅ |
| `docs/*` par domaine | ✅ | ✅ |
| `docs/ETAT_DU_PROJET.md` | ❌ | — |
| `livrables/Sprint-0x/` | ✅ | ✅ |
| `livrables/Prototype-*` | ❌ | N/A (suivi par sprint) |
| Messages de commit proposés dans livrables | Incomplet / variable selon sprints | — |

Documentation **suffisante** pour reprendre le développement, mais l’absence d’**état du projet** centralisé complique le onboarding rapide.

---

## 13. Git

| Élément | Constat |
|---------|---------|
| Branche | `main` |
| Historique `11-finance` | Quasi uniquement le commit d’init labo ; travail sprints **non commité** |
| Statut | `README.md` modifié + **très nombreux fichiers untracked** (apps, tests, docs, docker, livrables…) |
| Remote / push | Non audité en profondeur ; pas de commit demandé ni réalisé |
| Risque | Perte de travail / non traçabilité des sprints 0–6 |

**Priorité haute** : versionner l’état Sprint 6 après validation explicite (un ou plusieurs commits), sans amendement forcé.

---

## 14. Points forts

1. **Architecture services** claire et respectée (y compris factorisation des mouvements).
2. **Suite de tests verte** (80/80) et `manage.py check` sans alerte.
3. **Progression sprint / prototype** documentée et alignée README ↔ CHANGELOG ↔ livrables.
4. **Sécurité métier** sur les flux d’argent (transactions atomiques, validations solde / bénéficiaire).
5. **Administration fonctionnelle** sans capacité de modifier les soldes.
6. **Docker Compose** propre (healthcheck, ports labo 8001/5433).
7. **Admin Django** restreint sur les opérations financières.

---

## 15. Anomalies et écarts

| ID | Sévérité | Description |
|----|----------|-------------|
| A1 | 🔴 Haute | Travail Sprints 0–6 **non versionné** Git (presque tout untracked). |
| A2 | 🟠 Moyenne | Paramètres `montant_*_max` et `mode_maintenance` **non appliqués** dans les services virement/paiement. |
| A3 | 🟠 Moyenne | API utilisateurs / wallets / historique : tout utilisateur authentifié peut consulter **l’ensemble** des données (pas de scoping propriétaire). |
| A4 | 🟡 Basse | Absence de `docs/ETAT_DU_PROJET.md`. |
| A5 | 🟡 Basse | PostgreSQL local non démarré au moment de l’audit (runtime non vérifié hors tests). |
| A6 | 🟡 Basse | Login web via `/admin/login/` uniquement (pas d’UI auth métier). |
| A7 | 🟡 Basse | Pas de dépôt/crédit métier (soldes de test via helpers) — hors scope mais limite les scénarios démo. |
| A8 | 🟢 Info | Duplication légère `_validation_error_response` (API métier / admin). |
| A9 | 🟢 Info | Pas de dossiers `livrables/Prototype-*` (suivi par sprint seulement). |
| A10 | 🟢 Info | Livrables sprint parfois réduits à un seul `rapport-technique.md` (pas toujours de proposition de commit dédiée). |

Aucune anomalie bloquant la **cohérence avec le Sprint 6 validé** n’a été trouvée dans le code livré ; les écarts ci-dessus sont des **dettes / risques** pour la suite.

---

## 16. Fichiers inutilisés / duplications

- Pas de gros modules morts détectés : apps installées = apps utilisées.
- Duplication mineure de helpers de réponse d’erreur API.
- Pas de double arborescence prototype/sprint contradictoire.
- `.venv` correctement hors périmètre Git (attendu).

---

## 17. Recommandations (sans correction dans cet audit)

1. **Après validation** : créer le(s) commit(s) Git couvrant l’état Sprint 6 (message du type `feat(finance): administration et paramètres — Prototype 3 Sprint 6`).
2. Ajouter `docs/ETAT_DU_PROJET.md` (statut prototype/sprint, inventaire modules, dette connue).
3. Dans un prochain sprint sécurité / règles métier : **brancher** plafonds et mode maintenance dans `virement_service` / `paiement_service` (et tests associés).
4. Renforcer le **scoping** API lecture (utilisateurs, wallets, historique) — propriétaire ou staff uniquement.
5. Vérifier le runtime Docker (`docker compose up` + migrate) avant démo.
6. Envisager une UI de login métier si les écrans web doivent être utilisés hors `/admin/`.
7. Conserver la règle « logique dans les services » ; éviter d’empiler de la logique dans les vues API au fil des sprints.

---

## 18. Conclusion

L’application **11-finance** est dans un état **sain et aligné** avec le **Prototype 3 — Sprint 6**. Les contrôles automatisés (`check`, `pytest`) sont verts. La reprise peut s’envisager dès validation de cet audit, en priorisant le **versionnement Git** et en traitant ensuite les dettes de **paramètres effectifs** et de **scoping API**.

**Aucun code n’a été modifié** (hors création de ce rapport).  
**Aucun commit n’a été créé.**  
**Aucun développement n’a été poursuivi.**

---

*Fin de l’audit technique — en attente de validation.*
