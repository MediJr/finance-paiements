"""
Vues API — authentification des clients et alimentation du Wallet.

L'inscription et la connexion n'ont pas de classe d'authentification : DRF
n'y applique donc pas le CSRF. Il est imposé explicitement (`csrf_protect`)
pour empêcher un site tiers de connecter un visiteur à son insu.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import authentifier_client, deconnecter, inscrire_client
from beneficiaires.services import get_utilisateur_connecte
from wallets.models import Alimentation
from wallets.services import alimenter_wallet, list_alimentations


class InscriptionSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    prenom = serializers.CharField(max_length=150)
    nom = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telephone = serializers.CharField(max_length=30, required=False, allow_blank=True)


class ConnexionSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class AlimentationCreateSerializer(serializers.Serializer):
    montant = serializers.DecimalField(max_digits=14, decimal_places=2)
    numero_carte = serializers.CharField(max_length=23, write_only=True)


class AlimentationSerializer(serializers.ModelSerializer):
    wallet_id = serializers.IntegerField(source='wallet.id', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Alimentation
        fields = [
            'id',
            'reference',
            'wallet_id',
            'montant',
            'devise',
            'statut',
            'statut_display',
            'carte_masquee',
            'motif_refus',
            'date_creation',
        ]
        read_only_fields = fields


def _erreurs(exc: ValidationError) -> Response:
    if hasattr(exc, 'message_dict'):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)


def _profil(user) -> dict:
    return {'id': user.pk, 'username': user.username, 'is_staff': user.is_staff}


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenAPIView(APIView):
    """GET /api/auth/csrf/ — jeton CSRF (cookie + corps), à appeler avant la connexion."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)})


@method_decorator(csrf_protect, name='dispatch')
class InscriptionAPIView(APIView):
    """POST /api/auth/inscription/"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = InscriptionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            utilisateur = inscrire_client(**payload.validated_data, request=request)
        except ValidationError as exc:
            return _erreurs(exc)
        return Response(_profil(utilisateur.user), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name='dispatch')
class ConnexionAPIView(APIView):
    """POST /api/auth/connexion/ — ouvre une session (blocage après échecs répétés)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = ConnexionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        user, erreur = authentifier_client(request, **payload.validated_data)
        if user is None:
            return Response({'detail': erreur}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_profil(user))


class DeconnexionAPIView(APIView):
    """POST /api/auth/deconnexion/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        deconnecter(request)
        return Response({'detail': 'Déconnecté.'})


class AlimentationListCreateAPIView(APIView):
    """
    GET  /api/alimentations/ — alimentations du client connecté.
    POST /api/alimentations/ — `{montant, numero_carte}` ; en-tête `Idempotency-Key` conseillé.
    """

    def get(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            AlimentationSerializer(list_alimentations(utilisateur=utilisateur), many=True).data
        )

    def post(self, request):
        try:
            utilisateur = get_utilisateur_connecte(request.user)
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        payload = AlimentationCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            alimentation = alimenter_wallet(
                utilisateur=utilisateur,
                montant=payload.validated_data['montant'],
                numero_carte=payload.validated_data['numero_carte'],
                cle_idempotence=request.headers.get('Idempotency-Key'),
            )
        except ValidationError as exc:
            return _erreurs(exc)
        if alimentation.est_rejeu:
            code = status.HTTP_200_OK
        elif alimentation.statut == Alimentation.Statut.ACCEPTEE:
            code = status.HTTP_201_CREATED
        else:
            code = status.HTTP_402_PAYMENT_REQUIRED
        return Response(AlimentationSerializer(alimentation).data, status=code)
