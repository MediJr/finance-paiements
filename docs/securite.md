# Sécurité

> Phases du cycle de vie : **Conception** (exigences ENF-01 à ENF-10, sprint 7
> *Security by Design*) et **Audit / validation** (sprint 11).

## 1. Modèle de menace

| Actif à protéger | Menace | Attaquant |
|------------------|--------|-----------|
| Fonds des clients | Débit en double, solde négatif, contournement des plafonds | Client malveillant, erreur réseau |
| Annuaire des clients | Collecter nom et e-mail de tous les clients (hameçonnage ciblé) | Client authentifié |
| Comptes clients | Deviner un mot de passe, connecter une victime à un compte piégé | Attaquant externe |
| Données d'un autre client | Lire un portefeuille, un virement ou un historique qui ne lui appartient pas | Client authentifié |
| Back-office | Accéder aux paramètres ou aux exports | Client authentifié |
| Poste de l'administrateur | Exécution de formules à l'ouverture d'un export | Client malveillant |
| Traçabilité | Falsifier l'adresse IP journalisée | Attaquant externe |

## 2. Mesures en place

| Domaine | Mesure | Où |
|---------|--------|-----|
| Authentification | Espace client dédié ; mots de passe validés et hachés ; message d'échec identique ; blocage après 5 échecs par compte ou 20 par IP | `accounts/services/auth_service.py` |
| Sessions | Cookies `HttpOnly`, `SameSite=Lax`, durée paramétrable ; en production `Secure`, HSTS, redirection HTTPS | `settings/`, `administration/middleware.py` |
| CSRF | Sur tout le site ; imposé explicitement à l'inscription et à la connexion API ; déconnexion en POST | `api/views_client.py`, `accounts/views_auth.py` |
| Cloisonnement | Chaque service filtre sur l'utilisateur connecté ; vision globale réservée au personnel | `*/services/` |
| Annuaire | Bénéficiaire désigné par son e-mail exact ; aucune liste ni identifiant séquentiel exposé | `beneficiaires/services/` |
| Intégrité des fonds | Transaction atomique, verrous de ligne ordonnés, solde vérifié après verrouillage | `wallets/services/mouvement_service.py` |
| Idempotence | Clé unique par émetteur (formulaires : champ caché ; API : en-tête `Idempotency-Key`) | `virements`, `paiements`, `wallets` |
| Plafonds | Par opération, journalier cumulé, alimentation ; mode maintenance | `administration/services/securite_service.py` |
| Montants | 2 décimales maximum, valeurs finies, borne technique — refus plutôt qu'arrondi | `parse_montant` |
| Données de carte | Seuls les 4 derniers chiffres sont conservés | `wallets/services/passerelle_carte.py` |
| Exports | Réservés au personnel ; formules CSV neutralisées | `administration/services/export_service.py` |
| Adresse IP | `X-Forwarded-For` ignoré sauf proxy de confiance déclaré | `commun/http.py` |
| Journalisation | Connexions, échecs, blocages, alimentations, virements, paiements, actions d'administration | `observabilite/` |
| Déploiement | `DEBUG` désactivé par défaut ; démarrage refusé sans clé secrète ; conteneur non-root | `settings/production.py`, `docker/` |

Vérification automatique : `python backend/manage.py check --deploy` ne
remonte **aucun avertissement** avec `config.settings.production` (contrôlé en CI).

## 3. Audit — sprint 11

À la fin du prototype 4, j'ai audité mon propre code : lecture des services
(mouvements de fonds, bénéficiaires, paramètres, exports), des vues et des 31
routes API, puis parcours manuel complet en tant que client et administrateur.
Chaque défaut de sécurité ou fonctionnel (F1 à F10) a été corrigé **et** couvert par des tests (`tests/test_durcissement.py`).

| ID | Gravité | Défaut constaté | Correction |
|----|:-------:|-----------------|------------|
| F1 | 🔴 Critique | **Fuite de l'annuaire** : `POST /api/beneficiaires/` avec un identifiant séquentiel renvoyait le nom et l'e-mail du client ciblé ; le formulaire web affichait la liste de **tous** les clients. | Ajout uniquement par e-mail exact ; liste déroulante supprimée ; message d'erreur générique. |
| F2 | 🔴 Bloquant | **Aucun espace client** : seule la connexion `/admin/` (réservée au personnel) existait ; pas d'inscription, pas de déconnexion. | Inscription, connexion et déconnexion (web + API), espace client avec solde et dernières opérations. |
| F3 | 🔴 Bloquant | **Aucun moyen d'approvisionner un portefeuille** : tous les soldes restaient à 0 €, l'application était inutilisable. | Alimentation par carte via une passerelle simulée côté serveur (Luhn, refus, masquage, plafond). |
| F4 | 🟠 Élevée | **Double débit** : un double clic ou une requête rejouée exécutait deux virements. | Clé d'idempotence (champ caché, en-tête `Idempotency-Key`) + contrainte d'unicité en base. |
| F5 | 🟠 Élevée | **Plafond contournable** : seul le montant *par opération* était limité ; 10 virements de 9 999 € passaient. | Plafond journalier cumulé des sorties, contrôlé portefeuille verrouillé. |
| F6 | 🟡 Moyenne | **Arrondi silencieux** : `0.001` devenait `0.00` (opération de 0 €) ; `1e30` provoquait une erreur 500. | Refus des montants à plus de 2 décimales, non finis ou hors capacité. |
| F7 | 🟡 Moyenne | **Injection de formules CSV** : un motif `=HYPERLINK(...)` s'exécutait à l'ouverture d'un export par l'administrateur. | Neutralisation des cellules commençant par `=`, `+`, `-`, `@`. |
| F8 | 🟡 Moyenne | Pas de protection contre la **force brute** ni contre le **login CSRF** (à la création de l'espace client). | Blocage temporaire compte / IP ; `csrf_protect` sur l'API d'authentification ; redirection `next` validée. |
| F9 | 🟡 Moyenne | `X-Forwarded-For` toujours cru : IP falsifiable dans les journaux et contournement du blocage par IP. | En-tête ignoré sauf `TRUST_X_FORWARDED_FOR=True`. |
| F10 | 🟡 Moyenne | Configuration non sûre par défaut : `DEBUG=True`, pas de HSTS ni de cookies sécurisés, conteneur root avec le serveur de développement. | `settings/production.py`, `DEBUG=False` par défaut, Dockerfile non-root + Gunicorn + WhiteNoise. |
| F11 | 🔵 Qualité | Fichiers source en double interligne, nom de laboratoire visible dans l'interface et les exports. | Normalisation des fichiers ; produit renommé « Finance Paiements ». |

## 4. Limites connues et pistes

| Limite | Piste |
|--------|-------|
| Ajout d'un bénéficiaire : savoir si une adresse est cliente reste possible (comme sur les applications de paiement entre particuliers) | Limitation de débit sur l'ajout de bénéficiaires ; confirmation par le destinataire |
| Pas de double authentification | TOTP pour les opérations au-delà d'un seuil |
| Compteurs de connexion en cache mémoire | Redis en déploiement multi-instance |
| Passerelle de carte simulée | Prestataire réel en mode test ; l'interface `autoriser_carte()` reste identique |
