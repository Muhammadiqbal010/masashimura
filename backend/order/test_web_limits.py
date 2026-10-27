"""Tes batas order web. Jalankan: python manage.py test order.test_web_limits"""
from django.test import TestCase
from rest_framework.test import APIClient
from menu.models import Category, Menu
from order.models import Order


class WebOrderLimitTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        cat = Category.objects.create(name='U')
        self.a = Menu.objects.create(name='Dimsum A', price=18500, category=cat)
        self.b = Menu.objects.create(name='Dimsum B', price=12500, category=cat)

    def post(self, items, method='cash', phone='081234567890'):
        return self.c.post('/api/orders/', {
            'source': 'web', 'payment_method': method,
            'customer': {'name': 'Budi Santoso', 'phone': phone},
            'items': items,
        }, format='json')

    def test_qty_per_item_over_10_rejected(self):
        r = self.post([{'menu_id': self.a.id, 'quantity': 11}])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_same_menu_split_across_lines_still_counts(self):
        r = self.post([{'menu_id': self.a.id, 'quantity': 6}, {'menu_id': self.a.id, 'quantity': 6}])
        self.assertEqual(r.status_code, 400)

    def test_total_portions_over_30_rejected(self):
        cat = Category.objects.first()
        ms = [Menu.objects.create(name=f'M{i}', price=1000, category=cat) for i in range(4)]
        r = self.post([{'menu_id': m.id, 'quantity': 8} for m in ms], method='gateway')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_cash_over_150k_rejected_and_rolled_back(self):
        r = self.post([{'menu_id': self.a.id, 'quantity': 9}])   # ~Rp 170rb dgn markup web
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_big_order_ok_with_qris(self):
        r = self.post([{'menu_id': self.a.id, 'quantity': 9}], method='gateway')
        self.assertEqual(r.status_code, 201)

    def test_small_cash_ok(self):
        r = self.post([{'menu_id': self.a.id, 'quantity': 2}])
        self.assertEqual(r.status_code, 201)

    def test_pending_cash_per_phone_capped(self):
        for _ in range(2):
            self.assertEqual(self.post([{'menu_id': self.b.id, 'quantity': 1}]).status_code, 201)
        self.assertEqual(self.post([{'menu_id': self.b.id, 'quantity': 1}]).status_code, 429)
