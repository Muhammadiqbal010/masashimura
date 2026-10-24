"""Tes Simulasi (#19). Jalankan: python manage.py test order.test_simulation"""
from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from order import simulation
from order.models import Order, StoreSettings, WIB
from promotions.models import Promo

NOW = datetime(2026, 10, 14, 15, 0, tzinfo=WIB)   # Rabu; hari ke-14 bulan Oktober (31 hari)


def day(n):
    """Pukul 12 WIB, n hari sebelum NOW."""
    return (NOW - timedelta(days=n)).replace(hour=12)


def order(when, total, promo=None, disc=0):
    return Order.objects.create(
        created_at=when, status="completed", payment_status="paid",
        subtotal=total + disc, total_price=total, promo=promo, promo_discount_amount=disc,
    )


def fake_pack(per_day, today=NOW.date()):
    """Prediksi model palsu: per_day rupiah untuk setiap hari dari hari ini sampai 31 Okt."""
    days = [{"predicted_revenue": per_day, "is_regular_closed_day": False} for _ in range((today.replace(day=31) - today).days + 1)]
    return {"method": "baseline", "confidence": "rendah", "days": days}


class TargetTests(TestCase):
    def setUp(self):
        p = mock.patch("order.simulation._model_pack", return_value=None)
        p.start()
        self.addCleanup(p.stop)
        self.store = StoreSettings.get()
        self.store.monthly_revenue_target = 6_000_000
        self.store.operating_hours = {}      # semua hari buka
        self.store.save()

    def test_arithmetic_base(self):
        # 13 hari lewat (1..13 Okt) x Rp100.000 + hari ini Rp50.000
        for n in range(1, 14):
            order(day(n), 100_000)
        order(day(0), 50_000)
        t = simulation.target_base(StoreSettings.get(), NOW.date(), NOW)
        self.assertTrue(t["enough_data"])
        self.assertEqual(t["open_days_elapsed"], 13)
        self.assertEqual(t["remaining_open_days"], 17)            # 15..31 Okt
        self.assertEqual(t["realized"], 1_350_000)
        self.assertEqual(t["avg_open_day"], 100_000)
        self.assertEqual(t["projected_base"], 1_350_000 + 17 * 100_000)
        # butuh (6.000.000-1.350.000)/(100.000*17) - 1 = 173,5% kenaikan
        self.assertEqual(t["basis"], "average")
        self.assertEqual(t["needed_growth_pct"], 173.5)
        self.assertEqual(t["needed_per_open_day"], 273_529)       # 4.650.000 / 17
        self.assertEqual(t["needed_multiplier"], 2.7)

    def test_uses_model_forecast_like_briefing(self):
        # Hari ini (Rabu 15.00, toko buka sepanjang hari) belum tuntas: bagian hari ini = max(aktual, prediksi).
        for n in range(1, 14):
            order(day(n), 100_000)
        order(day(0), 50_000)
        with mock.patch("order.simulation._model_pack", return_value=fake_pack(80_000)):
            t = simulation.target_base(StoreSettings.get(), NOW.date(), NOW)
        self.assertEqual(t["basis"], "model")
        # 1.300.000 (1..13 Okt) + 80.000 (hari ini, prediksi > aktual) + 17 x 80.000 sisa
        self.assertEqual(t["fixed_part"], 1_380_000)
        self.assertEqual(t["forecast_remaining"], 1_360_000)
        self.assertEqual(t["projected_base"], 2_740_000)
        self.assertEqual(t["forecast_per_open_day"], 80_000)

    def test_model_works_even_with_few_open_days(self):
        with mock.patch("order.simulation._model_pack", return_value=fake_pack(80_000)):
            t = simulation.target_base(StoreSettings.get(), NOW.date(), NOW)
        self.assertTrue(t["enough_data"])
        self.assertEqual(t["basis"], "model")

    def test_closed_days_not_counted(self):
        # Rabu (2) tutup. 1..13 Okt memuat satu Rabu (7 Okt); 15..31 Okt memuat dua Rabu (21 dan 28 Okt)
        self.store.operating_hours = {str(i): {"open": "10:00", "close": "20:00"} for i in (0, 1, 3, 4, 5, 6)}
        self.store.save()
        for n in range(1, 14):
            order(day(n), 100_000)
        t = simulation.target_base(StoreSettings.get(), NOW.date(), NOW)
        self.assertEqual(t["open_days_elapsed"], 12)              # 13 hari lewat dikurangi 1 Rabu (7 Okt)
        self.assertEqual(t["remaining_open_days"], 15)            # 17 hari tersisa dikurangi 2 Rabu
        self.assertEqual(t["avg_open_day"], round(1_300_000 / 12))

    def test_not_enough_data(self):
        # Tanggal 3 Okt: baru 2 hari buka yang lewat (1 dan 2 Okt), di bawah MIN_OPEN_DAYS (3).
        early = datetime(2026, 10, 3, 15, 0, tzinfo=WIB)
        order(early - timedelta(days=1), 100_000)
        t = simulation.target_base(StoreSettings.get(), early.date(), early)
        self.assertEqual(t["open_days_elapsed"], 2)
        self.assertFalse(t["enough_data"])
        self.assertIsNone(t["projected_base"])
        self.assertIsNone(t["needed_growth_pct"])

    def test_target_reached_has_no_needed_growth(self):
        for n in range(1, 14):
            order(day(n), 600_000)
        t = simulation.target_base(StoreSettings.get(), NOW.date(), NOW)
        self.assertTrue(t["target_reached"])
        self.assertIsNone(t["needed_growth_pct"])


class PromoTests(TestCase):
    def setUp(self):
        self.promo = Promo.objects.create(
            code="HEMAT", discount_type="fixed", discount_value=2000,
            valid_from=NOW - timedelta(days=100), valid_until=NOW + timedelta(days=30),
        )

    def test_difference_between_promo_and_non_promo_days(self):
        for n in range(1, 6):
            order(day(n), 150_000, promo=self.promo, disc=2000)
        for n in range(6, 11):
            order(day(n), 100_000)
        p = simulation.promo_base(NOW.date())
        self.assertTrue(p["enough_data"])
        self.assertEqual((p["promo_days"], p["non_promo_days"]), (5, 5))
        self.assertEqual(p["diff"], 50_000)
        self.assertEqual(p["diff_pct"], 50.0)

    def test_one_promo_order_makes_the_day_a_promo_day(self):
        order(day(1), 100_000)
        order(day(1), 100_000, promo=self.promo, disc=2000)
        p = simulation.promo_base(NOW.date())
        self.assertEqual(p["promo_days"], 1)
        self.assertEqual(p["avg_promo_day"], 200_000)

    def test_not_enough_days(self):
        for n in range(1, 4):
            order(day(n), 150_000, promo=self.promo, disc=2000)
        p = simulation.promo_base(NOW.date())
        self.assertFalse(p["enough_data"])
        self.assertIsNone(p["diff"])

    def test_today_and_cancelled_are_excluded(self):
        order(day(0), 999_000, promo=self.promo, disc=2000)
        o = order(day(1), 500_000)
        Order.objects.filter(pk=o.pk).update(status="cancelled")
        p = simulation.promo_base(NOW.date())
        self.assertEqual((p["promo_days"], p["non_promo_days"]), (0, 0))


class EndpointTests(TestCase):
    def client_for(self, role):
        u, _ = User.objects.get_or_create(username=role)
        UserProfile.objects.update_or_create(user=u, defaults={"role": role})
        c = APIClient()
        c.force_authenticate(u)
        return c

    def test_permissions_and_shape(self):
        url = "/api/orders/analytics/simulation/"
        self.assertEqual(self.client_for("kasir").get(url).status_code, 403)
        self.assertIn(APIClient().get(url).status_code, (401, 403))
        r = self.client_for("admin").get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.data), {"target", "promo", "notes"})
