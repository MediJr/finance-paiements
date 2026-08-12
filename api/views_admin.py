"""
Vues API — administration fonctionnelle + pilotage (Sprint 8).
"""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.http import client_ip
from administration.services import (
    exporter,
    generer_rapport,
    get_dashboard,
    get_parametres,
    get_statistiques,
    list_historique_admin,
    list_paiements_admin,
    list_remboursements_admin,
    list_utilisateurs_admin,
    list_virements_admin,
    list_wallets_admin,
    update_parametres,
)
from api.permissions import IsAdministrateur
from api.serializers import (
    AdminUtilisateurSerializer,
    AdminWalletSerializer,
    EvenementSerializer,
    HistoriqueOperationSerializer,
    PaiementSerializer,
    ParametresSerializer,
    RemboursementSerializer,
    VirementSerializer,
)
from observabilite.services.journal_service import get_evenement, list_evenements


def _validation_error_response(exc: ValidationError):
    messages = getattr(exc, 'messages', [str(exc)])
    return Response({'detail': messages}, status=status.HTTP_400_BAD_REQUEST)


def _filtres_request(request):
    return {
        'date_debut': request.query_params.get('date_debut') or None,
        'date_fin': request.query_params.get('date_fin') or None,
        'statut': request.query_params.get('statut') or None,
        'utilisateur_id': request.query_params.get('utilisateur') or None,
    }


class AdminParametresAPIView(APIView):
    """GET/PUT/PATCH /api/administration/parametres/"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        parametres = get_parametres(administrateur=request.user)
        return Response(ParametresSerializer(parametres).data)

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, *, partial):
        serializer = ParametresSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            parametres = update_parametres(
                administrateur=request.user,
                adresse_ip=client_ip(request),
                **serializer.validated_data,
            )
        except (ValidationError, PermissionDenied) as exc:
            if isinstance(exc, PermissionDenied):
                return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
            return _validation_error_response(exc)
        return Response(ParametresSerializer(parametres).data)


class AdminUtilisateursAPIView(APIView):
    """GET /api/administration/utilisateurs/"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        actif = request.query_params.get('est_actif')
        est_actif = None
        if actif in ('1', 'true', 'True'):
            est_actif = True
        elif actif in ('0', 'false', 'False'):
            est_actif = False
        utilisateurs = list_utilisateurs_admin(
            administrateur=request.user,
            q=request.query_params.get('q') or None,
            est_actif=est_actif,
        )
        return Response(AdminUtilisateurSerializer(utilisateurs, many=True).data)


class AdminWalletsAPIView(APIView):
    """GET /api/administration/wallets/"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        wallets = list_wallets_admin(
            administrateur=request.user,
            q=request.query_params.get('q') or None,
            statut=request.query_params.get('statut') or None,
            devise=request.query_params.get('devise') or None,
        )
        return Response(AdminWalletSerializer(wallets, many=True).data)


class AdminOperationsAPIView(APIView):
    """GET /api/administration/operations/?type=historique|virements|paiements|remboursements"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        type_op = request.query_params.get('type') or 'historique'
        q = request.query_params.get('q') or None
        statut = request.query_params.get('statut') or None
        admin = request.user

        if type_op == 'virements':
            data = VirementSerializer(
                list_virements_admin(administrateur=admin, q=q, statut=statut),
                many=True,
            ).data
        elif type_op == 'paiements':
            data = PaiementSerializer(
                list_paiements_admin(administrateur=admin, q=q, statut=statut),
                many=True,
            ).data
        elif type_op == 'remboursements':
            data = RemboursementSerializer(
                list_remboursements_admin(administrateur=admin, q=q, statut=statut),
                many=True,
            ).data
        else:
            data = HistoriqueOperationSerializer(
                list_historique_admin(
                    administrateur=admin,
                    q=q,
                    type_operation=request.query_params.get('type_operation') or None,
                    statut=statut,
                ),
                many=True,
            ).data
            type_op = 'historique'

        return Response({'type': type_op, 'results': data})


class AdminDashboardAPIView(APIView):
    """GET /api/administration/dashboard/"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        return Response(get_dashboard(administrateur=request.user))


class AdminStatistiquesAPIView(APIView):
    """GET /api/administration/statistiques/"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        try:
            data = get_statistiques(
                administrateur=request.user,
                **_filtres_request(request),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(data)


class AdminRapportsAPIView(APIView):
    """GET /api/administration/rapports/?type=virements|paiements|…"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        try:
            data = generer_rapport(
                administrateur=request.user,
                type_rapport=request.query_params.get('type') or 'virements',
                **_filtres_request(request),
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(data)


class AdminEvenementListAPIView(APIView):
    """GET /api/administration/evenements/ — lecture seule."""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        try:
            evenements = list_evenements(
                administrateur=request.user,
                niveau=request.query_params.get('niveau') or None,
                module=request.query_params.get('module') or None,
                type_evenement=request.query_params.get('type') or None,
                utilisateur_id=request.query_params.get('utilisateur') or None,
                date_debut=request.query_params.get('date_debut') or None,
                date_fin=request.query_params.get('date_fin') or None,
                q=request.query_params.get('q') or None,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        return Response(EvenementSerializer(evenements, many=True).data)


class AdminEvenementDetailAPIView(APIView):
    """GET /api/administration/evenements/<id>/ — lecture seule."""

    permission_classes = [IsAdministrateur]

    def get(self, request, pk):
        evenement = get_evenement(administrateur=request.user, evenement_id=pk)
        return Response(EvenementSerializer(evenement).data)


class AdminExportAPIView(APIView):
    """GET /api/administration/exports/?type=…&export_format=csv|json"""

    permission_classes = [IsAdministrateur]

    def get(self, request):
        # Ne pas utiliser le query param DRF « format » (négociation de contenu).
        format_export = (
            request.query_params.get('export_format')
            or request.query_params.get('fmt')
            or 'json'
        )
        try:
            result = exporter(
                administrateur=request.user,
                type_export=request.query_params.get('type') or 'utilisateurs',
                format_export=format_export,
                date_debut=request.query_params.get('date_debut') or None,
                date_fin=request.query_params.get('date_fin') or None,
                statut=request.query_params.get('statut') or None,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)

        from django.http import HttpResponse

        response = HttpResponse(
            result['content'],
            content_type=result['content_type'],
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{result["filename"]}"'
        )
        return response
