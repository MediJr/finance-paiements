# Stratégie de test

> Phase du cycle de vie : **Tests**.

## 1. Chiffres

| Indicateur | Valeur |
|------------|--------|
| Tests automatisés | **169** (pytest + pytest-django) |
| Résultat | 169 réussis (SQLite et PostgreSQL) |
| Couverture du code applicatif | **86 %** (migrations et tests exclus) |
| Durée de la suite | ≈ 6 secondes |
| Exécution automatique | GitHub Actions à chaque push et pull request |

## 2. Niveaux de test

| Niveau | Ce qui est vérifié | Exemples |
|--------|--------------------|----------|
| Unitaire (services) | Règles métier isolées : solde, plafonds, montants, passerelle de carte | `test_solde_insuffisant`, `test_montants_invalides_rejetes` |
| Intégrité financière | Atomicité : un échec en cours de route n'altère aucun solde | `test_transaction_atomique_en_cas_echec_historique`, `test_remboursement_historique_et_atomicite` |
| Intégration (web / API) | Requête HTTP complète : permissions, codes de retour, rendu | `test_api_virement_et_acces`, `test_vues_web_paiements_remboursements` |
| Sécurité | Une attaque par test : accès aux données d'autrui (IDOR), énumération, double soumission, force brute, CSRF | `tests/test_securite.py`, `tests/test_durcissement.py` |
| Non-régression | Défaut corrigé = test ajouté | `test_api_refuse_l_ajout_par_identifiant` |

## 3. Exécuter les tests

```bash
pip install -r requirements-dev.txt

pytest                                  # suite complète (SQLite en mémoire)
pytest tests/test_durcissement.py       # audit de sécurité du sprint 11
pytest --cov --cov-report=term          # avec couverture
pytest --ds=config.settings.test_postgres   # sur PostgreSQL (verrous de ligne réels)
```

## 4. Répartition par fichier

| Fichier | Tests | Sprint | Domaine |
|---------|:-----:|:------:|---------|
| `test_configuration.py` | 7 | 0 | Configuration |
| `test_utilisateurs_wallets.py` | 14 | 1 | Utilisateurs, portefeuilles |
| `test_historique.py` | 11 | 2 | Historique des opérations |
| `test_beneficiaires.py` | 12 | 3 | Bénéficiaires |
| `test_virements.py` | 15 | 4 | Virements |
| `test_paiements.py` | 13 | 5 | Paiements, remboursements |
| `test_administration.py` | 8 | 6 | Administration, paramètres |
| `test_securite.py` | 12 | 7 | Security by Design (cloisonnement, plafonds, maintenance) |
| `test_pilotage.py` | 11 | 8 | Tableau de bord, statistiques, rapports |
| `test_observabilite.py` | 9 | 9 | Journal d'événements |
| `test_exports.py` | 9 | 10 | Exports |
| `test_durcissement.py` | 48 | 11 | Audit de sécurité (F1 à F10), espace client, alimentation |

## 5. Matrice de traçabilité

Chaque exigence du [cahier des charges](cahier-des-charges.md) est vérifiée
par au moins un test.

| Exigence | Tests représentatifs |
|----------|----------------------|
| EF-01 Compte et portefeuille | `test_inscription_web_cree_compte_wallet_et_session`, `test_wallet_cree_automatiquement`, `test_solde_initial_est_zero` |
| EF-02 Connexion client | `test_client_se_connecte_hors_du_site_admin`, `test_deconnexion_post_uniquement`, `test_accueil_oriente_client_et_personnel` |
| EF-03 Consultation | `test_api_wallet_lecture`, `test_vues_web_utilisateurs_et_wallet` |
| EF-04 Alimentation | `test_alimentation_acceptee_credite_et_trace`, `test_alimentation_refusee_ne_credite_pas`, `test_api_alimentation_codes_retour` |
| EF-05 Historique | `test_filtres_type_et_statut`, `test_filtre_periode`, `test_historique_automatique` |
| EF-06 Bénéficiaires | `test_api_ajout_par_email`, `test_unicite_beneficiaire_par_utilisateur`, `test_desactivation_et_reactivation` |
| EF-07 Virements | `test_virement_valide`, `test_solde_insuffisant`, `test_transaction_atomique_en_cas_echec_historique` |
| EF-08 Paiements / remboursements | `test_paiement_valide`, `test_remboursement_total_puis_refus`, `test_remboursement_montant_excessif` |
| EF-09 Idempotence | `test_double_soumission_virement_un_seul_debit`, `test_api_virement_idempotency_key`, `test_double_soumission_paiement_web` |
| EF-10 Supervision | `test_consultation_wallets_et_operations`, `test_activation_desactivation_utilisateur` |
| EF-11 Paramètres et plafonds | `test_plafond_virement`, `test_plafond_journalier_cumule`, `test_mode_maintenance_bloque_operations` |
| EF-12 Journal d'administration | `test_journal_modification_parametres_et_activation`, `test_journal_acces_admin` |
| EF-13 Pilotage | `test_dashboard_compteurs`, `test_statistiques_filtre_utilisateur`, `test_rapport_virements` |
| EF-14 Événements | `test_evenement_immutable`, `test_middleware_journalise_exception` |
| EF-15 Exports | `test_export_tous_types_json`, `test_export_csv_neutralise_motif` |
| ENF-02 Cloisonnement | `test_idor_api_utilisateurs_wallets`, `test_idor_api_historique`, `test_acces_interdit_autre_proprietaire` |
| ENF-03 Annuaire | `test_formulaire_beneficiaire_ne_liste_pas_les_clients`, `test_api_refuse_l_ajout_par_identifiant` |
| ENF-04 Force brute | `test_blocage_apres_echecs`, `test_blocage_par_adresse_ip` |
| ENF-05 CSRF, redirections, CSV | `test_connexion_api_exige_csrf`, `test_connexion_ignore_une_redirection_externe`, `test_neutraliser_formule` |
| ENF-06 Données de carte | `test_numero_de_carte_jamais_conserve`, `test_carte_invalide_rejetee_sans_trace` |
| ENF-08 Montants | `test_montants_invalides_rejetes`, `test_montant_non_positif` |
| ENF-12 Production | `test_production_refuse_de_demarrer_sans_cle_secrete`, `test_production_active_les_protections_https` |
