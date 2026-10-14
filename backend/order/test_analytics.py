"""Tes analitik menu. Jalankan: python manage.py test order.test_analytics"""
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import analytics
from order.models import Order, OrderItem, WIB

NOW = datetime(2026, 10, 14, 15, 0, tzinfo=WIB)


def wib(d, h=12):
    return datetime(2026, 10, d, h, 0, tzinfo=WIB)


def order(menus, day=10, source="pos", method="cash", status="completed", pay="paid", reward=()):
    o = Order.objects.create(created_at=wib(day), source=source, payment_method=method,
                             status=status, payment_status=pay, total_price=sum(m.price * q for m, q in menus))
    for m, q in menus:
        OrderItem.objects.create(order=o, menu=m, quantity=q, price=m.price)
    for m in reward:
        OrderItem.objects.create(order=o, menu=m, quantity=1, price=0, is_point_redemption=True)
    return o


class Base(TestCase):
    def setUp(self):
        c = Category.objects.create(name="Utama")
        self.katsu = Menu.objects.create(name="Katsu", price=20000, category=c)
        self.teh = Menu.objects.create(name="Es Teh", price=5000, category=c)
        self.ramen = Menu.objects.create(name="Ramen", price=35000, category=c)
        self.mochi = Menu.objects.create(name="Mochi", price=30000, category=c)
        self.off = Menu.objects.create(name="Lama", price=1000, category=c, is_active=False)


class PerformanceTests(Base):
    def test_classes_and_filters(self):
        for _ in range(12):
            order([(self.katsu, 1), (self.teh, 1)])
        for _ in range(8):
            order([(self.ramen, 1)])
        order([(self.mochi, 1)])
        order([(self.katsu, 5)], status="cancelled")     # tidak dihitung
        order([(self.katsu, 5)], pay="unpaid")            # tidak dihitung
        d = analytics.menu_performance({}, NOW)
        by = {m["name"]: m for m in d["menus"]}
        self.assertNotIn("Lama", by)                      # nonaktif tidak ikut
        self.assertEqual(by["Katsu"]["qty"], 12)
        self.assertEqual(by["Katsu"]["revenue"], 240000)
        self.assertEqual(by["Ramen"]["class"], "bintang")   # populer + harga di atas rata-rata
        self.assertEqual(by["Es Teh"]["class"], "andalan")  # populer, harga rendah
        self.assertEqual(by["Mochi"]["class"], "potensial") # jarang, harga tinggi
        self.assertEqual(sum(d["summary"].values()), 4)
        self.assertTrue(d["enough_data"])
        self.assertEqual(d["menus"][0]["name"], "Ramen")    # urut omzet

    def test_period_filter_and_empty(self):
        order([(self.katsu, 1)], day=3)
        d = analytics.menu_performance({"period": "week", "days": "7"}, NOW)   # 8-14 Okt
        self.assertEqual(d["total_qty"], 0)
        self.assertFalse(d["enough_data"])
        d = analytics.menu_performance({"period": "month", "month": "10", "year": "2026"}, NOW)
        self.assertEqual(d["total_qty"], 1)
        self.assertEqual(d["period"]["end"], "2026-10-31")

    def test_bad_params_do_not_crash(self):
        d = analytics.menu_performance({"period": "month", "month": "99", "year": "abc", "days": "x"}, NOW)
        self.assertEqual(d["period"]["start"], "2026-10-01")


class PairTests(Base):
    def test_pairs_lift_and_exclusions(self):
        for _ in range(6):
            order([(self.katsu, 2), (self.teh, 1)])      # qty tidak menggandakan pasangan
        for _ in range(4):
            order([(self.katsu, 1)])
        for _ in range(4):
            order([(self.ramen, 1)])
        order([(self.ramen, 1), (self.mochi, 1)])         # 1x saja, di bawah min_count
        order([(self.katsu, 1)], reward=[self.mochi])     # reward tidak jadi pasangan
        d = analytics.menu_pairs({}, NOW)
        self.assertEqual(d["total_orders"], 16)
        self.assertEqual(d["multi_item_orders"], 7)
        self.assertEqual(len(d["pairs"]), 1)
        p = d["pairs"][0]
        self.assertEqual((p["a"]["name"], p["b"]["name"], p["count"]), ("Katsu", "Es Teh", 6))
        self.assertEqual(p["confidence_b_to_a"], 100.0)   # tiap Es Teh ada Katsu
        self.assertEqual(p["confidence_a_to_b"], 54.5)    # 6 dari 11 order Katsu
        self.assertGreater(p["lift"], 1)
        self.assertTrue(p["bundle_candidate"])
        self.assertFalse(d["enough_data"])   # baru 7 order multi-item

    def test_empty(self):
        d = analytics.menu_pairs({}, NOW)
        self.assertEqual((d["total_orders"], d["pairs"]), (0, []))


class ChannelTests(Base):
    def test_channel_split_and_trend(self):
        for _ in range(3):
            order([(self.katsu, 1)], source="web", method="gateway")
        order([(self.katsu, 2), (self.teh, 2)], source="pos", method="cash", day=11)
        order([(self.ramen, 1)], source="pos", method="qris", day=11)
        d = analytics.channels({"period": "month", "month": "10", "year": "2026"}, NOW)
        ch = {c["source"]: c for c in d["channels"]}
        self.assertEqual(ch["web"]["orders"], 3)
        self.assertEqual(ch["pos"]["orders"], 2)
        self.assertEqual(ch["pos"]["avg_order"], round((50000 + 35000) / 2))
        self.assertEqual(ch["pos"]["items_per_order"], 2.5)
        self.assertEqual(ch["web"]["payment_methods"][0]["method"], "gateway")
        self.assertAlmostEqual(ch["web"]["order_share"] + ch["pos"]["order_share"], 100, places=1)
        self.assertEqual(d["trend"]["unit"], "day")
        self.assertEqual(len(d["trend"]["labels"]), 31)
        self.assertEqual(sum(d["trend"]["series"]["web"]), 60000)

    def test_lifetime_long_range_goes_monthly(self):
        o = order([(self.katsu, 1)])
        Order.objects.filter(pk=o.pk).update(created_at=datetime(2026, 1, 5, 12, tzinfo=WIB))
        order([(self.katsu, 1)])
        d = analytics.channels({}, NOW)
        self.assertEqual(d["trend"]["unit"], "month")
        self.assertEqual(d["trend"]["labels"][0], "Jan 26")
        self.assertEqual(len(d["trend"]["labels"]), 10)


class ApiTests(Base):
    def api(self, role):
        u, _ = User.objects.get_or_create(username=role)
        UserProfile.objects.update_or_create(user=u, defaults={"role": role})
        c = APIClient(); c.force_authenticate(u); return c

    def test_permissions(self):
        for path in ("menu-performance", "menu-pairs", "channels"):
            url = f"/api/orders/analytics/{path}/"
            self.assertIn(APIClient().get(url).status_code, (401, 403))
            self.assertEqual(self.api("kasir").get(url).status_code, 403)
            self.assertEqual(self.api("admin").get(url).status_code, 200)
