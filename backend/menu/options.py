"""
Opsi pilihan menu (pedas, suhu, ukuran, add-on).

Struktur yang disimpan di Menu.options:
[
  {"name": "Level Pedas", "required": true, "multiple": false,
   "choices": [{"label": "Nggak pedas", "price": 0}, {"label": "Pedas", "price": 0}]},
  {"name": "Tambahan", "required": false, "multiple": true,
   "choices": [{"label": "Extra keju", "price": 3000}]}
]

Format pilihan dari client (order): {"Level Pedas": ["Pedas"], "Tambahan": ["Extra keju"]}

Harga add-on TIDAK kena markup web 1%: angka yang dilihat pelanggan = angka yang ditagih.
"""
from decimal import Decimal, InvalidOperation

MAX_GROUPS = 6
MAX_CHOICES = 15


class OptionError(ValueError):
    """Pesan error ramah-pengguna (Bahasa Indonesia)."""


def _to_price(value, where):
    if value in (None, ""):
        return 0
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise OptionError(f"{where}: harga tidak valid.")
    if d < 0 or d != d.to_integral_value():
        raise OptionError(f"{where}: harga harus bilangan bulat dan tidak negatif.")
    return int(d)


def clean_options(raw):
    """Validasi + normalisasi struktur opsi yang diisi admin. Return list bersih."""
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        raise OptionError("Opsi harus berupa daftar grup.")
    if len(raw) > MAX_GROUPS:
        raise OptionError(f"Maksimal {MAX_GROUPS} grup opsi per menu.")

    cleaned, seen_groups = [], set()
    for group in raw:
        if not isinstance(group, dict):
            raise OptionError("Format grup opsi tidak valid.")
        name = str(group.get("name") or "").strip()
        if not name:
            raise OptionError("Nama grup opsi wajib diisi.")
        if name.lower() in seen_groups:
            raise OptionError(f'Grup opsi "{name}" dobel.')
        seen_groups.add(name.lower())

        raw_choices = group.get("choices")
        if not isinstance(raw_choices, list) or not raw_choices:
            raise OptionError(f'Grup "{name}" minimal punya 1 pilihan.')
        if len(raw_choices) > MAX_CHOICES:
            raise OptionError(f'Grup "{name}" maksimal {MAX_CHOICES} pilihan.')

        choices, seen_labels = [], set()
        for choice in raw_choices:
            if not isinstance(choice, dict):
                raise OptionError(f'Format pilihan di grup "{name}" tidak valid.')
            label = str(choice.get("label") or "").strip()
            if not label:
                raise OptionError(f'Ada pilihan kosong di grup "{name}".')
            if label.lower() in seen_labels:
                raise OptionError(f'Pilihan "{label}" dobel di grup "{name}".')
            seen_labels.add(label.lower())
            choices.append({"label": label, "price": _to_price(choice.get("price"), f"{name} / {label}")})

        cleaned.append({
            "name": name,
            "required": bool(group.get("required")),
            "multiple": bool(group.get("multiple")),
            "choices": choices,
        })
    return cleaned


def resolve_selection(menu, selected):
    """
    Validasi pilihan customer/kasir terhadap opsi menu (sumber kebenaran = database).

    Return (chosen, extra_price, label_text):
      chosen      -> [{"group": "...", "choices": [{"label": "...", "price": 0}]}]  (disimpan di OrderItem)
      extra_price -> Decimal total harga tambahan per 1 porsi
      label_text  -> "Pedas · Extra keju" (digabung ke OrderItem.notes oleh pemanggil)
    Raise OptionError kalau ada yang tidak valid.
    """
    groups = menu.options or []
    selected = selected or {}
    if not isinstance(selected, dict):
        raise OptionError("Format pilihan opsi tidak valid.")

    known = {g["name"] for g in groups}
    for key in selected:
        if key not in known:
            raise OptionError(f'Opsi "{key}" tidak ada di menu {menu.name}.')

    chosen, labels, extra = [], [], 0
    for group in groups:
        picks = selected.get(group["name"]) or []
        if isinstance(picks, str):
            picks = [picks]
        if not isinstance(picks, list):
            raise OptionError(f'Pilihan untuk "{group["name"]}" tidak valid.')
        if len(set(picks)) != len(picks):
            raise OptionError(f'Pilihan dobel di "{group["name"]}".')

        if not picks:
            if group.get("required"):
                raise OptionError(f'Pilih "{group["name"]}" dulu untuk {menu.name}.')
            continue
        if len(picks) > 1 and not group.get("multiple"):
            raise OptionError(f'"{group["name"]}" hanya boleh pilih satu.')

        by_label = {c["label"]: c for c in group["choices"]}
        rows = []
        for label in picks:
            choice = by_label.get(label)
            if not choice:
                raise OptionError(f'Pilihan "{label}" tidak ada di "{group["name"]}".')
            rows.append({"label": choice["label"], "price": choice["price"]})
            labels.append(choice["label"])
            extra += choice["price"]
        chosen.append({"group": group["name"], "choices": rows})

    return chosen, Decimal(extra), " · ".join(labels)