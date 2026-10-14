"""Tes snapshot prediksi (Prediksi vs Realisasi). Jalankan: python manage.py test prediction.test_snapshots"""
from datetime import date, datetime, time, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from order.models import Order, StoreSettings, WIB
from prediction import snapshots
from prediction.models import RevenuePredictionSnapshot as Snap

TODAY = date(2026, 10, 14)


def item(d, pred, lo=None, hi=None, closed=False, conf="sedang"):
    return {
        "date": d.isoformat(), "predicted_revenue": pred,
        "lower_bound": pred * 0.8 if lo is None else lo,
        "upper_bound": pred * 1.2 if hi is None else hi,
        "confidence": conf, "is_regular_closed_day": closed,
    }


def snap(target, made_on, pred, lo=0, hi=0):
    return Snap.objects.create(target_date=target, made_on=made_on, predicted_revenue=pred,
                               lower_bound=lo, upper_bound=hi, method="baseline", confidence="sedang")


class SaveTests(TestCase):
    def test_saves_open_days_only_and_caps_horizon(self):
        items = [item(TODAY + timedelta(days=i), 100_000, closed=(i == 4)) for i in range(20)]
        n = snapshots.save_forecast(items, method="baseline", made_on=TODAY)
        self.assertEqual(n, 13)       # 14 hari pertama, minus 1 hari libur
        self.assertEqual(Snap.objects.count(), 13)
        self.assertFalse(Snap.objects.filter(target_date=TODAY + timedelta(days=4)).exists())
        self.assertFalse(Snap.objects.filter(target_date__gt=TODAY + timedelta(days=13)).exists())

    def test_same_day_reopen_does_not_duplicate_or_rewrite(self):
        items = [item(TODAY + timedelta(days=i), 100_000) for i in range(1, 4)]
        self.assertEqual(snapshots.save_forecast(items, "baseline", TODAY), 3)
        self.assertEqual(snapshots.save_forecast(items, "baseline", TODAY), 0)    # tidak ada yang berubah
        self.assertEqual(Snap.objects.count(), 3)

    def test_changed_values_overwrite_same_day_row(self):
        snapshots.save_forecast([item(TODAY + timedelta(days=1), 100_000)], "baseline", TODAY)
        n = snapshots.save_forecast([item(TODAY + timedelta(days=1), 150_000)], "random_forest", TODAY)
        self.assertEqual(n, 1)
        row = Snap.objects.get()
        self.assertEqual(row.predicted_revenue, 150_000)
        self.assertEqual(row.method, "random_forest")

    def test_new_day_keeps_history_of_earlier_predictions(self):
        target = TODAY + timedelta(days=2)
        snapshots.save_forecast([item(target, 100_000)], "baseline", TODAY)
        snapshots.save_forecast([item(target, 120_000)], "baseline", TODAY + timedelta(days=1))
        self.assertEqual(Snap.objects.filter(target_date=target).count(), 2)

    def test_dates_before_made_on_ignored(self):
        self.assertEqual(snapshots.save_forecast([item(TODAY - timedelta(days=1), 1)], "baseline", TODAY), 0)

    def test_database_error_never_raises(self):
        with mock.patch("prediction.snapshots.RevenuePredictionSnapshot.objects") as m:
            m.filter.side_effect = DatabaseError("tabel belum ada")
            self.assertEqual(snapshots.save_forecast([item(TODAY, 1)], "baseline", TODAY), 0)


class CompareTests(TestCase):
    def test_picks_latest_snapshot_made_on_or_before_the_day(self):
        target = date(2026, 10, 10)
        snap(target, date(2026, 10, 7), 100_000)
        snap(target, date(2026, 10, 9), 120_000)      # terbaru sebelum hari H -> dipakai
        snap(target, date(2026, 10, 11), 999_999)     # dibuat setelah harinya -> bukan prediksi
        pairs = snapshots.saved_vs_actual({"2026-10-10": 110_000.0}, date(2026, 10, 1), TODAY, today=TODAY)
        self.assertEqual(len(pairs), 1)
        p = pairs[0]
        self.assertEqual(p["predicted_revenue"], 120_000)
        self.assertEqual(p["error"], 10_000)
        self.assertEqual(p["horizon_days"], 1)

    def test_same_day_snapshot_counts(self):
        snap(date(2026, 10, 12), date(2026, 10, 12), 90_000)
        pairs = snapshots.saved_vs_actual({"2026-10-12": 100_000.0}, date(2026, 10, 1), TODAY, today=TODAY)
        self.assertEqual(pairs[0]["horizon_days"], 0)

    def test_today_and_future_excluded_and_missing_actual_skipped(self):
        snap(TODAY, TODAY, 100_000)
        snap(date(2026, 10, 12), date(2026, 10, 11), 100_000)      # tidak ada data omzet pembanding
        snap(date(2026, 10, 13), date(2026, 10, 12), 100_000)
        pairs = snapshots.saved_vs_actual({"2026-10-14": 5.0, "2026-10-13": 80_000.0}, date(2026, 10, 1), TODAY, today=TODAY)
        self.assertEqual([p["date"] for p in pairs], ["2026-10-13"])

    def test_summary_numbers(self):
        pairs = [
            {"error": 20_000, "actual_revenue": 80_000.0, "lower_bound": 70_000, "upper_bound": 130_000},   # 25%, di dalam
            {"error": -10_000, "actual_revenue": 110_000.0, "lower_bound": 90_000, "upper_bound": 105_000},  # ~9.1%, di luar
            {"error": 50_000, "actual_revenue": 0.0, "lower_bound": 60_000, "upper_bound": 140_000},         # omzet 0: di luar MAPE
        ]
        snap(date(2026, 10, 5), date(2026, 10, 4), 1)
        s = snapshots.summarize(pairs)
        self.assertEqual(s["n_days"], 3)
        self.assertEqual(s["mae"], 26_667)
        self.assertEqual(s["mape"], 17.0)           # (25 + 9.09) / 2
        self.assertEqual(s["within_band_pct"], 33)
        self.assertEqual(s["saved_since"], "2026-10-04")

    def test_summary_when_empty(self):
        s = snapshots.summarize([])
        self.assertEqual((s["n_days"], s["mae"], s["mape"], s["within_band_pct"]), (0, None, None, None))

    def test_read_error_returns_empty(self):
        with mock.patch("prediction.snapshots.RevenuePredictionSnapshot.objects") as m:
            m.filter.side_effect = DatabaseError("x")
            self.assertEqual(snapshots.saved_vs_actual({"2026-10-10": 1.0}, date(2026, 10, 1), TODAY, today=TODAY), [])


class ViewTests(TestCase):
    """GET /api/prediction/revenue/ memakai jam asli server, jadi tanggal dibuat relatif terhadap hari ini."""

    def setUp(self):
        store = StoreSettings.get()
        store.operating_hours = {str(d): {"open": "10:00", "close": "22:00"} for d in range(7)}
        store.save()
        self.today = snapshots.today_wib()
        for i in range(1, 22):
            day = self.today - timedelta(days=i)
            Order.objects.create(
                created_at=datetime.combine(day, time(12, 0), tzinfo=WIB),
                status="completed", payment_status="paid", total_price=80_000,
            )
        u = User.objects.create_user("adm", password="x")
        UserProfile.objects.update_or_create(user=u, defaults={"role": "admin"})
        self.client = APIClient()
        self.client.force_authenticate(u)

    def test_opening_prediction_saves_snapshots_and_reports_history(self):
        res = self.client.get("/api/prediction/revenue/?days=7&history_days=30")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(Snap.objects.filter(made_on=self.today).count(), 7)
        self.assertEqual(min(Snap.objects.values_list("target_date", flat=True)), self.today + timedelta(days=1))
        self.assertEqual(data["saved_history"], [])                  # belum ada hari lewat yang punya snapshot
        self.assertEqual(data["saved_accuracy"]["n_days"], 0)

        # Snapshot lama untuk kemarin (dibuat 2 hari lalu) -> sekarang bisa dibandingkan dengan omzet sebenarnya.
        yesterday = self.today - timedelta(days=1)
        snap(yesterday, self.today - timedelta(days=2), 100_000, lo=70_000, hi=130_000)
        data = self.client.get("/api/prediction/revenue/?days=7&history_days=30").json()
        self.assertEqual(len(data["saved_history"]), 1)
        row = data["saved_history"][0]
        self.assertEqual(row["date"], yesterday.isoformat())
        self.assertEqual(row["actual_revenue"], 80_000)
        self.assertEqual(row["error"], 20_000)
        acc = data["saved_accuracy"]
        self.assertEqual((acc["n_days"], acc["mae"], acc["mape"], acc["within_band_pct"]), (1, 20_000, 25.0, 100))
        self.assertEqual(Snap.objects.filter(made_on=self.today).count(), 7)    # tidak dobel

    def test_snapshot_failure_does_not_break_prediction(self):
        with mock.patch("prediction.views.snapshots.save_forecast", side_effect=RuntimeError("boom")):
            res = self.client.get("/api/prediction/revenue/?days=7")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["saved_history"], [])
        self.assertIsNone(res.json()["saved_accuracy"])
        self.assertEqual(len(res.json()["forecast"]), 7)

    def test_existing_response_keys_unchanged(self):
        data = self.client.get("/api/prediction/revenue/?days=7").json()
        for key in ("forecast", "history", "weekly_summary", "trend", "confidence",
                    "total_estimated_revenue", "best_model", "data_range"):
            self.assertIn(key, data)
