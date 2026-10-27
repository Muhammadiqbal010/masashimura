"""
Tes aturan anti-scam: pengalihan ke QRIS, daftar blokir, tombol/perintah Telegram, tanda tambahan,
skor 🟢🟡🔴, laporan mingguan, dan cron. Jalankan: python manage.py test order.test_scam_guard
(Telegram di-mock, tidak ada pesan sungguhan terkirim.)
"""
import json
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from menu.models import Category, Menu
from order import blocklist, guards, notify, scam_report, scam_signals, telegram_bot
from order import client_info as ci
from order import telegram_ui as ui
from order.models import BlockedContact, Order, OrderItem, StoreSettings
from order.test_client_trace import bekasi_meta

TG = dict(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111")


class BaseCase(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Dimsum", price=18500, category=cat)
        self.api = APIClient()

    def order(self, phone="081234567890", name="Budi Santoso", method="cash", qty=1, notes="", **meta):
        return self.api.post("/api/orders/", {
            "source": "web", "payment_method": method, "notes": notes,
            "customer": {"name": name, "phone": phone},
            "items": [{"menu_id": self.menu.pk, "quantity": qty}],
        }, format="json", **bekasi_meta(**meta))

    def make_regular(self, phone, n=1):
        """Pelanggan lama: n pesanan selesai dari nomor ini."""
        for _ in range(n):
            Order.objects.create(source="pos", status="completed", payment_status="paid",
                                 payment_method="cash", customer_phone=phone, customer_name="Langganan")

    def sent_texts(self, urlopen):
        return [json.loads(c[0][0].data)["text"] for c in urlopen.call_args_list]


# ── Pengalihan ke QRIS (bukan ditolak) ──────────────────────────────────────

class QrisRedirectTests(BaseCase):
    def test_new_phone_small_cash_ok_big_cash_goes_to_qris(self):
        self.assertEqual(self.order(qty=2).status_code, 201)                      # ±Rp38rb, di bawah batas nomor baru
        r = self.order(phone="081200000099", qty=3)                               # ±Rp57rb
        self.assertEqual(r.status_code, 409)
        self.assertTrue(r.data["require_qris"])
        self.assertEqual(r.data["reason"], guards.QRIS_NEW_PHONE)
        self.assertEqual(Order.objects.filter(customer_phone="081200000099").count(), 0)   # tidak ada order nyangkut

    def test_known_customer_keeps_cash_up_to_150k(self):
        self.make_regular("081234567890")
        r = self.order(qty=5)                                                     # ±Rp95rb: pelanggan lama boleh cash
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.order(qty=9).status_code, 400)                      # di atas Rp150rb tetap wajib online

    def test_new_phone_can_always_pay_with_qris(self):
        self.assertEqual(self.order(phone="081200000099", qty=5, method="gateway").status_code, 201)

    def test_pending_phone_cap_redirects_instead_of_rejecting(self):
        self.make_regular("081234567890")
        for _ in range(2):
            self.assertEqual(self.order().status_code, 201)
        r = self.order()
        self.assertEqual((r.status_code, r.data["reason"]), (409, guards.QRIS_PHONE_PENDING))
        self.assertEqual(self.order(method="gateway").status_code, 201)

    def test_message_is_neutral_and_does_not_leak_rules(self):
        r = self.order(phone="081200000099", qty=3)
        self.assertNotIn("50", r.data["error"])
        self.assertIn("QRIS", r.data["error"])


# ── Daftar blokir ───────────────────────────────────────────────────────────

class BlocklistTests(BaseCase):
    def test_parse_target(self):
        self.assertEqual(blocklist.parse_target("+62 812-3456-7890"), ("phone", "081234567890"))
        self.assertEqual(blocklist.parse_target("114.122.1.2"), ("ip", "114.122.1.2"))
        self.assertIsNone(blocklist.parse_target("halo"))
        self.assertIsNone(blocklist.parse_target(""))

    def test_blocked_phone_is_rejected_for_cash_and_qris(self):
        blocklist.block("phone", "081234567890", actor="@owner")
        for method in ("cash", "gateway"):
            r = self.order(method=method)
            self.assertEqual(r.status_code, 403)
            self.assertTrue(r.data["blocked"])
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.order(phone="081200000002").status_code, 201)       # nomor lain tidak terpengaruh

    def test_unblock_restores_access(self):
        blocklist.block("phone", "081234567890")
        self.assertTrue(blocklist.unblock("phone", "081234567890"))
        self.assertEqual(self.order().status_code, 201)
        self.assertFalse(blocklist.unblock("phone", "081234567890"))              # sudah terbuka

    def test_blocked_ip_forces_qris_but_never_rejects(self):
        blocklist.block("ip", "114.122.10.20")
        r = self.order()
        self.assertEqual((r.status_code, r.data["reason"]), (409, guards.QRIS_IP_BLOCKED))
        self.assertEqual(self.order(method="gateway").status_code, 201)           # IP bersama: pelanggan asli tetap bisa QRIS

    def test_ip_block_expires(self):
        blocklist.block("ip", "114.122.10.20")
        BlockedContact.objects.update(blocked_at=timezone.now() - timedelta(days=blocklist.IP_BLOCK_DAYS + 1))
        self.assertFalse(blocklist.is_ip_blocked("114.122.10.20"))
        self.assertEqual(blocklist.expire_old_ip_blocks(), 1)
        self.assertEqual(self.order().status_code, 201)

    def test_phone_block_does_not_expire(self):
        blocklist.block("phone", "081234567890")
        BlockedContact.objects.update(blocked_at=timezone.now() - timedelta(days=500))
        self.assertTrue(blocklist.is_phone_blocked("081234567890"))
        self.assertEqual(blocklist.expire_old_ip_blocks(), 0)

    def test_reblock_after_unblock_reports_fresh(self):
        self.assertTrue(blocklist.block("phone", "081234567890"))
        self.assertFalse(blocklist.block("phone", "081234567890"))                # sudah aktif
        blocklist.unblock("phone", "081234567890")
        self.assertTrue(blocklist.block("phone", "081234567890"))

    def test_pos_orders_ignore_blocklist(self):
        blocklist.block("phone", "081234567890")
        staff = self.make_staff()
        self.api.force_authenticate(staff)
        r = self.api.post("/api/orders/", {
            "source": "pos", "payment_method": "cash", "payment_status": "paid",
            "customer": {"name": "Budi", "phone": "081234567890"},
            "items": [{"menu_id": self.menu.pk, "quantity": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def make_staff(self):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.create_user(username="kasir1", password="x", is_staff=True)


# ── Telegram: tombol, perintah, tampilan ────────────────────────────────────

@override_settings(**TG, STORE_LATITUDE="-6.2311", STORE_LONGITUDE="106.9974")
class TelegramBlockTests(BaseCase):
    def place(self, **kw):
        self.assertEqual(self.order(**kw).status_code, 201)
        return Order.objects.order_by("-pk").first()

    def press(self, act, order, urlopen):
        telegram_bot.handle_callback({
            "id": "cb1", "from": {"id": 5, "username": "owner"},
            "message": {"chat": {"id": 111}, "message_id": 9},
            "data": ui.build_callback(act, order.pk),
        })
        bodies = [json.loads(c[0][0].data) for c in urlopen.call_args_list]
        return bodies

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_block_button_blocks_phone_and_ip_then_unblock_button_reverts(self, urlopen):
        o = self.place()
        bodies = self.press(ui.ACT_BLOCK, o, urlopen)
        self.assertTrue(blocklist.is_phone_blocked(o.customer_phone))
        self.assertTrue(blocklist.is_ip_blocked(o.client_ip))
        edited = [b for b in bodies if "text" in b and "message_id" in b][-1]
        self.assertIn("🚫 DIBLOKIR: nomor WA & IP", edited["text"])
        buttons = json.dumps(edited["reply_markup"])
        self.assertIn("Buka blokir", buttons)
        self.assertNotIn("Blokir nomor", buttons)
        self.assertEqual(o.events.filter(action="blocked").count(), 1)

        urlopen.reset_mock()
        bodies = self.press(ui.ACT_UNBLOCK, o, urlopen)
        self.assertFalse(blocklist.is_phone_blocked(o.customer_phone))
        self.assertFalse(blocklist.is_ip_blocked(o.client_ip))
        edited = [b for b in bodies if "text" in b and "message_id" in b][-1]
        self.assertIn("Blokir nomor", json.dumps(edited["reply_markup"]))

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_block_button_does_not_cancel_the_order(self, urlopen):
        o = self.place()
        self.press(ui.ACT_BLOCK, o, urlopen)
        o.refresh_from_db()
        self.assertEqual(o.status, "pending")
        self.assertTrue(o.awaiting_confirmation)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_block_button_is_idempotent(self, urlopen):
        o = self.place()
        self.press(ui.ACT_BLOCK, o, urlopen)
        self.press(ui.ACT_BLOCK, o, urlopen)
        self.assertEqual(BlockedContact.objects.filter(is_active=True).count(), 2)   # 1 nomor + 1 IP, tidak dobel

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_strangers_cannot_press_block(self, urlopen):
        o = self.place()
        telegram_bot.handle_callback({
            "id": "cb1", "from": {"id": 5}, "message": {"chat": {"id": 999}, "message_id": 9},
            "data": ui.build_callback(ui.ACT_BLOCK, o.pk),
        })
        self.assertFalse(blocklist.is_phone_blocked(o.customer_phone))

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_commands(self, urlopen):
        def cmd(text, chat=111):
            urlopen.reset_mock()
            telegram_bot.handle_command({"chat": {"id": chat}, "from": {"id": 1, "username": "owner"}, "text": text})
            return self.sent_texts(urlopen)

        self.assertIn("diblokir", cmd("/blokir 0812-3456-7890")[0])
        self.assertTrue(blocklist.is_phone_blocked("081234567890"))
        self.assertIn("sudah ada", cmd("/blokir 081234567890")[0])
        self.assertIn("dipaksa bayar QRIS", cmd("/blokir 114.122.1.2")[0])
        daftar = cmd("/daftarblokir")[0]
        self.assertIn("081234567890", daftar)
        self.assertIn("114.122.1.2", daftar)
        self.assertIn("dibuka", cmd("/bukablokir 081234567890")[0])
        self.assertIn("tidak ada di daftar", cmd("/bukablokir 081234567890")[0])
        self.assertIn("Cara pakai", cmd("/blokir")[0])
        self.assertEqual(cmd("/blokir 0812", chat=999), [])   # chat asing: diam saja

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_old_and_new_customer_tag_in_message(self, urlopen):
        self.make_regular("081234567890", n=3)
        self.make_regular("081200000002", n=0)
        with self.captureOnCommitCallbacks(execute=True):
            self.order()
        self.assertIn("👤 Pelanggan lama (3 pesanan selesai)", self.sent_texts(urlopen)[-1])
        with self.captureOnCommitCallbacks(execute=True):
            self.order(phone="081200000002")
        self.assertIn("👤 Nomor baru, belum pernah ada pesanan selesai", self.sent_texts(urlopen)[-1])

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_clean_order_is_green_and_has_plain_chat_button(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            self.order()
        text = self.sent_texts(urlopen)[-1]
        self.assertTrue(text.startswith("🟢 AMAN · 🛎️ PESANAN WEB BARU"), text)
        buttons = json.dumps(json.loads(urlopen.call_args[0][0].data)["reply_markup"])
        self.assertIn("Chat pemesan (WA)", buttons)
        self.assertIn("Blokir nomor", buttons)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_suspicious_order_is_red_and_asks_to_confirm_first(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            self.order(HTTP_X_VERCEL_IP_COUNTRY="NG", HTTP_X_VERCEL_IP_COUNTRY_REGION="LA",
                       HTTP_X_VERCEL_IP_CITY="Lagos", HTTP_USER_AGENT="python-requests/2.31",
                       HTTP_X_VERCEL_IP_LATITUDE="6.5244", HTTP_X_VERCEL_IP_LONGITUDE="3.3792")
        text = self.sent_texts(urlopen)[-1]
        self.assertTrue(text.startswith("🔴 CURIGA · "), text)
        buttons = json.dumps(json.loads(urlopen.call_args[0][0].data)["reply_markup"])
        self.assertIn("Konfirmasi dulu (WA)", buttons)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_regular_customer_with_single_flag_stays_green(self, urlopen):
        self.make_regular("081234567890", n=2)
        with self.captureOnCommitCallbacks(execute=True):
            self.order(HTTP_X_VERCEL_IP_CITY="Bekasi", HTTP_X_VERCEL_IP_LATITUDE="-5.0", HTTP_X_VERCEL_IP_LONGITUDE="105.0")
        o = Order.objects.order_by("-pk").first()
        client, flags = notify.client_view(o)
        self.assertTrue(any("Jauh dari toko" in f for f in flags))
        self.assertEqual(client["risk"], "green")


# ── Tanda tambahan ──────────────────────────────────────────────────────────

class ExtraFlagTests(BaseCase):
    def place(self, **kw):
        r = self.order(**kw)
        self.assertEqual(r.status_code, 201, r.data)
        return Order.objects.get(order_number=r.data["order_number"])

    def flags(self, order):
        return notify.client_view(order)[1]

    def test_same_name_different_phones_from_one_ip(self):
        self.place(phone="081200000001", name="Andi Wijaya")
        self.place(phone="081200000002", name="andi  wijaya")
        o = self.place(phone="081200000003", name="Andi Wijaya")
        self.assertTrue(any("Nama yang sama dipakai 3 nomor WA" in f for f in self.flags(o)), self.flags(o))

    def test_same_phone_same_name_is_not_flagged(self):
        self.place(phone="081200000001", name="Andi Wijaya")
        o = self.place(phone="081200000001", name="Andi Wijaya")
        self.assertFalse(any("Nama yang sama" in f for f in self.flags(o)))

    def test_link_in_notes_is_flagged(self):
        o = self.place(notes="transfer dulu ke wa.me/628123456")
        self.assertIn("Catatan pesanan berisi link", self.flags(o))

    def test_plain_notes_are_not_flagged(self):
        o = self.place(notes="jangan pedas ya")
        self.assertNotIn("Catatan pesanan berisi link", self.flags(o))

    def test_after_hours_flag_uses_schedule(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"operating_hours": {"0": {"open": "08:00", "close": "22:00"}}})
        o = self.place()
        monday_3am_wib = datetime(2026, 10, 25, 20, 0, tzinfo=dt_timezone.utc)   # Senin 03:00 WIB
        monday_noon_wib = datetime(2026, 10, 26, 5, 0, tzinfo=dt_timezone.utc)   # Senin 12:00 WIB
        self.assertTrue(scam_signals.after_hours(monday_3am_wib))
        self.assertFalse(scam_signals.after_hours(monday_noon_wib))
        Order.objects.filter(pk=o.pk).update(created_at=monday_3am_wib)
        o.refresh_from_db()
        self.assertIn("Masuk di luar jam buka toko", self.flags(o))

    def test_no_schedule_means_never_after_hours(self):
        self.assertFalse(scam_signals.after_hours(timezone.now()))

    def test_big_portions_flag_needs_a_baseline(self):
        menu2 = Menu.objects.create(name="Siomay", price=15000, category=self.menu.category)

        def big_order(phone, ip):
            r = self.api.post("/api/orders/", {
                "source": "web", "payment_method": "gateway",
                "customer": {"name": "Budi Santoso", "phone": phone},
                "items": [{"menu_id": self.menu.pk, "quantity": 10}, {"menu_id": menu2.pk, "quantity": 4}],
            }, format="json", **bekasi_meta(HTTP_X_FORWARDED_FOR=ip))
            self.assertEqual(r.status_code, 201, r.data)
            return Order.objects.get(order_number=r.data["order_number"])

        o = big_order("081200000004", "114.122.70.1")
        self.assertFalse(any("Porsi jauh" in f for f in self.flags(o)))           # belum ada data pembanding
        for _ in range(12):
            po = Order.objects.create(source="pos", status="completed", payment_status="paid", payment_method="cash")
            OrderItem.objects.create(order=po, menu=self.menu, quantity=1, price=18500)
        o2 = big_order("081200000005", "114.122.77.7")
        self.assertTrue(any("Porsi jauh di atas kebiasaan toko (14 porsi" in f for f in self.flags(o2)), self.flags(o2))


class PureScoreTests(SimpleTestCase):
    def test_levels(self):
        self.assertEqual(ci.risk_level([], 0), "green")
        self.assertEqual(ci.risk_level([], None), "green")
        self.assertEqual(ci.risk_level([("a", 1)], 0), "yellow")      # nomor baru + 1 tanda
        self.assertEqual(ci.risk_level([("a", 1)], 4), "green")       # pelanggan lama + 1 tanda kecil
        self.assertEqual(ci.risk_level([("a", 2)], 0), "red")         # nomor baru + tanda kuat
        self.assertEqual(ci.risk_level([("a", 2)], 9), "yellow")      # pelanggan lama + 1 tanda kuat
        self.assertEqual(ci.risk_level([("a", 2), ("b", 2)], 9), "red")      # 2 tanda kuat: pelanggan lama pun dicurigai

    def test_link_detection(self):
        self.assertTrue(ci.has_link("klik https://x.co/abc"))
        self.assertTrue(ci.has_link("www.tokoku"))
        self.assertTrue(ci.has_link("chat t.me/abc"))
        self.assertFalse(ci.has_link("tanpa bawang, es teh manis"))
        self.assertFalse(ci.has_link(""))

    def test_assess_keeps_old_contract(self):
        flags = ci.assess("1.2.3.4", {"country": "NG"})
        self.assertEqual(flags, ["Berasal dari luar Indonesia (NG)"])


# ── Laporan mingguan & cron ─────────────────────────────────────────────────

@override_settings(**TG, CRON_SECRET="s3cret")
class ReportAndCronTests(BaseCase):
    def test_weekly_report_counts_and_compares(self):
        from order import events
        old = Order.objects.create(source="web", status="cancelled", payment_status="void", payment_method="cash",
                                   customer_phone="081200000001", client_ip="1.2.3.4", total_price=50000)
        events.record(old, "auto_cancelled", actor="sistem", channel="system")
        blocklist.block("phone", "081200000001")
        text = scam_report.build()
        self.assertIn("Laporan anti-scam mingguan", text)
        self.assertIn("Batal otomatis (tidak diterima kasir): 1", text)
        self.assertIn("Rp 50.000", text)
        self.assertIn("Diblokir minggu ini: 1 baru · 1 aktif", text)
        self.assertIn("Minggu sebelumnya: 0 → naik", text)

    def test_weekly_report_flags_repeat_ip(self):
        for i in range(3):
            Order.objects.create(source="web", payment_method="cash", customer_phone=f"08120000000{i}", client_ip="9.9.9.9")
        text = scam_report.build()
        self.assertIn("9.9.9.9 — 3 pesanan, 3 nomor WA", text)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_cron_housekeeping_requires_secret_and_purges(self, urlopen):
        old = Order.objects.create(source="web", client_ip="1.2.3.4", client_info={"city": "X"})
        Order.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=120))
        self.assertEqual(self.api.get("/api/orders/cron/?job=housekeeping").status_code, 403)
        r = self.api.get("/api/orders/cron/?job=housekeeping", HTTP_AUTHORIZATION="Bearer s3cret")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["purged_orders"], 1)
        old.refresh_from_db()
        self.assertIsNone(old.client_ip)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_cron_weekly_report_sends_to_telegram(self, urlopen):
        r = self.api.get("/api/orders/cron/?job=weekly_report", HTTP_AUTHORIZATION="Bearer s3cret")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["sent"])
        self.assertIn("Laporan anti-scam mingguan", self.sent_texts(urlopen)[-1])

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_daily_report_also_does_housekeeping(self, urlopen):
        r = self.api.get("/api/orders/cron/?job=daily_report", HTTP_AUTHORIZATION="Bearer s3cret")
        self.assertEqual(r.status_code, 200)
        self.assertIn("housekeeping", r.data)
