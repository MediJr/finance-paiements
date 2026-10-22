"""
Serializers API — lecture seule.

Aucune logique métier : mapping uniquement.
"""

from rest_framework import serializers

from accounts.models import Utilisateur
from beneficiaires.models import Beneficiaire
from historique.models import HistoriqueOperation
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Représentation lecture seule d'un Wallet."""

    utilisateur_id = serializers.IntegerField(source='utilisateur.id', read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id',
            'utilisateur_id',
            'solde',
            'devise',
            'statut',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class UtilisateurSerializer(serializers.ModelSerializer):
    """Représentation lecture seule d'un utilisateur métier."""

    username = serializers.CharField(source='user.username', read_only=True)
    wallet_id = serializers.IntegerField(
        source='wallet.id',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id',
            'username',
            'prenom',
            'nom',
            'email',
            'telephone',
            'est_actif',
            'wallet_id',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class HistoriqueOperationSerializer(serializers.ModelSerializer):
    """Représentation lecture seule d'une opération d'historique."""

    wallet_id = serializers.IntegerField(source='wallet.id', read_only=True)
    type_operation_display = serializers.CharField(
        source='get_type_operation_display',
        read_only=True,
    )
    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True,
    )

    class Meta:
        model = HistoriqueOperation
        fields = [
            'id',
            'wallet_id',
            'type_operation',
            'type_operation_display',
            'statut',
            'statut_display',
            'description',
            'montant',
            'devise',
            'reference',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class BeneficiaireSerializer(serializers.ModelSerializer):
    """Représentation d'un bénéficiaire."""

    proprietaire_id = serializers.IntegerField(source='proprietaire.id', read_only=True)
    utilisateur_beneficiaire_id = serializers.IntegerField(
        source='utilisateur_beneficiaire.id',
        read_only=True,
    )
    beneficiaire_nom = serializers.SerializerMethodField()
    beneficiaire_email = serializers.EmailField(
        source='utilisateur_beneficiaire.email',
        read_only=True,
    )
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Beneficiaire
        fields = [
            'id',
            'proprietaire_id',
            'utilisateur_beneficiaire_id',
            'beneficiaire_nom',
            'beneficiaire_email',
            'alias',
            'statut',
            'statut_display',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = [
            'id',
            'proprietaire_id',
            'utilisateur_beneficiaire_id',
            'beneficiaire_nom',
            'beneficiaire_email',
            'statut_display',
            'date_creation',
            'date_mise_a_jour',
        ]

    def get_beneficiaire_nom(self, obj):
        u = obj.utilisateur_beneficiaire
        return f'{u.prenom} {u.nom}'


class BeneficiaireCreateSerializer(serializers.Serializer):
    """Payload de création d'un bénéficiaire."""

    # Destinataire désigné par son e-mail exact (pas d'identifiant énumérable).
    email = serializers.EmailField()
    alias = serializers.CharField(max_length=150, required=False, allow_blank=True)


class BeneficiaireUpdateSerializer(serializers.Serializer):
    """Payload de modification d'un bénéficiaire."""

    alias = serializers.CharField(max_length=150, required=False, allow_blank=True)
    statut = serializers.ChoiceField(
        choices=Beneficiaire.Statut.choices,
        required=False,
    )


class VirementSerializer(serializers.ModelSerializer):
    """Représentation lecture seule d'un virement."""

    wallet_emetteur_id = serializers.IntegerField(
        source='wallet_emetteur.id',
        read_only=True,
    )
    wallet_beneficiaire_id = serializers.IntegerField(
        source='wallet_beneficiaire.id',
        read_only=True,
    )
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Virement
        fields = [
            'id',
            'reference',
            'wallet_emetteur_id',
            'wallet_beneficiaire_id',
            'montant',
            'devise',
            'statut',
            'statut_display',
            'motif',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class VirementCreateSerializer(serializers.Serializer):
    """Payload d'exécution d'un virement."""

    beneficiaire_id = serializers.IntegerField(min_value=1)
    montant = serializers.DecimalField(max_digits=14, decimal_places=2)
    motif = serializers.CharField(max_length=255, required=False, allow_blank=True)


class PaiementSerializer(serializers.ModelSerializer):
    wallet_payeur_id = serializers.IntegerField(source='wallet_payeur.id', read_only=True)
    wallet_beneficiaire_id = serializers.IntegerField(
        source='wallet_beneficiaire.id',
        read_only=True,
    )
    montant_restant = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Paiement
        fields = [
            'id',
            'reference',
            'wallet_payeur_id',
            'wallet_beneficiaire_id',
            'montant',
            'montant_rembourse',
            'montant_restant',
            'devise',
            'statut',
            'statut_display',
            'motif',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class PaiementCreateSerializer(serializers.Serializer):
    beneficiaire_id = serializers.IntegerField(min_value=1)
    montant = serializers.DecimalField(max_digits=14, decimal_places=2)
    motif = serializers.CharField(max_length=255, required=False, allow_blank=True)


class RemboursementSerializer(serializers.ModelSerializer):
    paiement_id = serializers.IntegerField(source='paiement.id', read_only=True)
    paiement_reference = serializers.CharField(source='paiement.reference', read_only=True)
    wallet_remboursant_id = serializers.IntegerField(
        source='wallet_remboursant.id',
        read_only=True,
    )
    wallet_rembourse_id = serializers.IntegerField(
        source='wallet_rembourse.id',
        read_only=True,
    )
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Remboursement
        fields = [
            'id',
            'reference',
            'paiement_id',
            'paiement_reference',
            'wallet_remboursant_id',
            'wallet_rembourse_id',
            'montant',
            'devise',
            'statut',
            'statut_display',
            'date_creation',
            'date_mise_a_jour',
        ]
        read_only_fields = fields


class RemboursementCreateSerializer(serializers.Serializer):
    paiement_id = serializers.IntegerField(min_value=1)
    montant = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
    )


class ParametresSerializer(serializers.Serializer):
    """Paramètres globaux (lecture / écriture admin)."""

    nom_application = serializers.CharField(max_length=200)
    devise_par_defaut = serializers.CharField(max_length=3)
    mode_maintenance = serializers.BooleanField()
    montant_virement_max = serializers.DecimalField(max_digits=14, decimal_places=2)
    montant_paiement_max = serializers.DecimalField(max_digits=14, decimal_places=2)
    plafond_journalier = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    montant_alimentation_max = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False
    )
    delai_session_minutes = serializers.IntegerField(min_value=1)
    date_mise_a_jour = serializers.DateTimeField(read_only=True)


class AdminUtilisateurSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source='user.username')
    prenom = serializers.CharField()
    nom = serializers.CharField()
    email = serializers.EmailField()
    est_actif = serializers.BooleanField()
    date_creation = serializers.DateTimeField()


class AdminWalletSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    utilisateur_id = serializers.IntegerField(source='utilisateur.id')
    utilisateur_email = serializers.EmailField(source='utilisateur.email')
    solde = serializers.DecimalField(max_digits=14, decimal_places=2)
    devise = serializers.CharField()
    statut = serializers.CharField()
    date_creation = serializers.DateTimeField()


class EvenementSerializer(serializers.Serializer):
    """Événement d'observabilité (lecture seule)."""

    id = serializers.IntegerField()
    date_creation = serializers.DateTimeField()
    type_evenement = serializers.CharField()
    niveau = serializers.CharField()
    module = serializers.CharField()
    utilisateur_id = serializers.IntegerField(allow_null=True)
    username = serializers.SerializerMethodField()
    description = serializers.CharField()
    contexte = serializers.JSONField()
    adresse_ip = serializers.CharField(allow_null=True, required=False)
    user_agent = serializers.CharField()

    def get_username(self, obj):
        user = getattr(obj, 'utilisateur', None)
        return user.username if user is not None else None
