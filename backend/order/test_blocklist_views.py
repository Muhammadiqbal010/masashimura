"""
Tes API Daftar Blokir untuk dashboard (khusus owner).
Jalankan: python manage.py test order.test_blocklist_views
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from order import blocklist
from order.models import BlockedContact, Order

URL = "/api/orders/blocklist/"


def client_for(role, superuser=False):
    u = User.objects.create_user(f"{role}{User.objects.count()}", password="x", is_superuser=superuser)
    UserProfile.objects.update_or_create(user=u, defaults={"role": role})
    c = APIClient()
    c.force_authenticate(u)
    return c


class PermissionTests(TestCase):
    def test_only_owner_can_read_add_or_unblock(self):
        row = BlockedContact.objects.create(kind="phone", value="081234567890")
        for role in ("admin", "kasir"):
            c = client_for(role)
            self.assertEqual(c.get(URL).status_code, 403, role)
            self.assertEqual(c.post(URL, {"target": "081234567891"}, format="json").status_code, 403, role)
            self.assertEqual(c.post(f"{URL}{row.pk}/unblock/").status_code, 403, role)
        self.assertTrue(BlockedContact.objects.get(pk=row.pk).is_active)
        self.assertFalse(BlockedContact.objects.filter(value="081234567891").exists())

    def test_anonymous_is_rejected(self):
        self.assertIn(APIClient().get(URL).status_code, (401, 403))

    def test_owner_by_superuser_or_profile_role(self):
        self.assertEqual(client_for("kasir", superuser=True).get(URL).status_code, 200)
        self.assertEqual(client_for("owner").get(URL).status_code, 200)


class ListTests(TestCase):
    def setUp(self):
        self.c = client_for("owner")
        now = timezone.now()
        blocklist.block("phone", "081234567890", actor="@owner", reason="Order MSH-1", order_number="MSH-1")
        blocklist.block("ip", "114.122.1.2", actor="@owner")
        blocklist.block("ip", "114.122.1.3")
        blocklist.block("ip", "114.122.1.4")
        blocklist.block("phone", "081111111111")
        blocklist.unblock("phone", "081111111111")
        BlockedContact.objects.filter(value="114.122.1.3").update(blocked_at=now - timedelta(days=blocklist.IP_BLOCK_DAYS + 5))
        BlockedContact.objects.filter(value="114.122.1.4").update(blocked_at=now - timedelta(days=blocklist.IP_BLOCK_DAYS - 3))

    def values(self, **params):
        r = self.c.get(URL, params)
        self.assertEqual(r.status_code, 200)
        return {x["value"]: x for x in r.data["results"]}, r.data

    def test_default_lists_only_effective_blocks(self):
        rows, data = self.values()
        self.assertEqual(set(rows), {"081234567890", "114.122.1.2", "114.122.1.4"})
        self.assertEqual(data["view"], "active")

    def test_summary_counts(self):
        _, data = self.values()
        s = data["summary"]
        self.assertEqual((s["active"], s["phone"], s["ip"]), (3, 1, 2))
        self.assertEqual(s["ip_expiring_soon"], 1)        # 114.122.1.4 sisa 3 hari
        self.assertEqual(s["history"], 2)                  # 1 dibuka + 1 kedaluwarsa
        self.assertEqual(s["ip_block_days"], blocklist.IP_BLOCK_DAYS)

    def test_row_details(self):
        rows, _ = self.values()
        phone = rows["081234567890"]
        self.assertEqual(phone["status"], "active")
        self.assertEqual(phone["kind_label"], "Nomor WA")
        self.assertEqual(phone["blocked_by"], "@owner")
        self.assertEqual(phone["order_number"], "MSH-1")
        self.assertIsNone(phone["expires_at"])
        self.assertIsNone(phone["days_left"])
        self.assertIn("ditolak total", phone["effect"])

        soon = rows["114.122.1.4"]
        self.assertTrue(soon["expiring_soon"])
        self.assertIn(soon["days_left"], (3, 4))
        self.assertIsNotNone(soon["expires_at"])
        self.assertIn("QRIS", soon["effect"])
        self.assertFalse(rows["114.122.1.2"]["expiring_soon"])

    def test_history_has_lifted_and_expired(self):
        rows, data = self.values(view="history")
        self.assertEqual(data["view"], "history")
        self.assertEqual(rows["081111111111"]["status"], "lifted")
        self.assertIsNotNone(rows["081111111111"]["unblocked_at"])
        self.assertEqual(rows["114.122.1.3"]["status"], "expired")
        self.assertEqual(len(rows), 2)

    def test_all_view_and_kind_filter(self):
        rows, _ = self.values(view="all")
        self.assertEqual(len(rows), 5)
        rows, _ = self.values(view="all", kind="ip")
        self.assertEqual(set(rows), {"114.122.1.2", "114.122.1.3", "114.122.1.4"})

    def test_unknown_view_falls_back_to_active(self):
        rows, data = self.values(view="ngawur")
        self.assertEqual(data["view"], "active")
        self.assertEqual(len(rows), 3)

    def test_search_by_value_reason_order_actor_and_formatted_phone(self):
        for q in ("5678", "MSH-1", "@owner"):
            rows, _ = self.values(q=q) if q != "5678" else self.values(q="1234")
            self.assertIn("081234567890", rows, q)
        rows, _ = self.values(q="+62 812-3456-7890")
        self.assertEqual(set(rows), {"081234567890"})
        rows, _ = self.values(q="tidak-ada")
        self.assertEqual(rows, {})

    def test_order_activity_and_names(self):
        o = Order.objects.create(order_number="MSH-1", customer_name="Budi", customer_phone="081234567890",
                                 client_ip="114.122.1.2", source="web")
        Order.objects.create(customer_name="Andi", customer_phone="081234567890", source="web")
        Order.objects.create(customer_name="Budi", customer_phone="089999999999", client_ip="114.122.1.2", source="web")
        rows, _ = self.values()
        phone, ip = rows["081234567890"], rows["114.122.1.2"]
        self.assertEqual(phone["order_count"], 2)
        self.assertEqual(sorted(phone["names"]), ["Andi", "Budi"])
        self.assertEqual(phone["order_id"], o.pk)           # order pemicu bisa dibuka dari daftar
        self.assertIsNotNone(phone["last_order_at"])
        self.assertEqual(ip["order_count"], 2)
        self.assertEqual(ip["names"], ["Budi"])
        self.assertEqual(rows["114.122.1.4"]["order_count"], 0)
        self.assertEqual(rows["114.122.1.4"]["names"], [])

    def test_list_runs_constant_queries(self):
        for i in range(30):
            blocklist.block("phone", f"0822000000{i:02d}")
        with self.assertNumQueries(10):   # tetap 10 berapa pun jumlah barisnya (tidak N+1)
            self.c.get(URL)


class AddTests(TestCase):
    def setUp(self):
        self.c = client_for("owner")

    def test_add_phone_normalizes_and_records_actor(self):
        r = self.c.post(URL, {"target": "+62 812-3456-7890", "reason": "Order palsu"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["created"])
        self.assertEqual(r.data["item"]["value"], "081234567890")
        self.assertEqual(r.data["item"]["reason"], "Order palsu")
        self.assertIn("(dashboard)", r.data["item"]["blocked_by"])
        self.assertTrue(blocklist.is_phone_blocked("081234567890"))
        self.assertEqual(r.data["summary"]["active"], 1)

    def test_add_ip_and_default_reason(self):
        r = self.c.post(URL, {"target": "114.122.1.2"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["item"]["kind"], "ip")
        self.assertEqual(r.data["item"]["reason"], "Manual lewat dashboard")
        self.assertTrue(blocklist.is_ip_blocked("114.122.1.2"))

    def test_duplicate_is_not_created_twice(self):
        self.c.post(URL, {"target": "081234567890"}, format="json")
        r = self.c.post(URL, {"target": "0812-3456-7890"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["created"])
        self.assertIn("sudah ada", r.data["message"])
        self.assertEqual(BlockedContact.objects.count(), 1)

    def test_reblocking_a_lifted_number_reactivates_it(self):
        blocklist.block("phone", "081234567890")
        blocklist.unblock("phone", "081234567890")
        r = self.c.post(URL, {"target": "081234567890"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(blocklist.is_phone_blocked("081234567890"))

    def test_invalid_target_is_rejected(self):
        for bad in ("", "halo", "123", "999.999.1.1", None):
            r = self.c.post(URL, {"target": bad}, format="json")
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("detail", r.data)
        self.assertEqual(BlockedContact.objects.count(), 0)

    def test_long_reason_is_trimmed(self):
        r = self.c.post(URL, {"target": "081234567890", "reason": "x" * 600}, format="json")
        self.assertEqual(len(r.data["item"]["reason"]), 255)


class UnblockTests(TestCase):
    def setUp(self):
        self.c = client_for("owner")

    def test_unblock_opens_the_block_and_updates_summary(self):
        blocklist.block("phone", "081234567890")
        row = BlockedContact.objects.get()
        r = self.c.post(f"{URL}{row.pk}/unblock/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["changed"])
        self.assertEqual(r.data["item"]["status"], "lifted")
        self.assertEqual(r.data["summary"]["active"], 0)
        self.assertFalse(blocklist.is_phone_blocked("081234567890"))

    def test_unblock_twice_is_harmless(self):
        blocklist.block("ip", "114.122.1.2")
        row = BlockedContact.objects.get()
        self.c.post(f"{URL}{row.pk}/unblock/")
        r = self.c.post(f"{URL}{row.pk}/unblock/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["changed"])

    def test_unknown_id_is_404(self):
        self.assertEqual(self.c.post(f"{URL}9999/unblock/").status_code, 404)

    def test_unblock_expired_ip_cleans_it_up(self):
        blocklist.block("ip", "114.122.1.2")
        BlockedContact.objects.update(blocked_at=timezone.now() - timedelta(days=blocklist.IP_BLOCK_DAYS + 1))
        row = BlockedContact.objects.get()
        r = self.c.post(f"{URL}{row.pk}/unblock/")
        self.assertEqual(r.data["item"]["status"], "lifted")
