from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Sama kayak TokenAuthentication bawaan DRF, tapi token dianggap
    kadaluarsa setelah TOKEN_EXPIRE_HOURS jam sejak dibuat. Kalau
    expired, token itu dihapus (dipaksa login ulang) — bukan cuma
    ditolak, biar gak numpuk token mati di database.
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        expire_hours = getattr(settings, 'TOKEN_EXPIRE_HOURS', 24 * 7)  # default 7 hari
        expiry_time = token.created + timedelta(hours=expire_hours)

        if timezone.now() > expiry_time:
            token.delete()
            raise AuthenticationFailed('Sesi kamu sudah kadaluarsa. Silakan login ulang.')

        return (user, token)