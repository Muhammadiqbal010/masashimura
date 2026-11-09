"""Tes library Grup Opsi. Jalankan: python manage.py test menu.test_option_groups"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from menu.models import Category, Menu, OptionGroup
from menu.options import resolve_selection


def client(role=None):
    c = APIClient()
    if role:
        u, _ = User.objects.get_or_create(username=role)
        UserProfile.objects.update_or_create(user=u, defaults={"role": role})
        c.force_authenticate(u)
    return c


PEDAS = {"name": "Level Pedas", "required": True, "multiple": False,
         "choices": [{"label": "Nggak pedas", "price": ""}, {"label": "Pedas", "price": 0}]}


class OptionGroupTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Utama")
        self.a = Menu.objects.create(name="Mie A", price=10000, category=cat)
        self.b = Menu.objects.create(name="Mie B", price=12000, category=cat)
        self.admin = client("admin")

    def make(self, **extra):
        r = self.admin.post("/api/option-groups/", {**PEDAS, **extra}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def test_create_with_menus_updates_menu_options(self):
        g = self.make(menu_ids=[self.a.pk, self.b.pk])
        self.assertEqual(g["menu_count"], 2)
        self.a.refresh_from_db()
        self.assertEqual(self.a.options[0]["name"], "Level Pedas")
        self.assertEqual(self.a.options[0]["choices"][0], {"label": "Nggak pedas", "price": 0})
        # server order memakai opsi turunan ini
        chosen, extra, text = resolve_selection(self.a, {"Level Pedas": ["Pedas"]})
        self.assertEqual(text, "Pedas")

    def test_edit_group_propagates_to_all_menus(self):
        g = self.make(menu_ids=[self.a.pk, self.b.pk])
        r = self.admin.patch(f"/api/option-groups/{g['id']}/", {
            "choices": [{"label": "Sedeng", "price": 0}, {"label": "Extra pedas", "price": 1000}],
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        for m in (self.a, self.b):
            m.refresh_from_db()
            self.assertEqual([c["label"] for c in m.options[0]["choices"]], ["Sedeng", "Extra pedas"])

    def test_assign_and_unassign_from_group(self):
        g = self.make(menu_ids=[self.a.pk])
        self.admin.patch(f"/api/option-groups/{g['id']}/", {"menu_ids": [self.b.pk]}, format="json")
        self.a.refresh_from_db(); self.b.refresh_from_db()
        self.assertEqual(self.a.options, [])
        self.assertEqual(len(self.b.options), 1)

    def test_delete_group_cleans_menus(self):
        g = self.make(menu_ids=[self.a.pk])
        self.assertEqual(self.admin.delete(f"/api/option-groups/{g['id']}/").status_code, 204)
        self.a.refresh_from_db()
        self.assertEqual(self.a.options, [])

    def test_menu_save_with_option_group_ids_json_string(self):
        g = self.make()
        r = self.admin.patch(f"/api/menus/{self.a.pk}/", {"option_group_ids": f"[{g['id']}]"}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["option_group_ids"], [g["id"]])
        self.assertEqual(r.data["options"][0]["name"], "Level Pedas")
        # "[]" mencabut semua opsi
        r = self.admin.patch(f"/api/menus/{self.a.pk}/", {"option_group_ids": "[]"}, format="multipart")
        self.assertEqual(r.data["options"], [])

    def test_plain_menu_patch_keeps_options(self):
        g = self.make(menu_ids=[self.a.pk])
        r = self.admin.patch(f"/api/menus/{self.a.pk}/", {"is_available": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(len(self.a.options), 1)

    def test_public_menu_still_exposes_options(self):
        self.make(menu_ids=[self.a.pk])
        rows = client().get("/api/menus/").data
        row = next(r for r in rows if r["id"] == self.a.pk)
        self.assertEqual(row["options"][0]["name"], "Level Pedas")
        self.assertNotIn("option_group_ids", row)

    def test_validation(self):
        self.make()
        for body in (
            {**PEDAS},                                                  # nama dobel
            {**PEDAS, "name": "level pedas"},                           # dobel beda huruf
            {**PEDAS, "name": "Baru", "choices": []},                   # tanpa pilihan
            {**PEDAS, "name": "Baru", "choices": [{"label": "A"}, {"label": "a"}]},
            {**PEDAS, "name": "Baru", "choices": [{"label": "A", "price": -1}]},
        ):
            self.assertEqual(self.admin.post("/api/option-groups/", body, format="json").status_code, 400, body)

    def test_max_groups_per_menu(self):
        for i in range(6):
            self.make(name=f"G{i}", menu_ids=[self.a.pk])
        r = self.admin.post("/api/option-groups/", {**PEDAS, "name": "G7", "menu_ids": [self.a.pk]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_permissions(self):
        self.assertEqual(client().get("/api/option-groups/").status_code, 401)
        self.assertEqual(client().post("/api/option-groups/", PEDAS, format="json").status_code, 401)
