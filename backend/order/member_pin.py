"""
PIN Member (langkah 6).

Aturan (lihat rancangan bagian 9):
  - Poin masuk tanpa PIN. Melihat dan menukar poin di WEB wajib PIN.
  - PIN 4 digit hanya dibuat/diganti admin atau owner, disimpan sebagai hash (tidak bisa dilihat ulang).
  - 5 kali salah → kunci 15 menit. Hitungan ada di database (backend serverless, bukan di memori).
  - Pesan gagal SELALU sama untuk nomor tanpa PIN, nomor tidak terdaftar, PIN salah, maupun akun
    terkunci, supaya orang tidak bisa menebak nomor mana yang member.
  - Kasir (POS, login staf) tidak memakai PIN: kasir bertemu orangnya langsung.
"""
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .models import CustomerLoyalty

PIN_LENGTH = 4
MAX_ATTEMPTS = 5
LOCK_MINUTES = 15

NEUTRAL_ERROR = "Nomor atau PIN salah, atau minta PIN ke kasir."

_dummy_hash = None


def _dummy():
    """Hash palsu untuk menyamakan waktu respons saat nomor tidak punya PIN."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = make_password("0" * PIN_LENGTH)
    return _dummy_hash


def generate_pin():
    return f"{secrets.randbelow(10 ** PIN_LENGTH):0{PIN_LENGTH}d}"


def is_valid_format(raw):
    return isinstance(raw, str) and len(raw) == PIN_LENGTH and raw.isascii() and raw.isdigit()


def set_pin(loyalty, raw, now=None):
    """Simpan PIN baru (hash), sekaligus membuka kunci dan mereset hitungan salah."""
    loyalty.pin_hash = make_password(raw)
    loyalty.pin_set_at = now or timezone.now()
    loyalty.pin_failed_attempts = 0
    loyalty.pin_locked_until = None
    loyalty.save(update_fields=["pin_hash", "pin_set_at", "pin_failed_attempts", "pin_locked_until"])


def verify_pin(phone, raw_pin, now=None):
    """
    Return objek CustomerLoyalty bila PIN benar, selain itu None (tanpa membedakan alasannya).
    Percobaan salah dicatat di database dan TIDAK ikut di-rollback oleh pemanggil
    (pemanggil tidak boleh memanggil transaction.set_rollback setelah ini).
    """
    now = now or timezone.now()
    raw = raw_pin if isinstance(raw_pin, str) else ("" if raw_pin is None else str(raw_pin))
    phone = (phone or "").strip()

    with transaction.atomic():
        loyalty = CustomerLoyalty.objects.select_for_update().filter(phone=phone).first() if phone else None

        if not loyalty or not loyalty.pin_hash:
            check_password(raw, _dummy())
            return None

        if loyalty.pin_locked_until and loyalty.pin_locked_until > now:
            check_password(raw, _dummy())
            return None

        if is_valid_format(raw) and check_password(raw, loyalty.pin_hash):
            if loyalty.pin_failed_attempts or loyalty.pin_locked_until:
                loyalty.pin_failed_attempts = 0
                loyalty.pin_locked_until = None
                loyalty.save(update_fields=["pin_failed_attempts", "pin_locked_until"])
            return loyalty

        loyalty.pin_failed_attempts += 1
        if loyalty.pin_failed_attempts >= MAX_ATTEMPTS:
            loyalty.pin_failed_attempts = 0
            loyalty.pin_locked_until = now + timedelta(minutes=LOCK_MINUTES)
        loyalty.save(update_fields=["pin_failed_attempts", "pin_locked_until"])
        return None
