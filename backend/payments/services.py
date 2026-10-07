import logging

import midtransclient
from django.conf import settings

logger = logging.getLogger(__name__)

_keys = dict(
    is_production=settings.MIDTRANS_IS_PRODUCTION,
    server_key=settings.MIDTRANS_SERVER_KEY,
    client_key=settings.MIDTRANS_CLIENT_KEY,
)

# DIAGNOSTIK SEMENTARA: hapus setelah masalah 401 ketemu.
# Cuma menampilkan 10 karakter awal, jadi key tidak bocor.
logger.warning(
    "Midtrans config: is_production=%r server_prefix=%r server_len=%d client_prefix=%r",
    settings.MIDTRANS_IS_PRODUCTION,
    settings.MIDTRANS_SERVER_KEY[:10],
    len(settings.MIDTRANS_SERVER_KEY),
    settings.MIDTRANS_CLIENT_KEY[:10],
)

snap = midtransclient.Snap(**_keys)
core = midtransclient.CoreApi(**_keys)


def cancel_midtrans_transaction(order_number):
    """Batalkan transaksi pending di Midtrans (dipakai saat admin cancel order)."""
    try:
        core.transactions.cancel(order_number)
    except Exception:
        logger.warning("Gagal cancel transaksi Midtrans %s", order_number, exc_info=True)