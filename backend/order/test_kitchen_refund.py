"""Tes siap diambil, tambah menu, menu habis & refund. Jalankan: python manage.py test order.test_kitchen_refund"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order.models import CustomerLoyalty, Order, OrderItem, OrderPayment


class KitchenRefundTests(TestCase):
    def setUp(self):
        u = User.objects.create(username='kasir', is_staff=True)
        UserProfile.objects.update_or_create(user=u, defaults={'role': 'kasir'})
        self.c = APIClient()
        self.c.force_authenticate(u)
        cat = Category.objects.create(name='U')
        self.katsu = Menu.objects.create(name='Katsu', price=20000, category=cat)
        self.teh = Menu.objects.create(name='Teh', price=5000, category=cat)

    def _order(self, paid, method='cash'):
        o = Order.objects.create(
            source='pos', customer_phone='0811', customer_name='A',
            payment_method=method, payment_status='paid' if paid else 'unpaid',
        )
        self.i_katsu = OrderItem.objects.create(order=o, menu=self.katsu, quantity=2, price=20000)
        self.i_teh = OrderItem.objects.create(order=o, menu=self.teh, quantity=1, price=5000)
        o.recalculate_totals()
        if paid:
            OrderPayment.objects.create(order=o, method=method, amount=o.total_price)
            o.amount_paid = o.total_price
            o.status = 'completed'
            o.save()
        o.refresh_from_db()
        return o

    # ── siap diambil ──
    def test_ready_toggle(self):
        o = self._order(paid=False)
        r = self.c.patch(f'/api/orders/{o.pk}/ready/', {'ready': True}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['is_ready'])
        r = self.c.patch(f'/api/orders/{o.pk}/ready/', {'ready': False}, format='json')
        self.assertFalse(r.data['is_ready'])

    def test_ready_rejected_for_cancelled(self):
        o = self._order(paid=False)
        Order.objects.filter(pk=o.pk).update(status='cancelled', payment_status='void')
        r = self.c.patch(f'/api/orders/{o.pk}/ready/', {'ready': True}, format='json')
        self.assertEqual(r.status_code, 400)

    # ── tambah menu ──
    def test_add_item_marks_addition_and_clears_ready(self):
        o = self._order(paid=False)
        Order.objects.filter(pk=o.pk).update(ready_at='2026-10-23T10:00:00+07:00')
        r = self.c.post(f'/api/orders/{o.pk}/items/', {'menu_id': self.teh.pk, 'quantity': 2}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['has_additions'])
        self.assertFalse(r.data['is_ready'])
        teh = OrderItem.objects.get(order=o, menu=self.teh)
        self.assertEqual((teh.quantity, teh.added_qty), (3, 2))
        self.assertIsNotNone(teh.added_at)

    # ── menu habis: belum dibayar ──
    def test_unavailable_unpaid_reduces_total_without_refund(self):
        o = self._order(paid=False)          # 2x20000 + 5000 = 45000
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/',
                        {'items': [{'item_id': self.i_katsu.pk, 'quantity': 1}], 'kasir_name': 'K'}, format='json')
        self.assertEqual(r.status_code, 200)
        s = r.data['summary']
        self.assertEqual((s['old_total'], s['new_total'], s['refund_due'], s['amount_to_pay_now']),
                         (45000, 25000, 0, 25000))
        o.refresh_from_db()
        self.assertEqual(int(o.total_price), 25000)
        self.assertEqual(o.refund_due, 0)
        self.assertEqual(o.unavailable_items[0]['name'], 'Katsu')

    # ── menu habis: sudah lunas (QRIS) ──
    def test_unavailable_paid_creates_pending_refund(self):
        o = self._order(paid=True, method='qris')
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/',
                        {'items': [{'item_id': self.i_teh.pk}], 'kasir_name': 'K'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['summary']['refund_due'], 5000)
        self.assertTrue(r.data['order']['refund_pending'])
        self.assertEqual(r.data['order']['amount_to_pay_now'], 0)
        # refund diserahkan saat pesanan diambil
        r = self.c.patch(f'/api/orders/{o.pk}/refund/', {'kasir_name': 'K'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data['refund_pending'])
        r = self.c.patch(f'/api/orders/{o.pk}/refund/', {'kasir_name': 'K'}, format='json')
        self.assertEqual(r.status_code, 400)          # tidak bisa dobel
        r = self.c.patch(f'/api/orders/{o.pk}/refund/', {'undo': True}, format='json')
        self.assertTrue(r.data['refund_pending'])

    def test_second_unavailable_after_refund_given_starts_new_debt(self):
        o = self._order(paid=True, method='qris')
        self.c.post(f'/api/orders/{o.pk}/unavailable/', {'items': [{'item_id': self.i_teh.pk}]}, format='json')
        self.c.patch(f'/api/orders/{o.pk}/refund/', {'kasir_name': 'K'}, format='json')
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/',
                        {'items': [{'item_id': self.i_katsu.pk, 'quantity': 1}]}, format='json')
        self.assertEqual(r.data['summary']['refund_due'], 20000)
        self.assertTrue(r.data['order']['refund_pending'])

    def test_unavailable_paid_shrinks_loyalty(self):
        CustomerLoyalty.objects.create(phone='0811', name='A', points=0)
        o = self._order(paid=True, method='cash')       # 45000 → 4 poin (Rp10.000/poin)
        o.refresh_from_db()
        self.assertEqual(o.loyalty_points_earned, 4)
        self.c.post(f'/api/orders/{o.pk}/unavailable/',
                    {'items': [{'item_id': self.i_katsu.pk}]}, format='json')   # total 5000 → 0 poin
        o.refresh_from_db()
        loy = CustomerLoyalty.objects.get(phone='0811')
        self.assertEqual((loy.points, o.loyalty_points_earned), (0, 0))
        self.assertEqual(int(loy.total_spent), 5000)

    # ── guard ──
    def test_all_items_unavailable_unpaid_cancels_order(self):
        o = self._order(paid=False)
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/', {'items': [
            {'item_id': self.i_katsu.pk}, {'item_id': self.i_teh.pk}]}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['summary']['cancelled'])
        o.refresh_from_db()
        self.assertEqual((o.status, o.payment_status, o.cancel_reason), ('cancelled', 'void', 'out_of_stock'))

    def test_all_items_unavailable_paid_is_refused(self):
        o = self._order(paid=True)
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/', {'items': [
            {'item_id': self.i_katsu.pk}, {'item_id': self.i_teh.pk}]}, format='json')
        self.assertEqual(r.status_code, 400)
        o.refresh_from_db()
        self.assertEqual(o.items.count(), 2)

    def test_point_redemption_item_cannot_be_marked(self):
        o = self._order(paid=False)
        free = OrderItem.objects.create(order=o, menu=self.katsu, quantity=1, price=0, is_point_redemption=True)
        r = self.c.post(f'/api/orders/{o.pk}/unavailable/', {'items': [{'item_id': free.pk}]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_affected_by_menu_and_pending_refunds(self):
        o = self._order(paid=True, method='qris')
        r = self.c.get(f'/api/orders/affected-by-menu/{self.teh.pk}/')
        self.assertEqual([x['id'] for x in r.data], [o.pk])
        self.c.post(f'/api/orders/{o.pk}/unavailable/', {'items': [{'item_id': self.i_teh.pk}]}, format='json')
        r = self.c.get('/api/orders/pending-refunds/')
        self.assertEqual([x['id'] for x in r.data], [o.pk])

    def test_split_keeps_added_markers(self):
        o = self._order(paid=False)
        self.c.post(f'/api/orders/{o.pk}/items/', {'menu_id': self.teh.pk, 'quantity': 2}, format='json')
        teh = OrderItem.objects.get(order=o, menu=self.teh)   # qty 3, added 2
        r = self.c.post(f'/api/orders/{o.pk}/split/',
                        {'items': [{'item_id': teh.pk, 'quantity': 2}]}, format='json')
        self.assertEqual(r.status_code, 200)
        new_item = r.data['new_order']['items'][0]
        self.assertEqual(new_item['added_qty'], 2)
        teh.refresh_from_db()
        self.assertEqual((teh.quantity, teh.added_qty), (1, 0))
