"""Tes pengaman order web. Jalankan: python manage.py test order.test_guards"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import guards
from order.models import Order


class NormalizePhoneTests(SimpleTestCase):
    def test_variants_become_08(self):
        for raw in ("+62 812-3456-7890", "6281234567890", "81234567890", "0812 3456 7890", "081234567890"):
            self.assertEqual(guards.normalize_phone(raw), "081234567890", raw)

    def test_empty_stays_empty(self):
        self.assertEqual(guards.normalize_phone(""), "")
        self.assertEqual(guards.normalize_phone(None), "")


class WebOrderGuardTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="U")
        self.menu = Menu.objects.create(name="Katsu", price=20000, category=cat)
        self.web = APIClient()
        u = User.objects.create(username="kasir", is_staff=True)
        UserProfile.objects.update_or_create(user=u, defaults={"role": "kasir"})
        self.staff = APIClient()
        self.staff.force_authenticate(u)

    def _web_order(self, qty, method="cash", phone="+62 812-3456-7890"):
        return self.web.post("/api/orders/", {
            "source": "web", "payment_method": method,
            "customer": {"name": "Budi Santoso", "phone": phone},
            "items": [{"menu_id": self.menu.pk, "quantity": qty}],
        }, format="json")

    def test_small_cash_order_awaits_confirmation_and_phone_is_normalized(self):
        r = self._web_order(2)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["awaiting_confirmation"])
        self.assertEqual(r.data["customer_phone"], "081234567890")

    def test_more_than_10_per_item_rejected(self):
        self.assertEqual(self._web_order(11, method="gateway").status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_big_cash_order_rejected_but_online_allowed(self):
        self.assertEqual(self._web_order(8).status_code, 400)          # > Rp150.000
        self.assertEqual(self._web_order(8, method="gateway").status_code, 201)

    def test_staff_can_accept_and_double_accept_is_safe(self):
        no = self._web_order(2).data["id"]
        for _ in range(2):
            r = self.staff.patch(f"/api/orders/{no}/accept/")
            self.assertEqual(r.status_code, 200, r.data)
            self.assertFalse(r.data["awaiting_confirmation"])

    def test_unaccepted_order_is_cancelled_after_timeout(self):
        o = Order.objects.get(pk=self._web_order(2).data["id"])
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(minutes=16))
        self.assertEqual(guards.expire_unconfirmed_orders(), 1)
        o.refresh_from_db()
        self.assertEqual((o.status, o.payment_status, o.cancelled_by), ("cancelled", "void", "sistem"))

    def test_accepted_order_is_not_cancelled(self):
        oid = self._web_order(2).data["id"]
        self.staff.patch(f"/api/orders/{oid}/accept/")
        Order.objects.filter(pk=oid).update(created_at=timezone.now() - timedelta(minutes=60))
        self.assertEqual(guards.expire_unconfirmed_orders(), 0)

    def test_pos_orders_are_never_auto_cancelled(self):
        r = self.staff.post("/api/orders/", {
            "source": "pos", "payment_method": "cash", "payment_status": "pending", "kasir_name": "K",
            "items": [{"menu_id": self.menu.pk, "quantity": 20}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        Order.objects.filter(pk=r.data["id"]).update(created_at=timezone.now() - timedelta(hours=3))
        self.assertEqual(guards.expire_unconfirmed_orders(), 0)
