"""
Logika Menu Paket. Semua angka dihitung di server, tidak pernah dipercaya dari frontend.

Harga per sumber order:
  - POS : harga normal = jumlah harga menu (price) x jumlah; harga paket = bundle.price
  - web : harga normal = jumlah harga web tiap menu (markup 1% dibulatkan ke 500);
          harga paket  = web_price(bundle.price), aturan markup yang sama dengan menu.

Saat dipesan, paket dipecah jadi baris OrderItem biasa. Harga paket dibagi proporsional
ke tiap baris menurut harga normalnya, dalam bilangan bulat rupiah, sehingga jumlah semua
baris SAMA PERSIS dengan harga paket. Baris yang tidak habis dibagi dipecah jadi dua baris
(harga satuan n dan n+1) supaya tidak ada selisih sen.
"""
from order.pricing import web_price


def unit_price(menu, source):
    return int(web_price(menu.price)) if source == "web" else int(menu.price)


def bundle_price(bundle, source):
    return int(web_price(bundle.price)) if source == "web" else int(bundle.price)


def normal_price(bundle, source):
    return sum(unit_price(i.menu, source) * i.quantity for i in bundle.items.all())


def pricing(bundle, source):
    """Harga paket, harga normal, dan potongan (0 bila paket tidak lebih murah)."""
    price = bundle_price(bundle, source)
    normal = normal_price(bundle, source)
    savings = normal - price
    return {
        "price": price,
        "normal_price": normal,
        "savings": savings if savings > 0 else 0,
        "not_cheaper": savings <= 0,   # label hemat disembunyikan, admin diberi peringatan
    }


def unavailable_reason(bundle, source):
    """Alasan paket tidak bisa dipesan, atau None bila bisa. Pesan tidak membocorkan menu secret."""
    items = list(bundle.items.all())
    if not items:
        return "Paket belum berisi menu."
    if not bundle.is_available:
        return "Paket sedang habis."
    for i in items:
        if not i.menu.is_active or (source == "web" and i.menu.is_secret):
            return "Paket sedang tidak tersedia."
    for i in items:
        if not i.menu.is_available:
            return f"{i.menu.name} sedang habis."
    return None


def _split_total(total, qty):
    """Bagi `total` rupiah ke `qty` unit bulat. Return [(harga_satuan, jumlah)] yang jumlahnya = total."""
    base, rem = divmod(total, qty)
    rows = []
    if qty - rem > 0:
        rows.append((base, qty - rem))
    if rem > 0:
        rows.append((base + 1, rem))
    return rows


def order_rows(bundle, quantity, source):
    """
    Pecah `quantity` paket jadi baris order: [(menu, harga_satuan, jumlah)].
    Jumlah harga x jumlah seluruh baris == bundle_price * quantity.
    """
    items = list(bundle.items.all())
    target = bundle_price(bundle, source) * quantity
    lines = [(i.menu, unit_price(i.menu, source), i.quantity * quantity) for i in items]
    normal_total = sum(unit * qty for _, unit, qty in lines)

    allocs, used = [], 0
    for idx, (_, unit, qty) in enumerate(lines):
        if idx == len(lines) - 1:
            alloc = target - used
        else:
            alloc = target * (unit * qty) // normal_total
        used += alloc
        allocs.append(alloc)

    rows = []
    for (menu, _, qty), alloc in zip(lines, allocs):
        for price, count in _split_total(alloc, qty):
            rows.append((menu, price, count))
    return rows
