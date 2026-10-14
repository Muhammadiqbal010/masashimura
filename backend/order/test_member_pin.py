"""Tes PIN member. Jalankan: python manage.py test order.test_member_pin"""
from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu
from order import member_pin
from order.models import CustomerLoyalty, Order, PointReward

PHONE = "081200000001"


def client(role=None, is_staff=False):
    c = APIClient()
    if role:
        u, _ = User.objects.get_or_create(username=role, defaults={"is_staff": is_staff})
        if is_staff and not u.is_staff:
            u.is_staff = True
            u.save()
        UserProfile.objects.update_or_create(user=u, defaults={"role": role})
        c.force_authenticate(u)
    return c


class Base(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Utama")
        self.menu = Menu.objects.create(name="Katsu", price=20000, category=cat)
        self.free = Menu.objects.create(name="Mochi", price=7000, category=cat)
        PointReward.objects.create(menu=self.free, point_cost=10)
        self.member = CustomerLoyalty.objects.create(phone=PHONE, name="Budi", points=25, total_orders=3,
                                                     last_order_at=timezone.now())

    def set_pin(self, pin="1234"):
        r = client("admin").post(f"/api/orders/loyal-customers/{PHONE}/pin/", {"pin": pin}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        return r

    def verify(self, pin, phone=PHONE):
        return APIClient().post("/api/orders/member/verify/", {"phone": phone, "pin": pin}, format="json")


class AdminPinTests(Base):
    def test_generate_and_store_only_hash(self):
        r = client("admin").post(f"/api/orders/loyal-customers/{PHONE}/pin/", {}, format="json")
        pin = r.data["pin"]
        self.assertTrue(member_pin.is_valid_format(pin))
        self.assertFalse(r.data["had_pin"])
        self.member.refresh_from_db()
        self.assertNotIn(pin, self.member.pin_hash)
        self.assertTrue(check_password(pin, self.member.pin_hash))
        self.assertIsNotNone(self.member.pin_set_at)

    def test_custom_pin_and_validation(self):
        self.set_pin("4321")
        self.assertTrue(self.set_pin("1111").data["had_pin"])
        for bad in ("12", "12345", "abcd", "12 4"):
            r = client("admin").post(f"/api/orders/loyal-customers/{PHONE}/pin/", {"pin": bad}, format="json")
            self.assertEqual(r.status_code, 400, bad)

    def test_permissions_and_unknown(self):
        url = f"/api/orders/loyal-customers/{PHONE}/pin/"
        self.assertEqual(client("kasir").post(url, {}, format="json").status_code, 403)
        self.assertEqual(client().post(url, {}, format="json").status_code, 403)
        self.assertEqual(client("admin").post("/api/orders/loyal-customers/0899/pin/", {}, format="json").status_code, 404)

    def test_list_shows_pin_status_and_expiry_detail(self):
        r = client("admin").get("/api/orders/loyal-customers/")
        row = r.data["customers"][0]
        self.assertFalse(row["has_pin"])
        self.assertIn("expiry_state", row)
        self.set_pin()
        row = client("admin").get("/api/orders/loyal-customers/").data["customers"][0]
        self.assertTrue(row["has_pin"])
        self.assertIsNotNone(row["pin_set_at"])
        self.assertFalse(row["pin_locked"])

    def test_expiry_states(self):
        from order.models import LoyaltySettings
        s = LoyaltySettings.get_settings()
        s.points_expiry_months = 3
        s.save()
        self.member.last_order_at = timezone.now() - timedelta(days=80)   # hangus ~10 hari lagi
        self.member.save()
        row = client("admin").get("/api/orders/loyal-customers/").data["customers"][0]
        self.assertEqual(row["expiry_state"], "soon")
        self.assertLessEqual(row["days_until_expiry"], 14)
        self.member.last_order_at = timezone.now() - timedelta(days=120)
        self.member.save()
        row = client("admin").get("/api/orders/loyal-customers/").data["customers"][0]
        self.assertEqual(row["expiry_state"], "expired")
        self.member.points = 0
        self.member.save()
        row = client("admin").get("/api/orders/loyal-customers/").data["customers"][0]
        self.assertEqual(row["expiry_state"], "none")


class VerifyTests(Base):
    def test_correct_pin_returns_points_progress_and_rewards(self):
        self.set_pin()
        r = self.verify("1234")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["points"], 25)
        self.assertEqual(r.data["progress"], {"target_name": "Mochi", "target_cost": 10, "points": 25})
        self.assertEqual(len(r.data["affordable"]), 1)
        self.assertIn("no-store", r["Cache-Control"])

    def test_every_failure_has_identical_response(self):
        self.set_pin()
        CustomerLoyalty.objects.create(phone="081200000002")      # member tanpa PIN
        responses = [
            self.verify("0000"),                                   # PIN salah
            self.verify("1234", phone="081200000002"),             # tanpa PIN
            self.verify("1234", phone="089999999999"),             # tidak terdaftar
            self.verify("", phone=PHONE),                          # kosong
        ]
        for r in responses:
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.data, {"detail": member_pin.NEUTRAL_ERROR})

    def test_lockout_after_five_wrong_then_even_correct_pin_is_rejected(self):
        self.set_pin()
        for _ in range(member_pin.MAX_ATTEMPTS):
            self.assertEqual(self.verify("0000").status_code, 403)
        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.pin_locked_until)
        r = self.verify("1234")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.data, {"detail": member_pin.NEUTRAL_ERROR})   # tidak membocorkan "terkunci"

    def test_lock_expires_and_admin_reset_unlocks(self):
        self.set_pin()
        for _ in range(member_pin.MAX_ATTEMPTS):
            self.verify("0000")
        CustomerLoyalty.objects.filter(pk=self.member.pk).update(pin_locked_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.verify("1234").status_code, 200)
        for _ in range(member_pin.MAX_ATTEMPTS):
            self.verify("0000")
        self.assertEqual(self.verify("1234").status_code, 403)
        self.set_pin("5678")                                       # ganti PIN = buka kunci
        self.assertEqual(self.verify("5678").status_code, 200)

    def test_success_resets_failed_counter(self):
        self.set_pin()
        for _ in range(member_pin.MAX_ATTEMPTS - 1):
            self.verify("0000")
        self.assertEqual(self.verify("1234").status_code, 200)
        for _ in range(member_pin.MAX_ATTEMPTS - 1):
            self.verify("0000")
        self.assertEqual(self.verify("1234").status_code, 200)     # belum terkunci


class PublicLeakTests(Base):
    def test_public_endpoints_do_not_reveal_member_or_points(self):
        public = APIClient()
        r = public.get("/api/orders/check_loyalty_status/", {"phone": PHONE})
        self.assertEqual(r.data, {"is_member": False, "points": 0, "points_expiring_note": None})
        r2 = public.get("/api/orders/point-rewards/available/", {"phone": PHONE})
        self.assertEqual(r2.data["points"], 0)
        self.assertEqual(r2.data["affordable"], [])

    def test_staff_still_sees_points_without_pin(self):
        staff = client("kasir", is_staff=True)
        r = staff.get("/api/orders/check_loyalty_status/", {"phone": PHONE})
        self.assertTrue(r.data["is_member"])
        self.assertEqual(r.data["points"], 25)
        r2 = staff.get("/api/orders/point-rewards/available/", {"phone": PHONE})
        self.assertEqual(r2.data["points"], 25)


class RedeemTests(Base):
    def redeem(self, c, **extra):
        reward = PointReward.objects.get()
        body = {"customer": {"phone": PHONE, "name": "Budi"}, "payment_method": "cash",
                "items": [{"menu_id": self.menu.pk, "quantity": 1}], "redeem_reward_ids": [reward.pk]}
        body.update(extra)
        return c.post("/api/orders/", body, format="json")

    def test_web_redeem_requires_correct_pin(self):
        self.set_pin()
        before = Order.objects.count()
        r = self.redeem(APIClient(), source="web")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.data["error"], member_pin.NEUTRAL_ERROR)
        r = self.redeem(APIClient(), source="web", member_pin="9999")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Order.objects.count(), before)
        self.member.refresh_from_db()
        self.assertEqual(self.member.points, 25)
        self.assertEqual(self.member.pin_failed_attempts, 2)       # salah tetap tercatat (tidak ikut rollback)

        r = self.redeem(APIClient(), source="web", member_pin="1234")
        self.assertEqual(r.status_code, 201, r.data)
        self.member.refresh_from_db()
        self.assertEqual(self.member.points, 15)

    def test_web_redeem_without_pin_set_is_rejected(self):
        r = self.redeem(APIClient(), source="web", member_pin="1234")
        self.assertEqual(r.status_code, 403)

    def test_web_order_without_redeem_needs_no_pin(self):
        r = APIClient().post("/api/orders/", {
            "source": "web", "customer": {"phone": PHONE, "name": "Budi"}, "payment_method": "cash",
            "items": [{"menu_id": self.menu.pk, "quantity": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_pos_redeem_needs_no_pin(self):
        r = self.redeem(client("kasir", is_staff=True), source="pos")
        self.assertEqual(r.status_code, 201, r.data)
        self.member.refresh_from_db()
        self.assertEqual(self.member.points, 15)

    def test_unauthenticated_source_pos_is_treated_as_web(self):
        self.set_pin()
        r = self.redeem(APIClient(), source="pos")                 # tidak login → dianggap web → butuh PIN
        self.assertEqual(r.status_code, 403)
