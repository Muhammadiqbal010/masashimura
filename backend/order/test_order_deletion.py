"""Tes hapus permanen order. Jalankan: python manage.py test order.test_order_deletion"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import UserProfile
from menu.models import Category, Menu
from order.models import (Order, OrderItem, OrderPayment, CustomerLoyalty, PointAdjustment,
                          PointReward, OrderDeletionLog)

class OrderDeletionTests(TestCase):
    def setUp(self):
        u = User.objects.create(username='own', is_staff=True)
        UserProfile.objects.update_or_create(user=u, defaults={'role': 'owner'})
        self.c = APIClient(); self.c.force_authenticate(u)
        cat = Category.objects.create(name='U')
        self.katsu = Menu.objects.create(name='Katsu', price=20000, category=cat)
        PointReward.objects.create(menu=self.katsu, point_cost=7)

    def test_delete_refunds_spent_and_reverts_earned(self):
        CustomerLoyalty.objects.create(phone='0811', name='A', points=20)
        # order dengan tukar poin 7 poin (seperti create_order)
        o = Order.objects.create(source='pos', customer_phone='0811', customer_name='A',
                                 payment_method='cash', payment_status='paid')
        OrderItem.objects.create(order=o, menu=self.katsu, quantity=2, price=50000, bundle_name='Paket X')
        OrderItem.objects.create(order=o, menu=self.katsu, quantity=1, price=0, is_point_redemption=True)
        l = CustomerLoyalty.objects.get(phone='0811'); l.points -= 7; l.save()
        PointAdjustment.objects.create(customer=l, amount=-7, reason='manual',
                                       note=f'Redeem reward saat order {o.order_number}', admin_name='k')
        OrderPayment.objects.create(order=o, method='cash', amount=100000)
        o.recalculate_totals(); o.status = 'completed'; o.amount_paid = 100000; o.save()  # signal earn 10 poin
        l.refresh_from_db(); o.refresh_from_db()
        # saldo awal 20, dipakai 7 buat reward, dapat 10 dari belanja Rp100.000
        self.assertEqual((l.points, o.loyalty_points_earned), (20 - 7 + 10, 10))
        from order.views import _delete_order_permanently
        res = _delete_order_permanently(o, deleted_by='own')
        l.refresh_from_db()
        self.assertEqual(l.points, 20)             # balik persis ke saldo awal
        self.assertEqual(l.total_orders, 0); self.assertEqual(l.total_spent, 0)
        self.assertEqual((res['points_refunded'], res['points_reverted']), (7, 10))
        self.assertFalse(Order.objects.filter(pk=o.pk).exists())
        self.assertFalse(OrderItem.objects.filter(order_id=o.pk).exists())
        self.assertFalse(OrderPayment.objects.filter(order_id=o.pk).exists())
        log = OrderDeletionLog.objects.get(order_number=o.order_number)
        self.assertEqual(log.loyalty_points_refunded, 7)
        # jejak audit minimal: tanpa data pelanggan / isi nota
        self.assertEqual((log.customer_name, log.customer_phone, log.items_snapshot, log.payments_snapshot), ('', '', [], []))
        # tidak ada catatan poin tersisa untuk order ini (tidak ada redeem lama, tidak ada reversal baru)
        self.assertFalse(PointAdjustment.objects.filter(customer=l, note__contains=o.order_number).exists())

    def test_delete_removes_customer_created_only_by_order(self):
        o = Order.objects.create(source='web', customer_phone='0899', customer_name='Baru',
                                 payment_method='cash', payment_status='paid')
        OrderItem.objects.create(order=o, menu=self.katsu, quantity=1, price=100000)
        OrderPayment.objects.create(order=o, method='cash', amount=100000)
        o.recalculate_totals(); o.status = 'completed'; o.amount_paid = 100000; o.save()
        self.assertTrue(CustomerLoyalty.objects.filter(phone='0899').exists())
        from order.views import _delete_order_permanently
        _delete_order_permanently(o)
        self.assertFalse(CustomerLoyalty.objects.filter(phone='0899').exists())

    def test_delete_clears_blocklist_order_reference(self):
        from order.models import BlockedContact
        o = Order.objects.create(source='web', payment_method='cash', payment_status='pending')
        BlockedContact.objects.create(kind='phone', value='0877', order_number=o.order_number)
        from order.views import _delete_order_permanently
        _delete_order_permanently(o)
        b = BlockedContact.objects.get(value='0877')
        self.assertEqual(b.order_number, '')

    def test_delete_without_loyalty_is_clean(self):
        o = Order.objects.create(source='pos', payment_method='cash', payment_status='pending')
        OrderItem.objects.create(order=o, menu=self.katsu, quantity=1, price=20000)
        from order.views import _delete_order_permanently
        res = _delete_order_permanently(o)
        self.assertEqual((res['points_refunded'], res['points_reverted']), (0, 0))

    def test_delete_endpoint_owner_only_and_reports_refund(self):
        CustomerLoyalty.objects.create(phone='0822', name='B', points=10)
        o = Order.objects.create(source='pos', customer_phone='0822', payment_method='cash', payment_status='pending')
        OrderItem.objects.create(order=o, menu=self.katsu, quantity=1, price=0, is_point_redemption=True)
        l = CustomerLoyalty.objects.get(phone='0822'); l.points -= 7; l.save()
        PointAdjustment.objects.create(customer=l, amount=-7, reason='manual',
                                       note=f'Redeem reward saat order {o.order_number}', admin_name='k')
        # kasir tidak boleh
        k = User.objects.create(username='ks', is_staff=True)
        UserProfile.objects.update_or_create(user=k, defaults={'role': 'kasir'})
        kc = APIClient(); kc.force_authenticate(k)
        self.assertEqual(kc.delete(f'/api/orders/{o.pk}/').status_code, 403)
        self.assertTrue(Order.objects.filter(pk=o.pk).exists())
        # owner boleh, poin balik
        r = self.c.delete(f'/api/orders/{o.pk}/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['points_refunded'], 7)
        self.assertIn('7 poin tukar reward dikembalikan', r.data['detail'])
        l.refresh_from_db()
        self.assertEqual(l.points, 10)