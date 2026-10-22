"""
Vues API REST.

La logique métier est déléguée aux services.
Security by Design — Sprint 7 : scoping propriétaire / vision admin.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import get_utilisateur, list_utilisateurs
from api.serializers import (
    BeneficiaireCreateSerializer,
    BeneficiaireSerializer,
    BeneficiaireUpdateSerializer,
    HistoriqueOperationSerializer,
    PaiementCreateSerializer,
    PaiementSerializer,
    RemboursementCreateSerializer,
    RemboursementSerializer,
    UtilisateurSerializer,
    VirementCreateSerializer,
    VirementSerializer,
    WalletSerializer,
)
from beneficiaires.services import (
    ajouter_beneficiaire_par_email,
    desactiver_beneficiaire,
    get_beneficiaire_pour_proprietaire,
    get_utilisateur_connecte,
    list_beneficiaires,
    update_beneficiaire,
)
from historique.services import get_historique_operation, list_historique_operations
from paiements.services import (
    executer_paiement,
    executer_remboursement,
    get_paiement_pour_utilisateur,
    get_remboursement_pour_utilisateur,
    list_paiements,
    list_remboursements,
)
from virements.services import (
    executer_virement,
    get_virement_pour_utilisateur,
    list_virements,
)
from wallets.services import get_wallet, get_wallet_for_utilisateur


def _validation_error_response(exc: ValidationError):
    if hasattr(exc, 'message_dict'):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    messages = getattr(exc, 'messages', [str(exc)])
    return Response({'detail': messages}, status=status.HTTP_400_BAD_REQUEST)


def _statut_creation(operation) -> int:
    """201 à la création, 200 lorsqu'une clé d'idempotence rejoue une opération existante."""
    if getattr(operation, 'est_rejeu', False):
        return status.HTTP_200_OK
    return status.HTTP_201_CREATED


def _scope_acteur(request):
    """
    Résout le scope API.

    Retourne (utilisateur_metier|None, vue_admin: bool).
    Staff → vision globale. Sinon → profil métier obligatoire.
    """
    if request.user.is_staff:
        return None, True
    try:
        return get_utilisateur_connecte(request.user), False
    except PermissionDenied as exc:
        raise PermissionDenied(str(exc)) from exc


def _filters_from_request(request, *, wallet_id=None):
    """Extrait les filtres d'historique depuis la requête HTTP."""
    raw_wallet = request.query_params.get('wallet')
    parsed_wallet = wallet_id
    if parsed_wallet is None and raw_wallet:
        try:
            parsed_wallet = int(raw_wallet)
        except (TypeError, ValueError):
            parsed_wallet = None
    return {
        'wallet_id': parsed_wallet,
        'type_operation': request.query_params.get('type') or None,
        'statut': request.query_params.get('statut') or None,
        'date_debut': request.query_params.get('date_debut') or None,
        'date_fin': request.query_params.get('date_fin') or None,
        'reference': request.query_params.get('reference') or None,
    }


class ApiRootView(APIView):
    """Racine technique de l'API."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                'application': 'finance-paiements',
                'api': 'v1',
                'status': 'ready',
                'endpoints': {
                    'utilisateurs': '/api/utilisateurs/',
                    'wallets': '/api/wallets/<id>/',
                    'historique': '/api/historique/',
                    'beneficiaires': '/api/beneficiaires/',
                    'virements': '/api/virements/',
                    'paiements': '/api/paiements/',
                    'remboursements': '/api/remboursements/',
                    'administration': '/api/administration/',
                    'dashboard': '/api/administration/dashboard/',
                    'statistiques': '/api/administration/statistiques/',
                    'rapports': '/api/administration/rapports/',
                },
            }
        )


class UtilisateurListAPIView(APIView):
    """GET /api/utilisateurs/ — profil propre ou liste admin."""

    def get(self, request):
        try:
            acteur, vue_admin = _scope_acteur(request)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        utilisateurs = list_utilisateurs(demandeur=acteur, vue_admin=vue_admin)
        serializer = UtilisateurSerializer(utilisateurs, many=True)
        return Response(serializer.data)


class UtilisateurDetailAPIView(APIView):
    """GET /api/utilisateurs/<id>/ — détail (propre ou admin)."""

    def get(self, request, pk):
        try:
            acteur, vue_admin = _scope_acteur(request)
            utilisateur = get_utilisateur(
                pk,
                demandeur=acteur,
                vue_admin=vue_admin,
            )
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        serializer = UtilisateurSerializer(utilisateur)
        return Response(serializer.data)


class UtilisateurWalletAPIView(APIView):
    """GET /api/utilisateurs/<id>/wallet/ — Wallet (propre ou admin)."""

    def get(self, request, pk):
        try:
            acteur, vue_admin = _scope_acteur(request)
            wallet = get_wallet_for_utilisateur(
                pk,
                demandeur=acteur,
                vue_admin=vue_admin,
            )
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class WalletDetailAPIView(APIView):
    """GET /api/wallets/<id>/ — consultation d'un Wallet (propre ou admin)."""

    def get(self, request, pk):
        try:
            acteur, vue_admin = _scope_acteur(request)
            wallet = get_wallet(pk, proprietaire=acteur, vue_admin=vue_admin)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class HistoriqueListAPIView(APIView):
    """GET /api/historique/ — historique scoped propriétaire."""

    def get(self, request):
        try:
            acteur, vue_admin = _scope_acteur(request)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        try:
            operations = list_historique_operations(
                **_filters_from_request(request),
                proprietaire=acteur,
                vue_admin=vue_admin,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        serializer = HistoriqueOperationSerializer(operations, many=True)
        return Response(serializer.data)


class HistoriqueDetailAPIView(APIView):
    """GET /api/historique/<id>/ — détail scoped."""

    def get(self, request, pk):
        try:
            acteur, vue_admin = _scope_acteur(request)
            operation = get_historique_operation(
                pk,
                proprietaire=acteur,
                vue_admin=vue_admin,
            )
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        serializer = HistoriqueOperationSerializer(operation)
        return Response(serializer.data)


class WalletHistoriqueAPIView(APIView):
    """GET /api/wallets/<id>/historique/ — historique d'un Wallet accessible."""

    def get(self, request, pk):
        try:
            acteur, vue_admin = _scope_acteur(request)
            get_wallet(pk, proprietaire=acteur, vue_admin=vue_admin)
            operations = list_historique_operations(
                **_filters_from_request(request, wallet_id=pk),
                proprietaire=acteur,
                vue_admin=vue_admin,
            )
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return _validation_error_response(exc)
        serializer = HistoriqueOperationSerializer(operations, many=True)
        return Response(serializer.data)


class BeneficiaireListCreateAPIView(APIView):
    """GET/POST /api/beneficiaires/ — liste et création (propriétaire connecté)."""

    def get(self, request):
        try:
            proprietaire = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        statut = request.query_params.get('statut') or None
        beneficiaires = list_beneficiaires(proprietaire=proprietaire, statut=statut)
        serializer = BeneficiaireSerializer(beneficiaires, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            proprietaire = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        payload = BeneficiaireCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            beneficiaire = ajouter_beneficiaire_par_email(
                proprietaire=proprietaire,
                email=payload.validated_data['email'],
                alias=payload.validated_data.get('alias', ''),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(
            BeneficiaireSerializer(beneficiaire).data,
            status=status.HTTP_201_CREATED,
        )


class BeneficiaireDetailAPIView(APIView):
    """GET/PATCH/PUT/DELETE /api/beneficiaires/<id>/."""

    def get(self, request, pk):
        try:
            proprietaire = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        beneficiaire = get_beneficiaire_pour_proprietaire(
            proprietaire=proprietaire,
            beneficiaire_id=pk,
        )
        return Response(BeneficiaireSerializer(beneficiaire).data)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def _update(self, request, pk, *, partial):
        try:
            proprietaire = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        payload = BeneficiaireUpdateSerializer(data=request.data, partial=partial)
        payload.is_valid(raise_exception=True)
        if not payload.validated_data:
            return Response(
                {'detail': 'Aucun champ à mettre à jour.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            beneficiaire = update_beneficiaire(
                proprietaire=proprietaire,
                beneficiaire_id=pk,
                alias=payload.validated_data.get('alias'),
                statut=payload.validated_data.get('statut'),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(BeneficiaireSerializer(beneficiaire).data)

    def delete(self, request, pk):
        """Désactivation logique (pas de suppression physique)."""
        try:
            proprietaire = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        try:
            beneficiaire = desactiver_beneficiaire(
                proprietaire=proprietaire,
                beneficiaire_id=pk,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(BeneficiaireSerializer(beneficiaire).data)


class VirementListCreateAPIView(APIView):
    """GET/POST /api/virements/ — liste et exécution."""

    def get(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        virements = list_virements(utilisateur=utilisateur)
        return Response(VirementSerializer(virements, many=True).data)

    def post(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        payload = VirementCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            virement = executer_virement(
                emetteur=utilisateur,
                beneficiaire_id=payload.validated_data['beneficiaire_id'],
                montant=payload.validated_data['montant'],
                motif=payload.validated_data.get('motif', ''),
                cle_idempotence=request.headers.get('Idempotency-Key'),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(
            VirementSerializer(virement).data,
            status=_statut_creation(virement),
        )


class VirementDetailAPIView(APIView):
    """GET /api/virements/<id>/ — détail d'un virement accessible."""

    def get(self, request, pk):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        virement = get_virement_pour_utilisateur(
            utilisateur=utilisateur,
            virement_id=pk,
        )
        return Response(VirementSerializer(virement).data)


class PaiementListCreateAPIView(APIView):
    """GET/POST /api/paiements/."""

    def get(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            PaiementSerializer(list_paiements(utilisateur=utilisateur), many=True).data
        )

    def post(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        payload = PaiementCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            paiement = executer_paiement(
                payeur=utilisateur,
                beneficiaire_id=payload.validated_data['beneficiaire_id'],
                montant=payload.validated_data['montant'],
                motif=payload.validated_data.get('motif', ''),
                cle_idempotence=request.headers.get('Idempotency-Key'),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(PaiementSerializer(paiement).data, status=_statut_creation(paiement))


class PaiementDetailAPIView(APIView):
    """GET /api/paiements/<id>/."""

    def get(self, request, pk):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        paiement = get_paiement_pour_utilisateur(
            utilisateur=utilisateur,
            paiement_id=pk,
        )
        return Response(PaiementSerializer(paiement).data)


class RemboursementListCreateAPIView(APIView):
    """GET/POST /api/remboursements/."""

    def get(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            RemboursementSerializer(
                list_remboursements(utilisateur=utilisateur),
                many=True,
            ).data
        )

    def post(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        payload = RemboursementCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            remboursement = executer_remboursement(
                acteur=utilisateur,
                paiement_id=payload.validated_data['paiement_id'],
                montant=payload.validated_data.get('montant'),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(
            RemboursementSerializer(remboursement).data,
            status=status.HTTP_201_CREATED,
        )


class RemboursementDetailAPIView(APIView):
    """GET /api/remboursements/<id>/."""

    def get(self, request, pk):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        remboursement = get_remboursement_pour_utilisateur(
            utilisateur=utilisateur,
            remboursement_id=pk,
        )
        return Response(RemboursementSerializer(remboursement).data)
