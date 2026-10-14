"""Tes indikator keramaian & Peta Jam Sibuk. Jalankan: python manage.py test order.test_crowd"""
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from order import crowd
from order.models import Order, StoreSettings, WIB

SCHEDULE = {str(d): {"open": "11:00", "close": "22:00"} for d in range(6)}
SCHEDULE["6"] = None  # Minggu libur


def wib(y, m, d, h=0, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=WIB)


def make_orders(at, n, **kw):
    for _ in range(n):
        Order.objects.create(created_at=at, **kw)


def make_user(role):
    u = User.objects.create_user(role, password="x")
    UserProfile.objects.update_or_create(user=u, defaults={"role": role})
    c = APIClient()
    c.force_authenticate(u)
    return c


class StatusTests(TestCase):
    def setUp(self):
        self.store = StoreSettings.get()
        self.store.operating_hours = SCHEDULE
        self.store.save()
        # Rabu 14 Okt 2026, 15.00 WIB (jam buka)
        self.now = wib(2026, 10, 14, 15, 0)

    def test_store_open_follows_schedule_and_override(self):
        self.assertTrue(crowd.is_store_open(self.store, self.now))
        self.assertFalse(crowd.is_store_open(self.store, wib(2026, 10, 14, 23, 0)))
        self.assertFalse(crowd.is_store_open(self.store, wib(2026, 10, 18, 15, 0)))  # Minggu
        self.store.is_open_override = True
        self.assertTrue(crowd.is_store_open(self.store, wib(2026, 10, 18, 15, 0)))
        self.store.is_open_override = False
        self.assertFalse(crowd.is_store_open(self.store, self.now))

    def test_fallback_thresholds_when_history_thin(self):
        self.assertEqual(crowd.auto_level(self.store, self.now)["level"], "santai")
        make_orders(self.now - timedelta(minutes=10), 4)
        a = crowd.auto_level(self.store, self.now)
        self.assertEqual((a["level"], a["source"]), ("sedang", "fallback"))
        make_orders(self.now - timedelta(minutes=20), 3)
        self.assertEqual(crowd.auto_level(self.store, self.now)["level"], "ramai")

    def test_cancelled_and_void_do_not_count(self):
        make_orders(self.now - timedelta(minutes=5), 9, status="cancelled")
        make_orders(self.now - timedelta(minutes=5), 9, payment_status="void")
        self.assertEqual(crowd.live_orders(self.now), 0)

    def test_thresholds_from_history(self):
        # 3 minggu lalu s/d kemarin: tiap hari buka (Sen-Sab) jam 12 & 13 masing-masing 6 pesanan
        for i in range(1, 22):
            d = (self.now - timedelta(days=i))
            if d.weekday() == 6:
                continue
            make_orders(wib(d.year, d.month, d.day, 12, 30), 6)
            make_orders(wib(d.year, d.month, d.day, 13, 30), 6)
        low, high, src = crowd.thresholds(self.store, self.now, weeks=4)
        self.assertEqual(src, "history")
        self.assertLess(low, high)
        make_orders(self.now - timedelta(minutes=5), high + 1)
        self.assertEqual(crowd.auto_level(self.store, self.now)["level"], "ramai")

    def test_manual_expires_without_cron(self):
        make_orders(self.now - timedelta(minutes=5), 8)  # auto = ramai
        self.assertIsNone(crowd.set_manual(self.store, "santai", minutes=60, now=self.now))
        s = crowd.crowd_status(self.store, self.now)
        self.assertEqual((s["level"], s["mode"]), ("santai", "manual"))
        later = self.now + timedelta(minutes=61)
        make_orders(later - timedelta(minutes=5), 8)
        s = crowd.crowd_status(self.store, later)
        self.assertEqual((s["level"], s["mode"]), ("ramai", "auto"))

    def test_manual_until_clock_and_validation(self):
        self.assertIsNone(crowd.set_manual(self.store, "ramai", until="20:00", now=self.now))
        self.assertEqual(crowd.to_wib(self.store.crowd_manual_until).hour, 20)
        self.assertIn("lewat", crowd.set_manual(self.store, "ramai", until="14:00", now=self.now))
        self.assertIn("Maksimal", crowd.set_manual(self.store, "ramai", until="23:00", now=wib(2026, 10, 14, 5, 0)))
        self.assertTrue(crowd.set_manual(self.store, "ramai", minutes=1, now=self.now))
        self.assertTrue(crowd.set_manual(self.store, "padat", minutes=30, now=self.now))
        self.assertTrue(crowd.set_manual(self.store, "ramai", until="abc", now=self.now))
        self.assertIsNone(crowd.set_manual(self.store, "auto", now=self.now))
        self.assertFalse(crowd.manual_active(self.store, self.now))

    def test_hidden_when_closed_or_disabled(self):
        closed = wib(2026, 10, 14, 23, 30)
        self.assertFalse(crowd.crowd_status(self.store, closed)["visible"])
        self.assertIsNone(crowd.crowd_status(self.store, closed)["level"])
        self.assertIsNotNone(crowd.crowd_status(self.store, closed, detail=True)["level"])
        crowd.set_manual(self.store, "ramai", minutes=60, now=self.now)
        self.store.crowd_indicator_enabled = False
        s = crowd.crowd_status(self.store, self.now)
        self.assertFalse(s["visible"])
        self.assertIsNone(s["level"])


class BusyHoursTests(TestCase):
    def setUp(self):
        self.store = StoreSettings.get()
        self.store.operating_hours = SCHEDULE
        self.store.save()
        self.now = wib(2026, 10, 14, 15, 0)

    def test_average_per_occurrence(self):
        # 4 minggu penuh; tiap Jumat jam 19 ada 8 pesanan -> rata-rata 8/jam
        d = wib(2026, 10, 9)  # Jumat
        for w in range(1, 5):
            day = d - timedelta(weeks=w - 1)
            make_orders(day.replace(hour=19, minute=15), 8)
        make_orders(wib(2026, 10, 7, 12), 2)  # Rabu
        data = crowd.busy_hours(self.store, self.now, weeks=4)
        self.assertEqual(data["grid"][4][19], 8.0)
        self.assertEqual(data["busiest"][0]["label"], "Jumat 19.00–20.00")
        self.assertEqual(data["total_orders"], 34)
        self.assertTrue(data["enough_data"])
        self.assertEqual(data["hour_range"], [11, 22])
        self.assertIsNone(data["open_hours"][6])
        # slot sepi tidak boleh jatuh di hari/jam tutup
        for q in data["quietest"]:
            self.assertNotEqual(q["day"], 6)
            self.assertTrue(11 <= q["hour"] < 22)

    def test_today_excluded_and_timezone_is_wib(self):
        make_orders(wib(2026, 10, 14, 11), 5)   # hari ini: dibuang
        # 23.30 WIB = 16.30 UTC masih hari yang sama di WIB, jam 23
        make_orders(wib(2026, 10, 13, 23, 30), 1)
        data = crowd.busy_hours(self.store, self.now, weeks=2)
        self.assertEqual(data["total_orders"], 1)
        self.assertGreater(data["grid"][1][23], 0)   # Selasa jam 23

    def test_empty_history(self):
        data = crowd.busy_hours(self.store, self.now)
        self.assertEqual(data["total_orders"], 0)
        self.assertFalse(data["enough_data"])
        self.assertEqual(data["busiest"], [])


class ApiTests(TestCase):
    def setUp(self):
        self.store = StoreSettings.get()
        self.store.operating_hours = {}   # selalu buka
        self.store.save()

    def test_public_status_no_auth_and_cache_header(self):
        r = APIClient().get("/api/orders/crowd/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Control"], "public, max-age=30")
        self.assertNotIn("auto", r.json())

    def test_manual_requires_staff_and_kasir_allowed(self):
        self.assertIn(APIClient().post("/api/orders/crowd/manual/", {"level": "ramai", "duration_minutes": 30}).status_code, (401, 403))
        kasir = make_user("kasir")
        r = kasir.post("/api/orders/crowd/manual/", {"level": "ramai", "duration_minutes": 30}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["level"], "ramai")
        self.assertEqual(APIClient().get("/api/orders/crowd/").json()["level"], "ramai")
        bad = kasir.post("/api/orders/crowd/manual/", {"level": "ramai", "duration_minutes": 9999}, format="json")
        self.assertEqual(bad.status_code, 400)
        r = kasir.post("/api/orders/crowd/manual/", {"level": "auto"}, format="json")
        self.assertEqual(r.json()["mode"], "auto")

    def test_busy_hours_admin_only(self):
        self.assertEqual(make_user("kasir").get("/api/orders/busy-hours/").status_code, 403)
        r = make_user("admin").get("/api/orders/busy-hours/?weeks=abc")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["weeks"], 8)
        self.assertEqual(make_user("owner").get("/api/orders/busy-hours/?weeks=999").json()["weeks"], 26)

    def test_toggle_via_settings_endpoint(self):
        r = make_user("owner").put("/api/orders/settings/", {"crowd_indicator_enabled": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(APIClient().get("/api/orders/crowd/").json()["visible"])
