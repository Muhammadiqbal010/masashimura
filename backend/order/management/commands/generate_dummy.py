# nama file: generate_dummy.py (di dalam folder management/commands)
import os

# 1. BATASI PENGGUNAAN MEMORI OPENBLAS (Wajib di bagian paling atas)
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, Max, Min

from menu.models import Menu
from order.models import Order, OrderItem, LoyaltySettings, CustomerLoyalty, StoreSettings


# Toko libur rutin tiap Minggu (6=Minggu, ikut konvensi dayofweek Python/pandas)
# -- konsisten sama field StoreSettings.operating_hours yang dipakai fitur
# ML (is_regular_closed_day) di order/prediction/data.py.
CLOSED_WEEKDAY = 6

# Selain libur rutin, tambahin beberapa hari libur INSIDENTAL (tanggal
# merah/cuti bersama) biar datanya lebih realistis -- toko riil kadang
# tutup mendadak, bukan cuma di hari libur rutin.
N_RANDOM_HOLIDAYS = 6


class Command(BaseCommand):
    help = "Generate 10,000 data dummy realistis dengan optimasi memori hemat RAM."

    def handle(self, *args, **options):
        # 1. BERSIHKAN SEMUA DATA LAMA
        self.stdout.write(self.style.WARNING("Menghapus semua data order dan loyalty lama dari database..."))
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CustomerLoyalty.objects.all().delete()

        # 1b. Set jadwal operasional toko: buka tiap hari 08:00-22:00,
        # KECUALI CLOSED_WEEKDAY yang emang libur rutin. Ini WAJIB diisi
        # supaya fitur is_regular_closed_day di model ML kebaca konsisten
        # sama data dummy yang di-generate di bawah.
        store_settings = StoreSettings.get()
        store_settings.operating_hours = {
            str(dow): (None if dow == CLOSED_WEEKDAY else {"open": "08:00", "close": "22:00"})
            for dow in range(7)
        }
        store_settings.save(update_fields=["operating_hours"])
        self.stdout.write(self.style.SUCCESS(
            f"Jadwal toko diset: libur rutin tiap hari ke-{CLOSED_WEEKDAY} (0=Senin, ..., 6=Minggu)."
        ))

        # 2. Ambil semua menu yang tersedia
        menus = list(Menu.objects.all())
        if not menus:
            self.stdout.write(
                self.style.ERROR("Database menu kosong! Masukkan data menu terlebih dahulu.")
            )
            return

        settings = LoyaltySettings.get_settings()
        rate_poin = settings.rupiah_per_point or 10000

        # 3. Definisikan Pool Pelanggan Realistis
        loyal_customers = [
            {"phone": "081234567890", "name": "Budi Setiawan"},
            {"phone": "089876543210", "name": "Bambang Sahputra"},
            {"phone": "085711223344", "name": "Rian Hidayat"},
            {"phone": "085761879278", "name": "Dadang Kusnandar"},
            {"phone": "088900223421", "name": "Ismail Komar"},
        ]

        first_names = ["Andi", "Siti", "Dewi", "Reza", "Fajar", "Rina", "Dedi", "Ayu", "Hendra", "Nia", "Eko", "Maya", "Rizky", "Dian", "Agus"]
        last_names = ["Pratama", "Lestari", "Kusuma", "Nugroho", "Santoso", "Putri", "Hidayat", "Saputra", "Wibowo", "Wijaya"]

        random.seed(42)
        casual_customers = []
        for _ in range(100):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"08{random.choice(['12', '13', '57', '81', '85'])}{random.randint(10000000, 99999999)}"
            casual_customers.append({"phone": phone, "name": name})

        # MAPPING KONSISTENSI NAMA
        phone_name_map = {cust["phone"]: cust["name"] for cust in loyal_customers + casual_customers}

        registered_customer_pool = (casual_customers * 2) + (loyal_customers * 6)
        pos_customer_pool = ([{"phone": "", "name": ""}] * 50) + registered_customer_pool

        TOTAL_TARGET = 10000
        BATCH_SIZE = 500  # Diturunkan dari 1000 ke 500 agar lebih ramah memori
        now = timezone.now()

        # Bangun daftar tanggal LIBUR dalam window 181 hari histori: hari
        # libur rutin (tiap CLOSED_WEEKDAY) + beberapa hari libur insidental
        # random (tanggal merah/cuti bersama), biar datanya kelihatan seperti
        # toko riil yang emang nggak buka 24/7/365.
        history_start = (now - timedelta(days=180)).date()
        all_dates = [history_start + timedelta(days=i) for i in range(181)]
        regular_closed_dates = {d for d in all_dates if d.weekday() == CLOSED_WEEKDAY}
        open_dates = [d for d in all_dates if d not in regular_closed_dates]
        random_holiday_dates = set(
            random.sample(open_dates, k=min(N_RANDOM_HOLIDAYS, len(open_dates)))
        )
        closed_dates = regular_closed_dates | random_holiday_dates
        self.stdout.write(self.style.SUCCESS(
            f"Total hari libur dalam 181 hari: {len(closed_dates)} "
            f"({len(regular_closed_dates)} rutin + {len(random_holiday_dates)} insidental)."
        ))

        self.stdout.write(self.style.SUCCESS(f"Memulai pembuatan {TOTAL_TARGET} data transaksi..."))

        total_created = 0

        for batch_start in range(0, TOTAL_TARGET, BATCH_SIZE):
            current_batch_size = min(BATCH_SIZE, TOTAL_TARGET - batch_start)
            orders_to_create = []
            
            for i in range(current_batch_size):
                source = random.choice(["web", "pos"])
                
                if source == "web":
                    cust_selected = random.choice(registered_customer_pool)
                    cust_phone = cust_selected["phone"]
                    cust_name = phone_name_map[cust_phone]
                else:
                    cust_selected = random.choice(pos_customer_pool)
                    cust_phone = cust_selected["phone"]
                    cust_name = phone_name_map.get(cust_phone, "") if cust_phone else ""

                # Tarik ulang tanggal kalau kebetulan jatuh di hari libur --
                # toko yang tutup nggak mungkin ada order beneran hari itu.
                for _attempt in range(30):
                    random_days = random.randint(0, 180)
                    candidate_date = (now - timedelta(days=random_days)).date()
                    if candidate_date not in closed_dates:
                        break
                # (kalau 30x tarikan tetap kena libur -- kemungkinannya sangat
                # kecil -- ya sudah, dipakai apa adanya daripada infinite loop)

                base_date = (now - timedelta(days=random_days)).replace(hour=0, minute=0, second=0, microsecond=0)
                random_time_seconds = random.randint(11 * 3600, int(22.5 * 3600))
                order_date = base_date + timedelta(seconds=random_time_seconds)

                order_idx = batch_start + i + 1
                unique_order_num = f"MSM-{order_date.strftime('%Y%m%d')}-{order_idx:05d}"

                orders_to_create.append(
                    Order(
                        order_number=unique_order_num,
                        source=source,
                        status="completed",
                        payment_status="paid",
                        payment_method=random.choice(["cash", "qris", "qris_manual"]),
                        is_deferred_payment=False,
                        customer_name=cust_name,
                        customer_phone=cust_phone,
                        table_number=str(random.randint(1, 15)),
                        kasir_name=random.choice(["Irfan Setiawan Dawolo", "Muhammad Iqbal", "Sistem"]),
                        created_at=order_date,
                    )
                )

            # Bulk Insert Order
            created_orders = Order.objects.bulk_create(orders_to_create)

            items_to_create = []
            orders_to_update = []

            for order in created_orders:
                selected_menus = random.sample(menus, k=random.randint(2, min(4, len(menus))))
                total_price = Decimal("0")

                for menu in selected_menus:
                    qty = random.randint(1, 3)
                    item_price = menu.price
                    subtotal = item_price * qty
                    total_price += subtotal

                    items_to_create.append(
                        OrderItem(
                            order=order,
                            menu=menu,
                            quantity=qty,
                            price=item_price,
                        )
                    )
                
                order.total_price = total_price
                orders_to_update.append(order)

            OrderItem.objects.bulk_create(items_to_create)
            Order.objects.bulk_update(orders_to_update, fields=["total_price"])

            total_created += current_batch_size
            self.stdout.write(f"-> Berhasil generate {total_created}/{TOTAL_TARGET} order...")

        # --- REBUILD SALDO POIN PELANGGAN (OPTIMASI MEMORI DENGAN AGREGASI SQL) ---
        self.stdout.write(self.style.WARNING("\nMerekonstruksi ulang saldo poin dan histori belanja..."))
        
        # Menggunakan GROUP BY di level Database (jauh lebih cepat dan hemat RAM)
        loyalty_data = (
            Order.objects.exclude(customer_phone="")
            .filter(payment_status="paid")
            .values("customer_phone")
            .annotate(
                total_spent=Sum("total_price"),
                total_orders=Count("id"),
                last_order_at=Max("created_at"),
            )
        )

        loyalty_records = []
        for item in loyalty_data:
            phone = item["customer_phone"]
            total_spent = int(item["total_spent"] or 0)
            calculated_points = total_spent // rate_poin
            
            loyalty_records.append(
                CustomerLoyalty(
                    phone=phone,
                    name=phone_name_map.get(phone, "Pelanggan"),
                    points=calculated_points,
                    total_orders=item["total_orders"],
                    total_spent=total_spent,
                    last_order_at=item["last_order_at"],
                )
            )

        CustomerLoyalty.objects.bulk_create(loyalty_records)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[SUKSES] Berhasil generate {total_created} order tanpa kendala memori!"
            )
        )