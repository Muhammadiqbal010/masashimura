"""Tes Ringkasan Order Reports (report_summary.full_report)."""
import datetime

from django.test import TestCase
from django.utils import timezone

from menu.models import Category, Menu
from order.models import Order, OrderItem
from order.report_summary import full_report


class FullReportTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Makanan")
        self.nasi = Menu.objects.create(name="Nasi", price=10000, category=cat, is_active=True)
        Menu.objects.create(name="Sepi", price=7000, is_active=True)
        now = timezone.now()
        for i, days in enumerate([0, 1, 3, 10]):
            o = Order.objects.create(
                payment_status="paid", status="completed", total_price=20000 + i * 1000,
                customer_phone=f"08{i % 2}", payment_method="cash", source="pos",
            )
            Order.objects.filter(pk=o.pk).update(created_at=now - datetime.timedelta(days=days))
            OrderItem.objects.create(order=o, menu=self.nasi, quantity=2, price=10000)
        # Order batal / belum lunas tidak boleh dihitung
        Order.objects.create(payment_status="paid", status="cancelled", total_price=99999)
        Order.objects.create(payment_status="unpaid", status="pending", total_price=88888)

    def test_lifetime_totals_and_filled_trend(self):
        r = full_report({})
        self.assertEqual(r["stats"]["total_transaksi"], 4)
        self.assertEqual(r["stats"]["total_omzet"], 86000.0)
        self.assertEqual(r["stats"]["porsi_terjual"], 8)
        # Tren tidak bolong: 11 hari berurutan (10 hari lalu s/d hari ini)
        self.assertEqual(len(r["trend"]["labels"]), 11)
        self.assertEqual(sum(r["trend"]["transaksi"]), 4)
        self.assertIsNone(r["previous"])
        self.assertIsNone(r["delta"]["omzet"] if r["delta"] else None)

    def test_week_has_previous_period_delta(self):
        r = full_report({"period": "week", "days": 7})
        self.assertEqual(r["stats"]["total_transaksi"], 3)
        self.assertEqual(r["previous"]["transaksi"], 1)
        self.assertEqual(r["delta"]["transaksi"], 200.0)

    def test_year_is_monthly_but_best_day_still_found(self):
        r = full_report({"period": "year"})
        self.assertEqual(r["trend"]["unit"], "month")
        self.assertEqual(len(r["trend"]["labels"]), 12)
        self.assertIsNotNone(r["highlights"]["best_day"])

    def test_category_unsold_and_customers(self):
        r = full_report({})
        self.assertEqual(r["kategori"][0]["name"], "Makanan")
        self.assertEqual(r["menu_tidak_terjual"], 1)
        self.assertEqual(r["pelanggan"]["baru"], 2)
        self.assertEqual(len(r["per_hari"]), 7)
        self.assertTrue(r["jam_distribusi"])

    def test_top_menu_never_has_null_name(self):
        o = Order.objects.create(payment_status="paid", status="completed", total_price=5000)
        OrderItem.objects.create(order=o, menu=None, quantity=1, price=5000)
        r = full_report({})
        self.assertTrue(all(m["name"] for m in r["top_menu"]))
