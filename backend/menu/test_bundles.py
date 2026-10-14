"""Tes Menu Paket. Jalankan: python manage.py test menu.test_bundles"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu import bundles
from menu.models import Category, Menu, MenuBundle, MenuBundleItem
from order.models import Order, OrderItem
from order.pricing import web_price


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
        self.katsu = Menu.objects.create(name="Katsu", price=20000, category=cat)
        self.teh = Menu.objects.create(name="Es Teh", price=5000, category=cat)
        self.mochi = Menu.objects.create(name="Mochi", price=7000, category=cat)
        self.bundle = self.make("Paket Hemat", 23000, [(self.katsu, 1), (self.teh, 1)])

    def make(self, name, price, lines):
        b = MenuBundle.objects.create(name=name, price=price)
        for menu, qty in lines:
            MenuBundleItem.objects.create(bundle=b, menu=menu, quantity=qty)
        return b


class PricingTests(Base):
    def test_savings_from_bundle_price_only(self):
        p = bundles.pricing(self.bundle, "pos")
        self.assertEqual((p["price"], p["normal_price"], p["savings"]), (23000, 25000, 2000))
        self.assertFalse(p["not_cheaper"])

    def test_web_uses_same_markup_rule_as_menu(self):
        p = bundles.pricing(self.bundle, "web")
        self.assertEqual(p["price"], int(web_price(23000)))
        self.assertEqual(p["normal_price"], int(web_price(20000) + web_price(5000)))

    def test_not_cheaper_hides_saving(self):
        b = self.make("Mahal", 30000, [(self.katsu, 1), (self.teh, 1)])
        p = bundles.pricing(b, "pos")
        self.assertTrue(p["not_cheaper"])
        self.assertEqual(p["savings"], 0)

    def test_rows_sum_exactly_to_bundle_price(self):
        # harga yang tidak habis dibagi dipecah jadi dua baris, total tetap persis
        for qty in (1, 2, 3, 7):
            for source in ("pos", "web"):
                b = self.make(f"X{qty}{source}", 22222, [(self.katsu, 2), (self.teh, 3), (self.mochi, 1)])
                rows = bundles.order_rows(b, qty, source)
                self.assertEqual(sum(p * c for _, p, c in rows), bundles.bundle_price(b, source) * qty)
                self.assertEqual(sum(c for _, _, c in rows), 6 * qty)
                self.assertTrue(all(p >= 0 and c > 0 for _, p, c in rows))


class AvailabilityTests(Base):
    def test_menu_habis_or_inactive_blocks_bundle(self):
        self.assertIsNone(bundles.unavailable_reason(self.bundle, "pos"))
        self.teh.is_available = False
        self.teh.save()
        self.assertIn("Es Teh", bundles.unavailable_reason(MenuBundle.objects.get(pk=self.bundle.pk), "web"))
        self.teh.is_available, self.teh.is_active = True, False
        self.teh.save()
        self.assertIsNotNone(bundles.unavailable_reason(MenuBundle.objects.get(pk=self.bundle.pk), "pos"))

    def test_manual_toggle(self):
        self.bundle.is_available = False
        self.bundle.save()
        self.assertEqual(bundles.unavailable_reason(self.bundle, "web"), "Paket sedang habis.")


class ApiTests(Base):
    def body(self, **kw):
        d = {"name": "Paket Baru", "price": 12000,
             "items": [{"menu": self.teh.pk, "quantity": 1}, {"menu": self.mochi.pk, "quantity": 1}]}
        d.update(kw)
        return d

    def test_admin_crud_and_kasir_cannot_write(self):
        r = client("admin").post("/api/bundles/", self.body(), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["pos"]["normal_price"], 12000)
        self.assertEqual(client("kasir").post("/api/bundles/", self.body(), format="json").status_code, 403)
        self.assertEqual(client().post("/api/bundles/", self.body(), format="json").status_code, 403)
        pk = r.data["id"]
        r = client("admin").patch(f"/api/bundles/{pk}/", {"price": 11000}, format="json")
        self.assertEqual(r.data["pos"]["savings"], 1000)
        self.assertEqual(client("admin").delete(f"/api/bundles/{pk}/").status_code, 204)

    def test_validation(self):
        a = client("admin")
        secret = Menu.objects.create(name="Rahasia", price=9000, is_secret=True)
        spicy = Menu.objects.create(name="Pedas", price=9000, options=[
            {"name": "Level", "required": True, "multiple": False, "choices": [{"label": "Pedas", "price": 0}]}])
        for items in (
            [],
            [{"menu": self.teh.pk, "quantity": 1}],                                   # kurang dari 2 porsi
            [{"menu": self.teh.pk, "quantity": 1}, {"menu": self.teh.pk, "quantity": 1}],  # dobel
            [{"menu": self.teh.pk, "quantity": 1}, {"menu": secret.pk, "quantity": 1}],
            [{"menu": self.teh.pk, "quantity": 1}, {"menu": spicy.pk, "quantity": 1}],
        ):
            r = a.post("/api/bundles/", self.body(items=items), format="json")
            self.assertEqual(r.status_code, 400, items)
        self.assertEqual(a.post("/api/bundles/", self.body(price=0), format="json").status_code, 400)

    def test_public_sees_web_prices_only(self):
        r = client().get("/api/bundles/")
        self.assertEqual(r.status_code, 200)
        row = r.data[0] if isinstance(r.data, list) else r.data["results"][0]
        self.assertEqual(row["price"], int(web_price(23000)))
        self.assertNotIn("pos", row)
        self.assertNotIn("web", row)

    def test_public_hides_bundle_with_inactive_menu(self):
        self.teh.is_active = False
        self.teh.save()
        r = client().get("/api/bundles/")
        rows = r.data if isinstance(r.data, list) else r.data["results"]
        self.assertEqual(rows, [])

    def test_menu_in_bundle_cannot_be_deleted(self):
        r = client("admin", is_staff=True).delete(f"/api/menus/{self.katsu.pk}/")
        self.assertEqual(r.status_code, 409)
        self.assertTrue(Menu.objects.filter(pk=self.katsu.pk).exists())
        self.assertIn("Paket Hemat", r.data["detail"])


class OrderTests(Base):
    def pos_order(self, **kw):
        body = {"source": "pos", "payment_method": "cash", "bundles": [{"bundle_id": self.bundle.pk, "quantity": 2}]}
        body.update(kw)
        return client("kasir", is_staff=True).post("/api/orders/", body, format="json")

    def test_pos_bundle_split_into_normal_items(self):
        r = self.pos_order()
        self.assertEqual(r.status_code, 201, r.data)
        o = Order.objects.get(pk=r.data["id"])
        self.assertEqual(int(o.total_price), 46000)
        self.assertEqual(int(o.subtotal), 46000)
        rows = list(o.items.order_by("id"))
        self.assertEqual({i.menu.name for i in rows}, {"Katsu", "Es Teh"})
        self.assertTrue(all(i.bundle_name == "Paket Hemat" for i in rows))
        self.assertEqual(sum(i.quantity for i in rows), 4)
        self.assertEqual(sum(i.price * i.quantity for i in rows), 46000)

    def test_web_price_is_computed_by_server_and_client_price_is_ignored(self):
        r = APIClient().post("/api/orders/", {
            "source": "web", "payment_method": "cash",
            "bundles": [{"bundle_id": self.bundle.pk, "quantity": 1, "price": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(int(Order.objects.get(pk=r.data["id"]).total_price), int(web_price(23000)))

    def test_mixed_with_normal_items_and_promo_on_total_after_bundle(self):
        from datetime import timedelta
        from django.utils import timezone
        from promotions.models import Promo
        promo = Promo.objects.create(code="P10", discount_type="percentage", discount_value=10,
                                     valid_from=timezone.now() - timedelta(days=1),
                                     valid_until=timezone.now() + timedelta(days=1))
        r = self.pos_order(items=[{"menu_id": self.mochi.pk, "quantity": 1}], promo_id=promo.pk)
        self.assertEqual(r.status_code, 201, r.data)
        o = Order.objects.get(pk=r.data["id"])
        self.assertEqual(int(o.subtotal), 2 * 23000 + 7000)
        self.assertEqual(int(o.promo_discount_amount), 5300)
        self.assertEqual(int(o.total_price), 53000 - 5300)

    def test_unavailable_bundle_rejected_and_rolls_back(self):
        self.teh.is_available = False
        self.teh.save()
        before = Order.objects.count()
        r = self.pos_order()
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Order.objects.count(), before)

    def test_bad_input(self):
        self.assertEqual(self.pos_order(bundles=[{"bundle_id": 9999, "quantity": 1}]).status_code, 400)
        self.assertEqual(self.pos_order(bundles=[{"bundle_id": self.bundle.pk, "quantity": 0}]).status_code, 400)
        self.assertEqual(self.pos_order(bundles=[{"bundle_id": "x"}]).status_code, 400)
        self.assertEqual(self.pos_order(bundles=[]).status_code, 400)   # tanpa item sama sekali

    def test_deleting_bundle_keeps_order_history(self):
        r = self.pos_order()
        self.bundle.delete()
        o = Order.objects.get(pk=r.data["id"])
        self.assertEqual(o.items.count(), 2)
        self.assertEqual(int(o.total_price), 46000)

    def test_add_item_does_not_merge_into_bundle_row(self):
        r = client("kasir", is_staff=True).post("/api/orders/", {
            "source": "pos", "payment_method": "cash", "payment_status": "pending",
            "bundles": [{"bundle_id": self.bundle.pk, "quantity": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        oid = r.data["id"]
        client("kasir", is_staff=True).post(f"/api/orders/{oid}/items/", {"menu_id": self.teh.pk, "quantity": 1}, format="json")
        self.assertEqual(OrderItem.objects.filter(order_id=oid, menu=self.teh).count(), 2)
