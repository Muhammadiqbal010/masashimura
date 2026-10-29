"""
Tes alat anti-scam tambahan: pencatatan percobaan order dari kontak terblokir, detail pesanan terakhir
per blokir (nama, nomor, IP, lokasi, tautan Maps), pencarian admin lengkap, /lacak nomor, /percobaan, dan
alert Telegram. Jalankan: python -m django test order.test_scam_tools
(Telegram di-mock, tidak ada pesan sungguhan terkirim.)
"""
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from finance.models import Expense
from menu.models import Category, Menu
from order import blocklist, trace
from order.models import BlockedAttempt, CustomerLoyalty, Order
from order.test_client_trace import bekasi_meta

TG = dict(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111")
PHONE = "081234567890"


def api_as(role, superuser=False):
    u = User.objects.create_user(f"{role}{User.objects.count()}", password="x", is_superuser=superuser,
                                 is_staff=role != "pelanggan", first_name="Sari" if role == "kasir" else "")
    UserProfile.objects.update_or_create(user=u, defaults={"role": role, "phone": "081777000111"})
    c = APIClient()
    c.force_authenticate(u)
    return c


class Base(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Dimsum Ayam", price=18500, category=cat)
        self.web = APIClient()

    def order(self, phone=PHONE, name="Budi Santoso", method="cash", **meta):
        return self.web.post("/api/orders/", {
            "source": "web", "payment_method": method,
            "customer": {"name": name, "phone": phone},
            "items": [{"menu_id": self.menu.pk, "quantity": 1}],
        }, format="json", **bekasi_meta(**meta))

    def texts(self, urlopen):
        return [json.loads(c[0][0].data)["text"] for c in urlopen.call_args_list]


@override_settings(**TG)
class AttemptRecordingTests(Base):
    @mock.patch("order.notify.urllib.request.urlopen")
    def test_blocked_phone_attempt_is_recorded_with_full_trace_and_alerted(self, urlopen):
        blocklist.block("phone", PHONE, actor="@owner")
        r = self.order()
        self.assertEqual(r.status_code, 403)
        a = BlockedAttempt.objects.get()
        self.assertEqual((a.kind, a.value, a.phone, a.name), ("phone", PHONE, PHONE, "Budi Santoso"))
        self.assertEqual(a.client_ip, "114.122.10.20")
        self.assertEqual(a.client_info["city"], "Bekasi")
        text = self.texts(urlopen)[0]
        for needle in ("Percobaan order dari kontak TERBLOKIR", "Budi Santoso", PHONE, "114.122.10.20",
                       "Bekasi", "google.com/maps", f"/blokir 114.122.10.20"):
            self.assertIn(needle, text)
        self.assertEqual(Order.objects.count(), 0)   # tetap ditolak total

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_repeated_attempts_are_all_recorded_but_alert_is_throttled(self, urlopen):
        blocklist.block("phone", PHONE)
        for _ in range(3):
            self.assertEqual(self.order().status_code, 403)
        self.assertEqual(BlockedAttempt.objects.count(), 3)
        self.assertEqual(len(self.texts(urlopen)), 1)
        BlockedAttempt.objects.update(created_at=timezone.now() - timedelta(minutes=blocklist.ATTEMPT_ALERT_GAP_MINUTES + 1))
        self.order()
        self.assertEqual(len(self.texts(urlopen)), 2)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_no_ip_block_hint_when_ip_already_blocked(self, urlopen):
        blocklist.block("phone", PHONE)
        blocklist.block("ip", "114.122.10.20")
        self.order()
        self.assertNotIn("/blokir 114.122.10.20", self.texts(urlopen)[0])

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_blocked_ip_forced_to_qris_is_recorded_as_ip_attempt(self, urlopen):
        blocklist.block("ip", "114.122.10.20")
        r = self.order()
        self.assertEqual(r.status_code, 409)
        a = BlockedAttempt.objects.get()
        self.assertEqual((a.kind, a.value, a.phone), ("ip", "114.122.10.20", PHONE))

    def test_clean_order_records_nothing_and_telegram_failure_never_breaks_response(self):
        self.assertEqual(self.order().status_code, 201)
        self.assertEqual(BlockedAttempt.objects.count(), 0)
        blocklist.block("phone", "081200000009")
        with mock.patch("order.notify.urllib.request.urlopen", side_effect=OSError("down")):
            self.assertEqual(self.order(phone="081200000009").status_code, 403)
        self.assertEqual(BlockedAttempt.objects.count(), 1)

    def test_pos_orders_are_not_recorded(self):
        blocklist.block("phone", PHONE)
        c = api_as("kasir")
        r = c.post("/api/orders/", {"source": "pos", "payment_method": "cash", "payment_status": "paid",
                                     "customer": {"name": "Walk In", "phone": PHONE},
                                     "items": [{"menu_id": self.menu.pk, "quantity": 1}]}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(BlockedAttempt.objects.count(), 0)

    def test_old_attempts_are_purged_by_daily_housekeeping(self):
        from order import housekeeping
        old = BlockedAttempt.objects.create(kind="phone", value=PHONE)
        BlockedAttempt.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=blocklist.ATTEMPT_KEEP_DAYS + 1))
        BlockedAttempt.objects.create(kind="phone", value=PHONE)
        self.assertEqual(housekeeping.run_daily()["purged_attempts"], 1)
        self.assertEqual(BlockedAttempt.objects.count(), 1)


class BlocklistDetailTests(Base):
    def setUp(self):
        super().setUp()
        self.owner = api_as("owner")
        for name in ["Budi Santoso", "Budi S", "Budi"]:
            self.assertEqual(self.order(name=name, method="gateway").status_code, 201)
        Order.objects.filter(source="web").update(status="cancelled", cancelled_by="sistem")
        blocklist.block("phone", PHONE, actor="@owner", reason="Order fiktif")
        blocklist.block("ip", "114.122.10.20")
        blocklist.record_attempt("phone", PHONE, phone=PHONE, name="Budi", ip="114.122.10.20",
                                 info={"city": "Bekasi", "region": "Jawa Barat", "country": "ID", "lat": -6.2349, "lng": 106.9896})

    def rows(self):
        r = self.owner.get("/api/orders/blocklist/")
        self.assertEqual(r.status_code, 200)
        return {x["value"]: x for x in r.data["results"]}, r.data

    def test_each_block_lists_recent_orders_with_full_trace(self):
        rows, _ = self.rows()
        recent = rows[PHONE]["recent_orders"]
        self.assertEqual(len(recent), 3)
        o = recent[0]
        self.assertEqual(o["phone"], PHONE)
        self.assertEqual(o["ip"], "114.122.10.20")
        self.assertIn("Bekasi", o["location_text"])
        self.assertTrue(o["maps_url"].startswith("https://www.google.com/maps?q=-6.2349,106.9896"))
        self.assertEqual(o["status_label"], "Batal otomatis")
        self.assertTrue(o["order_number"] and o["id"])
        self.assertIn("Android", o["device"])
        self.assertEqual(len(rows["114.122.10.20"]["recent_orders"]), 3)
        self.assertEqual({x["name"] for x in recent}, {"Budi Santoso", "Budi S", "Budi"})

    def test_recent_orders_capped_and_newest_first(self):
        for i in range(4):   # nomor ini sudah diblokir, jadi order tambahan dibuat langsung di database
            Order.objects.create(source="web", customer_phone=PHONE, customer_name=f"Lagi {i}", client_ip="114.122.10.20",
                                 created_at=timezone.now() + timedelta(minutes=i + 1))
        recent = self.rows()[0][PHONE]["recent_orders"]
        self.assertEqual(len(recent), 5)
        stamps = [x["created_at"] for x in recent]
        self.assertEqual(stamps, sorted(stamps, reverse=True))

    def test_attempts_included_with_counts_and_summary(self):
        rows, data = self.rows()
        self.assertEqual(rows[PHONE]["attempt_count"], 1)
        self.assertEqual(rows[PHONE]["attempts"][0]["ip"], "114.122.10.20")
        self.assertIsNone(rows[PHONE]["attempts"][0]["ip_blocked"])
        self.assertIn("google.com/maps", rows[PHONE]["attempts"][0]["maps_url"])
        self.assertEqual(rows["114.122.10.20"]["attempt_count"], 0)
        self.assertEqual(data["summary"]["attempts_7d"], 1)

    def test_attempts_endpoint_filters_and_is_owner_only(self):
        blocklist.record_attempt("phone", "081200000005", phone="081200000005", name="Andi", ip="1.2.3.4")
        r = self.owner.get("/api/orders/blocklist/attempts/")
        self.assertEqual((r.status_code, r.data["total"]), (200, 2))
        r = self.owner.get("/api/orders/blocklist/attempts/", {"q": "+62 812-0000-0005"})
        self.assertEqual([a["name"] for a in r.data["results"]], ["Andi"])
        old = BlockedAttempt.objects.get(phone="081200000005")
        BlockedAttempt.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=10))
        self.assertEqual(self.owner.get("/api/orders/blocklist/attempts/").data["total"], 1)
        self.assertEqual(self.owner.get("/api/orders/blocklist/attempts/", {"days": 30}).data["total"], 2)
        for role in ("admin", "kasir"):
            self.assertEqual(api_as(role).get("/api/orders/blocklist/attempts/").status_code, 403)

    def test_attempts_endpoint_flags_whether_the_ip_is_already_blocked(self):
        blocklist.record_attempt("phone", "081200000005", phone="081200000005", name="Andi", ip="1.2.3.4")
        by_ip = {a["ip"]: a["ip_blocked"] for a in self.owner.get("/api/orders/blocklist/attempts/").data["results"]}
        self.assertEqual(by_ip, {"114.122.10.20": True, "1.2.3.4": False})


class AdminSearchTests(Base):
    URL = "/api/orders/admin-search/"

    def setUp(self):
        super().setUp()
        self.owner = api_as("owner")
        self.order(name="Sari Dewi", phone="081355500001")
        self.order(name="Tono Scam", phone=PHONE)
        self.scam = Order.objects.get(customer_phone=PHONE)
        CustomerLoyalty.objects.create(phone="081355500001", name="Sari Dewi", points=120, total_orders=3)
        blocklist.block("phone", PHONE, reason="Order fiktif berulang", order_number=self.scam.order_number)
        blocklist.record_attempt("phone", PHONE, phone=PHONE, name="Tono", ip="114.122.10.20",
                                 info={"city": "Bekasi", "lat": -6.2349, "lng": 106.9896})
        Expense.objects.create(description="Beli ayam potong", amount=150000)

    def sections(self, client, q):
        r = client.get(self.URL, {"q": q})
        self.assertEqual(r.status_code, 200)
        return {s["title"]: s["items"] for s in r.data["sections"]}

    def test_short_or_empty_query_returns_nothing(self):
        for q in ("", " ", "a"):
            self.assertEqual(self.owner.get(self.URL, {"q": q}).data["sections"], [])

    def test_anonymous_rejected(self):
        self.assertIn(APIClient().get(self.URL, {"q": "budi"}).status_code, (401, 403))

    def test_owner_finds_order_by_phone_in_any_format(self):
        for q in (PHONE, "+62 812-3456-7890", "6281234567890", "34567"):
            items = self.sections(self.owner, q)["Pesanan"]
            self.assertEqual(items[0]["label"].split(" · ")[0], self.scam.order_number, q)

    def test_owner_finds_order_by_number_name_ip_city_and_item(self):
        for q in (self.scam.order_number, self.scam.order_number[-6:], "Tono", "114.122.10.20", "Bekasi", "Dimsum"):
            self.assertTrue(self.sections(self.owner, q).get("Pesanan"), q)

    def test_order_result_is_complete_for_owner(self):
        item = self.sections(self.owner, PHONE)["Pesanan"][0]
        self.assertIn(f"WA {PHONE}", item["details"])
        self.assertIn("IP 114.122.10.20", item["details"])
        self.assertTrue(any("Bekasi" in d for d in item["details"]))
        self.assertIn("google.com/maps", item["maps_url"])
        self.assertIn(f"q={self.scam.order_number}", item["to"])
        self.assertIn("Rp", item["hint"])

    def test_owner_sees_blocklist_attempts_staff_expenses_customers(self):
        s = self.sections(self.owner, PHONE)
        self.assertIn("Blokir anti-scam", s)
        self.assertIn("Percobaan terblokir", s)
        self.assertIn("Order fiktif", " ".join(s["Blokir anti-scam"][0]["details"]))
        self.assertIn("Pelanggan", self.sections(self.owner, "Sari"))
        self.assertIn("Staf", self.sections(self.owner, "081777000111"))
        self.assertIn("Pengeluaran", self.sections(self.owner, "ayam potong"))

    def test_staff_results_never_expose_pin_or_password(self):
        blob = json.dumps(self.owner.get(self.URL, {"q": "owner"}).data)
        self.assertNotIn("security_pin", blob)
        self.assertNotIn("pbkdf2", blob)

    def test_admin_gets_orders_and_customers_but_no_ip_location_or_owner_sections(self):
        admin = api_as("admin")
        s = self.sections(admin, PHONE)
        self.assertEqual(set(s), {"Pesanan"})
        blob = json.dumps(s)
        self.assertNotIn("114.122.10.20", blob)
        self.assertNotIn("Bekasi", blob)
        self.assertNotIn("google.com/maps", blob)
        self.assertEqual(self.sections(admin, "114.122.10.20"), {})       # IP tidak bisa dipakai mencari
        self.assertIn("Pelanggan", self.sections(admin, "Sari"))

    def test_kasir_only_sees_todays_orders(self):
        kasir = api_as("kasir")
        self.assertTrue(self.sections(kasir, PHONE).get("Pesanan"))
        Order.objects.update(created_at=timezone.now() - timedelta(days=3))
        self.assertEqual(self.sections(kasir, PHONE), {})
        self.assertTrue(self.sections(self.owner, PHONE).get("Pesanan"))   # owner tetap melihat semuanya

    def test_pelanggan_role_is_rejected(self):
        self.assertEqual(api_as("pelanggan").get(self.URL, {"q": "budi"}).status_code, 403)

    def test_search_does_not_duplicate_orders_with_many_items(self):
        o = Order.objects.get(pk=self.scam.pk)
        for _ in range(3):
            o.items.create(menu=self.menu, quantity=1, price=18500)
        self.assertEqual(len(self.sections(self.owner, "Dimsum")["Pesanan"]), 2)


@override_settings(**TG)
class TelegramTests(Base):
    def setUp(self):
        super().setUp()
        for name in ("Budi Santoso", "Budi S"):
            self.order(name=name)
        blocklist.block("phone", PHONE)
        blocklist.record_attempt("phone", PHONE, phone=PHONE, name="Budi", ip="114.122.10.20",
                                 info={"city": "Bekasi", "region": "Jawa Barat", "country": "ID"})

    def test_lacak_by_phone_in_any_format_shows_full_dossier(self):
        for q in (PHONE, "+62 812-3456-7890"):
            text = trace.lookup(q)
            for needle in (f"Jejak nomor {PHONE}", "Budi Santoso", "DIBLOKIR", "Percobaan order setelah diblokir: 1",
                           "114.122.10.20", "Bekasi", "google.com/maps", "Pesanan terakhir"):
                self.assertIn(needle, text, q)

    def test_lacak_unknown_phone_and_order_number_still_work(self):
        self.assertIn("Tidak ada pesanan dari nomor 081299999999", trace.lookup("081299999999"))
        o = Order.objects.first()
        self.assertIn(f"Jejak {o.order_number}", trace.lookup(o.order_number))
        self.assertIn("Jejak IP 114.122.10.20", trace.lookup("114.122.10.20"))

    def test_percobaan_command_lists_recent_attempts(self):
        text = trace.attempts_text()
        self.assertIn("Percobaan dari kontak terblokir (7 hari): 1", text)
        self.assertIn(PHONE, text)
        BlockedAttempt.objects.update(created_at=timezone.now() - timedelta(days=30))
        self.assertIn("Tidak ada percobaan", trace.attempts_text())

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_percobaan_and_lacak_commands_reach_the_right_chat_only(self, urlopen):
        from order import telegram_bot
        msg = lambda text, chat=111: {"chat": {"id": chat}, "from": {"id": 1}, "text": text}
        telegram_bot.handle_command(msg("/percobaan"))
        telegram_bot.handle_command(msg(f"/lacak {PHONE}"))
        telegram_bot.handle_command(msg("/percobaan", chat=999))      # chat asing: diam
        texts = self.texts(urlopen)
        self.assertEqual(len(texts), 2)
        self.assertIn("Percobaan dari kontak terblokir", texts[0])
        self.assertIn("Jejak nomor", texts[1])

    def test_help_mentions_new_commands(self):
        from order import telegram_ui
        self.assertIn("/percobaan", telegram_ui.HELP_TEXT)
        self.assertIn("nomor WA", telegram_ui.HELP_TEXT)
