"""Tes Strip Briefing & perkiraan menu besok. Jalankan: python manage.py test order.test_briefing"""
from datetime import datetime, timedelta
from unittest import mock

import pandas as pd
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import analytics, briefing
from order.models import Order, OrderItem, StoreSettings, WIB
from prediction.models import RevenuePredictionSnapshot
from promotions.models import Promo

SCHEDULE = {str(d): {"open": "11:00", "close": "22:00"} for d in range(6)}
SCHEDULE["6"] = None   # Minggu libur

NOW = datetime(2026, 10, 14, 15, 0, tzinfo=WIB)        # Rabu 14 Okt 2026, 15.00 (toko buka)
NOW_LATE = datetime(2026, 10, 14, 23, 0, tzinfo=WIB)   # lewat jam tutup


def wib(m, d, h=12, y=2026):
    return datetime(y, m, d, h, 0, tzinfo=WIB)


def paid(at, total):
    return Order.objects.create(created_at=at, status="completed", payment_status="paid", total_price=total)


def history_df(days=28, revenue=100_000):
    """Omzet harian rata Rp100.000 selama 28 hari sampai kemarin (13 Okt)."""
    end = pd.Timestamp("2026-10-13")
    idx = pd.date_range(end=end, periods=days, freq="D")
    return pd.DataFrame({"date": idx, "revenue": float(revenue)})


def with_history(df=None, closed=(6,)):
    """Patch sumber data prediksi supaya deterministik, lepas dari jam asli server."""
    frame = history_df() if df is None else df
    return (
        mock.patch("prediction.ml.predict.get_daily_revenue_df", return_value=frame),
        mock.patch("prediction.ml.predict.get_regular_closed_weekdays", return_value=set(closed)),
        mock.patch("prediction.ml.predict._load_metadata", return_value={}),
    )


def make_client(role):
    u = User.objects.filter(username=role).first() or User.objects.create_user(role, password="x")
    UserProfile.objects.update_or_create(user=u, defaults={"role": role})
    c = APIClient()
    c.force_authenticate(u)
    return c


class BriefingBase(TestCase):
    def setUp(self):
        self.store = StoreSettings.get()
        self.store.operating_hours = SCHEDULE
        self.store.save()
        # Omzet bulan ini: 10 order x Rp100.000 pada 5 Okt, + Rp40.000 hari ini.
        for _ in range(10):
            paid(wib(10, 5), 100_000)
        paid(wib(10, 14, 12), 40_000)

    def run_briefing(self, now=NOW, df=None):
        p1, p2, p3 = with_history(df)
        with p1, p2, p3:
            return briefing.briefing(self.store, now)


class TargetTests(BriefingBase):
    def test_projection_and_gap(self):
        self.store.monthly_revenue_target = 3_000_000
        self.store.save()
        d = self.run_briefing()
        t = d["target"]
        # realisasi = 1.000.000 + 40.000; hari ini = max(40.000, prediksi 100.000);
        # sisa 15 hari buka (15-31 Okt, tanpa 2 hari Minggu) x 100.000 = 1.500.000
        self.assertEqual(t["realized"], 1_040_000)
        self.assertEqual(t["projected"], 2_600_000)
        self.assertEqual(t["gap"], 400_000)
        self.assertEqual(t["status"], "di_bawah")
        self.assertEqual(t["days_left"], 17)
        self.assertEqual(t["month_label"], "Oktober 2026")
        self.assertEqual(t["confidence"], "sedang")

    def test_after_closing_uses_actual_today(self):
        self.store.monthly_revenue_target = 3_000_000
        self.store.save()
        t = self.run_briefing(NOW_LATE)["target"]
        self.assertEqual(t["projected"], 2_540_000)     # hari ini = omzet aktual saja

    def test_statuses(self):
        self.store.monthly_revenue_target = 2_000_000
        self.store.save()
        self.assertEqual(self.run_briefing()["target"]["status"], "di_jalur")
        self.store.monthly_revenue_target = 500_000
        self.store.save()
        self.assertEqual(self.run_briefing()["target"]["status"], "tercapai")
        self.store.monthly_revenue_target = None
        self.store.save()
        t = self.run_briefing()["target"]
        self.assertEqual(t["status"], "belum_ada_target")
        self.assertIsNone(t["target"])
        self.assertIsNone(t["gap"])

    def test_no_history_means_no_projection_but_realized_stays(self):
        self.store.monthly_revenue_target = 3_000_000
        self.store.save()
        empty = pd.DataFrame(columns=["date", "revenue"])
        d = self.run_briefing(df=empty)
        self.assertEqual(d["errors"], [])
        self.assertIsNone(d["target"]["projected"])
        self.assertEqual(d["target"]["status"], "proyeksi_tidak_tersedia")
        self.assertEqual(d["target"]["realized"], 1_040_000)
        self.assertIsNone(d["prediction_today"]["predicted"])
        self.assertEqual(d["prediction_today"]["actual_so_far"], 40_000)

    def test_cancelled_and_unpaid_not_counted_as_revenue(self):
        Order.objects.create(created_at=wib(10, 6), status="cancelled", payment_status="paid", total_price=999_999)
        Order.objects.create(created_at=wib(10, 6), status="pending", payment_status="unpaid", total_price=888_888)
        self.assertEqual(self.run_briefing()["target"]["realized"], 1_040_000)


class SectionTests(BriefingBase):
    def test_prediction_today(self):
        p = self.run_briefing()["prediction_today"]
        self.assertEqual(p["predicted"], 100_000)
        self.assertEqual(p["actual_so_far"], 40_000)
        self.assertFalse(p["is_closed_day"])
        self.assertEqual(p["confidence"], "sedang")

    def test_closed_day_today(self):
        sunday = datetime(2026, 10, 18, 15, 0, tzinfo=WIB)
        p = self.run_briefing(sunday)["prediction_today"]
        self.assertTrue(p["is_closed_day"])
        self.assertEqual(p["predicted"], 0)

    def test_crowd_and_unpaid(self):
        Order.objects.create(created_at=wib(10, 13, 12), status="pending", payment_status="unpaid", total_price=50_000)
        Order.objects.create(created_at=wib(10, 14, 13), status="pending", payment_status="unpaid", total_price=30_000)
        Order.objects.create(created_at=wib(10, 14, 13), status="cancelled", payment_status="unpaid", total_price=70_000)
        d = self.run_briefing()
        self.assertEqual(d["unpaid"], {"count": 2, "total": 80_000.0, "older_count": 1, "older_total": 50_000.0})
        self.assertIn(d["crowd"]["level"], ("santai", "sedang", "ramai"))
        self.assertTrue(d["crowd"]["store_open"])

    def test_one_failing_section_does_not_break_others(self):
        with mock.patch("order.briefing._unpaid_section", side_effect=RuntimeError("boom")):
            d = self.run_briefing()
        self.assertEqual(d["errors"], ["unpaid"])
        self.assertIsNone(d["unpaid"])
        self.assertIsNotNone(d["target"])
        self.assertIsNotNone(d["prediction_today"])
        self.assertIsNotNone(d["crowd"])

    def test_saves_snapshots_open_days_only(self):
        self.run_briefing()
        rows = RevenuePredictionSnapshot.objects.all()
        self.assertTrue(rows.exists())
        self.assertLessEqual(rows.count(), 14)
        self.assertEqual({r.made_on.isoformat() for r in rows}, {"2026-10-14"})
        self.assertEqual(min(r.target_date for r in rows).isoformat(), "2026-10-14")   # hari ini ikut
        self.assertNotIn(6, {r.target_date.weekday() for r in rows})                   # Minggu libur
        count = rows.count()
        self.run_briefing()                                                             # buka lagi: tidak dobel
        self.assertEqual(RevenuePredictionSnapshot.objects.count(), count)


class RecommendationTests(BriefingBase):
    def test_short_target_advice_mentions_gap_with_reason(self):
        self.store.monthly_revenue_target = 3_000_000
        self.store.save()
        recs = self.run_briefing()["recommendations"]
        top = recs[0]
        self.assertEqual(top["id"], "target_short")
        self.assertIn("Rp400.000", top["text"])
        self.assertIn("17 hari", top["reason"])

    def test_missing_target_prompts_setup(self):
        ids = [r["id"] for r in self.run_briefing()["recommendations"]]
        self.assertIn("target_missing", ids)

    def test_unpaid_from_earlier_day(self):
        Order.objects.create(created_at=wib(10, 12), status="pending", payment_status="unpaid", total_price=45_000)
        recs = self.run_briefing()["recommendations"]
        rec = next(r for r in recs if r["id"] == "unpaid_old")
        self.assertIn("1 tagihan", rec["text"])
        self.assertIn("Rp45.000", rec["text"])

    def test_unused_promo(self):
        Promo.objects.create(
            code="SEPI", discount_type="fixed", discount_value=5000,
            valid_from=NOW - timedelta(days=30), valid_until=NOW + timedelta(days=30), used_count=0,
        )
        Promo.objects.create(   # baru berjalan: belum dinilai
            code="BARU", discount_type="fixed", discount_value=5000,
            valid_from=NOW - timedelta(days=3), valid_until=NOW + timedelta(days=30), used_count=0,
        )
        recs = self.run_briefing()["recommendations"]
        promo = [r for r in recs if r["id"] == "promo_unused"]
        self.assertEqual(len(promo), 1)
        self.assertIn("SEPI", promo[0]["text"])

    def test_at_most_three_and_warnings_first(self):
        self.store.monthly_revenue_target = 3_000_000
        self.store.save()
        Order.objects.create(created_at=wib(10, 12), status="pending", payment_status="unpaid", total_price=45_000)
        Promo.objects.create(
            code="SEPI", discount_type="fixed", discount_value=5000,
            valid_from=NOW - timedelta(days=30), valid_until=NOW + timedelta(days=30), used_count=0,
        )
        recs = self.run_briefing()["recommendations"]
        self.assertLessEqual(len(recs), 3)
        self.assertEqual([r["id"] for r in recs][:2], ["target_short", "unpaid_old"])
        self.assertEqual(recs[0]["tone"], "warn")


class MenuTomorrowTests(TestCase):
    def setUp(self):
        self.store = StoreSettings.get()
        self.store.operating_hours = SCHEDULE
        self.store.save()
        c = Category.objects.create(name="Utama")
        self.a = Menu.objects.create(name="Katsu", price=20000, category=c)
        self.b = Menu.objects.create(name="Es Teh", price=5000, category=c)
        self.c = Menu.objects.create(name="Mochi", price=30000, category=c)
        self.off = Menu.objects.create(name="Lama", price=1000, category=c, is_active=False)

    def order(self, at, items, status="completed", pay="paid"):
        o = Order.objects.create(created_at=at, status=status, payment_status=pay)
        for m, q in items:
            OrderItem.objects.create(order=o, menu=m, quantity=q, price=m.price)
        return o

    # Besok = Kamis 15 Okt. Kamis sebelumnya: 8 Okt, 1 Okt, 24 Sep, 17 Sep, ...
    def test_ranking_labels_and_exclusions(self):
        for day in [(10, 8), (10, 1), (9, 24)]:
            self.order(wib(*day), [(self.a, 3), (self.b, 1)])
        self.order(wib(9, 24), [(self.c, 1)])
        self.order(wib(10, 8), [(self.a, 50)], status="cancelled")           # tidak dihitung
        self.order(wib(10, 8), [(self.a, 50)], pay="void")                   # tidak dihitung
        self.order(wib(10, 8), [(self.off, 9)])                              # menu nonaktif
        self.order(wib(10, 7), [(self.c, 99)])                               # Rabu, bukan hari yang sama
        self.order(wib(10, 1, 14), [(self.b, 1)], pay="unpaid", status="pending")  # belum lunas tetap dihitung
        d = analytics.menu_tomorrow(self.store, NOW)
        self.assertFalse(d["closed"])
        self.assertEqual(d["day_name"], "Kamis")
        self.assertEqual(d["sample_days"], 3)
        self.assertTrue(d["enough_data"])
        names = [m["name"] for m in d["menus"]]
        self.assertEqual(names[0], "Katsu")
        self.assertNotIn("Lama", names)
        by = {m["name"]: m for m in d["menus"]}
        self.assertEqual(by["Katsu"]["level"], "tinggi")
        self.assertEqual(by["Es Teh"]["level"], "sedang")
        for m in d["menus"]:
            self.assertNotIn("qty", m)       # tanpa angka porsi
            self.assertNotIn("score", m)

    def test_recent_weeks_weigh_more(self):
        # A: 4 porsi di dua Kamis terlama. B: 3 porsi di dua Kamis terbaru.
        for day in [(9, 24), (9, 17)]:
            self.order(wib(*day), [(self.a, 4)])
        for day in [(10, 8), (10, 1)]:
            self.order(wib(*day), [(self.b, 3)])
        names = [m["name"] for m in analytics.menu_tomorrow(self.store, NOW)["menus"]]
        self.assertEqual(names[:2], ["Es Teh", "Katsu"])    # 5,4 vs 4,608 -> B menang walau total lebih sedikit

    def test_not_enough_data_flag(self):
        self.order(wib(10, 8), [(self.a, 3)])
        d = analytics.menu_tomorrow(self.store, NOW)
        self.assertEqual(d["sample_days"], 1)
        self.assertFalse(d["enough_data"])
        self.assertEqual(len(d["menus"]), 1)

    def test_no_history_at_all(self):
        d = analytics.menu_tomorrow(self.store, NOW)
        self.assertEqual(d["menus"], [])
        self.assertEqual(d["sample_days"], 0)

    def test_tomorrow_closed(self):
        saturday = datetime(2026, 10, 17, 15, 0, tzinfo=WIB)     # besok Minggu libur
        d = analytics.menu_tomorrow(self.store, saturday)
        self.assertTrue(d["closed"])
        self.assertEqual(d["menus"], [])

    def test_only_top_five(self):
        c = Category.objects.first()
        extra = [Menu.objects.create(name=f"Menu{i}", price=1000, category=c) for i in range(5)]
        for day in [(10, 8), (10, 1), (9, 24)]:
            self.order(wib(*day), [(m, 1) for m in [self.a, self.b, self.c, *extra]])
        self.assertEqual(len(analytics.menu_tomorrow(self.store, NOW)["menus"]), 5)


class EndpointTests(BriefingBase):
    def test_permissions(self):
        for url in ("/api/orders/briefing/", "/api/orders/analytics/menu-tomorrow/"):
            self.assertIn(APIClient().get(url).status_code, (401, 403))
            self.assertEqual(make_client("kasir").get(url).status_code, 403)

    def test_admin_gets_briefing(self):
        p1, p2, p3 = with_history()
        with p1, p2, p3:
            res = make_client("admin").get("/api/orders/briefing/")
        self.assertEqual(res.status_code, 200)
        for key in ("prediction_today", "crowd", "target", "unpaid", "recommendations", "errors", "data_note"):
            self.assertIn(key, res.json())
        self.assertEqual(res["Cache-Control"], "no-store")

    def test_admin_gets_menu_tomorrow(self):
        res = make_client("owner").get("/api/orders/analytics/menu-tomorrow/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("menus", res.json())

    def test_target_saved_through_settings_endpoint(self):
        admin = make_client("admin")
        res = admin.put("/api/orders/settings/", {"monthly_revenue_target": 25_000_000}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["monthly_revenue_target"], 25_000_000)
        res = admin.put("/api/orders/settings/", {"monthly_revenue_target": 0}, format="json")
        self.assertIsNone(res.json()["monthly_revenue_target"])
        res = admin.put("/api/orders/settings/", {"monthly_revenue_target": -5}, format="json")
        self.assertEqual(res.status_code, 400)
        res = admin.put("/api/orders/settings/", {"monthly_revenue_target": 10**12}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(make_client("kasir").put("/api/orders/settings/", {"monthly_revenue_target": 1}, format="json").status_code, 403)
