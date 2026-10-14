"""Tes segmentasi, efektivitas promo/poin, dan hapus member. Jalankan: python manage.py test order.test_loyalty_tools"""
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import effectiveness, segmentation
from order.models import (
    CustomerLoyalty, Order, OrderItem, PointAdjustment, PointReward, WIB,
)
from promotions.models import Promo

NOW = datetime(2026, 10, 14, 15, 0, tzinfo=WIB)


def ago(days):
    return NOW - timedelta(days=days)


def member(phone, orders, last_days):
    return CustomerLoyalty.objects.create(
        phone=phone, name=phone, total_orders=orders,
        last_order_at=None if last_days is None else ago(last_days),
    )


def api(role):
    u, _ = User.objects.get_or_create(username=role)
    UserProfile.objects.update_or_create(user=u, defaults={"role": role})
    c = APIClient()
    c.force_authenticate(u)
    return c


class SegmentationTests(TestCase):
    def test_rules(self):
        cases = [
            ((6, 3), "setia"), ((6, 31), "tidur"), ((3, 10), "aktif"),
            ((1, 5), "baru"), ((0, 0), "baru"), ((3, 45), "berisiko"),
            ((2, 60), "berisiko"), ((2, 61), "tidur"), ((1, 45), "tidur"),
        ]
        for (orders, days), want in cases:
            got, _ = segmentation.classify(orders, ago(days), NOW)
            self.assertEqual(got, want, (orders, days))
        self.assertEqual(segmentation.classify(0, None, NOW), ("baru", None))

    def test_overview_and_at_risk(self):
        member("0811", 4, 40)
        member("0812", 2, 50)
        member("0813", 8, 2)
        assigned, summary = segmentation.segment_overview(CustomerLoyalty.objects.all(), NOW)
        counts = {s["key"]: s["count"] for s in summary}
        self.assertEqual(counts["berisiko"], 2)
        self.assertEqual(counts["setia"], 1)
        self.assertEqual(len(summary), 5)
        self.assertEqual(assigned["0813"][0], "setia")


class DeleteTests(TestCase):
    def setUp(self):
        self.cl = member("0811", 3, 5)
        PointAdjustment.objects.create(customer=self.cl, amount=5, note="x")
        member("0812", 1, 1)

    def test_single_delete_cascades_adjustments(self):
        r = api("admin").delete("/api/orders/loyal-customers/0811/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {"deleted": 1, "adjustments_deleted": 1})
        self.assertFalse(CustomerLoyalty.objects.filter(phone="0811").exists())
        self.assertEqual(PointAdjustment.objects.count(), 0)
        self.assertEqual(api("admin").delete("/api/orders/loyal-customers/0811/").status_code, 404)

    def test_keeps_orders(self):
        o = Order.objects.create(customer_phone="0811", status="completed", payment_status="paid", total_price=1000)
        api("admin").delete("/api/orders/loyal-customers/0811/")
        self.assertTrue(Order.objects.filter(pk=o.pk).exists())

    def test_bulk_requires_confirm(self):
        url = "/api/orders/loyal-customers/bulk-delete/"
        c = api("admin")
        self.assertEqual(c.post(url, {"phones": ["0811"]}, format="json").status_code, 400)
        self.assertEqual(CustomerLoyalty.objects.count(), 2)
        r = c.post(url, {"phones": ["0811"], "confirm": "HAPUS"}, format="json")
        self.assertEqual(r.data["deleted"], 1)
        r = c.post(url, {"all": True, "confirm": "HAPUS"}, format="json")
        self.assertEqual(r.data["deleted"], 1)
        self.assertEqual(CustomerLoyalty.objects.count(), 0)

    def test_bulk_empty_list_rejected(self):
        r = api("admin").post("/api/orders/loyal-customers/bulk-delete/", {"phones": [], "confirm": "HAPUS"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_kasir_forbidden(self):
        self.assertEqual(api("kasir").delete("/api/orders/loyal-customers/0811/").status_code, 403)
        r = api("kasir").post("/api/orders/loyal-customers/bulk-delete/", {"all": True, "confirm": "HAPUS"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_list_has_segments(self):
        r = api("admin").get("/api/orders/loyal-customers/")
        self.assertEqual(len(r.data["segments"]), 5)
        self.assertIn("segment", r.data["customers"][0])


class EffectivenessTests(TestCase):
    def setUp(self):
        c = Category.objects.create(name="Utama")
        self.katsu = Menu.objects.create(name="Katsu", price=20000, category=c)
        self.promo = Promo.objects.create(
            code="HEMAT", discount_type="fixed", discount_value=2000,
            valid_from=ago(30), valid_until=NOW + timedelta(days=30),
        )
        Promo.objects.create(
            code="SEPI", discount_type="fixed", discount_value=1000,
            valid_from=ago(30), valid_until=NOW + timedelta(days=30),
        )

    def mk(self, subtotal, promo=None, disc=0, days=1, **kw):
        return Order.objects.create(
            created_at=ago(days), status="completed", payment_status="paid",
            subtotal=subtotal, total_price=subtotal - disc, promo=promo,
            promo_discount_amount=disc, **kw,
        )

    def test_promo_comparison(self):
        for _ in range(5):
            self.mk(40000, self.promo, 2000)
            self.mk(30000)
        d = effectiveness.promo_effectiveness({}, NOW)
        self.assertTrue(d["enough_data"])
        self.assertEqual(d["totals"]["orders_with_promo"], 5)
        self.assertEqual(d["totals"]["discount_total"], 10000)
        self.assertEqual(d["comparison"]["avg_basket_with"], 40000)
        self.assertEqual(d["comparison"]["basket_diff_pct"], 33.3)
        by = {p["code"]: p for p in d["promos"]}
        self.assertEqual(by["HEMAT"]["orders"], 5)
        self.assertEqual(by["SEPI"]["orders"], 0)     # promo aktif tanpa pemakaian tetap tampil

    def test_not_enough_data(self):
        self.mk(40000, self.promo, 2000)
        d = effectiveness.promo_effectiveness({}, NOW)
        self.assertFalse(d["enough_data"])
        self.assertIsNone(d["comparison"]["basket_diff_pct"])

    def test_points(self):
        PointReward.objects.create(menu=self.katsu, point_cost=10)
        o = self.mk(50000, loyalty_applied=True, loyalty_points_earned=5)
        o2 = self.mk(0, loyalty_applied=True, loyalty_points_earned=0)
        OrderItem.objects.create(order=o2, menu=self.katsu, quantity=1, price=0, is_point_redemption=True)
        cl = member("0811", 2, 1)
        PointAdjustment.objects.create(customer=cl, amount=-10, note=f"Redeem reward saat order {o2.order_number}")
        PointAdjustment.objects.create(customer=cl, amount=-3, reason="expired")
        PointAdjustment.objects.create(customer=cl, amount=4, note="bonus")
        d = effectiveness.point_effectiveness({}, NOW)
        p = d["points"]
        self.assertEqual((p["issued"], p["redeemed"], p["expired"]), (5, 10, 3))
        self.assertEqual((p["manual_added"], p["manual_removed"]), (4, 0))
        self.assertEqual(p["redeem_rate_pct"], 200.0)
        self.assertEqual(d["top_rewards"][0]["name"], "Katsu")
        self.assertEqual(d["top_rewards"][0]["points_estimate"], 10)
        self.assertEqual(d["redemption_orders"], 1)

    def test_endpoints_permissions(self):
        for name in ("promo-effectiveness", "point-effectiveness"):
            url = f"/api/orders/analytics/{name}/"
            self.assertEqual(api("kasir").get(url).status_code, 403)
            self.assertEqual(api("admin").get(url).status_code, 200)
