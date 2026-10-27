"""
Atur webhook bot Telegram.

  python manage.py telegram_webhook set https://masashimura-backend.vercel.app/api/telegram/webhook/
  python manage.py telegram_webhook info
  python manage.py telegram_webhook delete

Butuh env TELEGRAM_BOT_TOKEN dan TELEGRAM_WEBHOOK_SECRET (huruf/angka/_/-, 1-256 karakter).
"""
import json
import re
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Atur / cek / hapus webhook bot Telegram"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["set", "info", "delete"])
        parser.add_argument("url", nargs="?", help="URL HTTPS webhook (untuk 'set')")

    def _call(self, method, payload=None):
        token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN belum diisi.")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/{method}",
            data=json.dumps(payload or {}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception as exc:   # noqa: BLE001 - jangan cetak URL (memuat token)
            raise CommandError(f"Panggilan Telegram gagal ({exc.__class__.__name__}).")

    def handle(self, *args, **opts):
        action = opts["action"]
        if action == "set":
            url = opts.get("url") or ""
            secret = (settings.TELEGRAM_WEBHOOK_SECRET or "").strip()
            if not url.startswith("https://"):
                raise CommandError("URL webhook wajib HTTPS.")
            if not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", secret):
                raise CommandError("TELEGRAM_WEBHOOK_SECRET wajib diisi (16-256 karakter huruf/angka/_/-).")
            res = self._call("setWebhook", {
                "url": url,
                "secret_token": secret,
                "allowed_updates": ["callback_query", "message"],
                "drop_pending_updates": True,
            })
        elif action == "delete":
            res = self._call("deleteWebhook", {"drop_pending_updates": True})
        else:
            res = self._call("getWebhookInfo")
            res.get("result", {}).pop("ip_address", None)
        self.stdout.write(json.dumps(res, indent=2, ensure_ascii=False))
