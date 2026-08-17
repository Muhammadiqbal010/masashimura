from django.core.management.base import BaseCommand

from menu.models import Menu
from order.models import PointReward


class Command(BaseCommand):
    help = (
        "Seed katalog reward poin (menu HPP kecil -> point_cost) sesuai daftar "
        "yang udah disepakati. Aman dijalankan berkali-kali (pakai update_or_create, "
        "jadi kalau menu-nya udah ada rewardnya, tinggal di-update point_cost-nya)."
    )

    # (nama_menu, point_cost) — nama HARUS persis sama kayak di database (menu.name),
    # jadi kalau lu rename menu, tinggal update baris ini juga.
    REWARDS = [
        ("Air Mineral", 150),
        ("Nutrisari", 150),
        ("Es Teh Manis", 150),
        ("Kopi Hitam Panas", 150),
        ("Nasi", 150),
        ("Kopi Panas", 180),
        ("Kukubima", 200),
        ("Extrajoss", 200),
        ("Lemon Tea", 250),
        ("Teh Tarik", 250),
        # "Goodday Cappuccino/Freeze" di daftar itu sebenernya 2 menu beda di DB
        ("Goodday Cappucinno", 250),
        ("Goodday Freeze", 250),
        ("Milo", 250),
        # "(polos)" = varian tanpa telur, bedain sama "Indomie Telur Rebus/Goreng"
        ("Indomie Rebus/Goreng", 250),
        ("Kentang Goreng", 350),
        ("Piscok", 350),
        ("Dimsum Original Isi 4", 400),
    ]

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        not_found = []

        for menu_name, point_cost in self.REWARDS:
            menu_qs = Menu.objects.filter(name__iexact=menu_name)
            menu_count = menu_qs.count()

            if menu_count == 0:
                not_found.append(menu_name)
                continue

            if menu_count > 1:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ Ada {menu_count} menu bernama '{menu_name}' — dipakai yang pertama ketemu (id={menu_qs.first().id})."
                ))

            menu = menu_qs.first()

            reward, created = PointReward.objects.update_or_create(
                menu=menu,
                defaults={"point_cost": point_cost, "is_active": True},
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  + Dibuat: {menu.name} -> {point_cost} poin"
                ))
            else:
                updated_count += 1
                self.stdout.write(
                    f"  ~ Diupdate: {menu.name} -> {point_cost} poin"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Selesai. {created_count} reward baru dibuat, {updated_count} diupdate."
        ))

        if not_found:
            self.stdout.write(self.style.ERROR(
                f"\n{len(not_found)} menu TIDAK ketemu di database (cek lagi nama-nya, "
                f"mungkin beda spasi/typo dengan yang di menu.name):"
            ))
            for name in not_found:
                self.stdout.write(self.style.ERROR(f"  - {name}"))
