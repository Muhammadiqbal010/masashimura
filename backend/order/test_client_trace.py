"""
Tes pelacakan asal pemesan (IP, lokasi perkiraan, perangkat).
Jalankan: python manage.py test order.test_client_trace   (Telegram di-mock, tidak ada pesan sungguhan terkirim)
"""
import json
from datetime import timedelta
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from menu.models import Category, Menu
from order import client_info as ci
from order import notify, trace
from order import telegram_ui as ui
from order.models import Order

ANDROID_CHROME = (
    "Mozilla/5.0 (Linux; Android 13; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36"
)
IPHONE_SAFARI = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1"
)


def bekasi_meta(**extra):
    meta = {
        "HTTP_X_FORWARDED_FOR": "114.122.10.20",
        "HTTP_X_VERCEL_IP_COUNTRY": "ID",
        "HTTP_X_VERCEL_IP_COUNTRY_REGION": "JB",
        "HTTP_X_VERCEL_IP_CITY": "Bekasi",
        "HTTP_X_VERCEL_IP_LATITUDE": "-6.2349",
        "HTTP_X_VERCEL_IP_LONGITUDE": "106.9896",
        "HTTP_X_VERCEL_IP_TIMEZONE": "Asia/Jakarta",
        "HTTP_USER_AGENT": ANDROID_CHROME,
    }
    meta.update(extra)
    return meta


# ── Bagian murni (tanpa DB) ─────────────────────────────────────────────────

class CollectTests(SimpleTestCase):
    def test_reads_vercel_headers(self):
        info = ci.collect(bekasi_meta())
        self.assertEqual(info["ip"], "114.122.10.20")
        self.assertEqual(info["country"], "ID")
        self.assertEqual(info["region"], "Jawa Barat")
        self.assertEqual(info["city"], "Bekasi")
        self.assertAlmostEqual(info["lat"], -6.2349)
        self.assertEqual(info["device"], "Android 13 · Chrome (SM-A546E)")
        self.assertFalse(info["bot"])

    def test_first_forwarded_entry_is_client_not_proxy(self):
        self.assertEqual(ci.get_ip({"HTTP_X_FORWARDED_FOR": "114.122.10.20, 76.76.21.21, 10.0.0.1"}), "114.122.10.20")

    def test_garbage_forwarded_falls_back_to_remote_addr(self):
        self.assertEqual(ci.get_ip({"HTTP_X_FORWARDED_FOR": "bukan-ip", "REMOTE_ADDR": "203.0.113.9"}), "203.0.113.9")

    def test_ip_with_port_and_ipv6(self):
        self.assertEqual(ci.get_ip({"HTTP_X_FORWARDED_FOR": "1.2.3.4:5678"}), "1.2.3.4")
        self.assertEqual(ci.get_ip({"HTTP_X_FORWARDED_FOR": "[2001:db8::1]:443"}), "2001:db8::1")

    def test_url_encoded_city_is_decoded(self):
        self.assertEqual(ci.collect({"HTTP_X_VERCEL_IP_CITY": "S%C3%A3o%20Paulo"})["city"], "São Paulo")

    def test_missing_headers_do_not_crash(self):
        info = ci.collect({})
        self.assertEqual(info["ip"], "")
        self.assertIsNone(info["lat"])
        self.assertTrue(info["bot"])   # tanpa User-Agent = bukan browser biasa

    def test_bad_coordinates_are_dropped(self):
        info = ci.collect({"HTTP_X_VERCEL_IP_LATITUDE": "999", "HTTP_X_VERCEL_IP_LONGITUDE": "abc"})
        self.assertIsNone(info["lat"])
        self.assertIsNone(info["lng"])

    def test_device_parsing(self):
        self.assertEqual(ci.parse_device(IPHONE_SAFARI), "iOS 17 · Safari")
        self.assertEqual(
            ci.parse_device("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36 Edg/124.0"),
            "Windows · Edge",
        )
        # Chrome modern menulis model "K": jangan ditampilkan
        self.assertEqual(
            ci.parse_device("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36"),
            "Android 10 · Chrome",
        )

    def test_script_user_agents_flagged_as_bot(self):
        for ua in ("python-requests/2.31", "curl/8.4.0", "PostmanRuntime/7.36", "", "HeadlessChrome Mozilla/5.0"):
            self.assertTrue(ci.looks_like_bot(ua), ua)
        self.assertFalse(ci.looks_like_bot(ANDROID_CHROME))
        self.assertFalse(ci.looks_like_bot(IPHONE_SAFARI))


class DistanceAndMapTests(SimpleTestCase):
    def test_jakarta_to_bandung_is_about_120km(self):
        km = ci.distance_km(-6.2088, 106.8456, -6.9175, 107.6191)
        self.assertTrue(110 < km < 130, km)

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(ci.distance_km(-6.2, 106.9, -6.2, 106.9), 0, places=3)

    def test_distance_needs_both_sides(self):
        self.assertIsNone(ci.distance_from_store({"lat": -6.2, "lng": 106.9}, None))
        self.assertIsNone(ci.distance_from_store({}, (-6.2, 106.9)))

    def test_maps_url(self):
        self.assertEqual(ci.maps_url(-6.2349, 106.9896), "https://www.google.com/maps?q=-6.2349,106.9896")
        self.assertEqual(ci.maps_url(None, 1), "")


class AssessTests(SimpleTestCase):
    def info(self, **kw):
        base = {"country": "ID", "bot": False}
        base.update(kw)
        return base

    def test_clean_order_has_no_flags(self):
        self.assertEqual(ci.assess("114.122.10.20", self.info(), history={"orders_24h": 1, "phones_24h": 1}), [])

    def test_foreign_country(self):
        flags = ci.assess("1.2.3.4", self.info(country="US"))
        self.assertEqual(len(flags), 1)
        self.assertIn("luar Indonesia (US)", flags[0])

    def test_bot_and_missing_ip(self):
        flags = ci.assess("", self.info(bot=True))
        self.assertTrue(any("IP tidak terbaca" in f for f in flags))
        self.assertTrue(any("skrip/bot" in f for f in flags))

    def test_far_from_store(self):
        self.assertTrue(any("Jauh dari toko (±120 km)" in f for f in ci.assess("1.2.3.4", self.info(), distance=120, radius_km=30)))
        self.assertEqual(ci.assess("1.2.3.4", self.info(), distance=12, radius_km=30), [])

    def test_repeat_ip_patterns(self):
        flags = ci.assess("1.2.3.4", self.info(), history={"orders_24h": 4, "phones_24h": 3, "auto_cancelled_7d": 2})
        self.assertEqual(len(flags), 3)

    def test_below_threshold_not_flagged(self):
        self.assertEqual(ci.assess("1.2.3.4", self.info(), history={"orders_24h": 2, "phones_24h": 2, "auto_cancelled_7d": 1}), [])


class RenderTests(SimpleTestCase):
    def view(self, **kw):
        v = {
            "id": 1, "order_number": "MSM-261027-AB12", "customer_name": "Budi", "customer_phone": "0812345678",
            "lines": ["• 2× Dimsum"], "total": 47500, "status": "pending", "payment_status": "pending",
            "awaiting": True, "tracks_readiness": True, "confirm_minutes": 15, "minutes_left": 12,
            "client": {
                "ip": "114.122.10.20", "city": "Bekasi", "region": "Jawa Barat", "country": "ID",
                "country_label": ci.country_label("ID"), "device": "Android 13 · Chrome (SM-A546E)",
                "maps_url": "https://www.google.com/maps?q=-6.2349,106.9896", "distance_km": 18.4,
            },
            "client_flags": [],
        }
        v.update(kw)
        return v

    def test_block_shows_ip_place_device_and_all_clear(self):
        text = ui.render_text(self.view())
        self.assertIn("IP: 114.122.10.20", text)
        self.assertIn("📍 Bekasi, Jawa Barat 🇮🇩 Indonesia", text)
        self.assertIn("📏 ±18 km dari toko", text)
        self.assertIn("📱 Android 13 · Chrome (SM-A546E)", text)
        self.assertIn("https://www.google.com/maps?q=-6.2349,106.9896", text)
        self.assertIn("✅ Tidak ada tanda janggal", text)

    def test_flags_are_listed(self):
        text = ui.render_text(self.view(client_flags=["Berasal dari luar Indonesia (US)"]))
        self.assertIn("🚩 Perhatikan:", text)
        self.assertIn("• Berasal dari luar Indonesia (US)", text)
        self.assertNotIn("✅ Tidak ada tanda janggal", text)

    def test_order_without_trace_has_no_block(self):
        text = ui.render_text(self.view(client=None, client_flags=[]))
        self.assertNotIn("Asal pemesan", text)

    def test_unreadable_ip_is_shown_as_such(self):
        v = self.view()
        v["client"] = dict(v["client"], ip="")
        self.assertIn("IP: tidak terbaca", ui.render_text(v))


# ── Dengan database ─────────────────────────────────────────────────────────

@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111", STORE_LATITUDE="-6.2400", STORE_LONGITUDE="106.9900")
class TraceFlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Dimsum", price=18500, category=cat)
        self.client_api = APIClient()

    def order(self, phone="081234567890", name="Budi Santoso", method="cash", **meta):
        return self.client_api.post("/api/orders/", {
            "source": "web", "payment_method": method,
            "customer": {"name": name, "phone": phone},
            "items": [{"menu_id": self.menu.pk, "quantity": 1}],
        }, format="json", **(bekasi_meta(**meta)))

    def sent_text(self, urlopen):
        return json.loads(urlopen.call_args[0][0].data)["text"]

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_ip_location_device_are_saved_and_sent_to_telegram(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.order()
        self.assertEqual(r.status_code, 201, r.data)
        o = Order.objects.get()
        self.assertEqual(o.client_ip, "114.122.10.20")
        self.assertEqual(o.client_info["city"], "Bekasi")
        self.assertEqual(o.client_info["device"], "Android 13 · Chrome (SM-A546E)")
        self.assertNotIn("ip", o.client_info)   # IP hanya di kolomnya sendiri
        text = self.sent_text(urlopen)
        self.assertIn("PESANAN WEB BARU", text)
        self.assertIn("IP: 114.122.10.20", text)
        self.assertIn("Bekasi, Jawa Barat", text)
        self.assertIn("dari toko", text)          # koordinat toko diisi → jarak tampil
        self.assertIn("✅ Tidak ada tanda janggal", text)

    def test_trace_never_leaks_to_customer_response(self):
        r = self.order()
        self.assertEqual(r.status_code, 201)
        body = json.dumps(r.data, default=str)
        self.assertNotIn("114.122.10.20", body)
        self.assertNotIn("client_ip", body)
        self.assertNotIn("client_info", body)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_foreign_and_script_orders_are_flagged(self, urlopen):
        with self.captureOnCommitCallbacks(execute=True):
            self.order(HTTP_X_VERCEL_IP_COUNTRY="NG", HTTP_X_VERCEL_IP_COUNTRY_REGION="LA",
                       HTTP_X_VERCEL_IP_CITY="Lagos", HTTP_USER_AGENT="python-requests/2.31",
                       HTTP_X_VERCEL_IP_LATITUDE="6.5244", HTTP_X_VERCEL_IP_LONGITUDE="3.3792")
        text = self.sent_text(urlopen)
        self.assertIn("🚩 Perhatikan:", text)
        self.assertIn("luar Indonesia (NG)", text)
        self.assertIn("skrip/bot", text)
        self.assertIn("Jauh dari toko", text)

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_same_ip_with_many_phones_is_flagged(self, urlopen):
        for phone, name in (("081200000001", "Orang Satu"), ("081200000002", "Orang Dua"), ("081200000003", "Orang Tiga")):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.order(phone=phone, name=name).status_code, 201)
        text = self.sent_text(urlopen)   # pesan order ke-3
        self.assertIn("3 nomor WA berbeda", text)
        self.assertIn("3 pesanan dalam 24 jam", text)

    def test_pending_cap_per_ip_redirects_to_qris(self):
        with override_settings(WEB_MAX_PENDING_PER_IP="2"):
            self.assertEqual(self.order(phone="081200000001").status_code, 201)
            self.assertEqual(self.order(phone="081200000002").status_code, 201)
            r = self.order(phone="081200000003")
            self.assertEqual(r.status_code, 409)
            self.assertTrue(r.data["require_qris"])
            self.assertEqual(r.data["reason"], "ip_pending")
            self.assertEqual(self.order(phone="081200000003", method="gateway").status_code, 201)   # QRIS tetap boleh
            # IP lain tidak ikut terkunci
            self.assertEqual(self.order(phone="081200000004", HTTP_X_FORWARDED_FOR="114.122.99.99").status_code, 201)

    def test_pending_cap_per_ip_can_be_disabled(self):
        with override_settings(WEB_MAX_PENDING_PER_IP="0"):
            for i in range(6):
                self.assertEqual(self.order(phone=f"08120000010{i}").status_code, 201)

    def test_accepted_orders_do_not_count_toward_cap(self):
        with override_settings(WEB_MAX_PENDING_PER_IP="1"):
            self.assertEqual(self.order(phone="081200000001").status_code, 201)
            Order.objects.update(awaiting_confirmation=False)   # kasir sudah menerima
            self.assertEqual(self.order(phone="081200000002").status_code, 201)

    def test_qris_orders_skip_pending_cap(self):
        with override_settings(WEB_MAX_PENDING_PER_IP="1"):
            self.assertEqual(self.order(phone="081200000001").status_code, 201)
            self.assertEqual(self.order(phone="081200000002", method="gateway").status_code, 201)


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_CHAT_ID="111")
class LacakCommandTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Dimsum", price=18500, category=cat)
        self.api = APIClient()

    def make(self, phone, name, ip="114.122.10.20", **meta):
        r = self.api.post("/api/orders/", {
            "source": "web", "payment_method": "cash",
            "customer": {"name": name, "phone": phone},
            "items": [{"menu_id": self.menu.pk, "quantity": 1}],
        }, format="json", **bekasi_meta(HTTP_X_FORWARDED_FOR=ip, **meta))
        self.assertEqual(r.status_code, 201, r.data)
        return Order.objects.get(order_number=r.data["order_number"])

    def test_lookup_by_order_number_lists_other_orders_from_same_ip(self):
        a = self.make("081200000001", "Andi")
        b = self.make("081200000002", "Budi")
        text = trace.lookup(b.order_number.lower())
        self.assertIn(f"Jejak {b.order_number}", text)
        self.assertIn("IP: 114.122.10.20", text)
        self.assertIn(a.order_number, text)         # order lain dari IP yang sama
        self.assertIn("Andi", text)
        self.assertNotIn(f"• {b.order_number}", text)   # dirinya sendiri tidak diulang di daftar

    def test_lookup_by_last_four_characters(self):
        o = self.make("081200000001", "Andi")
        self.assertIn(f"Jejak {o.order_number}", trace.lookup(o.order_number[-4:]))

    def test_lookup_by_ip(self):
        self.make("081200000001", "Andi")
        self.make("081200000002", "Budi")
        text = trace.lookup("114.122.10.20")
        self.assertIn("Jejak IP 114.122.10.20", text)
        self.assertIn("2 nomor WA berbeda", text)

    def test_lookup_unknown_and_empty(self):
        self.assertIn("tidak ditemukan", trace.lookup("TIDAKADA"))
        self.assertIn("Tidak ada pesanan web dari IP 9.9.9.9", trace.lookup("9.9.9.9"))
        self.assertIn("/lacak", trace.lookup(""))

    def test_pos_or_old_order_without_trace(self):
        o = Order.objects.create(source="pos", status="completed", payment_status="paid", payment_method="cash")
        self.assertIn("Tidak ada jejak asal", trace.lookup(o.order_number))

    @mock.patch("order.notify.urllib.request.urlopen")
    def test_telegram_command_replies_only_to_registered_chat(self, urlopen):
        from order import telegram_bot
        o = self.make("081200000001", "Andi")
        telegram_bot.handle_command({"chat": {"id": 999}, "from": {"id": 1}, "text": f"/lacak {o.order_number}"})
        urlopen.assert_not_called()                 # chat asing: diam saja
        telegram_bot.handle_command({"chat": {"id": 111}, "from": {"id": 1}, "text": f"/lacak {o.order_number}"})
        body = json.loads(urlopen.call_args[0][0].data)
        self.assertEqual(body["chat_id"], "111")
        self.assertIn("Jejak " + o.order_number, body["text"])

    def test_auto_cancelled_history_is_flagged(self):
        from order import events
        for i, name in enumerate(("Hantu Satu", "Hantu Dua")):
            o = self.make(f"08120000000{i}", name)
            Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(days=1, hours=i))
            events.record(Order.objects.get(pk=o.pk), "auto_cancelled", actor="sistem", channel="system")
        new = self.make("081200000009", "Baru")
        client, flags = notify.client_view(new)
        self.assertTrue(any("tidak pernah diterima" in f for f in flags), flags)


class PurgeCommandTests(TestCase):
    def test_purge_only_old_orders_and_keeps_the_order_itself(self):
        old = Order.objects.create(source="web", client_ip="1.2.3.4", client_info={"city": "X"})
        new = Order.objects.create(source="web", client_ip="5.6.7.8", client_info={"city": "Y"})
        Order.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=120))
        call_command("purge_client_info", "--days", "90", "--dry-run")
        old.refresh_from_db()
        self.assertEqual(old.client_ip, "1.2.3.4")   # dry-run tidak mengubah apa pun
        call_command("purge_client_info", "--days", "90")
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertIsNone(old.client_ip)
        self.assertEqual(old.client_info, {})
        self.assertEqual(new.client_ip, "5.6.7.8")   # order baru utuh
