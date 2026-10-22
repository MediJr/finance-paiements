# Guide de démonstration (5 minutes)

Scénario pour présenter l'application en direct. Prérequis : application lancée
avec les comptes de démonstration ([installation.md](installation.md), option 1).

## 1. Le parcours client (2 min)

1. Se connecter avec `alice` / `Alice-Demo-2026` → **Mon espace** : solde de
   1 500 EUR, actions rapides, dernières opérations.
2. **Alimenter** avec la carte refusée `4000 0000 0000 0002` → refus de la
   « banque », solde inchangé, tentative tracée avec `•••• 0002`.
3. **Alimenter** 100 EUR avec `4242 4242 4242 4242` → solde crédité.
4. **Faire un virement** de 120 EUR à Bob → débit et crédit atomiques, historique
   des deux côtés.
5. **Payer** Bob, puis se connecter en `bob` et **rembourser** partiellement.
6. Montrer **Ajouter un bénéficiaire** : on saisit un e-mail, aucune liste de
   clients n'apparaît.

## 2. L'administration (1 min)

Se connecter avec `admin` / `Admin-Demo-2026` :

- **Tableau de bord** et **statistiques** ;
- **Paramètres** : plafond par opération, plafond journalier, plafond
  d'alimentation, mode maintenance — puis activer la maintenance et montrer
  qu'un virement est refusé ;
- **Journal** des actions d'administration et **événements** (connexions,
  alimentations, virements) ;
- **Exports** CSV / JSON.

## 3. La qualité (2 min)

```bash
pytest -q                            # 169 tests en quelques secondes
pytest tests/test_durcissement.py -v
```

Points à présenter :

- **Un seul module modifie les soldes** (`mouvement_service`) : verrous de ligne
  dans un ordre stable, solde vérifié après verrouillage, tout dans une
  transaction ([architecture.md](architecture.md)).
- **Audit de sécurité de mon propre code** : 11 défauts corrigés, dont la fuite
  de l'annuaire des clients et le double débit sur double clic ([securite.md](securite.md)).
- **Idempotence** : même clé = même opération, comme les API de paiement réelles.
- **Méthode** : prototypage évolutif + Scrum, exigences tracées jusqu'aux tests
  ([cycle-de-vie.md](cycle-de-vie.md), [tests.md](tests.md#5-matrice-de-traçabilité)).

## Questions probables et réponses courtes

| Question | Réponse |
|----------|---------|
| Comment évitez-vous un solde négatif avec deux virements simultanés ? | Les deux portefeuilles sont verrouillés (`select_for_update`) avant le contrôle du solde ; le second virement attend le premier puis voit le solde à jour. |
| Et un interblocage entre deux virements croisés ? | Les verrous sont toujours pris dans l'ordre des identifiants. |
| Que se passe-t-il si l'historique échoue après le débit ? | Tout est dans la même transaction : rollback complet, testé. |
| Pourquoi refuser `0.001` au lieu d'arrondir ? | Un arrondi silencieux crée des opérations de 0 € et masque des erreurs du client. |
| Pourquoi une carte simulée ? | Pas de compte marchand ; l'interface `autoriser_carte()` se remplace par un prestataire réel sans toucher au reste. |
| Que feriez-vous ensuite ? | Double authentification, prestataire de paiement réel en mode test, Redis pour le cache en multi-serveur. |
