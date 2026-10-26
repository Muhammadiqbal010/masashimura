"""Tes QRIS dinamis POS. Jalankan: python manage.py test payments (Midtrans di-mock)."""
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order.models import Order

SNAP_OK = {'token': 'tok-123', 'redirect_url': 'https://x/redirect'}


class PosQrisTests(TestCase):
    def setUp(self):
        u = User.objects.create(username='kasir', is_staff=True)
        UserProfile.objects.update_or_create(user=u, defaults={'role': 'kasir'})
        self.c = APIClient()
        self.c.force_authenticate(u)
        cat = Category.objects.create(name='U')
        self.menu = Menu.objects.create(name='Katsu', price=20000, category=cat)

    def _make_order(self):
        r = self.c.post('/api/orders/', {
            'source': 'pos', 'payment_method': 'gateway', 'kasir_name': 'K',
            'items': [{'menu_id': self.menu.pk, 'quantity': 2}],
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def test_pos_gateway_order_starts_pending(self):
        d = self._make_order()
        self.assertEqual((d['payment_status'], d['status']), ('pending', 'pending'))

    @mock.patch('payments.views.snap')
    def test_create_qr_then_reuse(self, core):
        core.create_transaction.return_value = SNAP_OK
        no = self._make_order()['order_number']
        r = self.c.post(f'/api/payments/pos/{no}/qris/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['snap_token'], 'tok-123')
        self.assertEqual(r.data['total'], 40000)
        self.c.post(f'/api/payments/pos/{no}/qris/')
        self.assertEqual(core.create_transaction.call_count, 1)      # QR yang masih berlaku dipakai ulang

    @mock.patch('payments.views.snap')
    def test_create_qr_failure_shows_midtrans_reason(self, snap):
        snap.create_transaction.side_effect = Exception('Access denied')
        no = self._make_order()['order_number']
        r = self.c.post(f'/api/payments/pos/{no}/qris/')
        self.assertEqual(r.status_code, 502)
        self.assertIn('Access denied', r.data['detail'])

    @mock.patch('payments.views.snap')
    def test_create_qr_uses_snap_other_qris(self, snap):
        snap.create_transaction.return_value = SNAP_OK
        no = self._make_order()['order_number']
        self.c.post(f'/api/payments/pos/{no}/qris/')
        param = snap.create_transaction.call_args[0][0]
        self.assertEqual(param['enabled_payments'], ['other_qris'])
        self.assertEqual(param['transaction_details']['gross_amount'], 40000)

    @mock.patch('payments.views.snap')
    def test_snap_item_details_sum_equals_total(self, core):
        core.create_transaction.return_value = SNAP_OK
        no = self._make_order()['order_number']
        self.c.post(f'/api/payments/pos/{no}/qris/')
        param = core.create_transaction.call_args[0][0]
        total = sum(i['price'] * i['quantity'] for i in param['item_details'])
        self.assertEqual(total, param['transaction_details']['gross_amount'])

    @mock.patch('payments.views.fetch_midtrans_status')
    @mock.patch('payments.views.snap')
    def test_status_marks_paid_on_settlement(self, core, status):
        core.create_transaction.return_value = SNAP_OK
        no = self._make_order()['order_number']
        self.c.post(f'/api/payments/pos/{no}/qris/')
        status.return_value = {'transaction_status': 'settlement', 'gross_amount': '40000.00'}
        r = self.c.get(f'/api/payments/pos/{no}/status/')
        self.assertEqual(r.data['payment_status'], 'paid')
        o = Order.objects.get(order_number=no)
        self.assertEqual((o.status, int(o.amount_paid)), ('completed', 40000))
        self.assertEqual(o.payments.count(), 1)
        self.c.get(f'/api/payments/pos/{no}/status/')    # polling berulang tidak mencatat bayar dobel
        self.assertEqual(o.payments.count(), 1)

    @mock.patch('payments.views.fetch_midtrans_status')
    @mock.patch('payments.views.snap')
    def test_cancel_deletes_unpaid_but_refuses_if_paid(self, core, status):
        core.create_transaction.return_value = SNAP_OK
        no = self._make_order()['order_number']
        self.c.post(f'/api/payments/pos/{no}/qris/')
        status.return_value = {'transaction_status': 'pending'}
        with mock.patch('payments.services.core'):
            r = self.c.post(f'/api/payments/pos/{no}/cancel/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Order.objects.filter(order_number=no).exists())

        no2 = self._make_order()['order_number']
        self.c.post(f'/api/payments/pos/{no2}/qris/')
        status.return_value = {'transaction_status': 'settlement', 'gross_amount': '40000'}
        r = self.c.post(f'/api/payments/pos/{no2}/cancel/')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Order.objects.get(order_number=no2).payment_status, 'paid')

    def test_web_cannot_use_pos_endpoints(self):
        self.c.force_authenticate(None)
        r = self.c.post('/api/payments/pos/ANY/qris/')
        self.assertIn(r.status_code, (401, 403))


class PosQrisBillTests(TestCase):
    """Nota "bayar nanti" (makan dulu / bungkus bayar setelah jadi) dilunasi lewat QRIS."""

    def setUp(self):
        u = User.objects.create(username='kasir2', is_staff=True)
        UserProfile.objects.update_or_create(user=u, defaults={'role': 'kasir'})
        self.c = APIClient()
        self.c.force_authenticate(u)
        cat = Category.objects.create(name='U')
        self.menu = Menu.objects.create(name='Katsu', price=20000, category=cat)

    def _bill(self, service_type='dine_in'):
        r = self.c.post('/api/orders/', {
            'source': 'pos', 'payment_method': 'cash', 'payment_status': 'pending',
            'service_type': service_type, 'kasir_name': 'K',
            'items': [{'menu_id': self.menu.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['payment_status'], 'unpaid')
        return r.data

    @mock.patch('payments.views.snap')
    def test_takeaway_bill_can_get_qr_and_blocks_edits(self, core):
        core.create_transaction.return_value = SNAP_OK
        d = self._bill('takeaway')
        r = self.c.post(f"/api/payments/pos/{d['order_number']}/qris/")
        self.assertEqual((r.status_code, r.data['mode']), (200, 'bill'))
        self.assertEqual(core.create_transaction.call_args[0][0]['transaction_details']['order_id'], f"{d['order_number']}-Q1")
        # selama QR hidup: tidak boleh ubah item / lunasi cara lain
        r = self.c.post(f"/api/orders/{d['id']}/items/", {'menu_id': self.menu.pk, 'quantity': 1}, format='json')
        self.assertEqual(r.status_code, 409)
        r = self.c.patch(f"/api/orders/{d['id']}/pay/", {'payment_method': 'cash', 'amount_paid': 20000}, format='json')
        self.assertEqual(r.status_code, 409)

    @mock.patch('payments.views.fetch_midtrans_status')
    @mock.patch('payments.views.snap')
    def test_bill_cancel_keeps_order_and_settlement_pays_it(self, core, status):
        core.create_transaction.return_value = SNAP_OK
        d = self._bill()
        no = d['order_number']
        self.c.post(f'/api/payments/pos/{no}/qris/')
        status.return_value = {'transaction_status': 'pending'}
        r = self.c.post(f'/api/payments/pos/{no}/cancel/')
        self.assertEqual(r.status_code, 200)
        o = Order.objects.get(order_number=no)
        self.assertEqual(o.payment_status, 'unpaid')          # nota tetap ada
        self.assertEqual(o.midtrans_qr_url, '')
        # QR baru → ID transaksi baru (-Q2), lalu dibayar
        self.c.post(f'/api/payments/pos/{no}/qris/')
        self.assertEqual(core.create_transaction.call_args[0][0]['transaction_details']['order_id'], f'{no}-Q2')
        status.return_value = {'transaction_status': 'settlement', 'gross_amount': '20000'}
        r = self.c.get(f'/api/payments/pos/{no}/status/')
        self.assertEqual(r.data['payment_status'], 'paid')
        o.refresh_from_db()
        self.assertEqual((o.payment_method, o.status), ('gateway', 'completed'))
