import json

from django.db import migrations, models


def options_to_groups(apps, schema_editor):
    """Pindahkan opsi yang dulu diketik per menu (Menu.options) ke library OptionGroup.

    Grup yang isinya identik (nama, wajib, banyak, pilihan) dipakai bersama oleh semua menu
    yang punya opsi itu. Kalau ada dua grup bernama sama tapi isi berbeda, yang kedua diberi
    akhiran "(2)", dst, karena nama grup unik. Setelah itu Menu.options dirakit ulang dari
    grup supaya nama yang berubah ikut konsisten."""
    Menu = apps.get_model("menu", "Menu")
    OptionGroup = apps.get_model("menu", "OptionGroup")
    by_signature = {}

    for menu in Menu.objects.all().order_by("id"):
        for g in (menu.options or []):
            if not isinstance(g, dict) or not g.get("name") or not g.get("choices"):
                continue
            sig = json.dumps(
                [g["name"], bool(g.get("required")), bool(g.get("multiple")), g["choices"]],
                sort_keys=True, ensure_ascii=False,
            )
            group = by_signature.get(sig)
            if group is None:
                name, n = g["name"], 2
                while OptionGroup.objects.filter(name__iexact=name).exists():
                    name = f'{g["name"]} ({n})'
                    n += 1
                group = OptionGroup.objects.create(
                    name=name, required=bool(g.get("required")),
                    multiple=bool(g.get("multiple")), choices=g["choices"],
                )
                by_signature[sig] = group
            menu.option_groups.add(group)

    for menu in Menu.objects.all():
        groups = list(menu.option_groups.all().order_by("id"))
        if not groups:
            continue
        rebuilt = [
            {"name": g.name, "required": g.required, "multiple": g.multiple, "choices": g.choices}
            for g in groups
        ]
        if rebuilt != menu.options:
            Menu.objects.filter(pk=menu.pk).update(options=rebuilt)


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0013_menu_created_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="OptionGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("required", models.BooleanField(default=False)),
                ("multiple", models.BooleanField(default=False)),
                ("choices", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddField(
            model_name="menu",
            name="option_groups",
            field=models.ManyToManyField(blank=True, related_name="menus", to="menu.optiongroup"),
        ),
        migrations.RunPython(options_to_groups, migrations.RunPython.noop),
    ]
