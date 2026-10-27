"""Tes notifikasi Telegram. Jalankan: python manage.py test order.test_notify (Telegram di-mock)."""
import json
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from menu.models import Category, Menu
from order import notify


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111, 222")
class SendTests(SimpleTestCase):
    @mock.patch("order.notify.urllib.request.urlopen")
    def test_sends_to_every_chat_id(self, urlopen):
        self.assertTrue(notify.send("halo", [{"text": "Buka", "url": "https://x.y"}]))
        self.assertEqual(urlopen.call_count, 2)
        body = json.loads(urlopen.call_args[0][0].data)
        self.assertEqual(body["text"], "halo")
        self.assertEqual(body["reply_markup"]["inline_keyboard"][0][0]["url"], "https://x.y")

    @mock.patch("order.notify.urllib.request.urlopen", side_effect=OSError("boom"))
    def test_failure_is_swallowed(self, urlopen):
        self.assertFalse(notify.send("halo"))

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    @mock.patch("order.notify.urllib.request.urlopen")
    def test_disabled_without_env(self, urlopen):
        self.assertFalse(notify.send("halo"))
        urlopen.assert_not_called()


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111")
class WebOrderHookTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Katsu", price=20000, category=cat)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_new_web_cash_order_sends_telegram(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            r = APIClient().post("/api/orders/", {
                "source": "web", "payment_method": "cash",
                "customer": {"name": "Budi Santoso", "phone": "081234567890"},
                "items": [{"menu_id": self.menu.pk, "quantity": 2}],
            }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        urlopen.assert_called_once()
        text = json.loads(urlopen.call_args[0][0].data)["text"]
        self.assertIn("PESANAN WEB BARU", text)
        self.assertIn("2× Katsu", text)
