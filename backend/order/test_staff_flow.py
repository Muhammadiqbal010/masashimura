"""
Tes alur staff: aksi terima/batal/siap, riwayat event, pengingat & batal otomatis, webhook Telegram,
ringkasan. Jalankan: python manage.py test order.test_staff_flow  (Telegram di-mock).
"""
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import guards, staff_summary
from order import telegram_ui as ui
from order.models import Order

TG = dict(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111", TELEGRAM_WEBHOOK_SECRET="s3cret-s3cret-s3cret")


def make_staff(role="kasir", username="kasir"):
    u = User.objects.create(username=username, is_staff=(role != "kasir"))
    UserProfile.objects.update_or_create(user=u, defaults={"role": role})
    c = APIClient()
    c.force_authenticate(u)
    return c


class Base(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Katsu", price=20000, category=cat)
        self.staff = make_staff()

    def web_order(self, qty=2, **extra):
        r = APIClient().post("/api/orders/", {
            "source": "web", "payment_method": "cash",
            "customer": {"name": "Budi Santoso", "phone": "081234567890"},
            "items": [{"menu_id": self.menu.pk, "quantity": qty}], **extra,
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        return Order.objects.get(pk=r.data["id"])

    def actions(self, order):
        return list(order.events.values_list("action", "channel"))


class StaffActionTests(Base):
    def test_accept_records_event_once(self):
        o = self.web_order()
        self.assertEqual(self.staff.patch(f"/api/orders/{o.pk}/accept/").status_code, 200)
        self.assertEqual(self.staff.patch(f"/api/orders/{o.pk}/accept/").status_code, 200)   # dobel tekan aman
        self.assertEqual(self.actions(o), [("accepted", "staff")])

    def test_cancel_requires_valid_reason_and_logs(self):
        o = self.web_order()
        self.assertEqual(self.staff.patch(f"/api/orders/{o.pk}/cancel/", {"cancel_reason": "ngawur"}, format="json").status_code, 400)
        r = self.staff.patch(f"/api/orders/{o.pk}/cancel/", {"cancel_reason": "out_of_stock", "kasir_name": "Wawan"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        o.refresh_from_db()
        self.assertEqual((o.status, o.payment_status, o.cancelled_by), ("cancelled", "void", "Wawan"))
        ev = o.events.get()
        self.assertEqual((ev.action, ev.actor), ("cancelled", "Wawan"))
        self.assertIn("Stok habis", ev.note)
        self.assertEqual(self.staff.patch(f"/api/orders/{o.pk}/cancel/", {"cancel_reason": "other"}, format="json").status_code, 400)

    def test_cannot_mark_ready_before_accept(self):
        o = self.web_order()
        r = self.staff.patch(f"/api/orders/{o.pk}/ready/", {"ready": True}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_ready_and_unready_are_logged_and_idempotent(self):
        o = self.web_order()
        self.staff.patch(f"/api/orders/{o.pk}/accept/")
        for _ in range(2):
            self.assertEqual(self.staff.patch(f"/api/orders/{o.pk}/ready/", {"ready": True}, format="json").status_code, 200)
        self.staff.patch(f"/api/orders/{o.pk}/ready/", {"ready": False}, format="json")
        self.assertEqual([a for a, _ in self.actions(o)], ["accepted", "ready", "unready"])

    def test_events_endpoint_returns_timeline(self):
        o = self.web_order()
        self.staff.patch(f"/api/orders/{o.pk}/accept/")
        r = self.staff.get(f"/api/orders/{o.pk}/events/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([e["action"] for e in r.data["events"]], ["accepted"])
        self.assertEqual(r.data["events"][0]["channel_label"], "Admin")
        self.assertEqual(APIClient().get(f"/api/orders/{o.pk}/events/").status_code, 401)

    def test_accept_after_auto_cancel_is_409(self):
        o = self.web_order()
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(minutes=20))
        r = self.staff.patch(f"/api/orders/{o.pk}/accept/")
        self.assertEqual(r.status_code, 409)
        self.assertIn("otomatis", r.data["detail"])


@override_settings(**TG)
class ReminderAndAutoCancelTests(Base):
    @mock.patch("order.notify.urllib.request.urlopen")
    def test_reminder_sent_once_in_window(self, urlopen):
        o = self.web_order()
        urlopen.reset_mock()
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(minutes=11))
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(guards.process_unconfirmed()["reminded"], 1)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(guards.process_unconfirmed()["reminded"], 0)
        self.assertEqual(urlopen.call_count, 1)
        self.assertIn("SEGERA TERIMA", json.loads(urlopen.call_args[0][0].data)["text"])
        self.assertEqual(o.events.filter(action="reminded").count(), 1)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_no_reminder_too_early_or_after_accept(self, urlopen):
        o = self.web_order()
        self.assertEqual(guards.process_unconfirmed()["reminded"], 0)
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(minutes=11))
        self.staff.patch(f"/api/orders/{o.pk}/accept/")
        self.assertEqual(guards.process_unconfirmed()["reminded"], 0)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_auto_cancel_logs_and_notifies(self, urlopen):
        o = self.web_order()
        urlopen.reset_mock()
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(minutes=16))
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(guards.process_unconfirmed()["cancelled"], 1)
        self.assertEqual(self.actions(o), [("auto_cancelled", "system")])
        text = json.loads(urlopen.call_args[0][0].data)["text"]
        self.assertIn("DIBATALKAN OTOMATIS", text)


def cb_update(data, chat=111, user_id=7, username="wawan", message_id=50):
    return {"callback_query": {
        "id": "cbid", "data": data, "from": {"id": user_id, "username": username},
        "message": {"message_id": message_id, "chat": {"id": chat}},
    }}


@override_settings(**TG)
class WebhookTests(Base):
    def post(self, update, secret=TG["TELEGRAM_WEBHOOK_SECRET"]):
        headers = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": secret} if secret is not None else {}
        return APIClient().post("/api/telegram/webhook/", update, format="json", **headers)

    def calls(self, urlopen):
        return [(c[0][0].full_url.rsplit("/", 1)[-1], json.loads(c[0][0].data)) for c in urlopen.call_args_list]

    def test_wrong_or_missing_secret_is_403(self):
        o = self.web_order()
        self.assertEqual(self.post(cb_update(ui.build_callback("acc", o.pk)), secret="salah").status_code, 403)
        self.assertEqual(self.post(cb_update(ui.build_callback("acc", o.pk)), secret=None).status_code, 403)
        o.refresh_from_db()
        self.assertTrue(o.awaiting_confirmation)

    @override_settings(TELEGRAM_WEBHOOK_SECRET="")
    def test_webhook_disabled_without_secret(self):
        self.assertEqual(self.post({}, secret="").status_code, 403)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_accept_button_accepts_logs_and_edits_message(self, urlopen):
        o = self.web_order()
        urlopen.reset_mock()
        self.assertEqual(self.post(cb_update(ui.build_callback("acc", o.pk))).status_code, 200)
        o.refresh_from_db()
        self.assertFalse(o.awaiting_confirmation)
        ev = o.events.get()
        self.assertEqual((ev.action, ev.actor, ev.channel), ("accepted", "@wawan", "telegram"))
        methods = [m for m, _ in self.calls(urlopen)]
        self.assertEqual(methods, ["answerCallbackQuery", "editMessageText"])
        edit = self.calls(urlopen)[1][1]
        self.assertEqual(edit["message_id"], 50)
        self.assertIn("SEDANG DISIAPKAN", edit["text"])

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_reject_flow_asks_reason_then_cancels(self, urlopen):
        o = self.web_order()
        urlopen.reset_mock()
        self.post(cb_update(ui.build_callback("rjc", o.pk)))
        o.refresh_from_db()
        self.assertEqual(o.status, "pending")   # baru membuka menu alasan
        self.assertIn("Pilih alasan", self.calls(urlopen)[-1][1]["text"])
        self.post(cb_update(ui.build_callback("rjd", o.pk, "out_of_stock")))
        o.refresh_from_db()
        self.assertEqual((o.status, o.cancel_reason, o.cancelled_by), ("cancelled", "out_of_stock", "@wawan"))

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_unknown_chat_is_refused(self, urlopen):
        o = self.web_order()
        urlopen.reset_mock()
        self.post(cb_update(ui.build_callback("acc", o.pk), chat=999))
        o.refresh_from_db()
        self.assertTrue(o.awaiting_confirmation)
        self.assertEqual([m for m, _ in self.calls(urlopen)], ["answerCallbackQuery"])

    @override_settings(TELEGRAM_ALLOWED_USER_IDS="42")
    @mock.patch("order.notify.urllib.request.urlopen")
    def test_user_allowlist(self, urlopen):
        o = self.web_order()
        self.post(cb_update(ui.build_callback("acc", o.pk), user_id=7))
        o.refresh_from_db()
        self.assertTrue(o.awaiting_confirmation)
        self.post(cb_update(ui.build_callback("acc", o.pk), user_id=42))
        o.refresh_from_db()
        self.assertFalse(o.awaiting_confirmation)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_garbage_and_missing_order_never_500(self, urlopen):
        self.assertEqual(self.post(cb_update("sampah")).status_code, 200)
        self.assertEqual(self.post(cb_update(ui.build_callback("acc", 99999))).status_code, 200)
        self.assertEqual(self.post({"foo": "bar"}).status_code, 200)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_double_press_from_two_phones(self, urlopen):
        o = self.web_order()
        self.post(cb_update(ui.build_callback("acc", o.pk), username="a"))
        self.post(cb_update(ui.build_callback("acc", o.pk), username="b"))
        self.assertEqual(o.events.filter(action="accepted").count(), 1)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_ready_button(self, urlopen):
        o = self.web_order()
        self.staff.patch(f"/api/orders/{o.pk}/accept/")
        self.post(cb_update(ui.build_callback("rdy", o.pk)))
        o.refresh_from_db()
        self.assertIsNotNone(o.ready_at)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_commands_only_for_registered_chat(self, urlopen):
        msg = lambda chat: {"message": {"text": "/antrean", "chat": {"id": chat}, "from": {"id": 7}}}
        self.web_order()
        urlopen.reset_mock()
        self.post(msg(999))
        urlopen.assert_not_called()
        self.post(msg(111))
        self.assertIn("Perlu tindakan", json.loads(urlopen.call_args[0][0].data)["text"])


@override_settings(**TG, CRON_SECRET="cron-secret")
class CronAndSummaryTests(Base):
    def test_cron_requires_secret(self):
        c = APIClient()
        self.assertEqual(c.get("/api/orders/cron/").status_code, 403)
        self.assertEqual(c.get("/api/orders/cron/", HTTP_AUTHORIZATION="Bearer salah").status_code, 403)
        r = c.get("/api/orders/cron/?job=tick", HTTP_AUTHORIZATION="Bearer cron-secret")
        self.assertEqual((r.status_code, r.data["cancelled"], r.data["reminded"]), (200, 0, 0))

    @override_settings(CRON_SECRET="")
    def test_cron_disabled_without_env(self):
        self.assertEqual(APIClient().get("/api/orders/cron/", HTTP_AUTHORIZATION="Bearer ").status_code, 403)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_daily_report_job_sends_telegram(self, urlopen):
        self.web_order()
        urlopen.reset_mock()
        r = APIClient().get("/api/orders/cron/?job=daily_report", HTTP_AUTHORIZATION="Bearer cron-secret")
        self.assertEqual(r.status_code, 200)
        self.assertIn("RINGKASAN", json.loads(urlopen.call_args[0][0].data)["text"])

    def test_summary_hides_money_from_kasir_but_not_admin(self):
        o = self.web_order()
        self.staff.patch(f"/api/orders/{o.pk}/accept/")
        r = self.staff.get("/api/orders/staff-summary/")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIsNone(r.data["today"]["revenue"])
        self.assertEqual(r.data["today"]["orders"], 1)
        self.assertEqual(r.data["queue"]["preparing"], 1)
        admin = make_staff("admin", "adm").get("/api/orders/staff-summary/")
        self.assertIsNotNone(admin.data["today"]["revenue"])

    def test_summary_rejects_bad_date_and_anonymous(self):
        self.assertEqual(self.staff.get("/api/orders/staff-summary/?date=bukan").status_code, 400)
        self.assertEqual(APIClient().get("/api/orders/staff-summary/").status_code, 401)

    def test_queue_priority_order(self):
        a = self.web_order()
        b = self.web_order()
        self.staff.patch(f"/api/orders/{b.pk}/accept/")
        Order.objects.filter(pk=b.pk).update(created_at=timezone.now() - timedelta(minutes=40))
        kinds = [i["kind"] for i in staff_summary.queue_items()]
        self.assertEqual(kinds, ["awaiting", "late"])
        self.assertEqual(staff_summary.queue_items()[0]["id"], a.pk)

    def test_summary_counts_cancel_and_staff_actions(self):
        o = self.web_order()
        self.staff.patch(f"/api/orders/{o.pk}/cancel/", {"cancel_reason": "out_of_stock", "kasir_name": "Wawan"}, format="json")
        s = staff_summary.build_summary(include_money=True)
        self.assertEqual((s["today"]["orders"], s["today"]["cancelled"]), (0, 1))
        self.assertEqual(s["today"]["cancel_reasons"], {"stok habis": 1})
        self.assertEqual(s["staff"][0]["actor"], "Wawan")
        self.assertEqual(s["staff"][0]["cancelled"], 1)
