"""
Tes ubah tanggal/jam order (PATCH /api/orders/<id>/time/): hanya untuk order yang belum lunas.
Jalankan: python manage.py test order.test_edit_time
"""
from datetime import timedelta

from django.utils import timezone

from order.test_staff_flow import Base


class EditOrderTimeTests(Base):
    def patch(self, order, dt, client=None):
        return (client or self.staff).patch(
            f"/api/orders/{order.pk}/time/",
            {"created_at": dt.isoformat(), "kasir_name": "Wawan"}, format="json",
        )

    def test_unpaid_order_time_can_change_and_is_logged(self):
        o = self.web_order()
        target = timezone.now() - timedelta(days=2, hours=3)
        r = self.patch(o, target)
        self.assertEqual(r.status_code, 200, r.data)
        o.refresh_from_db()
        self.assertEqual(o.created_at.replace(second=0, microsecond=0), target.replace(second=0, microsecond=0))
        self.assertIsNotNone(o.entered_at)   # waktu lampau = input susulan
        self.assertIn(("time_changed", "staff"), self.actions(o))

    def test_paid_order_is_rejected(self):
        o = self.web_order()
        o.payment_status = "paid"
        o.save(update_fields=["payment_status"])
        before = o.created_at
        r = self.patch(o, timezone.now() - timedelta(days=1))
        self.assertEqual(r.status_code, 400)
        o.refresh_from_db()
        self.assertEqual(o.created_at, before)

    def test_cancelled_order_is_rejected(self):
        o = self.web_order()
        o.status = "cancelled"
        o.save(update_fields=["status"])
        self.assertEqual(self.patch(o, timezone.now() - timedelta(days=1)).status_code, 400)

    def test_future_and_too_old_and_garbage_rejected(self):
        o = self.web_order()
        self.assertEqual(self.patch(o, timezone.now() + timedelta(hours=1)).status_code, 400)
        self.assertEqual(self.patch(o, timezone.now() - timedelta(days=400)).status_code, 400)
        r = self.staff.patch(f"/api/orders/{o.pk}/time/", {"created_at": "ngawur"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.staff.patch(f"/api/orders/{o.pk}/time/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_same_minute_is_noop(self):
        o = self.web_order()
        r = self.patch(o, o.created_at)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.actions(o), [])

    def test_requires_staff_login(self):
        from rest_framework.test import APIClient
        o = self.web_order()
        r = self.patch(o, timezone.now() - timedelta(days=1), client=APIClient())
        self.assertIn(r.status_code, (401, 403))
