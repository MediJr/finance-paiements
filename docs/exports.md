# Exports de données — Prototype 4 Sprint 10

Exports CSV / JSON réservés aux administrateurs.

Ce n'est **pas** un moteur Analytics ni un SIEM.

## Service

`administration.services.export_service.exporter`

Unique point de génération des fichiers. Les vues délèguent uniquement.

## Format stable `finance-export-v1`

### JSON

```json
{
  "export": {
    "application": "11-finance",
    "version": "finance-export-v1",
    "type": "virements",
    "format": "json",
    "generated_at": "2026-08-06T04:00:00+01:00",
    "filtres": {
      "date_debut": null,
      "date_fin": null,
      "statut": null
    },
    "count": 1
  },
  "data": [
    {
      "id": 1,
      "reference": "VIR-…",
      "montant": "25.00",
      "statut": "reussi"
    }
  ]
}
```

### CSV

- UTF-8 avec BOM (`\ufeff`) pour compatibilité tableurs
- Première ligne = en-têtes
- Une ligne par enregistrement
- Les champs JSON (ex. `contexte` des événements) sont sérialisés en chaîne JSON

## Jeux de données

| Type | Contenu |
|------|---------|
| `utilisateurs` | Profils métier |
| `wallets` | Portefeuilles |
| `beneficiaires` | Liens bénéficiaires |
| `virements` | Virements |
| `paiements` | Paiements |
| `remboursements` | Remboursements |
| `historique` | Historique des opérations |
| `evenements` | Journal d'observabilité |

Chaque export est indépendant.

## Filtres

| Paramètre | Effet |
|-----------|-------|
| `type` | Jeu de données (obligatoire côté usage) |
| `format` (web) / `export_format` (API) | `csv` ou `json` |
| `date_debut` / `date_fin` | Période sur `date_creation` |
| `statut` | Statut métier, ou niveau pour `evenements` |

## Interfaces

| Canal | URL |
|-------|-----|
| Web | `/administration/exports/` |
| Téléchargement web | `/administration/exports/telecharger/?type=…&format=…` |
| API | `GET /api/administration/exports/?type=…&export_format=csv\|json` |

Permission : `is_staff` uniquement.

## Exemples

```bash
# JSON — utilisateurs
curl -b cookies.txt "http://127.0.0.1:8001/api/administration/exports/?type=utilisateurs&export_format=json"

# CSV — virements réussis sur une période
curl -b cookies.txt "http://127.0.0.1:8001/api/administration/exports/?type=virements&export_format=csv&statut=reussi&date_debut=2026-01-01&date_fin=2026-12-31"
```

Les exports sont journalisés dans l'observabilité (`admin_export`).
